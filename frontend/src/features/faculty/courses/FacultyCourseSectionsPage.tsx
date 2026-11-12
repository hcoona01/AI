import React, { useMemo, useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import {
  useFacultySections,
  useFacultyCourses,
  useFacultyTimeslots,
  useMyAssignments,
  useMyFacultyProfile,
  useUpdateFacultyPreferences,
  useCreateChangeRequest,
} from '../api';
import type { Course, Section, TimeSlot, Assignment } from '../../../types';

export const FacultyCourseSectionsPage: React.FC = () => {
  const { user } = useAuth();
  const facultyId = user?.faculty_id || 'f-01';

  const [currentTerm, setCurrentTerm] = useState<string>('Fall 2026');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterType, setFilterType] = useState<'all' | 'my_sections' | 'unassigned' | 'others'>('all');

  // Change request modal state
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [targetAssignment, setTargetAssignment] = useState<Assignment | null>(null);
  const [targetSection, setTargetSection] = useState<Section | null>(null);
  const [requestComment, setRequestComment] = useState('');
  const [requestSuccess, setRequestSuccess] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Queries
  const { data: sections, isLoading: loadingSections, isError: errorSections } = useFacultySections(currentTerm);
  const { data: courses, isLoading: loadingCourses } = useFacultyCourses();
  const { data: timeslots, isLoading: loadingTimeslots } = useFacultyTimeslots();
  const { data: assignments, isLoading: loadingAssignments } = useMyAssignments(currentTerm, null); // All assignments in term
  const { data: facultyProfile } = useMyFacultyProfile(facultyId);

  // Mutations
  const updatePreferencesMutation = useUpdateFacultyPreferences(facultyId);
  const createRequestMutation = useCreateChangeRequest();

  // Maps for rapid lookup
  const courseMap = useMemo(() => {
    const map = new Map<string, Course>();
    courses?.forEach((c) => map.set(c.id, c));
    return map;
  }, [courses]);

  const timeslotMap = useMemo(() => {
    const map = new Map<string, TimeSlot>();
    timeslots?.forEach((ts) => map.set(ts.id, ts));
    return map;
  }, [timeslots]);

  // Section ID to assignment mapping
  const assignmentBySection = useMemo(() => {
    const map = new Map<string, Assignment>();
    assignments?.forEach((a) => map.set(a.section_id, a));
    return map;
  }, [assignments]);

  // My assigned sections
  const myAssignedSectionIds = useMemo(() => {
    const set = new Set<string>();
    assignments?.forEach((a) => {
      if (a.faculty_id === facultyId) {
        set.add(a.section_id);
      }
    });
    return set;
  }, [assignments, facultyId]);

  // Handle adding course to preferences
  const handleAddPreference = (courseId: string) => {
    if (!facultyProfile) return;
    const current = facultyProfile.preferred_course_ids || [];
    if (current.includes(courseId)) return;

    updatePreferencesMutation.mutate(
      {
        unavailable_slots: facultyProfile.unavailable_slots,
        leave_terms: facultyProfile.leave_terms,
        preferred_course_ids: [...current, courseId],
        expertise: facultyProfile.expertise,
      },
      {
        onSuccess: () => {
          setActionSuccess(`Course ${courseId} added to your teaching preferences!`);
          setTimeout(() => setActionSuccess(null), 4000);
        },
      }
    );
  };

  // Handle open request modal
  const handleOpenRequest = (section: Section, assignment: Assignment) => {
    setTargetSection(section);
    setTargetAssignment(assignment);
    setRequestComment('');
    setRequestModalOpen(true);
  };

  // Submit change request
  const handleSubmitRequest = () => {
    if (!targetAssignment || !requestComment.trim()) return;

    createRequestMutation.mutate(
      {
        assignment_id: targetAssignment.id,
        comment: requestComment.trim(),
      },
      {
        onSuccess: () => {
          setRequestModalOpen(false);
          setRequestSuccess(`Change request submitted for Section ${targetSection?.id}. The department chair will review it.`);
          setTimeout(() => setRequestSuccess(null), 6000);
        },
      }
    );
  };

  // Filter sections
  const filteredSections = useMemo(() => {
    if (!sections) return [];

    return sections.filter((sec) => {
      const assignment = assignmentBySection.get(sec.id);
      const isMine = myAssignedSectionIds.has(sec.id);
      const isUnassigned = !assignment;

      // Filter category
      if (filterType === 'my_sections' && !isMine) return false;
      if (filterType === 'unassigned' && !isUnassigned) return false;
      if (filterType === 'others' && (isMine || isUnassigned)) return false;

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const course = courseMap.get(sec.course_id);
        const matchSecId = sec.id.toLowerCase().includes(q);
        const matchCourseCode = course?.code.toLowerCase().includes(q) ?? false;
        const matchCourseTitle = course?.title.toLowerCase().includes(q) ?? false;
        const matchSlot = sec.time_slot_id?.toLowerCase().includes(q) ?? false;

        if (!matchSecId && !matchCourseCode && !matchCourseTitle && !matchSlot) {
          return false;
        }
      }

      return true;
    });
  }, [sections, filterType, searchQuery, assignmentBySection, myAssignedSectionIds, courseMap]);

  // Aggregate Metrics
  const totalSectionsCount = sections?.length || 0;
  const mySectionsCount = myAssignedSectionIds.size;
  const unassignedCount = sections?.filter((s) => !assignmentBySection.has(s.id)).length || 0;

  // Calculate my weekly contact hours
  const myContactHours = useMemo(() => {
    let hours = 0;
    assignments?.forEach((a) => {
      if (a.faculty_id === facultyId) {
        const sec = sections?.find((s) => s.id === a.section_id);
        if (sec) {
          const c = courseMap.get(sec.course_id);
          hours += c?.contact_hours || 0;
        }
      }
    });
    return hours;
  }, [assignments, facultyId, sections, courseMap]);

  if (loadingSections || loadingCourses || loadingTimeslots || loadingAssignments) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 animate-pulse">
          Loading department course schedule and active class sections...
        </div>
      </div>
    );
  }

  if (errorSections) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-rose-950/40 border border-rose-800 rounded-2xl p-6 text-rose-300">
          Failed to load department sections for {currentTerm}.
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="pill">Curriculum Timetable</span>
            <span className="text-xs text-slate-500 font-mono">Term: {currentTerm}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-1" style={{ letterSpacing: '-0.03em' }}>
            Course Sections & Timetable Schedule
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Browse active lecture sections, scheduled temporal slots, class enrollment caps, and assigned instructors.
          </p>
        </div>

        {/* Global Term Selector */}
        <div className="flex items-center gap-2 bg-white border border-slate-300 px-3 py-1.5 rounded-xl shadow-2xs self-start md:self-auto">
          <label htmlFor="term-select" className="text-xs font-semibold text-slate-600 uppercase">
            Term:
          </label>
          <select
            id="term-select"
            value={currentTerm}
            onChange={(e) => setCurrentTerm(e.target.value)}
            className="text-xs font-medium rounded-lg px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-600"
          >
            <option value="Fall 2026">Fall 2026</option>
            <option value="Spring 2027">Spring 2027</option>
            <option value="Summer 2027">Summer 2027</option>
          </select>
        </div>
      </div>

      {/* Success Notification */}
      {requestSuccess && (
        <div className="bg-emerald-50 border border-emerald-300 rounded-xl p-3.5 text-xs text-emerald-900 flex items-center gap-2">
          <span className="text-emerald-700 font-bold">✓</span>
          <span>{requestSuccess}</span>
        </div>
      )}

      {actionSuccess && (
        <div className="bg-blue-50 border border-blue-300 rounded-xl p-3.5 text-xs text-blue-900 flex items-center gap-2">
          <span className="text-blue-700 font-bold">✓</span>
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Department Sections</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">{totalSectionsCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Active class offerings</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Assigned to You</div>
          <div className="text-2xl font-bold mt-1 text-emerald-700 font-mono">{mySectionsCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Your active sections</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Your Teaching Load</div>
          <div className="text-2xl font-bold mt-1 text-purple-700 font-mono">{myContactHours}h / wk</div>
          <div className="text-[11px] text-slate-500 mt-1">
            Max limit: {facultyProfile?.max_weekly_load_hours || 12}h
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Open / Unassigned</div>
          <div className="text-2xl font-bold mt-1 text-amber-700 font-mono">{unassignedCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Available for allocation</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Category Filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <button
            type="button"
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterType === 'all'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            All Sections ({totalSectionsCount})
          </button>
          <button
            type="button"
            onClick={() => setFilterType('my_sections')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterType === 'my_sections'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            My Sections ({mySectionsCount})
          </button>
          <button
            type="button"
            onClick={() => setFilterType('unassigned')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterType === 'unassigned'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Unassigned ({unassignedCount})
          </button>
          <button
            type="button"
            onClick={() => setFilterType('others')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterType === 'others'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Colleagues
          </button>
        </div>

        {/* Search Input */}
        <div className="w-full sm:w-64">
          <input
            type="text"
            placeholder="Search by code, title, or section ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
          />
        </div>
      </div>

      {/* Sections Cards Grid */}
      {filteredSections.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
          No class sections found matching your filter criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSections.map((sec) => {
            const course = courseMap.get(sec.course_id);
            const timeslot = sec.time_slot_id ? timeslotMap.get(sec.time_slot_id) : null;
            const assignment = assignmentBySection.get(sec.id);
            const isMine = myAssignedSectionIds.has(sec.id);
            const isUnassigned = !assignment;

            // Check if timeslot conflicts with faculty blackout slots
            const hasBlackoutConflict =
              sec.time_slot_id &&
              facultyProfile?.unavailable_slots?.includes(sec.time_slot_id);

            const isPreferredCourse =
              course && facultyProfile?.preferred_course_ids?.includes(course.id);

            return (
              <div
                key={sec.id}
                className={`bg-slate-900 border rounded-xl p-5 shadow-sm transition flex flex-col justify-between ${
                  isMine
                    ? 'border-emerald-500 ring-2 ring-emerald-200'
                    : 'border-slate-800 hover:shadow-md'
                }`}
              >
                <div>
                  {/* Top Bar: Course Code, Section ID, Status Badge */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                          {course?.code || 'COURSE'}
                        </span>
                        <span className="text-[11px] font-mono text-slate-500">
                          {sec.id}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-slate-900 mt-1.5 leading-snug">
                        {course?.title || 'Unknown Course'}
                      </h3>
                    </div>

                    {isMine ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-100 text-emerald-900 border border-emerald-300">
                        <span>●</span>
                        <span>Assigned to You</span>
                      </span>
                    ) : isUnassigned ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-100 text-amber-900 border border-amber-300">
                        <span>○</span>
                        <span>Open Section</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                        <span>👤</span>
                        <span>Assigned</span>
                      </span>
                    )}
                  </div>

                  {/* Schedule Timeslot Pill */}
                  <div className="mt-3 p-2.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1 text-xs">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-500 uppercase font-semibold text-[10px]">Timeslot</span>
                      <span className="font-mono font-medium text-slate-800">
                        {timeslot ? `${timeslot.day} ${timeslot.start} - ${timeslot.end}` : sec.time_slot_id || 'Unassigned'}
                      </span>
                    </div>

                    {/* Conflict Warning */}
                    {hasBlackoutConflict && (
                      <div className="text-[10px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 flex items-center gap-1">
                        <span>⚠️</span>
                        <span>Conflicts with your blackout preference</span>
                      </div>
                    )}
                  </div>

                  {/* Section Metrics: Capacity, Expected Size, Quantiles */}
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-slate-50 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] uppercase font-semibold text-slate-500">Cap / Expected</div>
                      <div className="font-mono font-bold text-slate-900 mt-0.5">
                        {sec.expected_size} / {sec.section_cap} seats
                      </div>
                    </div>

                    <div className="p-2 bg-slate-50 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] uppercase font-semibold text-slate-500">Demand Range</div>
                      <div className="font-mono text-slate-700 mt-0.5 text-[11px]">
                        P10: {sec.size_p10} | P90: {sec.size_p90}
                      </div>
                    </div>
                  </div>

                  {/* Required Syllabus Tags */}
                  {course?.required_tags && course.required_tags.length > 0 && (
                    <div className="mt-3">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">
                        Subject Competencies
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {course.required_tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px] font-medium text-slate-700"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Action Buttons */}
                <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between">
                  <div className="text-[10px] text-slate-400 font-mono">
                    {course?.contact_hours || 3}h/wk • {course?.credits || 3} cr
                  </div>

                  {isMine && assignment ? (
                    <button
                      type="button"
                      onClick={() => handleOpenRequest(sec, assignment)}
                      className="btn text-xs px-3 py-1 bg-amber-700 hover:bg-amber-800 text-white"
                    >
                      Request Swap / Change
                    </button>
                  ) : isUnassigned && course ? (
                    <button
                      type="button"
                      disabled={isPreferredCourse}
                      onClick={() => handleAddPreference(course.id)}
                      className={`text-xs px-2.5 py-1 rounded-md font-semibold transition ${
                        isPreferredCourse
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : 'btn text-xs px-3 py-1'
                      }`}
                    >
                      {isPreferredCourse ? '✓ In Preferences' : '+ Prefer Course'}
                    </button>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Change Request Modal */}
      {requestModalOpen && targetSection && targetAssignment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="pill text-[10px]">Section Change Request</span>
                <h2 className="text-lg font-bold text-slate-900 mt-1">
                  Request Adjustment for {targetSection.id}
                </h2>
                <p className="text-xs text-slate-500">
                  Course: {courseMap.get(targetSection.course_id)?.title || targetSection.course_id}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setRequestModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div>
              <label htmlFor="request-comment" className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Reason / Preferred Alternative
              </label>
              <textarea
                id="request-comment"
                rows={4}
                placeholder="Please state why you need to adjust this assignment (e.g. scheduling collision, research conflict, preference to teach an elective)..."
                value={requestComment}
                onChange={(e) => setRequestComment(e.target.value)}
                className="w-full text-xs p-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setRequestModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!requestComment.trim() || createRequestMutation.isPending}
                onClick={handleSubmitRequest}
                className="btn text-xs px-4 py-2 disabled:opacity-50"
              >
                {createRequestMutation.isPending ? 'Submitting...' : 'Submit Change Request'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default FacultyCourseSectionsPage;
