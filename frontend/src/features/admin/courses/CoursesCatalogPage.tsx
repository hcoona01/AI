import React, { useMemo, useState } from 'react';
import { useCoursesList, useSectionsList } from '../api';
import type { Course, CourseLevel, Section } from '../../../types';

const LEVEL_BADGE_STYLES: Record<CourseLevel, string> = {
  undergraduate: 'bg-blue-100 text-blue-900 border-blue-200',
  graduate: 'bg-purple-100 text-purple-900 border-purple-200',
  doctoral: 'bg-amber-100 text-amber-900 border-amber-200',
};

export const CoursesCatalogPage: React.FC = () => {
  const { data: coursesList, isLoading: loadingCourses, isError: errorCourses, error: courseError } = useCoursesList();
  const { data: sectionsList, isLoading: loadingSections } = useSectionsList();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<'all' | 'lab' | 'lecture'>('all');
  const [sortBy, setSortBy] = useState<'code' | 'title' | 'credits' | 'sections'>('code');
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);

  // Group sections by course_id
  const sectionsByCourse = useMemo(() => {
    const map = new Map<string, Section[]>();
    if (!sectionsList) return map;

    sectionsList.forEach((sec) => {
      const list = map.get(sec.course_id) || [];
      list.push(sec);
      map.set(sec.course_id, list);
    });
    return map;
  }, [sectionsList]);

  // Aggregate metrics
  const metrics = useMemo(() => {
    if (!coursesList) return { totalCourses: 0, totalSections: 0, labCourses: 0, undergrad: 0, grad: 0, avgContact: 0 };
    const totalCourses = coursesList.length;
    const totalSections = sectionsList?.length || 0;
    let labCourses = 0;
    let undergrad = 0;
    let grad = 0;
    let totalContact = 0;

    coursesList.forEach((c) => {
      if (c.is_lab) labCourses += 1;
      if (c.level === 'undergraduate') undergrad += 1;
      if (c.level === 'graduate' || c.level === 'doctoral') grad += 1;
      totalContact += c.contact_hours || 0;
    });

    const avgContact = totalCourses > 0 ? (totalContact / totalCourses).toFixed(1) : '0';
    return { totalCourses, totalSections, labCourses, undergrad, grad, avgContact };
  }, [coursesList, sectionsList]);

  // Filter and sort courses
  const filteredCourses = useMemo(() => {
    if (!coursesList) return [];

    return coursesList
      .filter((c) => {
        // Search query
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase().trim();
          const matchCode = c.code.toLowerCase().includes(q);
          const matchTitle = c.title.toLowerCase().includes(q);
          const matchDesc = c.description?.toLowerCase().includes(q) ?? false;
          const matchTag = c.required_tags?.some((t) => t.toLowerCase().includes(q)) ?? false;
          if (!matchCode && !matchTitle && !matchDesc && !matchTag) {
            return false;
          }
        }

        // Level filter
        if (selectedLevel !== 'all' && c.level !== selectedLevel) {
          return false;
        }

        // Lab / Lecture filter
        if (selectedType === 'lab' && !c.is_lab) return false;
        if (selectedType === 'lecture' && c.is_lab) return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'code') return a.code.localeCompare(b.code);
        if (sortBy === 'title') return a.title.localeCompare(b.title);
        if (sortBy === 'credits') return b.credits - a.credits;
        if (sortBy === 'sections') {
          const secA = sectionsByCourse.get(a.id)?.length || 0;
          const secB = sectionsByCourse.get(b.id)?.length || 0;
          return secB - secA;
        }
        return 0;
      });
  }, [coursesList, searchQuery, selectedLevel, selectedType, sortBy, sectionsByCourse]);

  if (loadingCourses || loadingSections) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 animate-pulse">
          Loading curriculum catalog and scheduled course sections...
        </div>
      </div>
    );
  }

  if (errorCourses) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-rose-950/40 border border-rose-800 rounded-2xl p-6 text-rose-300">
          Failed to load course catalog: {(courseError as Error)?.message}
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
            <span className="pill">Academic Curriculum</span>
            <span className="text-xs text-slate-500 font-mono">{metrics.totalCourses} Active Courses</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-1" style={{ letterSpacing: '-0.03em' }}>
            Course Catalog & Syllabi Requirements
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Curricular offerings, credit weightings, contact hours, required faculty expertise tags, and class sections.
          </p>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total Courses</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">{metrics.totalCourses}</div>
          <div className="text-[11px] text-slate-500 mt-1">Curriculum catalog</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Active Sections</div>
          <div className="text-2xl font-bold mt-1 text-emerald-700 font-mono">{metrics.totalSections}</div>
          <div className="text-[11px] text-slate-500 mt-1">Scheduled class offerings</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Undergrad / Grad</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">
            {metrics.undergrad} / {metrics.grad}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Academic levels</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Lab Offerings</div>
          <div className="text-2xl font-bold mt-1 text-amber-700 font-mono">{metrics.labCourses}</div>
          <div className="text-[11px] text-slate-500 mt-1">Specialized lab rooms</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm col-span-2 sm:col-span-1">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Avg Contact Hours</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">{metrics.avgContact}h</div>
          <div className="text-[11px] text-slate-500 mt-1">Weekly instructional hrs</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search Bar */}
          <div>
            <label htmlFor="search-course" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Search Courses
            </label>
            <input
              id="search-course"
              type="text"
              placeholder="Search by code (e.g. CS101), title, or tag..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            />
          </div>

          {/* Level Filter */}
          <div>
            <label htmlFor="filter-level" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Course Level
            </label>
            <select
              id="filter-level"
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="all">All Levels</option>
              <option value="undergraduate">Undergraduate</option>
              <option value="graduate">Graduate</option>
              <option value="doctoral">Doctoral</option>
            </select>
          </div>

          {/* Lab / Lecture Filter */}
          <div>
            <label htmlFor="filter-type" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Course Type
            </label>
            <select
              id="filter-type"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as 'all' | 'lab' | 'lecture')}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="all">All Offerings</option>
              <option value="lecture">Standard Lectures</option>
              <option value="lab">Laboratories (🧪)</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label htmlFor="sort-courses-by" className="block text-[11px] font-semibold text-slate-500 uppercase mb-1">
              Sort By
            </label>
            <select
              id="sort-courses-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'code' | 'title' | 'credits' | 'sections')}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="code">Course Code</option>
              <option value="title">Course Title (A – Z)</option>
              <option value="credits">Credits (High to Low)</option>
              <option value="sections">Scheduled Sections Count</option>
            </select>
          </div>
        </div>

        {/* Status Line */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-200">
          <div>
            Showing <span className="font-semibold text-slate-900">{filteredCourses.length}</span> of {coursesList?.length} courses
          </div>
          {(searchQuery || selectedLevel !== 'all' || selectedType !== 'all') && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setSelectedLevel('all');
                setSelectedType('all');
              }}
              className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Courses Grid */}
      {filteredCourses.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
          No courses matched your search criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCourses.map((course) => {
            const courseSections = sectionsByCourse.get(course.id) || [];

            return (
              <div
                key={course.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Code, Level, Lab Badge */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-900 border border-slate-300">
                        {course.code}
                      </span>
                      <span
                        className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          LEVEL_BADGE_STYLES[course.level] || 'bg-slate-100 text-slate-800'
                        }`}
                      >
                        {course.level}
                      </span>
                    </div>

                    {course.is_lab && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                        <span>🧪</span>
                        <span>Lab</span>
                      </span>
                    )}
                  </div>

                  {/* Course Title & Description */}
                  <h3 className="text-base font-bold text-slate-900 mt-2.5 leading-snug">
                    {course.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {course.description || 'No course syllabus description provided.'}
                  </p>

                  {/* Credits & Contact Hours Pill Row */}
                  <div className="mt-3 flex items-center gap-2 text-xs">
                    <span className="px-2.5 py-1 rounded-md bg-slate-50 text-slate-700 font-semibold border border-slate-200">
                      {course.credits} Credits
                    </span>
                    <span className="px-2.5 py-1 rounded-md bg-slate-50 text-slate-700 font-mono border border-slate-200">
                      {course.contact_hours}h Contact/Wk
                    </span>
                    <span className="px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
                      {courseSections.length} {courseSections.length === 1 ? 'Section' : 'Sections'}
                    </span>
                  </div>

                  {/* Required Expertise Tags */}
                  <div className="mt-4">
                    <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1 flex items-center justify-between">
                      <span>Required Faculty Expertise</span>
                      <span className="text-[10px] text-slate-400">
                        Min Level: <strong className="font-mono text-slate-700">{course.min_proficiency}/5</strong>
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {course.required_tags && course.required_tags.length > 0 ? (
                        course.required_tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[10px] font-medium text-slate-800 shadow-2xs"
                          >
                            <span>🏷️</span>
                            <span>{tag}</span>
                          </span>
                        ))
                      ) : (
                        <span className="text-[11px] text-slate-400 italic">Open assignment (no mandatory tags)</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Footer Link & Actions */}
                <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-400">ID: {course.id}</span>
                  <button
                    type="button"
                    onClick={() => setSelectedCourse(course)}
                    className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold inline-flex items-center gap-1"
                  >
                    <span>View Sections</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Course Detail Modal */}
      {selectedCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-900 border border-slate-300">
                    {selectedCourse.code}
                  </span>
                  <span className="pill text-[10px]">{selectedCourse.level}</span>
                  {selectedCourse.is_lab && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                      🧪 Lab Required
                    </span>
                  )}
                </div>
                <h2 className="text-xl font-bold text-slate-900 mt-2">{selectedCourse.title}</h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedCourse(null)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
              {selectedCourse.description || 'No comprehensive course syllabus description registered.'}
            </p>

            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-[10px] uppercase font-semibold text-slate-500">Credits</div>
                <div className="text-sm font-bold text-slate-900 font-mono mt-0.5">{selectedCourse.credits}</div>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-[10px] uppercase font-semibold text-slate-500">Contact Hours</div>
                <div className="text-sm font-bold text-slate-900 font-mono mt-0.5">{selectedCourse.contact_hours}h/wk</div>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-[10px] uppercase font-semibold text-slate-500">Min Proficiency</div>
                <div className="text-sm font-bold text-emerald-700 font-mono mt-0.5">{selectedCourse.min_proficiency} / 5</div>
              </div>
            </div>

            {/* Sections for this course */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase">
                  Scheduled Class Sections ({sectionsByCourse.get(selectedCourse.id)?.length || 0})
                </h4>
              </div>

              {(!sectionsByCourse.get(selectedCourse.id) || sectionsByCourse.get(selectedCourse.id)!.length === 0) ? (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-center text-xs text-slate-400">
                  No active sections scheduled for this course in the current catalog.
                </div>
              ) : (
                <div className="space-y-2">
                  {sectionsByCourse.get(selectedCourse.id)!.map((sec) => (
                    <div
                      key={sec.id}
                      className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-slate-900">{sec.id}</span>
                          <span className="text-[11px] text-slate-500">{sec.term}</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          Time Slot: <span className="font-mono font-medium text-slate-700">{sec.time_slot_id || 'Unassigned'}</span>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-[11px] text-slate-600">
                          Capacity: <strong className="font-mono text-slate-900">{sec.section_cap} seats</strong>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          Exp: {sec.expected_size} (P10: {sec.size_p10} | P90: {sec.size_p90})
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedCourse(null)}
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
export default CoursesCatalogPage;

