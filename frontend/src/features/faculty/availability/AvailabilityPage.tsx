import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../auth/AuthContext';
import {
  useMyFacultyProfile,
  useFacultyCourses,
  useFacultyTimeslots,
  useUpdateFacultyPreferences,
} from '../api';

const LEAVE_TERMS_CATALOG = ['Fall 2026', 'Spring 2027', 'Summer 2027', 'Fall 2027', 'Spring 2028'];

export const AvailabilityPage: React.FC = () => {
  const { user } = useAuth();
  const currentFacultyId = user?.faculty_id || 'f-01';

  const { data: profile, isLoading: loadingProfile, error: errorProfile } = useMyFacultyProfile(currentFacultyId);
  const { data: courses } = useFacultyCourses();
  const { data: timeslots } = useFacultyTimeslots();

  const updateMutation = useUpdateFacultyPreferences(currentFacultyId);

  // Form states
  const [unavailableSlots, setUnavailableSlots] = useState<string[]>([]);
  const [leaveTerms, setLeaveTerms] = useState<string[]>([]);
  const [preferredCourseIds, setPreferredCourseIds] = useState<string[]>([]);
  const [isPendingOptimization, setIsPendingOptimization] = useState<boolean>(false);
  const [courseSearch, setCourseSearch] = useState<string>('');
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Sync with loaded profile
  useEffect(() => {
    if (profile) {
      setUnavailableSlots(profile.unavailable_slots || []);
      setLeaveTerms(profile.leave_terms || []);
      setPreferredCourseIds(profile.preferred_course_ids || []);
    }
  }, [profile]);

  // Group timeslots by day for organized timetable grid
  const daysOfWeek = ['MON', 'TUE', 'WED', 'THU', 'FRI'] as const;
  const timeslotsByDay = useMemo(() => {
    const map = new Map<string, typeof timeslots>();
    daysOfWeek.forEach((day) => {
      map.set(
        day,
        (timeslots || [])
          .filter((t) => t.day === day)
          .sort((a, b) => a.start.localeCompare(b.start))
      );
    });
    return map;
  }, [timeslots]);

  const toggleUnavailableSlot = (slotId: string) => {
    setUnavailableSlots((prev) =>
      prev.includes(slotId) ? prev.filter((id) => id !== slotId) : [...prev, slotId]
    );
  };

  const toggleLeaveTerm = (term: string) => {
    setLeaveTerms((prev) =>
      prev.includes(term) ? prev.filter((t) => t !== term) : [...prev, term]
    );
  };

  const togglePreferredCourse = (courseId: string) => {
    setPreferredCourseIds((prev) =>
      prev.includes(courseId) ? prev.filter((id) => id !== courseId) : [...prev, courseId]
    );
  };

  const handleSave = () => {
    updateMutation.mutate(
      {
        unavailable_slots: unavailableSlots,
        leave_terms: leaveTerms,
        preferred_course_ids: preferredCourseIds,
      },
      {
        onSuccess: (data) => {
          setIsPendingOptimization(data.pending_optimization);
          setSuccessToast(data.message);
          setTimeout(() => setSuccessToast(null), 5000);
        },
      }
    );
  };

  const filteredCourses = useMemo(() => {
    if (!courses) return [];
    if (!courseSearch.trim()) return courses;
    const query = courseSearch.toLowerCase();
    return courses.filter(
      (c) => c.code.toLowerCase().includes(query) || c.title.toLowerCase().includes(query)
    );
  }, [courses, courseSearch]);

  if (loadingProfile) {
    return (
      <div className="max-w-5xl mx-auto p-6 text-center text-slate-400 animate-pulse">
        Loading availability and teaching preference configuration...
      </div>
    );
  }

  if (errorProfile) {
    return (
      <div className="max-w-5xl mx-auto p-6 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-300 text-xs">
        Failed to load faculty profile: {(errorProfile as Error)?.message}
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2.5 py-0.5 rounded border border-purple-500/20">
              Teaching Preferences
            </span>
            <span className="text-xs text-slate-400 font-mono">ID: {currentFacultyId}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
            Availability & Course Preferences
          </h1>
          <p className="text-xs text-slate-400">
            Configure blackout timeslots, approved sabbatical terms, and preferred courses for automated solver optimization.
          </p>
        </div>

        <button
          type="button"
          disabled={updateMutation.isPending}
          onClick={handleSave}
          className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-bold uppercase tracking-wider rounded-lg shadow-md shadow-purple-600/20 transition flex items-center gap-2 self-start md:self-auto"
        >
          {updateMutation.isPending ? 'Saving Preferences...' : 'Save Preferences'}
        </button>
      </div>

      {/* Success / Pending Optimization Banner */}
      {(successToast || isPendingOptimization) && (
        <div className="bg-amber-950/30 border border-amber-500/40 rounded-xl p-4 text-xs text-amber-200 flex items-start gap-3">
          <span className="text-lg">⏳</span>
          <div className="space-y-0.5">
            <div className="font-bold uppercase tracking-wider flex items-center gap-2">
              <span>Status: Pending Re-Optimization</span>
              <span className="px-2 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-300 font-mono">
                PENDING
              </span>
            </div>
            <p className="text-amber-300/80 leading-relaxed">
              {successToast ||
                'Your updated preferences have been recorded. Changes are marked "Pending" and will be incorporated when the curriculum administrator re-runs the solver.'}
            </p>
          </div>
        </div>
      )}

      {/* SECTION 1: BLACKOUT UNAVAILABLE SLOTS */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>⏱️</span>
              <span>Unavailable Timeslots (HC-03 & HC-04 Blackouts)</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Click a timeslot to mark it as unavailable. The solver will strictly avoid assigning you to highlighted blocks.
            </p>
          </div>
          <span className="text-xs font-mono text-purple-400 font-semibold">
            {unavailableSlots.length} Blackouts Active
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
          {daysOfWeek.map((day) => {
            const slots = timeslotsByDay.get(day) || [];

            return (
              <div key={day} className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 space-y-2">
                <div className="text-center pb-2 border-b border-slate-800">
                  <span className="font-mono font-bold text-xs text-slate-300">{day}</span>
                </div>

                <div className="space-y-1.5">
                  {slots.map((slot) => {
                    const isBlackedOut = unavailableSlots.includes(slot.id);

                    return (
                      <button
                        key={slot.id}
                        type="button"
                        onClick={() => toggleUnavailableSlot(slot.id)}
                        className={`w-full text-left p-2 rounded-lg text-[11px] font-mono transition border ${
                          isBlackedOut
                            ? 'bg-rose-950/40 border-rose-800/80 text-rose-300 ring-1 ring-rose-500/30'
                            : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold">{slot.start} - {slot.end}</span>
                          {isBlackedOut && <span className="text-[10px] text-rose-400">✕</span>}
                        </div>
                        <div className="text-[10px] text-slate-500">{slot.id}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* SECTION 2: APPROVED SABBATICAL & LEAVE TERMS */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span>🏖️</span>
            <span>Approved Sabbatical & Leave Terms (HC-04)</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Select semesters in which you have an institutional grant release, fellowship, or sabbatical.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
          {LEAVE_TERMS_CATALOG.map((term) => {
            const isSelected = leaveTerms.includes(term);

            return (
              <button
                key={term}
                type="button"
                onClick={() => toggleLeaveTerm(term)}
                className={`p-3 rounded-xl border text-left transition ${
                  isSelected
                    ? 'bg-purple-950/40 border-purple-500/60 text-purple-200 ring-1 ring-purple-500/30'
                    : 'bg-slate-950/70 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-white">{term}</span>
                  <span
                    className={`w-3.5 h-3.5 rounded-xs border flex items-center justify-center text-[10px] ${
                      isSelected
                        ? 'bg-purple-600 border-purple-500 text-white'
                        : 'border-slate-700 bg-slate-900'
                    }`}
                  >
                    {isSelected && '✓'}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {isSelected ? 'On Sabbatical / Leave' : 'Active Teaching'}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* SECTION 3: PREFERRED COURSES (SC-03) */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>🎯</span>
              <span>Course Preferences (SC-03 Bonus)</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Select courses you would like to teach. The solver incorporates these with a soft objective bonus.
            </p>
          </div>

          <input
            type="text"
            placeholder="Search catalog by code or title..."
            value={courseSearch}
            onChange={(e) => setCourseSearch(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-500 w-56"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-h-96 overflow-y-auto pr-1">
          {filteredCourses.map((c) => {
            const isPreferred = preferredCourseIds.includes(c.id);

            return (
              <div
                key={c.id}
                onClick={() => togglePreferredCourse(c.id)}
                className={`cursor-pointer p-3 rounded-xl border text-xs transition ${
                  isPreferred
                    ? 'bg-blue-950/30 border-blue-500/50 text-blue-200 ring-1 ring-blue-500/30'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="font-mono font-bold text-white">{c.code}</div>
                  <span
                    className={`w-3.5 h-3.5 rounded-xs border flex items-center justify-center text-[10px] ${
                      isPreferred
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'border-slate-700 bg-slate-900'
                    }`}
                  >
                    {isPreferred && '✓'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-300 mt-1 truncate">{c.title}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  {c.contact_hours}h • {c.level}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
