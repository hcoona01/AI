import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth, HealthResponse, API_BASE_URL } from '../../lib/apiClient';
import { useAuth } from '../auth/AuthContext';

export const LandingPage = () => {
  const { user, isAuthenticated } = useAuth();
  const dashboardLink = user?.role === 'admin' ? '/admin' : '/faculty';

  const { data: health, isLoading, isError, error, refetch, isFetching } = useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 10000, // auto-refresh every 10s
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-blue-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
              U
            </div>
            <span className="font-semibold tracking-tight text-white text-base">
              Faculty Workload Balancing System
            </span>
          </div>

          <nav className="flex items-center space-x-3 text-sm">
            {isAuthenticated && user ? (
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400 font-mono hidden sm:inline">
                  {user.email}
                </span>
                <Link
                  to={dashboardLink}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition shadow-md shadow-blue-600/20 text-xs sm:text-sm"
                >
                  Dashboard &rarr;
                </Link>
              </div>
            ) : (
              <Link
                to="/login"
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition shadow-md shadow-blue-600/20"
              >
                Sign In
              </Link>
            )}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12 flex-1 w-full space-y-12">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            AI-Assisted Academic Resource Optimization
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">
            Course Assignment & Workload Balancing
          </h1>
          <p className="text-base md:text-lg text-slate-400 leading-relaxed">
            Integrating quantile demand forecasting, faculty expertise matching, and Google OR-Tools CP-SAT constraint reasoning with quantified fairness metrics.
          </p>
        </div>

        {/* Backend Health Check Acceptance Banner */}
        <div className="max-w-4xl mx-auto bg-slate-900/90 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl backdrop-blur-sm relative overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <div className="text-xs font-medium uppercase tracking-wider text-slate-400">
                System Integration Status
              </div>
              <h2 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
                FastAPI Backend Health
                {isLoading && (
                  <span className="text-xs font-normal text-slate-400 animate-pulse">
                    (Connecting...)
                  </span>
                )}
              </h2>
              <div className="text-xs text-slate-500 font-mono mt-0.5">
                Target endpoint: <span className="text-slate-400">{API_BASE_URL}/health</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {isLoading ? (
                <div className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping mr-2"></span>
                  Checking...
                </div>
              ) : health?.status === 'healthy' ? (
                <div className="inline-flex items-center px-3.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm shadow-emerald-500/10">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 mr-2"></span>
                  BACKEND ONLINE (200 OK)
                </div>
              ) : (
                <div className="inline-flex items-center px-3.5 py-1.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                  <span className="w-2 h-2 rounded-full bg-rose-400 mr-2"></span>
                  DISCONNECTED
                </div>
              )}

              <button
                onClick={() => refetch()}
                disabled={isFetching}
                className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition disabled:opacity-50"
              >
                {isFetching ? 'Refreshing...' : 'Recheck'}
              </button>
            </div>
          </div>

          {/* Health Details Grid */}
          {health ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6">
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400 block font-medium">Service Name</span>
                <span className="text-sm font-semibold text-slate-200 mt-1 block truncate">
                  {health.service}
                </span>
              </div>
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400 block font-medium">API Version</span>
                <span className="text-sm font-semibold text-blue-400 mt-1 block font-mono">
                  v{health.version}
                </span>
              </div>
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400 block font-medium">Store Backend</span>
                <span className="text-sm font-semibold text-emerald-400 mt-1 block uppercase font-mono">
                  {health.store_backend}
                </span>
              </div>
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                <span className="text-xs text-slate-400 block font-medium">Forecast Mode</span>
                <span className="text-sm font-semibold text-indigo-400 mt-1 block uppercase font-mono">
                  {health.forecast_mode}
                </span>
              </div>
            </div>
          ) : isError ? (
            <div className="pt-6">
              <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/50 text-rose-300 text-sm flex flex-col gap-2">
                <span className="font-semibold">Unable to connect to FastAPI Backend</span>
                <span className="text-xs text-rose-400">
                  {error?.message || 'Network request failed. Ensure backend is running via `make dev-backend` on port 8000.'}
                </span>
              </div>
            </div>
          ) : null}
        </div>

        {/* Dashboard Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          <Link
            to="/admin"
            className="group block p-6 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-blue-500/40 transition shadow-lg"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md border border-blue-500/20">
                Department Chair
              </span>
              <span className="text-slate-500 group-hover:text-blue-400 transition">&rarr;</span>
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition">
              Admin Planner Portal
            </h3>
            <p className="text-sm text-slate-400 mt-2">
              Run CP-SAT solver, review demand quantiles (P10/P50/P90), monitor Gini fairness, and perform auditable manual overrides.
            </p>
          </Link>

          <Link
            to="/faculty"
            className="group block p-6 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-purple-500/40 transition shadow-lg"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2.5 py-1 rounded-md border border-purple-500/20">
                Instructors & Professors
              </span>
              <span className="text-slate-500 group-hover:text-purple-400 transition">&rarr;</span>
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-purple-400 transition">
              Faculty Load View
            </h3>
            <p className="text-sm text-slate-400 mt-2">
              View assigned course sections, verify credit hour allocation against contractual targets, and submit availability preferences.
            </p>
          </Link>

          <Link
            to="/login"
            className="group block p-6 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-emerald-500/40 transition shadow-lg"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                Security & RBAC
              </span>
              <span className="text-slate-500 group-hover:text-emerald-400 transition">&rarr;</span>
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-emerald-400 transition">
              OTP Authentication
            </h3>
            <p className="text-sm text-slate-400 mt-2">
              Role-based passwordless access with email-delivered one-time passcodes and secure JWT session management.
            </p>
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        University Faculty Workload & Course Assignment Balancing System &bull; CPU-Only LightGBM + OR-Tools Architecture
      </footer>
    </div>
  );
};
