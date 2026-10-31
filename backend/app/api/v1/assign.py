"""Assignment optimization, inspection, explanation, fairness, repair, and override endpoints."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.security import get_current_user, require_admin, require_authenticated, verify_faculty_access
from app.schemas.assignment import Assignment
from app.schemas.user import User
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assign", tags=["assignments"])


def get_assignment_service() -> AssignmentService:
    return AssignmentService()


class RunOptimizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    term: str = Field(..., min_length=1, description="Academic term to optimize (e.g., 'Fall 2026')")
    method: Literal["cpsat", "greedy"] = Field(
        default="cpsat", description="Optimization algorithm (cpsat or greedy)"
    )
    forecast_mode: Literal["p50", "p90"] = Field(
        default="p50", description="Demand scenario profile: p50 (median) or p90 (risk mitigation)"
    )
    weights: dict[str, float] | None = Field(
        default=None, description="Optional custom weights for soft objectives (SC-01 to SC-05)"
    )
    time_limit: float = Field(
        default=20.0, ge=1.0, le=60.0, description="Solver CPU time limit in seconds (default 20s)"
    )


class ApplyRepairRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    repair_type: str = Field(..., description="Repair strategy type (relax_hc05, add_adjunct, move_timeslot, expand_facility)")
    term: str = Field(..., description="Target academic term")
    changes: list[dict[str, Any]] | None = Field(default=None, description="Optional custom parameter modifications")


class ExecuteOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    assignment_id: str = Field(..., min_length=1, description="ID of assignment to override")
    new_faculty_id: str = Field(..., min_length=1, description="ID of newly assigned faculty member")
    reason: str = Field(..., min_length=5, description="Administrative justification for override")
    acknowledge_violations: bool = Field(
        default=False,
        description="Must be set to true if the override introduces hard constraint violations",
    )


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_optimization(
    payload: RunOptimizationRequest,
    current_user: Annotated[User, Depends(require_admin)],
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Trigger background course allocation optimization (Admin only)."""
    job_id = await service.start_optimization_job(
        term=payload.term,
        method=payload.method,
        forecast_mode=payload.forecast_mode,
        weights=payload.weights,
        time_limit=payload.time_limit,
        actor_id=current_user.id,
        background_tasks=background_tasks,
    )
    return {
        "job_id": job_id,
        "status": "RUNNING",
        "message": f"Optimization job '{job_id}' started in background.",
    }


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
) -> dict[str, Any]:
    """Retrieve optimization job execution status and results."""
    return service.get_job(job_id)


@router.get("", response_model=list[Assignment])
async def list_assignments(
    current_user: Annotated[User, Depends(require_authenticated)],
    term: str | None = Query(default=None, description="Filter assignments by academic term"),
    faculty_id: str | None = Query(default=None, description="Filter assignments by faculty member"),
    service: Annotated[AssignmentService, Depends(get_assignment_service)] = None,  # type: ignore[assignment]
) -> list[Assignment]:
    """Fetch assignments with role-based visibility restrictions."""
    # Enforce faculty access isolation
    if current_user.role.value == "faculty":
        # Faculty can ONLY view their own assignments
        target_fid = current_user.faculty_id or "unassigned"
        if faculty_id and faculty_id != target_fid:
            verify_faculty_access(faculty_id, current_user)
        return await service.get_assignments(term=term, faculty_id=target_fid)

    return await service.get_assignments(term=term, faculty_id=faculty_id)


@router.get("/explain/{assignment_id}")
async def explain_assignment(
    assignment_id: str,
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
) -> dict[str, Any]:
    """Explain why chosen faculty won, show top-3 alternatives and blocked reasons."""
    explanation = await service.explain_assignment(assignment_id)
    # If caller is faculty, ensure they can only inspect assignments assigned to them
    if current_user.role.value == "faculty":
        chosen_fid = explanation["chosen_faculty"]["faculty_id"]
        verify_faculty_access(chosen_fid, current_user)

    return explanation


@router.get("/fairness")
async def get_fairness_summary(
    term: str = Query(..., description="Academic term for workload evaluation"),
    current_user: Annotated[User, Depends(require_authenticated)] = None,  # type: ignore[assignment]
    service: Annotated[AssignmentService, Depends(get_assignment_service)] = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Retrieve workload fairness metrics, Gini index, std dev, and max-min gap."""
    return await service.get_fairness_metrics(term=term)


@router.get("/conflicts")
async def get_conflicts_and_repairs(
    term: str = Query(..., description="Academic term to inspect for constraint conflicts"),
    current_user: Annotated[User, Depends(require_authenticated)] = None,  # type: ignore[assignment]
    service: Annotated[AssignmentService, Depends(get_assignment_service)] = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Inspect schedule conflicts, hard/soft violations, and synthesized repair alternatives."""
    return await service.get_conflicts_and_repairs(term=term)


@router.post("/repair/apply")
async def apply_repair_alternative(
    payload: ApplyRepairRequest,
    current_user: Annotated[User, Depends(require_admin)],
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
) -> dict[str, Any]:
    """Apply an automated repair alternative (Admin only)."""
    return await service.apply_repair(
        repair_type=payload.repair_type,
        term=payload.term,
        actor_id=current_user.id,
        changes=payload.changes,
    )


@router.post("/override")
async def execute_override(
    payload: ExecuteOverrideRequest,
    current_user: Annotated[User, Depends(require_admin)],
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
) -> dict[str, Any]:
    """Manually reassign a section with constraint engine re-validation and audit snapshot."""
    return await service.execute_override(
        assignment_id=payload.assignment_id,
        new_faculty_id=payload.new_faculty_id,
        reason=payload.reason,
        actor_id=current_user.id,
        acknowledge_violations=payload.acknowledge_violations,
    )
