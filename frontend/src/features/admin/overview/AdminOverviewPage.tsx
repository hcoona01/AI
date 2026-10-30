import { Link } from 'react-router-dom';

export const AdminOverviewPage = () => {
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md border border-blue-500/20">
            Admin Workspace
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-white mt-2">Department Planning & Workload Balancing</h1>
          <p className="text-sm text-slate-400 mt-1">
            Overview of course assignments, forecast quantiles, and workload fairness metrics.
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
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Target Course Sections</div>
          <div className="text-3xl font-bold text-white mt-2">48</div>
          <div className="text-xs text-emerald-400 mt-2 font-mono">P50 Expected Demand</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Fairness Index (Gini)</div>
          <div className="text-3xl font-bold text-white mt-2">0.12</div>
          <div className="text-xs text-blue-400 mt-2 font-mono">Target: &lt; 0.15 (Balanced)</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-xl">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Unassigned / Conflict Count</div>
          <div className="text-3xl font-bold text-amber-400 mt-2">0</div>
          <div className="text-xs text-slate-400 mt-2 font-mono">Hard Constraints (HC) 100% Met</div>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-2">Solver Configuration & Fast Actions</h2>
        <p className="text-sm text-slate-400 mb-4">
          The CP-SAT multi-objective optimization engine balances expertise fit, time feasibility, and rank-adjusted teaching loads.
        </p>
        <div className="flex flex-wrap gap-3">
          <button disabled className="px-4 py-2 bg-blue-600/50 text-blue-200 text-sm font-medium rounded-lg cursor-not-allowed">
            Run CP-SAT Solver (P50)
          </button>
          <button disabled className="px-4 py-2 bg-slate-800 text-slate-400 text-sm font-medium rounded-lg cursor-not-allowed">
            Run Greedy Baseline
          </button>
          <button disabled className="px-4 py-2 bg-slate-800 text-slate-400 text-sm font-medium rounded-lg cursor-not-allowed">
            Audit Trail
          </button>
        </div>
      </div>
    </div>
  );
};
