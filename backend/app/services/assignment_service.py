"""Service orchestrating course assignment optimization, jobs, explain, fairness, conflicts, and repairs."""

from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.repositories import (
    get_assignment_repository,
    get_constraint_repository,
    get_course_repository,
    get_faculty_repository,
    get_override_repository,
    get_resource_repository,
    get_section_repository,
    get_timeslot_repository,
)
from app.repositories.base import Repository
from app.schemas.assignment import Assignment
from app.schemas.common import AssignmentSource, ViolationSeverity
from app.schemas.constraint import ConstraintRule, ValidationScenario
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.override import Override
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.services.audit_service import AuditService
from app.services.constraint_engine import ConstraintEngine
from ml.fit.scoring import check_hc01, fit
from ml.optimizer.cpsat import SolveResult, solve_cpsat
from ml.optimizer.explain import ExplanationResult, generate_explanation
from ml.optimizer.fairness import compute_fairness_summary
from ml.optimizer.greedy import solve_greedy
from ml.optimizer.repair import RepairAlternative, generate_repairs

logger = logging.getLogger("app.services.assignment")


class AssignmentService:
    """Orchestrates solver jobs, explanation, fairness metrics, conflicts, and repair routines."""

    _active_job: dict[str, Any] | None = None
    _jobs: dict[str, dict[str, Any]] = {}
    _lock = asyncio.Lock()

    def __init__(
        self,
        assignment_repo: Repository[Assignment] | None = None,
        faculty_repo: Repository[Faculty] | None = None,
        course_repo: Repository[Course] | None = None,
        section_repo: Repository[Section] | None = None,
        resource_repo: Repository[Resource] | None = None,
        timeslot_repo: Repository[TimeSlot] | None = None,
        constraint_repo: Repository[ConstraintRule] | None = None,
        override_repo: Repository[Override] | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.assignment_repo = assignment_repo or get_assignment_repository()
        self.faculty_repo = faculty_repo or get_faculty_repository()
        self.course_repo = course_repo or get_course_repository()
        self.section_repo = section_repo or get_section_repository()
        self.resource_repo = resource_repo or get_resource_repository()
        self.timeslot_repo = timeslot_repo or get_timeslot_repository()
        self.constraint_repo = constraint_repo or get_constraint_repository()
        self.override_repo = override_repo or get_override_repository()
        self.audit_service = audit_service or AuditService()
        self.constraint_engine = ConstraintEngine()

    @classmethod
    def get_job(cls, job_id: str) -> dict[str, Any]:
        job = cls._jobs.get(job_id)
        if not job:
            raise NotFoundError(f"Optimization job '{job_id}' not found")
        return job

    async def start_optimization_job(
        self,
        term: str,
        method: Literal["cpsat", "greedy"] = "cpsat",
        forecast_mode: Literal["p50", "p90"] = "p50",
        weights: dict[str, float] | None = None,
        time_limit: float = 20.0,
        actor_id: str = "system",
        background_tasks: Any = None,
    ) -> str:
        """Launch background optimization job enforcing single active job constraint."""
        async with self._lock:
            if self._active_job is not None and self._active_job.get("status") == "RUNNING":
                raise ConflictError("An optimization job is currently running. Please wait for it to finish.")

            job_id = f"job-{uuid.uuid4().hex[:10]}"
            job_state = {
                "id": job_id,
                "term": term,
                "method": method,
                "forecast_mode": forecast_mode,
                "status": "RUNNING",
                "created_at": datetime.now(UTC).isoformat(),
                "completed_at": None,
                "result": None,
                "error": None,
                "actor_id": actor_id,
            }
            self._jobs[job_id] = job_state
            self._active_job = job_state

        # Audit log job request
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="OPTIMIZE_JOB_START",
            entity="assignment",
            payload={"job_id": job_id, "term": term, "method": method, "forecast_mode": forecast_mode},
        )

        # Trigger background execution via background_tasks or asyncio task
        if background_tasks is not None:
            background_tasks.add_task(
                self._run_job_worker,
                job_id=job_id,
                term=term,
                method=method,
                forecast_mode=forecast_mode,
                weights=weights,
                time_limit=time_limit,
                actor_id=actor_id,
            )
        else:
            asyncio.create_task(
                self._run_job_worker(
                    job_id=job_id,
                    term=term,
                    method=method,
                    forecast_mode=forecast_mode,
                    weights=weights,
                    time_limit=time_limit,
                    actor_id=actor_id,
                )
            )

        return job_id

    async def _run_job_worker(
        self,
        job_id: str,
        term: str,
        method: str,
        forecast_mode: str,
        weights: dict[str, float] | None,
        time_limit: float,
        actor_id: str,
    ) -> None:
        try:
            logger.info(f"Starting optimization worker for job {job_id} on term '{term}' with {method}")

            # 1. Fetch domain data
            faculty_list = await self.faculty_repo.get_all()
            course_list = await self.course_repo.get_all()
            all_sections = await self.section_repo.get_all()
            resource_list = await self.resource_repo.get_all()
            timeslot_list = await self.timeslot_repo.get_all()
            prev_assignments = await self.assignment_repo.get_all()

            # Filter sections for term
            sections_for_term = [s for s in all_sections if s.term.lower() == term.lower()]
            if not sections_for_term:
                logger.info(f"No sections explicitly matching term '{term}'. Running across all sections.")
                sections_for_term = all_sections

            # Merge weights from DB constraint rules if not provided
            rule_weights = {}
            if not weights:
                try:
                    db_rules = await self.constraint_repo.get_all()
                    for r in db_rules:
                        if not r.is_hard and r.weight is not None:
                            rule_weights[r.rule_id] = r.weight
                except Exception as exc:
                    logger.debug(f"Could not load custom weights: {exc}")
            else:
                rule_weights = weights

            # 2. Run solver in worker thread to not block asyncio loop
            demand_prof = forecast_mode.upper()
            if method == "greedy":
                res = await asyncio.to_thread(
                    solve_greedy,
                    faculty=faculty_list,
                    courses=course_list,
                    sections=sections_for_term,
                    resources=resource_list,
                    timeslots=timeslot_list,
                    previous_assignments=prev_assignments,
                    weights=rule_weights,
                    demand_profile=demand_prof,
                    run_id=job_id,
                )
            else:
                res = await asyncio.to_thread(
                    solve_cpsat,
                    faculty=faculty_list,
                    courses=course_list,
                    sections=sections_for_term,
                    resources=resource_list,
                    timeslots=timeslot_list,
                    previous_assignments=prev_assignments,
                    weights=rule_weights,
                    demand_profile=demand_prof,
                    time_limit_seconds=time_limit,
                    run_id=job_id,
                )

            # 3. Post-process assignments with ConstraintEngine
            validation_scenario = ValidationScenario(
                faculty=faculty_list,
                courses=course_list,
                sections=sections_for_term,
                resources=resource_list,
                timeslots=timeslot_list,
                previous_assignments=prev_assignments,
            )

            engine = ConstraintEngine()
            violations = engine.validate(res.assignments, validation_scenario)

            # Map violations to assignments
            viols_by_section: dict[str, list[str]] = {}
            for v in violations:
                for eid in v.entity_ids:
                    viols_by_section.setdefault(eid, []).append(v.rule_id)

            persisted_assignments: list[Assignment] = []
            for asgn in res.assignments:
                sec_viols = viols_by_section.get(asgn.section_id, [])
                # Update rule_ids_violated
                updated_asgn = asgn.model_copy(
                    update={
                        "rule_ids_violated": list(set(asgn.rule_ids_violated + sec_viols)),
                    }
                )
                persisted_assignments.append(updated_asgn)

            # Persist assignments if feasible
            if res.feasible and persisted_assignments:
                # Remove prior assignments for these sections
                sec_ids = {a.section_id for a in persisted_assignments}
                all_prior = await self.assignment_repo.get_all()
                kept = [a for a in all_prior if a.section_id not in sec_ids]
                await self.assignment_repo.bulk_replace(kept + persisted_assignments)
                logger.info(f"Persisted {len(persisted_assignments)} assignments for job {job_id}")

            async with self._lock:
                self._jobs[job_id]["status"] = "COMPLETED"
                self._jobs[job_id]["completed_at"] = datetime.now(UTC).isoformat()
                self._jobs[job_id]["result"] = {
                    "feasible": res.feasible,
                    "status": res.status,
                    "objective_value": res.objective_value,
                    "assignments_count": len(res.assignments),
                    "solve_time_seconds": res.solve_time_seconds,
                    "fairness": res.fairness,
                    "fit_summary": res.fit_summary,
                    "blocking_rule_ids": res.blocking_rule_ids,
                    "explanation": res.explanation,
                }
                self._active_job = None

            await self.audit_service.log_event(
                actor_id=actor_id,
                action="OPTIMIZE_JOB_COMPLETE",
                entity="assignment",
                payload={"job_id": job_id, "feasible": res.feasible, "count": len(res.assignments)},
            )

        except Exception as exc:
            logger.exception(f"Job {job_id} failed: {exc}")
            async with self._lock:
                self._jobs[job_id]["status"] = "FAILED"
                self._jobs[job_id]["completed_at"] = datetime.now(UTC).isoformat()
                self._jobs[job_id]["error"] = str(exc)
                self._active_job = None

            await self.audit_service.log_event(
                actor_id=actor_id,
                action="OPTIMIZE_JOB_FAIL",
                entity="assignment",
                payload={"job_id": job_id, "error": str(exc)},
            )

    async def get_assignments(self, term: str | None = None, faculty_id: str | None = None) -> list[Assignment]:
        """Fetch assignments filtered by term and optional faculty_id."""
        all_assignments = await self.assignment_repo.get_all()
        if not term and not faculty_id:
            return all_assignments

        section_map = {}
        if term:
            all_sections = await self.section_repo.get_all()
            section_map = {s.id: s for s in all_sections}

        filtered = []
        for a in all_assignments:
            if faculty_id and a.faculty_id != faculty_id:
                continue
            if term:
                sec = section_map.get(a.section_id)
                if not sec or sec.term.lower() != term.lower():
                    continue
            filtered.append(a)
        return filtered

    async def explain_assignment(self, assignment_id: str) -> dict[str, Any]:
        """Explain why the faculty member was assigned, show top-3 alternatives and blocked reasons."""
        asgn = await self.assignment_repo.get(assignment_id)
        if not asgn:
            raise NotFoundError(f"Assignment '{assignment_id}' not found")

        section = await self.section_repo.get(asgn.section_id)
        if not section:
            raise NotFoundError(f"Section '{asgn.section_id}' not found")

        course = await self.course_repo.get(section.course_id)
        if not course:
            raise NotFoundError(f"Course '{section.course_id}' not found")

        faculty_list = await self.faculty_repo.get_all()
        assigned_faculty = next((f for f in faculty_list if f.id == asgn.faculty_id), None)

        # Evaluate all other faculty for this course/section
        scored_alternatives = []
        for fac in faculty_list:
            if fac.id == asgn.faculty_id:
                continue

            # Check HC-01
            hc01_ok, hc01_reason = check_hc01(fac, course)
            # Check HC-04
            leave_terms = fac.leave_terms or []
            on_leave = section.term in leave_terms
            unavail_slots = fac.unavailable_slots or []
            slot_clash = bool(section.time_slot_id and section.time_slot_id in unavail_slots)

            fit_res = fit(fac, course)
            fit_score = float(fit_res)

            blocked_reasons = []
            if not hc01_ok:
                blocked_reasons.append(f"HC-01: {hc01_reason}")
            if on_leave:
                blocked_reasons.append(f"HC-04: On sabbatical leave in {section.term}")
            if slot_clash:
                blocked_reasons.append(f"HC-04: Unavailable during time slot {section.time_slot_id}")

            scored_alternatives.append({
                "faculty_id": fac.id,
                "name": fac.name,
                "rank": fac.rank.value if hasattr(fac.rank, "value") else str(fac.rank),
                "fit_score": round(fit_score, 4),
                "fit_breakdown": fit_res.breakdown,
                "is_eligible": len(blocked_reasons) == 0,
                "blocked_reasons": blocked_reasons,
            })

        # Sort: eligible first (by fit_score desc), then ineligible (by fit_score desc)
        scored_alternatives.sort(key=lambda x: (1 if x["is_eligible"] else 0, x["fit_score"]), reverse=True)
        top_alternatives = scored_alternatives[:3]

        return {
            "assignment_id": asgn.id,
            "section_id": asgn.section_id,
            "course_code": course.code,
            "course_title": course.title,
            "chosen_faculty": {
                "faculty_id": assigned_faculty.id if assigned_faculty else asgn.faculty_id,
                "name": assigned_faculty.name if assigned_faculty else "Unknown",
                "fit_score": asgn.fit_score,
                "fit_breakdown": asgn.fit_breakdown,
                "rule_ids_satisfied": asgn.rule_ids_satisfied,
                "rule_ids_violated": asgn.rule_ids_violated,
                "rationale": (
                    f"Assigned by {asgn.source.value} matching course requirements with expertise score "
                    f"{asgn.fit_score:.2f} while satisfying departmental load and schedule constraints."
                ),
            },
            "top_alternatives": top_alternatives,
            "total_candidates_evaluated": len(faculty_list),
        }

    async def get_fairness_metrics(self, term: str) -> dict[str, Any]:
        """Calculate workload distribution metrics, Gini, standard deviation, and max-min gap for term."""
        faculty_list = await self.faculty_repo.get_all()
        course_list = await self.course_repo.get_all()
        course_map = {c.id: c for c in course_list}

        assignments_for_term = await self.get_assignments(term=term)
        sections = await self.section_repo.get_all()
        section_map = {s.id: s for s in sections}

        loads_by_faculty: dict[str, float] = {f.id: 0.0 for f in faculty_list}
        faculty_ranks: dict[str, str] = {
            f.id: f.rank.value if hasattr(f.rank, "value") else str(f.rank) for f in faculty_list
        }

        for a in assignments_for_term:
            sec = section_map.get(a.section_id)
            if sec:
                crs = course_map.get(sec.course_id)
                chours = crs.contact_hours if crs else 3.0
                loads_by_faculty[a.faculty_id] = loads_by_faculty.get(a.faculty_id, 0.0) + chours

        summary = compute_fairness_summary(loads_by_faculty, faculty_ranks)
        summary["term"] = term
        summary["faculty_loads"] = [
            {
                "faculty_id": f.id,
                "name": f.name,
                "rank": faculty_ranks.get(f.id, "Faculty"),
                "assigned_contact_hours": round(loads_by_faculty.get(f.id, 0.0), 2),
                "max_weekly_load_hours": f.max_weekly_load_hours,
                "load_ratio": round(loads_by_faculty.get(f.id, 0.0) / max(f.max_weekly_load_hours, 1.0), 2),
            }
            for f in faculty_list
        ]
        return summary

    async def get_conflicts_and_repairs(self, term: str) -> dict[str, Any]:
        """Validate current term assignments, detect violations, and synthesize repair alternatives."""
        faculty_list = await self.faculty_repo.get_all()
        course_list = await self.course_repo.get_all()
        all_sections = await self.section_repo.get_all()
        resource_list = await self.resource_repo.get_all()
        timeslot_list = await self.timeslot_repo.get_all()
        prev_assignments = await self.assignment_repo.get_all()

        sections_for_term = [s for s in all_sections if s.term.lower() == term.lower()] or all_sections
        assignments_for_term = await self.get_assignments(term=term)

        scenario = ValidationScenario(
            faculty=faculty_list,
            courses=course_list,
            sections=sections_for_term,
            resources=resource_list,
            timeslots=timeslot_list,
            previous_assignments=prev_assignments,
        )

        violations = self.constraint_engine.validate(assignments_for_term, scenario)
        hard_violations = [v for v in violations if v.severity == ViolationSeverity.ERROR]
        soft_violations = [v for v in violations if v.severity != ViolationSeverity.ERROR]

        repairs_output = []
        explanation_data = None

        if hard_violations:
            # Generate simulated solve_result for explanation/repair synthesis
            blocking_rules = list(set(v.rule_id for v in hard_violations))
            sim_solve_res = SolveResult(
                feasible=False,
                status="INFEASIBLE",
                assignments=assignments_for_term,
                solve_time_seconds=0.0,
                objective_value=None,
                objective_bound=None,
                variable_count=len(faculty_list) * len(sections_for_term),
                variables_avoided=0,
                peak_memory_mb=0.1,
                fairness={},
                fit_summary={},
                conflicts=[{"rule_id": v.rule_id, "entity_id": ", ".join(v.entity_ids), "description": v.explanation} for v in hard_violations],
                explanation=f"Detected {len(hard_violations)} hard violations in current term schedule.",
                blocking_rule_ids=blocking_rules,
            )

            explanation = generate_explanation(
                solve_result=sim_solve_res,
                faculty=faculty_list,
                courses=course_list,
                sections=sections_for_term,
                resources=resource_list,
                timeslots=timeslot_list,
            )
            explanation_data = {
                "summary": explanation.summary,
                "primary_rule_ids": explanation.primary_rule_ids,
                "detailed_narrative": explanation.detailed_narrative,
                "suggested_actions": explanation.suggested_actions,
            }

            repairs = generate_repairs(
                faculty=faculty_list,
                courses=course_list,
                sections=sections_for_term,
                resources=resource_list,
                timeslots=timeslot_list,
                solve_result=sim_solve_res,
                re_solve_time_limit=5.0,
            )
            for r in repairs:
                repairs_output.append({
                    "repair_type": r.repair_type,
                    "title": r.title,
                    "description": r.description,
                    "changes": r.changes,
                    "feasible_after_repair": r.feasible_after_repair,
                    "fairness_gini": r.fairness_gini,
                    "mean_fit": r.mean_fit,
                    "rule_relaxed": r.rule_relaxed,
                })

        return {
            "term": term,
            "has_hard_violations": len(hard_violations) > 0,
            "hard_violations_count": len(hard_violations),
            "soft_violations_count": len(soft_violations),
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity.value,
                    "entity_ids": v.entity_ids,
                    "explanation": v.explanation,
                    "suggested_repairs": v.suggested_repairs,
                }
                for v in violations
            ],
            "explanation": explanation_data,
            "repair_alternatives": repairs_output,
        }

    async def apply_repair(
        self,
        repair_type: str,
        term: str,
        actor_id: str,
        changes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Apply an automated repair alternative (e.g. relax_hc05, add_adjunct, move_timeslot)."""
        logger.info(f"Applying repair '{repair_type}' for term '{term}' by {actor_id}")

        applied_changes = []

        if repair_type == "relax_hc05":
            # Increase max preparations and max courses for faculty to maintain validation invariants
            faculty_list = await self.faculty_repo.get_all()
            for f in faculty_list:
                new_max_courses = f.max_courses + 2
                new_max_preps = f.max_preparations + 2
                if new_max_preps > new_max_courses:
                    new_max_preps = new_max_courses
                updated_fac = f.model_copy(
                    update={
                        "max_courses": new_max_courses,
                        "max_preparations": new_max_preps,
                        "max_weekly_load_hours": f.max_weekly_load_hours + 6.0,
                    }
                )
                await self.faculty_repo.upsert(updated_fac)
            applied_changes.append("Increased max preparations and course limits for departmental faculty by +2.")

        elif repair_type == "add_adjunct":
            # Inject adjunct faculty member with broad competency
            courses = await self.course_repo.get_all()
            all_tags = []
            for c in courses:
                all_tags.extend(c.required_tags)
            unique_tags = list(set(all_tags))

            adjunct_id = f"f-adjunct-{uuid.uuid4().hex[:6]}"
            adjunct = Faculty.model_validate({
                "id": adjunct_id,
                "name": "Adjunct Visiting Instructor",
                "email": f"{adjunct_id}@university.edu",
                "rank": "Adjunct",
                "expertise": [{"tag": t, "proficiency": 5} for t in unique_tags],
                "max_weekly_load_hours": 15.0,
                "max_courses": 4,
                "min_courses": 0,
                "max_preparations": 4,
                "unavailable_slots": [],
                "leave_terms": [],
                "preferred_course_ids": [],
            })
            await self.faculty_repo.upsert(adjunct)
            applied_changes.append(f"Added qualified adjunct faculty member '{adjunct_id}'.")

        elif repair_type == "move_timeslot":
            # Reschedule sections that conflict
            sections = await self.section_repo.get_all()
            term_secs = [s for s in sections if s.term.lower() == term.lower()]
            slots_seen = set()
            for s in term_secs:
                if s.time_slot_id and s.time_slot_id in slots_seen:
                    new_slot = "TS-WED-1430" if s.time_slot_id != "TS-WED-1430" else "TS-THU-1030"
                    updated_sec = s.model_copy(update={"time_slot_id": new_slot})
                    await self.section_repo.upsert(updated_sec)
                    applied_changes.append(f"Moved section '{s.id}' to open slot '{new_slot}'.")
                    break
                elif s.time_slot_id:
                    slots_seen.add(s.time_slot_id)

        # Trigger re-optimization job automatically
        job_id = await self.start_optimization_job(term=term, method="cpsat", actor_id=actor_id)

        await self.audit_service.log_event(
            actor_id=actor_id,
            action="REPAIR_APPLY",
            entity="assignment",
            payload={"repair_type": repair_type, "term": term, "changes": applied_changes, "triggered_job_id": job_id},
        )

        return {
            "success": True,
            "repair_type": repair_type,
            "applied_changes": applied_changes,
            "triggered_job_id": job_id,
            "message": f"Repair '{repair_type}' successfully applied. Re-optimization job '{job_id}' started.",
        }

    async def execute_override(
        self,
        assignment_id: str,
        new_faculty_id: str,
        reason: str,
        actor_id: str,
        acknowledge_violations: bool = False,
    ) -> dict[str, Any]:
        """Execute administrative override with constraint engine re-validation.

        The original recommendation is preserved, an Override record is written,
        and hard violations require acknowledge_violations=True.
        """
        asgn = await self.assignment_repo.get(assignment_id)
        if not asgn:
            raise NotFoundError(f"Assignment '{assignment_id}' not found")

        if asgn.faculty_id == new_faculty_id:
            raise ValidationError(f"new_faculty_id '{new_faculty_id}' is already assigned to this section")

        target_faculty = await self.faculty_repo.get(new_faculty_id)
        if not target_faculty:
            raise NotFoundError(f"Faculty member '{new_faculty_id}' not found")

        section = await self.section_repo.get(asgn.section_id)
        if not section:
            raise NotFoundError(f"Section '{asgn.section_id}' not found")

        course = await self.course_repo.get(section.course_id)

        # 1. Prepare simulated assignments with candidate change
        all_assignments = await self.assignment_repo.get_all()
        previous_faculty_id = asgn.faculty_id

        # Calculate new fit score for override
        new_fit_res = fit(target_faculty, course) if course else (0.5, {})
        new_fit_val = float(new_fit_res[0]) if isinstance(new_fit_res, tuple) else float(new_fit_res)
        new_bdown = new_fit_res.breakdown if hasattr(new_fit_res, "breakdown") else {}
        numeric_bdown = {k: float(v) for k, v in new_bdown.items() if isinstance(v, (int, float))}

        candidate_asgn = asgn.model_copy(
            update={
                "faculty_id": new_faculty_id,
                "source": AssignmentSource.OVERRIDE,
                "fit_score": round(new_fit_val, 4),
                "fit_breakdown": numeric_bdown,
            }
        )

        simulated_assignments = [
            candidate_asgn if a.id == assignment_id else a for a in all_assignments
        ]

        # 2. Re-validate complete schedule with ConstraintEngine
        faculty_list = await self.faculty_repo.get_all()
        course_list = await self.course_repo.get_all()
        section_list = await self.section_repo.get_all()
        resource_list = await self.resource_repo.get_all()
        timeslot_list = await self.timeslot_repo.get_all()

        scenario = ValidationScenario(
            faculty=faculty_list,
            courses=course_list,
            sections=section_list,
            resources=resource_list,
            timeslots=timeslot_list,
            previous_assignments=[],
        )

        violations = self.constraint_engine.validate(simulated_assignments, scenario)
        hard_violations = [v for v in violations if v.severity == ViolationSeverity.ERROR]
        hard_rule_ids = list(set(v.rule_id for v in hard_violations))

        # 3. If hard violations appear and not acknowledged, return rejection
        if hard_violations and not acknowledge_violations:
            return {
                "success": False,
                "requires_acknowledgement": True,
                "message": (
                    f"Override introduces {len(hard_violations)} hard constraint violation(s): "
                    f"{', '.join(hard_rule_ids)}. You must set acknowledge_violations=true to proceed."
                ),
                "hard_violations": [
                    {
                        "rule_id": v.rule_id,
                        "entity_ids": v.entity_ids,
                        "explanation": v.explanation,
                    }
                    for v in hard_violations
                ],
            }

        # 4. Save Override record preserving snapshot evidence
        evidence_snapshot = {
            "previous_faculty_id": previous_faculty_id,
            "previous_fit_score": asgn.fit_score,
            "previous_source": asgn.source.value,
            "previous_fit_breakdown": asgn.fit_breakdown,
            "new_fit_score": round(new_fit_val, 4),
            "new_fit_breakdown": numeric_bdown,
            "evaluated_hard_violations": hard_rule_ids,
        }

        override_record = Override(
            id=f"ovr-{uuid.uuid4().hex[:10]}",
            assignment_id=assignment_id,
            admin_id=actor_id,
            reason=reason,
            previous_faculty_id=previous_faculty_id,
            new_faculty_id=new_faculty_id,
            constraint_evidence_snapshot=evidence_snapshot,
            acknowledged_violations=hard_rule_ids if acknowledge_violations else [],
            timestamp=datetime.now(UTC),
        )
        await self.override_repo.upsert(override_record)

        # 5. Persist the updated assignment (preserving original record in history/snapshot)
        updated_assignment = candidate_asgn.model_copy(
            update={
                "rule_ids_violated": hard_rule_ids,
            }
        )
        await self.assignment_repo.upsert(updated_assignment)

        # 6. Audit log override
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="ASSIGNMENT_OVERRIDE",
            entity="assignment",
            payload={
                "override_id": override_record.id,
                "assignment_id": assignment_id,
                "section_id": section.id,
                "previous_faculty_id": previous_faculty_id,
                "new_faculty_id": new_faculty_id,
                "reason": reason,
                "acknowledged_violations": hard_rule_ids,
            },
        )

        return {
            "success": True,
            "override_id": override_record.id,
            "assignment": updated_assignment.model_dump(mode="json"),
            "snapshot": evidence_snapshot,
            "acknowledged_violations": hard_rule_ids,
            "message": "Administrative override successfully executed and recorded.",
        }
