import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { BrandMark } from '../brand/BrandMark';
import { DashboardBackground } from './DashboardBackground';

interface NavItem {
  name: string;
  path: string;
  icon: string;
  end?: boolean;
}

const adminNavItems: NavItem[] = [
  { name: 'Overview & Metrics', path: '/admin', icon: '📊', end: true },
  { name: 'Course Assignments', path: '/admin/assignments', icon: '📋' },
  { name: 'Conflicts & Diagnostics', path: '/admin/conflicts', icon: '⚠️' },
  { name: 'Manual Overrides', path: '/admin/overrides', icon: '✍️' },
  { name: 'Demand Forecasts', path: '/admin/forecasts', icon: '📈' },
  { name: 'Faculty Directory', path: '/admin/faculty', icon: '👨‍🏫' },
  { name: 'Courses & Syllabi', path: '/admin/courses', icon: '📚' },
  { name: 'Constraints & Rules', path: '/admin/constraints', icon: '⚖️' },
  { name: 'Scenarios & Tests', path: '/admin/scenarios', icon: '🧪' },
  { name: 'Audit Trail', path: '/admin/audit', icon: '📜' },
];

export const AdminLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="app-shell dashboard-shell min-h-screen flex flex-col md:flex-row relative">
      <DashboardBackground />
      <aside
        className={`app-aside fixed top-0 left-0 bottom-0 z-40 h-screen w-64 flex flex-col transition-transform duration-200 ease-in-out ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center justify-between">
            <span className="pill">Admin console</span>
            <button
              type="button"
              onClick={() => setMobileMenuOpen(false)}
              className="md:hidden text-slate-400 hover:text-slate-100"
              aria-label="Close navigation menu"
            >
              ✕
            </button>
          </div>
          <Link to="/" className="brand mt-3" style={{ fontSize: 20 }}>
            <BrandMark />
            <span>workload</span>
          </Link>
          <p className="text-xs text-slate-400 mt-1">Balancing & assignment</p>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto" aria-label="Admin Navigation">
          {adminNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition ${
                  isActive
                    ? 'nav-active'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
            >
              <span className="text-sm leading-none">{item.icon}</span>
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500 flex justify-between items-center">
          <span>v0.1.0 • Dev Mode</span>
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" title="Connected" />
        </div>
      </aside>

      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs z-30 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className="dashboard-content flex-1 md:pl-64 flex flex-col min-w-0">
        <header className="app-topbar sticky top-0 z-20 h-16 px-4 sm:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
              aria-label="Open navigation menu"
            >
              ☰
            </button>
            <div className="hidden sm:block text-xs font-medium text-slate-400">
              Department Administration Portal
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs font-mono font-medium text-slate-200">
                {user?.email || 'admin@university.edu'}
              </div>
              <div className="flex items-center justify-end gap-1.5 mt-0.5">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400" />
                <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider">
                  Admin
                </span>
              </div>
            </div>

            <div className="h-6 w-[1px] bg-slate-800" />

            <button
              type="button"
              onClick={() => void handleLogout()}
              className="px-3 py-1.5 rounded-full bg-white hover:bg-rose-50 border border-slate-700 hover:border-rose-800/60 text-xs font-medium text-slate-300 transition cursor-pointer"
              title="Sign Out of Session"
            >
              Sign Out
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
