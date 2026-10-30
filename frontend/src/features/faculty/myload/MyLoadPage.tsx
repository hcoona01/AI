import { Link } from 'react-router-dom';

export const MyLoadPage = () => {
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2.5 py-1 rounded-md border border-purple-500/20">
            Faculty Portal
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2">My Teaching Schedule & Workload</h1>
          <p className="text-sm text-slate-400 mt-1">
            Review assigned courses, semester credit hours, and submitted expertise tags.
          </p>
        </div>
        <Link
          to="/"
          className="self-start md:self-auto px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition"
        >
          &larr; Landing Page
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Assigned Credit Hours</div>
          <div className="text-3xl font-bold text-white mt-2">9.0 / 9.0</div>
          <div className="text-xs text-emerald-400 mt-2 font-mono">100% Target Met</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Assigned Sections</div>
          <div className="text-3xl font-bold text-white mt-2">3</div>
          <div className="text-xs text-purple-400 mt-2 font-mono">Undergraduate & Graduate</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Expertise Tag Match</div>
          <div className="text-3xl font-bold text-blue-400 mt-2">96%</div>
          <div className="text-xs text-slate-400 mt-2 font-mono">High Syllabus Fit</div>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-2">Availability & Preference Exceptions</h2>
        <p className="text-sm text-slate-400 mb-4">
          Submit blackout dates, preferred time slots, or course interest tags for the upcoming academic cycle.
        </p>
        <div className="flex flex-wrap gap-3">
          <button disabled className="px-4 py-2 bg-purple-600/50 text-purple-200 text-sm font-medium rounded-lg cursor-not-allowed">
            Submit Time Exceptions
          </button>
          <button disabled className="px-4 py-2 bg-slate-800 text-slate-400 text-sm font-medium rounded-lg cursor-not-allowed">
            Update Research & Expertise Tags
          </button>
        </div>
      </div>
    </div>
  );
};
