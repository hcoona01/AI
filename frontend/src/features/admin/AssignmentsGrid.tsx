import React, { useState, useMemo } from 'react';
import {
  useAssignments,
  useSectionsList,
  useFacultyList,
  useCoursesList,
  useExplainAssignment,
  useExecuteOverride,
  type OverrideResponse,
} from './api';
import type { Assignment, Faculty, Course } from '../../types';

interface AssignmentsGridProps {
  currentTerm: string;
}

export const AssignmentsGrid: React.FC<AssignmentsGridProps> = ({ currentTerm }) => {
  const { data: assignments, isLoading: loadingAssignments, isError: errorAssignments } = useAssignments(currentTerm);
  const { data: sections, isLoading: loadingSections } = useSectionsList(currentTerm);
  const { data: facultyList } = useFacultyList();
  const { data: coursesList } = useCoursesList();

  // Search and Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [ruleFilter, setRuleFilter] = useState<'all' | 'clean' | 'violated'>('all');
  const [fitFilter, setFitFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Active Modals
  const [explainAssignmentId, setExplainAssignmentId] = useState<string | null>(null);
  const [overrideAssignment, setOverrideAssignment] = useState<Assignment | null>(null);

  // Fast lookups
  const facultyMap = useMemo(() => {
    const map = new Map<string, Faculty>();
    facultyList?.forEach((f) => map.set(f.id, f));
    return map;
  }, [facultyList]);

  const courseMap = useMemo(() => {
    const map = new Map<string, Course>();
    coursesList?.forEach((c) => map.set(c.id, c));
    return map;
  }, [coursesList]);

  const assignmentBySection = useMemo(() => {
    const map = new Map<string, Assignment>();
    assignments?.forEach((a) => map.set(a.section_id, a));
    return map;
  }, [assignments]);

  // Combined Section-Assignment Rows
  const tableRows = useMemo(() => {
    if (!sections) return [];

    return sections.map((sec) => {
      const assignment = assignmentBySection.get(sec.id);
      const course = courseMap.get(sec.course_id);
      const faculty = assignment ? facultyMap.get(assignment.faculty_id) : undefined;

      const hasViolations = Boolean(assignment && assignment.rule_ids_violated && assignment.rule_ids_violated.length > 0);
      const fitScore = assignment?.fit_score ?? 0;

      return {
        section: sec,
        course,
        assignment,
        faculty,
        hasViolations,
        fitScore,
      };
    });
  }, [sections, assignmentBySection, courseMap, facultyMap]);

  // Filtered rows
  const filteredRows = useMemo(() => {
    return tableRows.filter((row) => {
      // Search filter
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchesSection = row.section.id.toLowerCase().includes(query);
        const matchesCourseCode = row.course?.code.toLowerCase().includes(query) ?? false;
        const matchesCourseTitle = row.course?.title.toLowerCase().includes(query) ?? false;
        const matchesFaculty = row.faculty?.name.toLowerCase().includes(query) ?? false;

        if (!matchesSection && !matchesCourseCode && !matchesCourseTitle && !matchesFaculty) {
          return false;
        }
      }

      // Rule violations filter
      if (ruleFilter === 'clean' && row.hasViolations) return false;
      if (ruleFilter === 'violated' && !row.hasViolations) return false;

      // Fit score filter
      if (fitFilter === 'high' && row.fitScore < 0.8) return false;
      if (fitFilter === 'medium' && (row.fitScore < 0.6 || row.fitScore >= 0.8)) return false;
      if (fitFilter === 'low' && row.fitScore >= 0.6) return false;

      return true;
    });
  }, [tableRows, searchTerm, ruleFilter, fitFilter]);

  // Pagination slicing
  const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize]);

  // Fit score chip color helper
  const getFitBadge = (score: number) => {
    const percentage = Math.round(score * 100);
    if (score >= 0.8) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          {percentage}% Fit
        </span>
      );
    }
    if (score >= 0.6) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-300 border border-sky-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
          {percentage}% Fit
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
        {percentage}% Fit
      </span>
    );
  };

  if (loadingAssignments || loadingSections) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 text-center text-slate-400 animate-pulse">
        <div className="h-6 w-56 bg-slate-800 rounded mx-auto mb-4" />
        <p className="text-sm">Loading course section assignments and constraint evaluations...</p>
      </div>
    );
  }

  if (errorAssignments) {
    return (
      <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-6 text-rose-300 text-sm">
        <h4 className="font-semibold text-rose-200 mb-1">Failed to Load Assignments</h4>
        <p>Could not retrieve assignment records for {currentTerm}. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20">
              Schedule Matrix
            </span>
            <span className="text-xs text-slate-400">
              Showing {filteredRows.length} of {tableRows.length} sections
            </span>
          </div>
          <h2 className="text-lg font-bold text-white mt-1">Section Assignments & Rule Compliance</h2>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2.5">
          <input
            type="text"
            placeholder="Search course, section, faculty..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 w-52"
          />

          <select
            value={ruleFilter}
            onChange={(e) => {
              setRuleFilter(e.target.value as 'all' | 'clean' | 'violated');
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-700 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Rules</option>
            <option value="clean">Fully Compliant</option>
            <option value="violated">Has Violations</option>
          </select>

          <select
            value={fitFilter}
            onChange={(e) => {
              setFitFilter(e.target.value as 'all' | 'high' | 'medium' | 'low');
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-700 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Fit Levels</option>
            <option value="high">High Fit (&ge; 80%)</option>
            <option value="medium">Good Fit (60-79%)</option>
            <option value="low">Suboptimal (&lt; 60%)</option>
          </select>
        </div>
      </div>

      {/* Assignments Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {paginatedRows.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <span className="text-3xl mb-2 block">🔍</span>
            <p className="font-semibold text-white">No section assignments match the current filter</p>
            <p className="text-xs text-slate-500 mt-1">Try clearing your search query or adjusting filter dropdowns.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Section / Course</th>
                  <th className="py-3 px-4">Schedule Slot</th>
                  <th className="py-3 px-4">Assigned Faculty</th>
                  <th className="py-3 px-4 text-center">Fit Score</th>
                  <th className="py-3 px-4">Rule Compliance Badges</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {paginatedRows.map(({ section, course, assignment, faculty, hasViolations, fitScore }) => {
                  return (
                    <tr key={section.id} className="hover:bg-slate-800/40 transition">
                      {/* Course / Section */}
                      <td className="py-3.5 px-4">
                        <div className="font-mono font-bold text-white text-sm">
                          {course?.code || section.course_id}
                        </div>
                        <div className="text-slate-400 text-[11px] truncate max-w-xs">
                          {course?.title || 'Unknown Course'}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          ID: {section.id} • Cap: {section.section_cap}
                        </div>
                      </td>

                      {/* Schedule Slot */}
                      <td className="py-3.5 px-4 font-mono text-slate-300">
                        {section.time_slot_id ? (
                          <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px]">
                            {section.time_slot_id}
                          </span>
                        ) : (
                          <span className="text-slate-500 italic">TBD</span>
                        )}
                      </td>

                      {/* Assigned Faculty */}
                      <td className="py-3.5 px-4">
                        {faculty ? (
                          <div>
                            <div className="font-semibold text-white text-xs">{faculty.name}</div>
                            <div className="text-slate-400 text-[10px]">{faculty.rank}</div>
                            <div className="text-slate-500 font-mono text-[10px]">{faculty.id}</div>
                          </div>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                            Unassigned
                          </span>
                        )}
                      </td>

                      {/* Fit Score Chip */}
                      <td className="py-3.5 px-4 text-center">
                        {assignment ? (
                          <button
                            type="button"
                            onClick={() => setExplainAssignmentId(assignment.id)}
                            className="cursor-pointer hover:opacity-85 transition transform hover:scale-105"
                            title="Click to view fit breakdown and alternative candidates"
                          >
                            {getFitBadge(fitScore)}
                          </button>
                        ) : (
                          <span className="text-slate-500 text-xs">&mdash;</span>
                        )}
                      </td>

                      {/* Rule Compliance Badges */}
                      <td className="py-3.5 px-4">
                        {assignment ? (
                          <div className="flex flex-wrap items-center gap-1 max-w-md">
                            {/* Violated Badges */}
                            {hasViolations &&
                              assignment.rule_ids_violated.map((ruleId) => (
                                <span
                                  key={ruleId}
                                  className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                  title={`Violated rule: ${ruleId}`}
                                >
                                  {ruleId}
                                </span>
                              ))}

                            {/* Satisfied Badges (first 4 for brevity) */}
                            {assignment.rule_ids_satisfied?.slice(0, 4).map((ruleId) => (
                              <span
                                key={ruleId}
                                className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700"
                                title={`Satisfied: ${ruleId}`}
                              >
                                {ruleId}
                              </span>
                            ))}

                            {assignment.rule_ids_satisfied && assignment.rule_ids_satisfied.length > 4 && (
                              <span className="text-[10px] font-mono text-slate-500">
                                +{assignment.rule_ids_satisfied.length - 4} more
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-500 text-xs italic">Pending solver run</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right space-x-2">
                        {assignment && (
                          <>
                            <button
                              type="button"
                              onClick={() => setExplainAssignmentId(assignment.id)}
                              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
                            >
                              Explain
                            </button>
                            <button
                              type="button"
                              onClick={() => setOverrideAssignment(assignment)}
                              className="px-2.5 py-1 rounded bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-500/30 text-xs font-medium transition"
                            >
                              Override
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-slate-950 border border-slate-800 text-slate-200 rounded px-2 py-1 text-xs"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span className="ml-2">
              Page {page} of {totalPages}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              &larr; Prev
            </button>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Next &rarr;
            </button>
          </div>
        </div>
      </div>

      {/* Explain Assignment Modal */}
      {explainAssignmentId && (
        <ExplainModal
          assignmentId={explainAssignmentId}
          onClose={() => setExplainAssignmentId(null)}
        />
      )}

      {/* Administrative Override Modal */}
      {overrideAssignment && (
        <OverrideModal
          assignment={overrideAssignment}
          facultyList={facultyList || []}
          onClose={() => setOverrideAssignment(null)}
        />
      )}
    </div>
  );
};

// ----------------------------------------------------------------------
// Explain Modal Sub-Component
// ----------------------------------------------------------------------
interface ExplainModalProps {
  assignmentId: string;
  onClose: () => void;
}

const ExplainModal: React.FC<ExplainModalProps> = ({ assignmentId, onClose }) => {
  const { data: explanation, isLoading, isError, error } = useExplainAssignment(assignmentId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20">
              Assignment Explanation
            </span>
            <h3 className="text-lg font-bold text-white mt-1">
              {explanation?.course_code}: {explanation?.course_title}
            </h3>
            <p className="text-xs text-slate-400">Section ID: {explanation?.section_id}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {isLoading && (
          <div className="text-center py-10 text-slate-400 animate-pulse text-sm">
            Evaluating candidate alternatives and fit breakdown...
          </div>
        )}

        {isError && (
          <div className="bg-rose-950/40 border border-rose-800/60 rounded-lg p-4 text-rose-300 text-xs">
            Failed to explain assignment: {(error as Error)?.message}
          </div>
        )}

        {explanation && (
          <div className="space-y-5">
            {/* Chosen Faculty Card */}
            <div className="bg-slate-950/70 border border-emerald-500/30 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                    Recommended Faculty
                  </span>
                  <div className="text-base font-bold text-white">
                    {explanation.chosen_faculty.name}
                  </div>
                  <div className="text-xs text-slate-400 font-mono">
                    ID: {explanation.chosen_faculty.faculty_id}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-emerald-400">
                    {Math.round(explanation.chosen_faculty.fit_score * 100)}%
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase">Composite Fit</div>
                </div>
              </div>

              {/* Fit Breakdown Progress Bars */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="text-xs font-semibold text-slate-300">Fit Component Breakdown:</div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Expertise Tag Match (60% weight)</span>
                    <span className="font-mono text-slate-200">
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

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>TF-IDF Syllabus Cosine Similarity (25% weight)</span>
                    <span className="font-mono text-slate-200">
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

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Past-Teaching Continuity Bonus (15% weight)</span>
                    <span className="font-mono text-slate-200">
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

              {/* Plain Rationale */}
              <div className="text-xs text-slate-300 bg-slate-900/90 rounded-lg p-2.5 border border-slate-800">
                <span className="font-semibold text-white">Rationale: </span>
                {explanation.chosen_faculty.rationale}
              </div>
            </div>

            {/* Top Alternatives Evaluated */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Top Alternative Faculty Evaluated ({explanation.top_alternatives.length} of{' '}
                {explanation.total_candidates_evaluated})
              </h4>
              <div className="space-y-2">
                {explanation.top_alternatives.map((alt) => (
                  <div
                    key={alt.faculty_id}
                    className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs flex flex-col md:flex-row md:items-center justify-between gap-2"
                  >
                    <div>
                      <div className="font-semibold text-white">
                        {alt.name} <span className="text-slate-400 font-normal">({alt.rank})</span>
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">{alt.faculty_id}</div>
                      {alt.blocked_reasons && alt.blocked_reasons.length > 0 && (
                        <div className="mt-1 space-y-0.5">
                          {alt.blocked_reasons.map((reason, idx) => (
                            <div key={idx} className="text-rose-400 text-[11px] flex items-center gap-1">
                              <span>&bull;</span>
                              <span>{reason}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="text-right flex items-center md:flex-col justify-between md:justify-center">
                      <div className="font-mono font-bold text-slate-200">
                        {Math.round(alt.fit_score * 100)}% Fit
                      </div>
                      <span
                        className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                          alt.is_eligible
                            ? 'bg-slate-800 text-slate-300'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {alt.is_eligible ? 'Eligible' : 'Blocked'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="pt-3 border-t border-slate-800 text-right">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// ----------------------------------------------------------------------
// Administrative Override Modal Sub-Component
// ----------------------------------------------------------------------
interface OverrideModalProps {
  assignment: Assignment;
  facultyList: Faculty[];
  onClose: () => void;
}

const OverrideModal: React.FC<OverrideModalProps> = ({ assignment, facultyList, onClose }) => {
  const [newFacultyId, setNewFacultyId] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [acknowledge, setAcknowledge] = useState<boolean>(false);
  const [overrideResult, setOverrideResult] = useState<OverrideResponse | null>(null);

  const overrideMutation = useExecuteOverride();

  const handleApplyOverride = () => {
    if (!newFacultyId || !reason.trim()) return;

    overrideMutation.mutate(
      {
        assignment_id: assignment.id,
        new_faculty_id: newFacultyId,
        reason: reason.trim(),
        acknowledge_violations: acknowledge,
      },
      {
        onSuccess: (data) => {
          if (data.requires_acknowledgement) {
            setOverrideResult(data);
          } else {
            onClose();
          }
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <div className="flex items-start justify-between border-b border-slate-800 pb-3">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              Administrative Action
            </span>
            <h3 className="text-base font-bold text-white mt-1">Manual Assignment Override</h3>
            <p className="text-xs text-slate-400">Section: {assignment.section_id}</p>
          </div>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white p-1">
            ✕
          </button>
        </div>

        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Select Replacement Faculty:</label>
            <select
              value={newFacultyId}
              onChange={(e) => setNewFacultyId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">-- Choose Faculty Member --</option>
              {facultyList
                .filter((f) => f.id !== assignment.faculty_id)
                .map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name} ({f.rank}) - {f.id}
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Administrative Justification (Required):
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="State institutional justification (e.g. specialized grant release, emergency co-teaching agreement)..."
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Warning banner if hard violations are flagged */}
          {overrideResult?.requires_acknowledgement && (
            <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-3 text-rose-300 space-y-2">
              <div className="font-bold flex items-center gap-1.5 text-rose-200">
                <span>⚠️</span>
                <span>Hard Constraint Violations Detected</span>
              </div>
              <p className="text-[11px]">
                This override violates institutional hard constraints. You must acknowledge this risk to persist the override.
              </p>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-rose-300">
                {overrideResult.hard_violations?.map((v, i) => (
                  <li key={i}>
                    <strong>{v.rule_id}:</strong> {v.explanation}
                  </li>
                ))}
              </ul>
              <label className="flex items-center gap-2 pt-2 cursor-pointer font-semibold text-rose-200">
                <input
                  type="checkbox"
                  checked={acknowledge}
                  onChange={(e) => setAcknowledge(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-rose-500 focus:ring-0"
                />
                <span>I acknowledge these violations and force this override</span>
              </label>
            </div>
          )}

          {overrideMutation.isError && (
            <div className="bg-rose-950/40 border border-rose-800/60 rounded-lg p-3 text-rose-300 text-xs">
              {(overrideMutation.error as Error)?.message || 'Failed to apply override.'}
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!newFacultyId || !reason.trim() || overrideMutation.isPending}
            onClick={handleApplyOverride}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition"
          >
            {overrideMutation.isPending ? 'Validating...' : 'Apply Override'}
          </button>
        </div>
      </div>
    </div>
  );
};
