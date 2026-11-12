import React, { useMemo, useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext';
import {
  useMyFacultyProfile,
  useFacultyCourses,
  useUpdateFacultyPreferences,
} from '../api';
import type { Course, FacultyExpertise } from '../../../types';

const PROFICIENCY_LABELS: Record<number, string> = {
  1: 'Novice (Foundational concepts)',
  2: 'Familiar (Working knowledge)',
  3: 'Competent (Standard university level)',
  4: 'Advanced (Specialized / Upper division)',
  5: 'Expert (Lead researcher / Doctoral level)',
};

const SUGGESTED_TAGS = [
  'Algorithms',
  'Theory of Computation',
  'Artificial Intelligence',
  'Machine Learning',
  'Deep Learning',
  'Data Structures',
  'Operating Systems',
  'Computer Networks',
  'Databases',
  'Distributed Systems',
  'Cybersecurity',
  'Cryptography',
  'Software Engineering',
  'Programming Languages',
  'Compilers',
  'Computer Architecture',
  'Cloud Computing',
  'Web Development',
  'Human-Computer Interaction',
  'Computer Graphics',
  'Robotics',
  'Bioinformatics',
  'Quantum Computing',
];

interface CourseFitAnalysis {
  course: Course;
  fitScore: number; // 0 to 100
  qualificationLevel: 'fully_qualified' | 'partially_qualified' | 'ineligible';
  missingTags: string[];
  matchedTags: { tag: string; required: number; actual: number }[];
  isPreferred: boolean;
}

export const ExpertiseFitPage: React.FC = () => {
  const { user } = useAuth();
  const facultyId = user?.faculty_id || 'f-01';

  const { data: faculty, isLoading: loadingFaculty, isError: errorFaculty } = useMyFacultyProfile(facultyId);
  const { data: courses, isLoading: loadingCourses } = useFacultyCourses();

  const updateMutation = useUpdateFacultyPreferences(facultyId);

  // Local state for interactive expertise editing
  const [localExpertise, setLocalExpertise] = useState<FacultyExpertise[]>([]);
  const [preferredCourses, setPreferredCourses] = useState<string[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Add new tag state
  const [newTagInput, setNewTagInput] = useState('');
  const [newProficiency, setNewProficiency] = useState<number>(3);

  // Filter state for courses
  const [courseSearch, setCourseSearch] = useState('');
  const [fitFilter, setFitFilter] = useState<'all' | 'qualified' | 'partial' | 'preferred'>('all');

  useEffect(() => {
    if (faculty) {
      setLocalExpertise(faculty.expertise || []);
      setPreferredCourses(faculty.preferred_course_ids || []);
      setIsDirty(false);
    }
  }, [faculty]);

  const handleSetProficiency = (tag: string, level: number) => {
    setLocalExpertise((prev) =>
      prev.map((e) => (e.tag === tag ? { ...e, proficiency: level } : e))
    );
    setIsDirty(true);
    setSaveSuccess(null);
  };

  // Handle removing a tag
  const handleRemoveTag = (tag: string) => {
    setLocalExpertise((prev) => prev.filter((e) => e.tag !== tag));
    setIsDirty(true);
    setSaveSuccess(null);
  };

  // Handle adding a new tag
  const handleAddTag = () => {
    const cleanTag = newTagInput.trim();
    if (!cleanTag) return;

    if (localExpertise.some((e) => e.tag.toLowerCase() === cleanTag.toLowerCase())) {
      return; // Already exists
    }

    setLocalExpertise((prev) => [...prev, { tag: cleanTag, proficiency: newProficiency }]);
    setNewTagInput('');
    setNewProficiency(3);
    setIsDirty(true);
    setSaveSuccess(null);
  };

  // Toggle preferred course
  const handleTogglePreference = (courseId: string) => {
    setPreferredCourses((prev) => {
      const exists = prev.includes(courseId);
      const updated = exists ? prev.filter((c) => c !== courseId) : [...prev, courseId];
      return updated;
    });
    setIsDirty(true);
    setSaveSuccess(null);
  };

  // Save changes
  const handleSave = () => {
    if (!faculty) return;

    updateMutation.mutate(
      {
        unavailable_slots: faculty.unavailable_slots,
        leave_terms: faculty.leave_terms,
        preferred_course_ids: preferredCourses,
        expertise: localExpertise,
      },
      {
        onSuccess: () => {
          setIsDirty(false);
          setSaveSuccess('Expertise competencies and preferences saved! Active for subsequent optimizer assignments.');
          setTimeout(() => setSaveSuccess(null), 5000);
        },
      }
    );
  };

  // Discard changes
  const handleReset = () => {
    if (faculty) {
      setLocalExpertise(faculty.expertise || []);
      setPreferredCourses(faculty.preferred_course_ids || []);
      setIsDirty(false);
      setSaveSuccess(null);
    }
  };

  // Calculate Syllabi Fit for all courses
  const courseFitList: CourseFitAnalysis[] = useMemo(() => {
    if (!courses) return [];

    const facultyMap = new Map<string, number>();
    localExpertise.forEach((e) => facultyMap.set(e.tag.toLowerCase(), e.proficiency));

    return courses.map((course) => {
      const reqTags = course.required_tags || [];
      const minProf = course.min_proficiency || 1;

      if (reqTags.length === 0) {
        return {
          course,
          fitScore: 100,
          qualificationLevel: 'fully_qualified',
          missingTags: [],
          matchedTags: [],
          isPreferred: preferredCourses.includes(course.id),
        };
      }

      let satisfiedCount = 0;
      const missingTags: string[] = [];
      const matchedTags: { tag: string; required: number; actual: number }[] = [];

      reqTags.forEach((tag) => {
        const actual = facultyMap.get(tag.toLowerCase()) || 0;
        if (actual >= minProf) {
          satisfiedCount += 1;
          matchedTags.push({ tag, required: minProf, actual });
        } else if (actual > 0) {
          // Partial proficiency
          satisfiedCount += 0.5;
          matchedTags.push({ tag, required: minProf, actual });
        } else {
          missingTags.push(tag);
        }
      });

      const fitScore = Math.round((satisfiedCount / reqTags.length) * 100);
      let qualificationLevel: 'fully_qualified' | 'partially_qualified' | 'ineligible' = 'ineligible';

      if (fitScore >= 95) {
        qualificationLevel = 'fully_qualified';
      } else if (fitScore >= 40) {
        qualificationLevel = 'partially_qualified';
      }

      return {
        course,
        fitScore,
        qualificationLevel,
        missingTags,
        matchedTags,
        isPreferred: preferredCourses.includes(course.id),
      };
    });
  }, [courses, localExpertise, preferredCourses]);

  // Filtered course fit
  const filteredCourses = useMemo(() => {
    return courseFitList.filter((item) => {
      // Search
      if (courseSearch.trim()) {
        const q = courseSearch.toLowerCase().trim();
        const matchCode = item.course.code.toLowerCase().includes(q);
        const matchTitle = item.course.title.toLowerCase().includes(q);
        const matchTag = item.course.required_tags?.some((t) => t.toLowerCase().includes(q));
        if (!matchCode && !matchTitle && !matchTag) return false;
      }

      // Filter
      if (fitFilter === 'qualified' && item.qualificationLevel !== 'fully_qualified') return false;
      if (fitFilter === 'partial' && item.qualificationLevel !== 'partially_qualified') return false;
      if (fitFilter === 'preferred' && !item.isPreferred) return false;

      return true;
    });
  }, [courseFitList, courseSearch, fitFilter]);

  // Metrics
  const fullyQualifiedCount = courseFitList.filter((c) => c.qualificationLevel === 'fully_qualified').length;
  const partialCount = courseFitList.filter((c) => c.qualificationLevel === 'partially_qualified').length;
  const expertTagsCount = localExpertise.filter((e) => e.proficiency >= 4).length;

  if (loadingFaculty || loadingCourses) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 animate-pulse">
          Loading faculty profile and curriculum syllabi qualifications...
        </div>
      </div>
    );
  }

  if (errorFaculty || !faculty) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        <div className="bg-rose-950/40 border border-rose-800 rounded-2xl p-6 text-rose-300">
          Failed to load faculty expertise profile. Please verify credentials.
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
            <span className="pill">Faculty Instructional Profile</span>
            <span className="text-xs text-slate-500 font-mono">{faculty.name} ({faculty.rank})</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-1" style={{ letterSpacing: '-0.03em' }}>
            Expertise & Syllabi Fit Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Maintain your research tags, self-evaluated proficiencies (1 to 5), and review eligibility matching across department courses.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {isDirty && (
            <button
              type="button"
              onClick={handleReset}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Discard
            </button>
          )}
          <button
            type="button"
            disabled={!isDirty || updateMutation.isPending}
            onClick={handleSave}
            className={`btn text-xs px-4 py-2 ${
              isDirty
                ? 'bg-emerald-700 hover:bg-emerald-800 text-white'
                : 'opacity-50 cursor-not-allowed'
            }`}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Profile Changes'}
          </button>
        </div>
      </div>

      {/* Save Success Alert */}
      {saveSuccess && (
        <div className="bg-emerald-50 border border-emerald-300 rounded-xl p-3.5 text-xs text-emerald-900 flex items-center gap-2">
          <span className="text-emerald-700 font-bold">✓</span>
          <span>{saveSuccess}</span>
        </div>
      )}

      {/* KPI Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Registered Competencies</div>
          <div className="text-2xl font-bold mt-1 text-slate-900 font-mono">{localExpertise.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Specialized domains</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Fully Qualified Courses</div>
          <div className="text-2xl font-bold mt-1 text-emerald-700 font-mono">{fullyQualifiedCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Meets 100% syllabus criteria</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Partial Competency Fit</div>
          <div className="text-2xl font-bold mt-1 text-amber-700 font-mono">{partialCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Foundational knowledge match</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Lead Specialties (★4-5)</div>
          <div className="text-2xl font-bold mt-1 text-purple-700 font-mono">{expertTagsCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Doctoral & advanced courses</div>
        </div>
      </div>

      {/* SECTION 1: INTERACTIVE EXPERTISE EDITOR */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🎯</span>
              <span>My Teaching Competencies & Proficiencies</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Proficiency levels directly feed the CP-SAT solver objective function ($SC-01$) and qualification constraints ($HC-01$).
            </p>
          </div>
          {isDirty && (
            <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 self-start sm:self-auto">
              ● Unsaved changes
            </span>
          )}
        </div>

        {/* Current Competencies List */}
        <div className="space-y-2">
          {localExpertise.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-200">
              No competencies registered. Use the form below to add your research and teaching domains.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {localExpertise.map((exp) => (
                <div
                  key={exp.tag}
                  className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between shadow-2xs hover:border-slate-300 transition"
                >
                  <div className="space-y-0.5">
                    <div className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      <span>🏷️</span>
                      <span>{exp.tag}</span>
                    </div>
                    <div className="text-[10px] text-slate-500">
                      {PROFICIENCY_LABELS[exp.proficiency] || `Level ${exp.proficiency}`}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {/* Interactive Star Buttons */}
                    <div className="flex items-center">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => handleSetProficiency(exp.tag, star)}
                          className={`text-sm px-0.5 transition ${
                            star <= exp.proficiency
                              ? 'text-amber-500 hover:text-amber-600'
                              : 'text-slate-300 hover:text-slate-400'
                          }`}
                          title={`Set proficiency to ${star} of 5`}
                        >
                          ★
                        </button>
                      ))}
                    </div>

                    <span className="font-mono font-bold text-xs text-slate-900 w-6 text-right">
                      {exp.proficiency}/5
                    </span>

                    {/* Remove Tag */}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(exp.tag)}
                      className="text-slate-400 hover:text-rose-600 text-xs px-1.5 py-0.5 rounded hover:bg-rose-50 transition"
                      title="Remove competency"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add New Tag Bar */}
        <div className="pt-3 border-t border-slate-200">
          <div className="text-xs font-semibold text-slate-700 mb-2">Add Competency / Research Specialty</div>
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                list="suggested-tags-list"
                placeholder="Enter or select tag (e.g. Distributed Systems, Quantum Computing)..."
                value={newTagInput}
                onChange={(e) => setNewTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
              />
              <datalist id="suggested-tags-list">
                {SUGGESTED_TAGS.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
            </div>

            <div className="w-full sm:w-44">
              <select
                value={newProficiency}
                onChange={(e) => setNewProficiency(Number(e.target.value))}
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
              >
                <option value={1}>★ 1 - Novice</option>
                <option value={2}>★★ 2 - Familiar</option>
                <option value={3}>★★★ 3 - Competent</option>
                <option value={4}>★★★★ 4 - Advanced</option>
                <option value={5}>★★★★★ 5 - Lead Expert</option>
              </select>
            </div>

            <button
              type="button"
              onClick={handleAddTag}
              disabled={!newTagInput.trim()}
              className="btn text-xs px-4 py-2 disabled:opacity-50"
            >
              + Add Tag
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 2: CURRICULUM SYLLABI FIT MATRIX */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>📚</span>
              <span>Curriculum Syllabi Qualification & Matching Matrix</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live automated matching between your current competencies and course catalog syllabus requirements.
            </p>
          </div>

          {/* Fit Filter & Search */}
          <div className="flex flex-col sm:flex-row items-center gap-2">
            <select
              value={fitFilter}
              onChange={(e) => setFitFilter(e.target.value as 'all' | 'qualified' | 'partial' | 'preferred')}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="all">All Catalog Courses ({courseFitList.length})</option>
              <option value="qualified">Fully Qualified Only ({fullyQualifiedCount})</option>
              <option value="partial">Partial Fit Only ({partialCount})</option>
              <option value="preferred">My Preferred Courses ({preferredCourses.length})</option>
            </select>

            <input
              type="text"
              placeholder="Search by code or title..."
              value={courseSearch}
              onChange={(e) => setCourseSearch(e.target.value)}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            />
          </div>
        </div>

        {/* Courses Fit Cards Grid */}
        {filteredCourses.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-200">
            No department courses match your current search and qualification filter.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredCourses.map((item) => {
              const { course, fitScore, qualificationLevel, missingTags, matchedTags, isPreferred } = item;

              let badgeBg = 'bg-rose-50 text-rose-800 border-rose-200';
              let badgeText = 'Ineligible (Skill Gap)';
              if (qualificationLevel === 'fully_qualified') {
                badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-300';
                badgeText = 'Fully Qualified (Eligible)';
              } else if (qualificationLevel === 'partially_qualified') {
                badgeBg = 'bg-amber-50 text-amber-800 border-amber-300';
                badgeText = 'Partially Qualified';
              }

              return (
                <div
                  key={course.id}
                  className={`bg-white rounded-xl p-4 border transition flex flex-col justify-between shadow-2xs ${
                    isPreferred
                      ? 'border-emerald-500 ring-1 ring-emerald-200'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div>
                    {/* Top Row: Code, Level, Fit Badge */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                          {course.code}
                        </span>
                        <span className="text-[10px] uppercase font-semibold text-slate-500">
                          {course.level}
                        </span>
                      </div>

                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeBg}`}>
                        <span>{badgeText}</span>
                        <span>•</span>
                        <span>{fitScore}%</span>
                      </span>
                    </div>

                    {/* Course Title */}
                    <h3 className="text-sm font-bold text-slate-900 mt-2 leading-tight">
                      {course.title}
                    </h3>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      {course.credits} Credits • {course.contact_hours}h/wk {course.is_lab ? '• 🧪 Lab' : ''}
                    </div>

                    {/* Required Syllabus Criteria & Matches */}
                    <div className="mt-3 space-y-1.5 text-xs">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 flex items-center justify-between">
                        <span>Syllabus Requirements</span>
                        <span>Min Req: ★{course.min_proficiency}</span>
                      </div>

                      {course.required_tags && course.required_tags.length > 0 ? (
                        <div className="space-y-1">
                          {matchedTags.map((m) => (
                            <div
                              key={m.tag}
                              className="flex items-center justify-between text-[11px] px-2 py-1 rounded bg-emerald-50/70 border border-emerald-200 text-emerald-900"
                            >
                              <span className="font-medium">✓ {m.tag}</span>
                              <span className="font-mono text-[10px]">
                                You: ★{m.actual} (Req: ★{m.required})
                              </span>
                            </div>
                          ))}

                          {missingTags.map((tag) => (
                            <div
                              key={tag}
                              className="flex items-center justify-between text-[11px] px-2 py-1 rounded bg-rose-50/70 border border-rose-200 text-rose-800"
                            >
                              <span className="font-medium">✕ {tag}</span>
                              <span className="font-mono text-[10px]">Missing</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-[11px] text-slate-400 italic">
                          Open teaching qualification (no mandatory tags)
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Footer Preference Button */}
                  <div className="mt-4 pt-2.5 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-mono">
                      {qualificationLevel === 'fully_qualified' ? 'Eligible for solver' : 'Prerequisites unmet'}
                    </span>

                    <button
                      type="button"
                      onClick={() => handleTogglePreference(course.id)}
                      className={`text-xs px-2.5 py-1 rounded-md font-semibold transition flex items-center gap-1 ${
                        isPreferred
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200'
                      }`}
                    >
                      <span>{isPreferred ? '★ Preferred' : '+ Prefer Course'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
export default ExpertiseFitPage;
