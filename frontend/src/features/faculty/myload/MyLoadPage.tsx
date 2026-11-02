import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ReferenceLine,
} from 'recharts';
import { useAuth } from '../../auth/AuthContext';
import {
  useMyFacultyProfile,
  useMyAssignments,
  useFacultyCourses,
  useFacultySections,
  useFacultyTimeslots,
  useAnonymizedLoadComparison,
  useAssignmentExplanation,
  useCreateChangeRequest,
  useMyChangeRequests,
  type AnonymizedPeerLoad,
} from '../api';
import type { Assignment, Course, Section, TimeSlot } from '../../../types';

export const MyLoadPage: React.FC = () => {
  const { user } = useAuth();
  const currentFacultyId = user?.faculty_id || 'f-01'; // Default for demo/dev

  const [currentTerm, setCurrentTerm] = useState<string>('Fall 2026');
  const [activeTab, setActiveTab] = useState<'schedule' | 'why' | 'requests'>('schedule');

  // Change request modal
  const [changeRequestAssignment, setChangeRequestAssignment] = useState<Assignment | null>(null);
  const [changeComment, setChangeComment] = useState<string>('');
  const [changeSuccess, setChangeSuccess] = useState<string | null>(null);

  // Explanation slide-over
  const [explainAssignmentId, setExplainAssignmentId] = useState<string | null>(null);

  // Queries
  const { data: profile } = useMyFacultyProfile(currentFacultyId);
  const { data: assignments, isLoading: loadingAssignments } = useMyAssignments(currentTerm, currentFacultyId);
  const { data: courses } = useFacultyCourses();
  const { data: sections } = useFacultySections(currentTerm);
  const { data: timeslots } = useFacultyTimeslots();
  const { data: loadComparison, isLoading: loadingComparison } = useAnonymizedLoadComparison(currentFacultyId, currentTerm);
  const { data: myChangeRequests } = useMyChangeRequests();

  const createChangeRequestMutation = useCreateChangeRequest();

  // Lookups
  const courseMap = useMemo(() => new Map<string, Course>(courses?.map((c) => [c.id, c]) || []), [courses]);
  const sectionMap = useMemo(() => new Map<string, Section>(sections?.map((s) => [s.id, s]) || []), [sections]);
  const timeslotMap = useMemo(() => new Map<string, TimeSlot>(timeslots?.map((t) => [t.id, t]) || []), [timeslots]);

  // Aggregate load
  const totalAssignedHours = useMemo(() => {
    if (!assignments || !sections || !courses) return 0;
    return assignments.reduce((acc, a) => {
      const sec = sectionMap.get(a.section_id);
      const crs = sec ? courseMap.get(sec.course_id) : undefined;
      return acc + (crs?.contact_hours || 3.0);
    }, 0);
  }, [assignments, sectionMap, courseMap, sections, courses]);

  const maxLimit = profile?.max_weekly_load_hours || 12.0;
  const loadPercentage = Math.round((totalAssignedHours / maxLimit) * 100);

  // Weekly timetable days and slots
  const daysOfWeek = ['MON', 'TUE', 'WED', 'THU', 'FRI'] as const;

  const handleSubmittingChangeRequest = () => {
    if (!changeRequestAssignment || !changeComment.trim()) return;

    createChangeRequestMutation.mutate(
      {
        assignment_id: changeRequestAssignment.id,
        comment: changeComment.trim(),
      },
      {
        onSuccess: () => {
          setChangeSuccess('Change request submitted to curriculum administration.');
          setChangeComment('');
          setTimeout(() => {
            setChangeSuccess(null);
            setChangeRequestAssignment(null);
          }, 2000);
        },
      }
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2.5 py-0.5 rounded border border-purple-500/20">
              Faculty Teaching Portal
            </span>
            <span className="text-xs text-slate-400 font-mono">ID: {currentFacultyId}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-1">
            {profile ? `${profile.name} • ${profile.rank}` : 'My Teaching Schedule'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Personal teaching assignments, load capacity metrics, timetable schedule, and assignment rationale.
          </p>
        </div>

        {/* Term Selector */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl self-start md:self-auto">
          <label htmlFor="term-select" className="text-xs font-semibold text-slate-400 uppercase">
            Term:
          </label>
          <select
            id="term-select"
            value={currentTerm}
            onChange={(e) => setCurrentTerm(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-white text-xs font-medium rounded-lg px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-purple-500"
          >
            <option value="Fall 2026">Fall 2026</option>
            <option value="Spring 2027">Spring 2027</option>
            <option value="Summer 2027">Summer 2027</option>
          </select>
        </div>
      </div>

      {/* KPI Workload Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Card 1: Hours against contractual limit */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Teaching Contact Hours
            </span>
            <span
              className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                totalAssignedHours > maxLimit
                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                  : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
              }`}
            >
              {totalAssignedHours > maxLimit ? 'Over Limit' : 'Balanced'}
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white font-mono">{totalAssignedHours.toFixed(1)}</span>
            <span className="text-slate-400 text-sm font-mono">/ {maxLimit.toFixed(1)} hrs/wk limit</span>
          </div>

          <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                totalAssignedHours > maxLimit ? 'bg-rose-500' : 'bg-purple-500'
              }`}
              style={{ width: `${Math.min(loadPercentage, 100)}%` }}
            />
          </div>

          <div className="text-[11px] text-slate-400 flex justify-between font-mono">
            <span>{loadPercentage}% contractual load</span>
            <span>{Math.max(0, maxLimit - totalAssignedHours).toFixed(1)}h available slack</span>
          </div>
        </div>

        {/* Card 2: Assigned sections count */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Assigned Course Sections
          </span>
          <div className="text-3xl font-bold text-white font-mono mt-1">
            {assignments?.length || 0}
            <span className="text-xs font-normal text-slate-400 ml-2">sections</span>
          </div>
          <div className="text-xs text-purple-400 font-mono mt-1">
            Max permitted: {profile?.max_courses || 3} courses • {profile?.max_preparations || 2} preps
          </div>
        </div>

        {/* Card 3: Department Relative Load Status */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Department Median Benchmark
          </span>
          <div className="text-3xl font-bold text-blue-400 font-mono mt-1">
            {loadComparison?.department_median_load ?? 9.0}
            <span className="text-xs font-normal text-slate-400 ml-2">hrs median</span>
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Your load:{' '}
            <strong className="text-white font-mono">{totalAssignedHours.toFixed(1)}h</strong>{' '}
            ({totalAssignedHours >= (loadComparison?.department_median_load ?? 9.0) ? 'At / above median' : 'Below median'})
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-2">
        <button
          type="button"
          onClick={() => setActiveTab('schedule')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-lg transition ${
            activeTab === 'schedule'
              ? 'bg-slate-900 text-white border-t-2 border-purple-500 shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/50'
          }`}
        >
          <span>📅</span>
          <span>My Assignments & Weekly Timetable</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('why')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-lg transition ${
            activeTab === 'why'
              ? 'bg-slate-900 text-white border-t-2 border-purple-500 shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/50'
          }`}
        >
          <span>💡</span>
          <span>Why I Was Assigned (Fit & Peer Benchmark)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('requests')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-lg transition ${
            activeTab === 'requests'
              ? 'bg-slate-900 text-white border-t-2 border-purple-500 shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-900/50'
          }`}
        >
          <span>📝</span>
          <span>My Change Requests ({myChangeRequests?.length || 0})</span>
        </button>
      </div>

      {/* TAB 1: SCHEDULE & TIMETABLE */}
      {activeTab === 'schedule' && (
        <div className="space-y-6">
          {loadingAssignments ? (
            <div className="p-12 text-center text-slate-400 animate-pulse text-xs bg-slate-900/80 rounded-xl border border-slate-800">
              Loading your teaching assignments for {currentTerm}...
            </div>
          ) : !assignments || assignments.length === 0 ? (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
              <span className="text-4xl mb-2 block">🏖️</span>
              <h3 className="text-base font-bold text-white">No Assigned Teaching Load</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                You have no scheduled teaching sections for {currentTerm}. If this is unexpected, contact your department chair.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Course Section Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {assignments.map((asgn) => {
                  const sec = sectionMap.get(asgn.section_id);
                  const crs = sec ? courseMap.get(sec.course_id) : undefined;
                  const tslot = sec?.time_slot_id ? timeslotMap.get(sec.time_slot_id) : undefined;

                  return (
                    <div
                      key={asgn.id}
                      className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3 hover:border-slate-700 transition"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-base text-white">
                              {crs?.code || asgn.section_id}
                            </span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
                              Section {sec?.id || asgn.section_id}
                            </span>
                            {asgn.source === 'override' && (
                              <span className="text-[9px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/15 px-1.5 py-0.5 rounded border border-amber-500/30">
                                Overridden
                              </span>
                            )}
                          </div>
                          <h4 className="text-xs font-semibold text-slate-300 mt-1">
                            {crs?.title || 'Course Offering'}
                          </h4>
                        </div>

                        <div className="text-right">
                          <span className="font-mono text-sm font-bold text-emerald-400">
                            {Math.round(asgn.fit_score * 100)}% Fit
                          </span>
                          <span className="text-[10px] text-slate-500 block uppercase">Expertise Score</span>
                        </div>
                      </div>

                      <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 text-xs text-slate-300 grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase block">Weekly Schedule</span>
                          <span className="font-mono font-medium text-slate-200">
                            {tslot ? `${tslot.day} ${tslot.start} - ${tslot.end}` : sec?.time_slot_id || 'TBD'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase block">Contact Hours</span>
                          <span className="font-mono font-medium text-slate-200">
                            {crs?.contact_hours || 3.0} hrs/week
                          </span>
                        </div>
                      </div>

                      {/* Card Actions */}
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                        <button
                          type="button"
                          onClick={() => setExplainAssignmentId(asgn.id)}
                          className="text-xs text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1"
                        >
                          <span>🔍 View Fit Breakdown & Rationale</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            setChangeRequestAssignment(asgn);
                            setChangeComment('');
                          }}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition"
                        >
                          Request Change
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Weekly Timetable Grid */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                      Weekly Teaching Timetable
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Class schedule across days and institutional timeslots for {currentTerm}.
                    </p>
                  </div>
                  <span className="text-xs font-mono text-purple-400 font-semibold">
                    {assignments.length} Scheduled Meetings
                  </span>
                </div>

                <div className="grid grid-cols-5 gap-3 pt-2">
                  {daysOfWeek.map((day) => {
                    // Find assignments for this day
                    const dayAssignments = assignments.filter((a) => {
                      const sec = sectionMap.get(a.section_id);
                      const ts = sec?.time_slot_id ? timeslotMap.get(sec.time_slot_id) : undefined;
                      return ts?.day === day;
                    });

                    return (
                      <div key={day} className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 min-h-[160px] flex flex-col">
                        <div className="text-center pb-2 border-b border-slate-800">
                          <span className="font-mono font-bold text-xs text-slate-300">{day}</span>
                        </div>

                        <div className="flex-1 py-2 space-y-2">
                          {dayAssignments.length === 0 ? (
                            <div className="h-full flex items-center justify-center text-[10px] text-slate-600 italic">
                              No classes
                            </div>
                          ) : (
                            dayAssignments.map((a) => {
                              const sec = sectionMap.get(a.section_id);
                              const crs = sec ? courseMap.get(sec.course_id) : undefined;
                              const ts = sec?.time_slot_id ? timeslotMap.get(sec.time_slot_id) : undefined;

                              return (
                                <div
                                  key={a.id}
                                  className="bg-purple-950/30 border border-purple-800/40 rounded-lg p-2 text-xs space-y-1"
                                >
                                  <div className="font-mono font-bold text-purple-300">
                                    {crs?.code || sec?.id}
                                  </div>
                                  <div className="text-[10px] text-slate-400 font-mono">
                                    {ts ? `${ts.start} - ${ts.end}` : 'TBD'}
                                  </div>
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: WHY I WAS ASSIGNED & ANONYMIZED PEER BENCHMARK */}
      {activeTab === 'why' && (
        <div className="space-y-6">
          {/* Fit Explanations */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Assignment Fit Breakdown & Justifying Constraints
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {assignments?.map((asgn) => {
                const sec = sectionMap.get(asgn.section_id);
                const crs = sec ? courseMap.get(sec.course_id) : undefined;

                return (
                  <div key={asgn.id} className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="font-mono font-bold text-base text-white">
                          {crs?.code || asgn.section_id}
                        </span>
                        <div className="text-xs text-slate-400 mt-0.5">{crs?.title}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold font-mono text-emerald-400">
                          {Math.round(asgn.fit_score * 100)}%
                        </div>
                        <span className="text-[10px] text-slate-500 uppercase">Composite Fit</span>
                      </div>
                    </div>

                    {/* Breakdown bars */}
                    <div className="space-y-2 pt-2 border-t border-slate-800 text-xs">
                      <div>
                        <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                          <span>Expertise Tag Match (60% weight)</span>
                          <span className="font-mono text-blue-400 font-bold">
                            {Math.round((asgn.fit_breakdown?.tag_match ?? 0.8) * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full"
                            style={{ width: `${Math.round((asgn.fit_breakdown?.tag_match ?? 0.8) * 100)}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                          <span>TF-IDF Syllabus Cosine Similarity (25% weight)</span>
                          <span className="font-mono text-purple-400 font-bold">
                            {Math.round((asgn.fit_breakdown?.tfidf_similarity ?? 0.7) * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-purple-500 h-1.5 rounded-full"
                            style={{ width: `${Math.round((asgn.fit_breakdown?.tfidf_similarity ?? 0.7) * 100)}%` }}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                          <span>Past-Teaching Continuity Bonus (15% weight)</span>
                          <span className="font-mono text-emerald-400 font-bold">
                            {Math.round((asgn.fit_breakdown?.past_bonus ?? 0.5) * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-emerald-500 h-1.5 rounded-full"
                            style={{ width: `${Math.round((asgn.fit_breakdown?.past_bonus ?? 0.5) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Satisfied Rules */}
                    <div className="pt-2 border-t border-slate-800">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">
                        Invariants Satisfied:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {asgn.rule_ids_satisfied?.slice(0, 5).map((ruleId) => (
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
                );
              })}
            </div>
          </div>

          {/* Anonymized Department Load Distribution Benchmark */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <span>📊</span>
                  <span>Teaching Load Relative to Department Median</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Anonymized distribution of teaching contact hours across departmental faculty.
                </p>
              </div>

              <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
                <span className="text-slate-400">Department Median:</span>
                <span className="font-mono font-bold text-blue-400">
                  {loadComparison?.department_median_load ?? 9.0} hrs/week
                </span>
              </div>
            </div>

            {loadingComparison ? (
              <div className="p-8 text-center text-slate-400 animate-pulse text-xs">
                Computing anonymized peer workload distribution...
              </div>
            ) : !loadComparison?.anonymized_peers || loadComparison.anonymized_peers.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No peer load distribution available for this term.
              </div>
            ) : (
              <div>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={loadComparison.anonymized_peers}
                      margin={{ top: 10, right: 10, left: -20, bottom: 25 }}
                    >
                      <XAxis
                        dataKey="label"
                        tick={{ fill: '#5c634c', fontSize: 10 }}
                        angle={-45}
                        textAnchor="end"
                        interval={0}
                      />
                      <YAxis
                        tick={{ fill: '#5c634c', fontSize: 10 }}
                        label={{
                          value: 'Contact Hours / Wk',
                          angle: -90,
                          position: 'insideLeft',
                          fill: '#5c634c',
                          fontSize: 10,
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          borderColor: '#e8ece0',
                          color: '#121410',
                          borderRadius: '0.5rem',
                          fontSize: '0.75rem',
                        }}
                        formatter={(value: unknown, _: unknown, entry: unknown) => {
                          const item = (entry as { payload: AnonymizedPeerLoad }).payload;
                          return [`${value} hrs/wk (${item.rank})`, item.label];
                        }}
                      />
                      <ReferenceLine
                        y={loadComparison.department_median_load}
                        stroke="#4d6a10"
                        strokeDasharray="4 4"
                        label={{
                          value: `Median: ${loadComparison.department_median_load}h`,
                          fill: '#4d6a10',
                          fontSize: 10,
                          position: 'top',
                        }}
                      />
                      <Bar dataKey="assigned_hours" radius={[3, 3, 0, 0]}>
                        {loadComparison.anonymized_peers.map((entry) => (
                          <Cell
                            key={entry.peer_id}
                            fill={entry.is_current_user ? '#4d6a10' : '#cfd6c0'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Privacy Guarantee Note */}
                <div className="mt-3 p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block" />
                    <span>Your Load ({totalAssignedHours.toFixed(1)}h)</span>
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-600 inline-block ml-3" />
                    <span>Anonymized Colleagues</span>
                  </div>
                  <span className="text-slate-500 font-mono">
                    Strict privacy: peer identities anonymized per project brief
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: CHANGE REQUESTS */}
      {activeTab === 'requests' && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Submitted Assignment Change Requests
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                History of comments and modification requests submitted to curriculum administrators.
              </p>
            </div>
          </div>

          {!myChangeRequests || myChangeRequests.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              <span className="text-3xl mb-2 block">📝</span>
              <p className="font-semibold text-white">No Change Requests Submitted</p>
              <p className="text-slate-500 mt-1">
                You can request changes on any assigned course from your schedule tab.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {myChangeRequests.map((cr) => (
                <div
                  key={cr.id}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white font-mono">{cr.course_code || cr.section_id}</span>
                        <span className="text-[10px] font-mono text-slate-500">
                          {new Date(cr.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono mt-0.5">ID: {cr.id}</div>
                    </div>

                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                        cr.status === 'approved'
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : cr.status === 'rejected'
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      {cr.status}
                    </span>
                  </div>

                  <p className="text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">
                    "{cr.comment}"
                  </p>

                  {cr.admin_response && (
                    <div className="text-[11px] text-purple-300 bg-purple-950/20 border border-purple-800/30 p-2 rounded-lg">
                      <strong className="text-purple-200">Admin Response:</strong> {cr.admin_response}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CHANGE REQUEST MODAL */}
      {changeRequestAssignment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                  Assignment Feedback
                </span>
                <h3 className="text-base font-bold text-white mt-1">Submit Change Request</h3>
                <p className="text-xs text-slate-400 font-mono">
                  Section ID: {changeRequestAssignment.section_id}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setChangeRequestAssignment(null)}
                className="text-slate-400 hover:text-white p-1"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            {changeSuccess && (
              <div className="bg-emerald-950/40 border border-emerald-800/80 rounded-lg p-3 text-emerald-300 text-xs">
                {changeSuccess}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <label className="block text-slate-300 font-semibold">
                Reason / Comment for Department Chair:
              </label>
              <textarea
                rows={4}
                value={changeComment}
                onChange={(e) => setChangeComment(e.target.value)}
                placeholder="Describe your scheduling conflict, research commitment, or preferred course adjustment..."
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
              <p className="text-[11px] text-slate-500">
                This will create a notification for the curriculum administrator and be reviewed prior to final schedule lock.
              </p>
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setChangeRequestAssignment(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!changeComment.trim() || createChangeRequestMutation.isPending}
                onClick={handleSubmittingChangeRequest}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-bold uppercase tracking-wider rounded-lg shadow-sm transition"
              >
                {createChangeRequestMutation.isPending ? 'Submitting...' : 'Submit Request'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EXPLAIN ASSIGNMENT SLIDE-OVER */}
      {explainAssignmentId && (
        <ExplainModal
          assignmentId={explainAssignmentId}
          onClose={() => setExplainAssignmentId(null)}
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
  const { data: explanation, isLoading, isError, error } = useAssignmentExplanation(assignmentId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto">
        <div className="flex items-start justify-between border-b border-slate-800 pb-3">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
              Assignment Rationale
            </span>
            <h3 className="text-base font-bold text-white mt-1">
              {explanation?.course_code}: {explanation?.course_title}
            </h3>
            <p className="text-xs text-slate-400 font-mono">Section ID: {explanation?.section_id}</p>
          </div>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white p-1">
            ✕
          </button>
        </div>

        {isLoading && (
          <div className="py-8 text-center text-slate-400 animate-pulse text-xs">
            Loading assignment explainability breakdown...
          </div>
        )}

        {isError && (
          <div className="bg-rose-950/40 border border-rose-800/60 p-3 text-rose-300 text-xs rounded-lg">
            {(error as Error)?.message}
          </div>
        )}

        {explanation && (
          <div className="space-y-4 text-xs">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase">Assigned Instructor</span>
                  <div className="font-bold text-white text-sm">{explanation.chosen_faculty.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold font-mono text-emerald-400">
                    {Math.round(explanation.chosen_faculty.fit_score * 100)}%
                  </div>
                  <span className="text-[10px] text-slate-500 uppercase">Overall Fit</span>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Expertise Tag Match</span>
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

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>TF-IDF Syllabus Cosine Similarity</span>
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

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Past-Teaching Continuity Bonus</span>
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

              <div className="pt-2 border-t border-slate-800 text-slate-300">
                <span className="font-semibold text-white">Rationale: </span>
                {explanation.chosen_faculty.rationale}
              </div>
            </div>
          </div>
        )}

        <div className="pt-2 border-t border-slate-800 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
