import React, { useMemo, useState } from 'react';
import { useFacultyList } from '../api';
import type { Faculty, FacultyRank } from '../../../types';

const RANK_BADGE_STYLES: Record<FacultyRank, string> = {
  Professor: 'bg-purple-100 text-purple-900 border-purple-200',
  'Associate Professor': 'bg-blue-100 text-blue-900 border-blue-200',
  'Assistant Professor': 'bg-emerald-100 text-emerald-900 border-emerald-200',
  Lecturer: 'bg-amber-100 text-amber-900 border-amber-200',
  Adjunct: 'bg-stone-100 text-stone-800 border-stone-200',
  Visiting: 'bg-teal-100 text-teal-900 border-teal-200',
};

export const FacultyDirectoryPage: React.FC = () => {
  const { data: facultyList, isLoading, isError, error } = useFacultyList();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRank, setSelectedRank] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'active' | 'on_leave'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'rank' | 'capacity'>('name');
  const [selectedFaculty, setSelectedFaculty] = useState<Faculty | null>(null);

  // Compute metrics
  const metrics = useMemo(() => {
    if (!facultyList) return { total: 0, fullTime: 0, adjunct: 0, totalCapacity: 0, onLeave: 0 };
    const total = facultyList.length;
    let fullTime = 0;
    let adjunct = 0;
    let totalCapacity = 0;
    let onLeave = 0;

    facultyList.forEach((f) => {
      if (['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer'].includes(f.rank)) {
        fullTime += 1;
      } else {
        adjunct += 1;
      }
      totalCapacity += f.max_weekly_load_hours || 0;
      if (f.leave_terms && f.leave_terms.length > 0) {
        onLeave += 1;
      }
    });

    return { total, fullTime, adjunct, totalCapacity, onLeave };
  }, [facultyList]);

  // Filter and sort faculty
  const filteredFaculty = useMemo(() => {
    if (!facultyList) return [];

    return facultyList
      .filter((faculty) => {
        // Search filter
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase().trim();
          const matchName = faculty.name.toLowerCase().includes(q);
          const matchEmail = faculty.email.toLowerCase().includes(q);
          const matchRank = faculty.rank.toLowerCase().includes(q);
          const matchExpertise = faculty.expertise?.some((e) => e.tag.toLowerCase().includes(q));
          const matchPref = faculty.preferred_course_ids?.some((c) => c.toLowerCase().includes(q));
          if (!matchName && !matchEmail && !matchRank && !matchExpertise && !matchPref) {
            return false;
          }
        }

        // Rank filter
        if (selectedRank !== 'all' && faculty.rank !== selectedRank) {
          return false;
        }

        // Leave status filter
        if (selectedStatus === 'active' && faculty.leave_terms?.length > 0) {
          return false;
        }
        if (selectedStatus === 'on_leave' && (!faculty.leave_terms || faculty.leave_terms.length === 0)) {
          return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'name') {
          return a.name.localeCompare(b.name);
        }
        if (sortBy === 'rank') {
          return a.rank.localeCompare(b.rank);
        }
        if (sortBy === 'capacity') {
          return (b.max_weekly_load_hours || 0) - (a.max_weekly_load_hours || 0);
        }
        return 0;
      });
  }, [facultyList, searchQuery, selectedRank, selectedStatus, sortBy]);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 animate-pulse">
          Loading faculty directory and instructional capacity...
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-rose-950/40 border border-rose-800 rounded-2xl p-6 text-rose-300">
          Failed to load faculty directory: {(error as Error)?.message}
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
            <span className="pill">Personnel & Instruction</span>
            <span className="text-xs text-slate-500 font-mono">{metrics.total} Registered Faculty</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-1" style={{ letterSpacing: '-0.03em' }}>
            Faculty Directory & Expertise Profiles
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Department roster, academic rank, contractual teaching limits, course preferences, and syllabus expertise.
          </p>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Faculty</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">{metrics.total}</div>
          <div className="text-[11px] text-slate-500 mt-1">Department members</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Full-Time Faculty</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">{metrics.fullTime}</div>
          <div className="text-[11px] text-slate-500 mt-1">Prof, Assoc, Asst, Lecturer</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Adjunct / Visiting</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">{metrics.adjunct}</div>
          <div className="text-[11px] text-slate-500 mt-1">Flexible capacity</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Capacity</div>
          <div className="text-2xl font-bold mt-1 text-emerald-700 font-mono">{metrics.totalCapacity}h</div>
          <div className="text-[11px] text-slate-500 mt-1">Max weekly teaching hrs</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm col-span-2 sm:col-span-1">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">On Sabbatical / Leave</div>
          <div className={`text-2xl font-bold mt-1 font-mono ${metrics.onLeave > 0 ? 'text-amber-700' : 'text-slate-900'}`}>
            {metrics.onLeave}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">HC-04 constraint active</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search Bar */}
          <div>
            <label htmlFor="search-faculty" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Search Faculty
            </label>
            <input
              id="search-faculty"
              type="text"
              placeholder="Search by name, email, or tag..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            />
          </div>

          {/* Rank Filter */}
          <div>
            <label htmlFor="filter-rank" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Academic Rank
            </label>
            <select
              id="filter-rank"
              value={selectedRank}
              onChange={(e) => setSelectedRank(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="all">All Ranks ({facultyList?.length})</option>
              <option value="Professor">Professor</option>
              <option value="Associate Professor">Associate Professor</option>
              <option value="Assistant Professor">Assistant Professor</option>
              <option value="Lecturer">Lecturer</option>
              <option value="Adjunct">Adjunct</option>
              <option value="Visiting">Visiting</option>
            </select>
          </div>

          {/* Sabbatical Status */}
          <div>
            <label htmlFor="filter-status" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Availability Status
            </label>
            <select
              id="filter-status"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as 'all' | 'active' | 'on_leave')}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="all">All Faculty</option>
              <option value="active">Active & Available</option>
              <option value="on_leave">On Sabbatical / Leave</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label htmlFor="sort-by" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Sort By
            </label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'rank' | 'capacity')}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="name">Name (A – Z)</option>
              <option value="rank">Academic Rank</option>
              <option value="capacity">Teaching Capacity (High to Low)</option>
            </select>
          </div>
        </div>

        {/* Active Filter Indicators */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-200">
          <div>
            Showing <span className="font-semibold text-slate-900">{filteredFaculty.length}</span> of {facultyList?.length} faculty members
          </div>
          {(searchQuery || selectedRank !== 'all' || selectedStatus !== 'all') && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setSelectedRank('all');
                setSelectedStatus('all');
              }}
              className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Faculty Cards Grid */}
      {filteredFaculty.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
          No faculty members matched the specified criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredFaculty.map((faculty) => {
            const isOnLeave = faculty.leave_terms && faculty.leave_terms.length > 0;
            const initials = faculty.name
              .replace(/^(Dr\.|Prof\.|Mr\.|Ms\.)\s*/i, '')
              .split(' ')
              .map((w) => w[0])
              .filter(Boolean)
              .slice(0, 2)
              .join('');

            return (
              <div
                key={faculty.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between"
              >
                <div>
                  {/* Top: Avatar, Name, Rank */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-800 font-bold text-sm flex items-center justify-center border border-emerald-300">
                        {initials}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 leading-tight">{faculty.name}</h3>
                        <p className="text-[11px] text-slate-500 font-mono">{faculty.email}</p>
                      </div>
                    </div>
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                        RANK_BADGE_STYLES[faculty.rank] || 'bg-slate-100 text-slate-800 border-slate-200'
                      }`}
                    >
                      {faculty.rank}
                    </span>
                  </div>

                  {/* Sabbatical Status Alert */}
                  {isOnLeave && (
                    <div className="mt-3 px-2.5 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px] flex items-center gap-1.5">
                      <span>⚠️</span>
                      <span>
                        On Leave: <strong className="font-semibold">{faculty.leave_terms.join(', ')}</strong>
                      </span>
                    </div>
                  )}

                  {/* Contractual Limits Matrix */}
                  <div className="mt-4 grid grid-cols-3 gap-2 bg-slate-50/70 p-2.5 rounded-lg border border-slate-200 text-center text-xs">
                    <div>
                      <div className="text-[10px] uppercase font-semibold text-slate-500">Max Load</div>
                      <div className="text-xs font-bold text-slate-900 font-mono mt-0.5">
                        {faculty.max_weekly_load_hours}h/wk
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase font-semibold text-slate-500">Courses</div>
                      <div className="text-xs font-bold text-slate-900 font-mono mt-0.5">
                        {faculty.min_courses} – {faculty.max_courses}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase font-semibold text-slate-500">Max Preps</div>
                      <div className="text-xs font-bold text-slate-900 font-mono mt-0.5">
                        {faculty.max_preparations}
                      </div>
                    </div>
                  </div>

                  {/* Expertise Proficiencies Tags */}
                  <div className="mt-4">
                    <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1.5 flex items-center justify-between">
                      <span>Expertise & Proficiencies</span>
                      <span className="text-[10px] text-slate-400">{faculty.expertise?.length ?? 0} competencies</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {faculty.expertise && faculty.expertise.length > 0 ? (
                        faculty.expertise.map((exp) => (
                          <span
                            key={exp.tag}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[10px] font-medium text-slate-700 shadow-2xs"
                            title={`${exp.tag}: Level ${exp.proficiency} of 5`}
                          >
                            <span>{exp.tag}</span>
                            <span className="text-amber-500 font-mono font-bold">
                              {'★'.repeat(exp.proficiency)}
                            </span>
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-slate-400 italic">No expertise tags specified</span>
                      )}
                    </div>
                  </div>

                  {/* Course Preferences */}
                  {faculty.preferred_course_ids && faculty.preferred_course_ids.length > 0 && (
                    <div className="mt-3">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">
                        Preferred Courses
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {faculty.preferred_course_ids.map((cId) => (
                          <span
                            key={cId}
                            className="px-1.5 py-0.5 bg-blue-50 text-blue-800 border border-blue-200 rounded text-[10px] font-mono font-semibold"
                          >
                            {cId}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Unavailable Time Slots Preview */}
                  {faculty.unavailable_slots && faculty.unavailable_slots.length > 0 && (
                    <div className="mt-3">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">
                        Blocked Time Slots
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {faculty.unavailable_slots.map((slot) => (
                          <span
                            key={slot}
                            className="px-1.5 py-0.5 bg-rose-50 text-rose-800 border border-rose-200 rounded text-[10px] font-mono"
                          >
                            {slot}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Action */}
                <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-400">ID: {faculty.id}</span>
                  <button
                    type="button"
                    onClick={() => setSelectedFaculty(faculty)}
                    className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold inline-flex items-center gap-1"
                  >
                    <span>View Profile</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Faculty Detail Modal */}
      {selectedFaculty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between">
              <div>
                <span className="pill text-[10px]">{selectedFaculty.rank}</span>
                <h2 className="text-xl font-bold text-slate-900 mt-1">{selectedFaculty.name}</h2>
                <p className="text-xs text-slate-500 font-mono">{selectedFaculty.email}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFaculty(null)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
              <div className="font-semibold text-slate-700 uppercase text-[10px]">Teaching Constraints & Contract</div>
              <div className="grid grid-cols-2 gap-2 text-slate-600">
                <div>Max Weekly Hours: <strong className="text-slate-900">{selectedFaculty.max_weekly_load_hours}h</strong></div>
                <div>Course Load: <strong className="text-slate-900">{selectedFaculty.min_courses} to {selectedFaculty.max_courses} courses</strong></div>
                <div>Max Preparations: <strong className="text-slate-900">{selectedFaculty.max_preparations} distinct courses</strong></div>
                <div>Faculty ID: <strong className="font-mono text-slate-900">{selectedFaculty.id}</strong></div>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-800 uppercase mb-2">Expertise Proficiency Matrix</h4>
              <div className="space-y-1.5">
                {selectedFaculty.expertise.map((exp) => (
                  <div key={exp.tag} className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="font-medium text-slate-800">{exp.tag}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-emerald-600 h-1.5 rounded-full"
                          style={{ width: `${(exp.proficiency / 5) * 100}%` }}
                        />
                      </div>
                      <span className="font-mono font-bold text-emerald-700 w-8 text-right">{exp.proficiency}/5</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {selectedFaculty.unavailable_slots.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase mb-1">Unavailable Time Slots</h4>
                <div className="flex flex-wrap gap-1">
                  {selectedFaculty.unavailable_slots.map((slot) => (
                    <span key={slot} className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-xs font-mono">
                      {slot}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedFaculty(null)}
                className="btn text-xs px-4"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default FacultyDirectoryPage;

