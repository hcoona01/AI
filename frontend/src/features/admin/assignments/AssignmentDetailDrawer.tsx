import React, { useState, useMemo } from 'react';
import {
  useExplainAssignment,
  useFacultyList,
  useCoursesList,
  useSectionsList,
  useAssignments,
  useOverrides,
  useExecuteOverride,
  type OverrideResponse,
} from '../api';
import type { Section, Override } from '../../../types';

interface AssignmentDetailDrawerProps {
  assignmentId: string;
  onClose: () => void;
  onOverrideCompleted?: () => void;
}

export const AssignmentDetailDrawer: React.FC<AssignmentDetailDrawerProps> = ({
  assignmentId,
  onClose,
  onOverrideCompleted,
}) => {
  const { data: explanation, isLoading, isError, error } = useExplainAssignment(assignmentId);
  const { data: facultyList } = useFacultyList();
  const { data: coursesList } = useCoursesList();
  const { data: sectionsList } = useSectionsList();
  const { data: assignmentsList } = useAssignments('Fall 2026'); // Can match current term
  const { data: overrides } = useOverrides(assignmentId);

  // Active view: 'details' or 'override'
  const [isOverrideMode, setIsOverrideMode] = useState<boolean>(false);
  const [selectedFacultyId, setSelectedFacultyId] = useState<string>('');
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [acknowledged, setAcknowledged] = useState<boolean>(false);
  const [overrideResponse, setOverrideResponse] = useState<OverrideResponse | null>(null);

  const overrideMutation = useExecuteOverride();

  // Find associated data
  const currentAssignment = useMemo(() => {
    return assignmentsList?.find((a) => a.id === assignmentId);
  }, [assignmentsList, assignmentId]);

  const currentSection = useMemo(() => {
    if (!currentAssignment && !explanation) return undefined;
    const secId = currentAssignment?.section_id || explanation?.section_id;
    return sectionsList?.find((s) => s.id === secId);
  }, [sectionsList, currentAssignment, explanation]);

  const currentCourse = useMemo(() => {
    if (!currentSection) return undefined;
    return coursesList?.find((c) => c.id === currentSection.course_id);
  }, [coursesList, currentSection]);

  const overrideRecord: Override | undefined = useMemo(() => {
    if (!overrides || overrides.length === 0) return undefined;
    return overrides.find((o) => o.assignment_id === assignmentId);
  }, [overrides, assignmentId]);

  const isOverridden = currentAssignment?.source === 'override' || Boolean(overrideRecord);

  // Previous faculty info if overridden
  const previousFaculty = useMemo(() => {
    if (!overrideRecord?.previous_faculty_id) return undefined;
    return facultyList?.find((f) => f.id === overrideRecord.previous_faculty_id);
  }, [facultyList, overrideRecord]);

  // Selected replacement faculty info
  const selectedFaculty = useMemo(() => {
    if (!selectedFacultyId) return undefined;
    return facultyList?.find((f) => f.id === selectedFacultyId);
  }, [facultyList, selectedFacultyId]);

  // Live Constraint Validation for Candidate Faculty
  const liveViolations = useMemo(() => {
    if (!selectedFaculty || !currentCourse || !currentSection) return [];
    const violations: { rule_id: string; severity: 'error' | 'warning'; explanation: string }[] = [];

    // HC-01: Proficiency check
    for (const tag of currentCourse.required_tags) {
      const exp = selectedFaculty.expertise.find((e) => e.tag.toLowerCase() === tag.toLowerCase());
      if (!exp || exp.proficiency < currentCourse.min_proficiency) {
        violations.push({
          rule_id: 'HC-01',
          severity: 'error',
          explanation: `Lacks required proficiency for tag '${tag}' (${exp?.proficiency ?? 0}/5 vs min ${currentCourse.min_proficiency}/5).`,
        });
      }
    }

    // HC-04: Leave terms
    if (selectedFaculty.leave_terms.includes(currentSection.term)) {
      violations.push({
        rule_id: 'HC-04',
        severity: 'error',
        explanation: `Faculty member is on scheduled leave during ${currentSection.term}.`,
      });
    }

    // HC-03: Timeslot clash
    if (currentSection.time_slot_id && selectedFaculty.unavailable_slots.includes(currentSection.time_slot_id)) {
      violations.push({
        rule_id: 'HC-03',
        severity: 'error',
        explanation: `Faculty has marked timeslot '${currentSection.time_slot_id}' as blackout unavailable.`,
      });
    }

    // Check existing assignments for timeslot overlap
    if (currentSection.time_slot_id && assignmentsList && sectionsList) {
      const secMap = new Map<string, Section>(sectionsList.map((s) => [s.id, s]));
      const facultySecs = assignmentsList
        .filter((a) => a.faculty_id === selectedFaculty.id && a.id !== assignmentId)
        .map((a) => secMap.get(a.section_id))
        .filter(Boolean);

      const hasClash = facultySecs.some((s) => s?.time_slot_id === currentSection.time_slot_id);
      if (hasClash) {
        violations.push({
          rule_id: 'HC-03',
          severity: 'error',
          explanation: `Time clash: Faculty already has an assigned section in timeslot '${currentSection.time_slot_id}'.`,
        });
      }
    }

    // SC-03: Preferred courses warning
    if (
      selectedFaculty.preferred_course_ids.length > 0 &&
      !selectedFaculty.preferred_course_ids.includes(currentCourse.id)
    ) {
      violations.push({
        rule_id: 'SC-03',
        severity: 'warning',
        explanation: `Course '${currentCourse.code}' is not in faculty member's preferred courses list.`,
      });
    }

    return violations;
  }, [selectedFaculty, currentCourse, currentSection, assignmentsList, sectionsList, assignmentId]);

  const hasLiveHardViolations = liveViolations.some((v) => v.severity === 'error');

  const handleApplyOverride = () => {
    if (!selectedFacultyId || !overrideReason.trim()) return;

    overrideMutation.mutate(
      {
        assignment_id: assignmentId,
        new_faculty_id: selectedFacultyId,
        reason: overrideReason.trim(),
        acknowledge_violations: acknowledged,
      },
      {
        onSuccess: (resp) => {
          if (resp.requires_acknowledgement) {
            setOverrideResponse(resp);
          } else {
            setIsOverrideMode(false);
            if (onOverrideCompleted) {
              onOverrideCompleted();
            }
          }
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/80 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-800 flex items-start justify-between bg-slate-950/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                Assignment Inspector
              </span>
              {isOverridden && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/15 px-2.5 py-0.5 rounded-full border border-amber-500/30 flex items-center gap-1">
                  <span>⚠️</span>
                  <span>Overridden</span>
                </span>
              )}
            </div>
            <h2 className="text-lg font-bold text-white mt-1">
              {currentCourse ? `${currentCourse.code} • ${currentCourse.title}` : explanation?.course_title || 'Section Assignment'}
            </h2>
            <div className="text-xs text-slate-400 font-mono mt-0.5">
              Section: {currentSection?.id || explanation?.section_id} • Timeslot: {currentSection?.time_slot_id || 'TBD'}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 text-base rounded-lg hover:bg-slate-800 transition"
            aria-label="Close drawer"
          >
            ✕
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {isLoading && (
            <div className="py-16 text-center text-slate-400 animate-pulse text-xs">
              Fetching assignment explainability rationale and constraint audits...
            </div>
          )}

          {isError && (
            <div className="bg-rose-950/40 border border-rose-800/80 rounded-xl p-4 text-rose-300 text-xs">
              {(error as Error)?.message || 'Failed to load assignment details.'}
            </div>
          )}

          {explanation && !isOverrideMode && (
            <div className="space-y-6">
              {/* Preserved Override Evidence Snapshot (If Overridden) */}
              {isOverridden && (
                <div className="bg-amber-950/20 border border-amber-500/40 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📜</span>
                      <span>Administrative Override Record</span>
                    </span>
                    <span className="text-[10px] font-mono text-amber-400/80">
                      {overrideRecord ? new Date(overrideRecord.timestamp).toLocaleString() : 'Audited'}
                    </span>
                  </div>

                  <div className="text-xs text-slate-300 bg-slate-950/80 rounded-lg p-3 border border-amber-500/20">
                    <div className="font-semibold text-white mb-1">Administrative Justification:</div>
                    <p className="italic text-slate-300">
                      "{overrideRecord?.reason || 'Manual reassignment approved by curriculum administrator.'}"
                    </p>
                    <div className="text-[11px] text-slate-400 mt-2 font-mono">
                      Admin ID: {overrideRecord?.admin_id || 'admin-root'}
                    </div>
                  </div>

                  {/* Original Recommendation Evidence */}
                  <div className="pt-2 border-t border-amber-500/20 grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block">Original Instructor</span>
                      <span className="font-semibold text-white">
                        {previousFaculty ? previousFaculty.name : overrideRecord?.previous_faculty_id || 'System Recommendation'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block">Original Fit Score</span>
                      <span className="font-mono font-bold text-amber-400">
                        {overrideRecord?.constraint_evidence_snapshot?.previous_fit_score
                          ? `${Math.round(Number(overrideRecord.constraint_evidence_snapshot.previous_fit_score) * 100)}%`
                          : 'Original Solver Output'}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Chosen Faculty Card */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                      {isOverridden ? 'Current Assigned Instructor' : 'Solver Recommended Instructor'}
                    </span>
                    <h3 className="text-base font-bold text-white mt-0.5">
                      {explanation.chosen_faculty.name}
                    </h3>
                    <div className="text-xs text-slate-400 font-mono">
                      Faculty ID: {explanation.chosen_faculty.faculty_id}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-emerald-400 font-mono">
                      {Math.round(explanation.chosen_faculty.fit_score * 100)}%
                    </div>
                    <span className="text-[10px] text-slate-500 uppercase">Composite Fit</span>
                  </div>
                </div>

                {/* Fit Score Breakdown Bars */}
                <div className="space-y-2.5 pt-3 border-t border-slate-800">
                  <div className="text-xs font-semibold text-slate-300">
                    Fit Score Breakdown (0.00 – 1.00):
                  </div>

                  {/* 1. Tag Match */}
                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Weighted Tag Match (60% weight)</span>
                      <span className="font-mono text-blue-400 font-bold">
                        {Math.round((explanation.chosen_faculty.fit_breakdown?.tag_match ?? 0) * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full"
                        style={{
                          width: `${Math.round((explanation.chosen_faculty.fit_breakdown?.tag_match ?? 0) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* 2. TF-IDF Similarity */}
                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>TF-IDF Syllabus Cosine Similarity (25% weight)</span>
                      <span className="font-mono text-purple-400 font-bold">
                        {Math.round((explanation.chosen_faculty.fit_breakdown?.tfidf_similarity ?? 0) * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-purple-500 h-1.5 rounded-full"
                        style={{
                          width: `${Math.round((explanation.chosen_faculty.fit_breakdown?.tfidf_similarity ?? 0) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* 3. Continuity Bonus */}
                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Past-Teaching Continuity Bonus (15% weight)</span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {Math.round((explanation.chosen_faculty.fit_breakdown?.past_bonus ?? 0) * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-1.5 rounded-full"
                        style={{
                          width: `${Math.round((explanation.chosen_faculty.fit_breakdown?.past_bonus ?? 0) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* "Why this faculty" Section */}
                <div className="pt-3 border-t border-slate-800 space-y-2">
                  <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <span>💡</span>
                    <span>Why This Faculty Was Assigned:</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-900 p-3 rounded-lg border border-slate-800">
                    {explanation.chosen_faculty.rationale}
                  </p>

                  {/* Responsible Justifying Rules */}
                  <div className="pt-1">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">
                      Institutional Invariants Satisfied:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {explanation.chosen_faculty.rule_ids_satisfied?.map((ruleId) => (
                        <span
                          key={ruleId}
                          className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                        >
                          ✓ {ruleId}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Top Alternatives & Constraints That Blocked Others */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Top Alternative Candidates Evaluated ({explanation.top_alternatives.length} of{' '}
                    {explanation.total_candidates_evaluated})
                  </h4>
                  <span className="text-[11px] text-slate-500">Ranked by Fit</span>
                </div>

                <div className="space-y-2">
                  {explanation.top_alternatives.map((alt) => (
                    <div
                      key={alt.faculty_id}
                      className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-xs space-y-2"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-semibold text-white">
                            {alt.name}{' '}
                            <span className="text-slate-400 font-normal">({alt.rank})</span>
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono">{alt.faculty_id}</div>
                        </div>

                        <div className="text-right">
                          <span className="font-mono font-bold text-slate-200">
                            {Math.round(alt.fit_score * 100)}% Fit
                          </span>
                          <div className="mt-0.5">
                            <span
                              className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                                alt.is_eligible
                                  ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                                  : 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
                              }`}
                            >
                              {alt.is_eligible ? 'Eligible Alternate' : 'Blocked by Invariants'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Constraints That Blocked This Alternate */}
                      {alt.blocked_reasons && alt.blocked_reasons.length > 0 && (
                        <div className="bg-rose-950/20 border border-rose-800/30 rounded-lg p-2 space-y-1">
                          <span className="text-[10px] font-bold text-rose-300 uppercase tracking-wider block">
                            Blocking Constraints:
                          </span>
                          {alt.blocked_reasons.map((reason, idx) => (
                            <div key={idx} className="text-[11px] text-rose-300 flex items-start gap-1.5">
                              <span className="text-rose-400 mt-0.5">&bull;</span>
                              <span>{reason}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* OVERRIDE FLOW INTERACTION MODE */}
          {isOverrideMode && (
            <div className="space-y-5 bg-slate-950/70 border border-blue-500/30 rounded-xl p-5">
              <div className="border-b border-slate-800 pb-3">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                  Administrative Action
                </span>
                <h3 className="text-base font-bold text-white mt-1">Manual Faculty Override</h3>
                <p className="text-xs text-slate-400">
                  Reassign section with live constraint validation and required justification.
                </p>
              </div>

              {/* Faculty Selector */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Select Candidate Faculty Member:
                </label>
                <select
                  value={selectedFacultyId}
                  onChange={(e) => {
                    setSelectedFacultyId(e.target.value);
                    setAcknowledged(false);
                  }}
                  className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">-- Choose Instructor --</option>
                  {facultyList
                    ?.filter((f) => f.id !== explanation?.chosen_faculty.faculty_id)
                    .map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name} ({f.rank}) • Max {f.max_weekly_load_hours}h
                      </option>
                    ))}
                </select>
              </div>

              {/* LIVE CONSTRAINT VALIDATION WARNINGS */}
              {selectedFaculty && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>Live Constraint Assessment:</span>
                    <span
                      className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                        hasLiveHardViolations
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {hasLiveHardViolations ? 'Violates Hard Invariants' : 'Feasible Candidate'}
                    </span>
                  </div>

                  {liveViolations.length > 0 ? (
                    <div className="space-y-1.5">
                      {liveViolations.map((v, idx) => (
                        <div
                          key={idx}
                          className={`p-2.5 rounded-lg text-xs flex items-start gap-2 border ${
                            v.severity === 'error'
                              ? 'bg-rose-950/30 border-rose-800/50 text-rose-300'
                              : 'bg-amber-950/30 border-amber-800/50 text-amber-300'
                          }`}
                        >
                          <span className="font-mono font-bold text-[11px] px-1.5 py-0.5 rounded bg-slate-950 text-white">
                            {v.rule_id}
                          </span>
                          <span className="leading-tight">{v.explanation}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-emerald-950/20 border border-emerald-800/40 rounded-lg p-3 text-emerald-300 text-xs flex items-center gap-2">
                      <span>✓</span>
                      <span>No constraint conflicts detected for this candidate faculty.</span>
                    </div>
                  )}
                </div>
              )}

              {/* Justification Text Area */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Mandatory Administrative Justification:
                </label>
                <textarea
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Explain institutional necessity (e.g., sabbatical replacement, grant load-release swap)..."
                  className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Explicit Acknowledgement Checkbox for Hard Violations */}
              {hasLiveHardViolations && (
                <div className="bg-rose-950/40 border border-rose-800/80 rounded-xl p-3.5 space-y-2">
                  <div className="font-bold text-rose-200 text-xs flex items-center gap-1.5">
                    <span>⚠️</span>
                    <span>Hard Rule Invariant Override Acknowledgement</span>
                  </div>
                  <p className="text-[11px] text-rose-300 leading-relaxed">
                    This manual assignment breaks institutional hard constraints. You must certify that department leadership has approved this exception.
                  </p>
                  <label className="flex items-center gap-2.5 pt-1 cursor-pointer text-xs font-semibold text-rose-200">
                    <input
                      type="checkbox"
                      checked={acknowledged}
                      onChange={(e) => setAcknowledged(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-950 text-rose-500 focus:ring-0 w-4 h-4"
                    />
                    <span>I explicitly acknowledge and accept these hard constraint violations</span>
                  </label>
                </div>
              )}

              {/* Server-side response error if acknowledgement was missing */}
              {overrideResponse?.requires_acknowledgement && (
                <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-3 text-rose-300 text-xs">
                  {overrideResponse.message}
                </div>
              )}

              {overrideMutation.isError && (
                <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-3 text-rose-300 text-xs">
                  {(overrideMutation.error as Error)?.message || 'Failed to apply override.'}
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsOverrideMode(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={
                    !selectedFacultyId ||
                    !overrideReason.trim() ||
                    overrideMutation.isPending ||
                    (hasLiveHardViolations && !acknowledged)
                  }
                  onClick={handleApplyOverride}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-bold uppercase tracking-wider rounded-lg shadow-sm transition"
                >
                  {overrideMutation.isPending ? 'Validating...' : 'Confirm Override'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/70 flex items-center justify-between">
          {!isOverrideMode ? (
            <>
              <button
                type="button"
                onClick={() => setIsOverrideMode(true)}
                className="px-4 py-2 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-500/30 rounded-lg text-xs font-bold transition flex items-center gap-1.5"
              >
                <span>✏️</span>
                <span>Initiate Override</span>
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
              >
                Done
              </button>
            </>
          ) : (
            <div className="text-xs text-slate-400">
              Live constraint validation active &bull; Original evidence preserved
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
