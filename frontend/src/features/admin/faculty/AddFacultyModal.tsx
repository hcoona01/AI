import React, { useState } from 'react';
import { useCreateFaculty } from '../api';
import type { Faculty, FacultyRank } from '../../../types';

interface AddFacultyModalProps {
  onClose: () => void;
}

const RANKS: FacultyRank[] = [
  'Professor',
  'Associate Professor',
  'Assistant Professor',
  'Lecturer',
  'Adjunct',
  'Visiting',
];

const initialForm = {
  id: '',
  name: '',
  email: '',
  rank: 'Assistant Professor' as FacultyRank,
  maxWeeklyLoad: '12',
  minCourses: '1',
  maxCourses: '3',
  maxPreparations: '2',
  expertiseTags: '',
  proficiency: '3',
};

export const AddFacultyModal: React.FC<AddFacultyModalProps> = ({ onClose }) => {
  const [form, setForm] = useState(initialForm);
  const [validationError, setValidationError] = useState<string | null>(null);
  const createFaculty = useCreateFaculty();

  const update = (field: keyof typeof initialForm, value: string): void => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    setValidationError(null);

    const id = form.id.trim();
    const name = form.name.trim();
    const email = form.email.trim().toLowerCase();
    const maxWeeklyLoad = Number(form.maxWeeklyLoad);
    const minCourses = Number(form.minCourses);
    const maxCourses = Number(form.maxCourses);
    const maxPreparations = Number(form.maxPreparations);
    const proficiency = Number(form.proficiency);

    if (!id || !name || !email) {
      setValidationError('Faculty ID, full name, and institutional email are required.');
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setValidationError('Enter a valid institutional email address.');
      return;
    }
    if (maxWeeklyLoad <= 0 || minCourses < 0 || maxCourses < minCourses || maxPreparations > maxCourses) {
      setValidationError('Check the load limits: maximum courses must cover the minimum, and preparations cannot exceed maximum courses.');
      return;
    }

    const expertise = [...new Set(form.expertiseTags.split(',').map((tag) => tag.trim()).filter(Boolean))]
      .map((tag) => ({ tag, proficiency }));
    const faculty: Faculty = {
      id,
      name,
      email,
      rank: form.rank,
      expertise,
      max_weekly_load_hours: maxWeeklyLoad,
      min_courses: minCourses,
      max_courses: maxCourses,
      max_preparations: maxPreparations,
      unavailable_slots: [],
      leave_terms: [],
      preferred_course_ids: [],
    };

    createFaculty.mutate(faculty, { onSuccess: onClose });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-5 max-h-[90vh] overflow-y-auto" aria-labelledby="add-faculty-title">
        <div className="flex items-start justify-between gap-4">
          <div>
            <span className="pill text-[10px]">Directory management</span>
            <h2 id="add-faculty-title" className="text-xl font-bold text-slate-900 mt-1">Add faculty member</h2>
            <p className="text-xs text-slate-600 mt-1">Create a profile that the optimizer can evaluate for future teaching assignments.</p>
          </div>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-900 text-xl font-bold" aria-label="Close add faculty form">×</button>
        </div>

        {(validationError || createFaculty.isError) && (
          <div role="alert" className="rounded-lg border border-rose-300 bg-rose-50 p-3 text-xs text-rose-800">
            {validationError || createFaculty.error?.message || 'Unable to create the faculty profile.'}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="text-xs font-semibold text-slate-700">Faculty ID<input required value={form.id} onChange={(event) => update('id', event.target.value)} placeholder="f-026" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono font-normal" /></label>
          <label className="text-xs font-semibold text-slate-700">Academic rank<select value={form.rank} onChange={(event) => update('rank', event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal">{RANKS.map((rank) => <option key={rank} value={rank}>{rank}</option>)}</select></label>
          <label className="text-xs font-semibold text-slate-700">Full name<input required value={form.name} onChange={(event) => update('name', event.target.value)} placeholder="Dr. Grace Hopper" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" /></label>
          <label className="text-xs font-semibold text-slate-700">Institutional email<input required type="email" value={form.email} onChange={(event) => update('email', event.target.value)} placeholder="grace.hopper@university.edu" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" /></label>
          <label className="text-xs font-semibold text-slate-700">Weekly hours<input required min="0.5" max="80" step="0.5" type="number" value={form.maxWeeklyLoad} onChange={(event) => update('maxWeeklyLoad', event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" /></label>
          <label className="text-xs font-semibold text-slate-700">Minimum courses<input required min="0" max="10" type="number" value={form.minCourses} onChange={(event) => update('minCourses', event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" /></label>
          <label className="text-xs font-semibold text-slate-700">Maximum courses<input required min="0" max="10" type="number" value={form.maxCourses} onChange={(event) => update('maxCourses', event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" /></label>
          <label className="text-xs font-semibold text-slate-700">Maximum preparations<input required min="0" max="10" type="number" value={form.maxPreparations} onChange={(event) => update('maxPreparations', event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" /></label>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[1fr_9rem] gap-3">
          <label className="text-xs font-semibold text-slate-700">Expertise tags <span className="font-normal text-slate-500">(comma-separated)</span><input value={form.expertiseTags} onChange={(event) => update('expertiseTags', event.target.value)} placeholder="Algorithms, Machine Learning" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" /></label>
          <label className="text-xs font-semibold text-slate-700">Proficiency<select value={form.proficiency} onChange={(event) => update('proficiency', event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal">{[1, 2, 3, 4, 5].map((level) => <option key={level} value={level}>{level} / 5</option>)}</select></label>
        </div>

        <div className="flex justify-end gap-3 border-t border-slate-200 pt-4">
          <button type="button" onClick={onClose} className="rounded-lg px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100">Cancel</button>
          <button type="submit" disabled={createFaculty.isPending} className="btn text-xs px-4 disabled:cursor-not-allowed disabled:opacity-60">{createFaculty.isPending ? 'Creating…' : 'Create faculty profile'}</button>
        </div>
      </form>
    </div>
  );
};
