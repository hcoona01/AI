import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';

interface NavItem {
  name: string;
  path: string;
  icon: string;
  end?: boolean;
}

const adminNavItems: NavItem[] = [
  { name: 'Overview & Metrics', path: '/admin', icon: '📊', end: true },
  { name: 'Course Assignments', path: '/admin/assignments', icon: '📋' },
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
    <div className="min-h-screen bg-slate-950 flex flex-col md:flex-row text-slate-100">
      {/* Sidebar - Desktop & Tablet */}
      <aside
        className={`fixed md:sticky top-0 z-40 h-screen w-64 bg-slate-900 border-r border-slate-800 flex flex-col transition-transform duration-200 ease-in-out ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand / Header */}
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              ADMIN CONSOLE
            </span>
            <button
              type="button"
              onClick={() => setMobileMenuOpen(false)}
              className="md:hidden text-slate-400 hover:text-white"
              aria-label="Close navigation menu"
            >
              ✕
            </button>
          </div>
          <h2 className="text-base font-bold text-white mt-2 leading-tight">Faculty Workload</h2>
          <p className="text-xs text-slate-400 mt-0.5">Balancing & Assignment</p>
        </div>

        {/* Navigation Links */}
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
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <span className="text-sm leading-none">{item.icon}</span>
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-500 flex justify-between items-center">
          <span>v0.1.0 • Dev Mode</span>
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" title="Connected" />
        </div>
      </aside>

      {/* Backdrop for mobile drawer */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs z-30 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="sticky top-0 z-20 h-16 bg-slate-900/90 border-b border-slate-800 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              aria-label="Open navigation menu"
            >
              ☰
            </button>
            <div className="hidden sm:block text-xs font-medium text-slate-400">
              Department Administration Portal
            </div>
          </div>

          {/* User Info & Logout */}
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
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/50 hover:text-rose-300 border border-slate-700 hover:border-rose-800/60 text-xs font-medium text-slate-300 transition cursor-pointer flex items-center gap-1.5"
              title="Sign Out of Session"
            >
              <span>Sign Out</span>
              <span className="text-xs">🚪</span>
            </button>
          </div>
        </header>

        {/* Content Outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

