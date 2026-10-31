import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';

interface NavItem {
  name: string;
  path: string;
  icon: string;
  end?: boolean;
}

const facultyNavItems: NavItem[] = [
  { name: 'My Schedule & Load', path: '/faculty', icon: '📅', end: true },
  { name: 'Availability & Blackouts', path: '/faculty/preferences', icon: '⏱️' },
  { name: 'Change Requests', path: '/faculty/requests', icon: '📝' },
  { name: 'Expertise & Syllabi Fit', path: '/faculty/expertise', icon: '🎯' },
  { name: 'Course Sections', path: '/faculty/courses', icon: '📖' },
];

export const FacultyLayout: React.FC = () => {
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
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
              FACULTY PORTAL
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
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto" aria-label="Faculty Navigation">
          {facultyNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition ${
                  isActive
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/20'
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
          <span>v0.1.0 • Connected</span>
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
              Faculty Workload & Schedule
            </div>
          </div>

          {/* User Info & Logout */}
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs font-mono font-medium text-slate-200">
                {user?.email || 'faculty@university.edu'}
              </div>
              <div className="flex items-center justify-end gap-2 mt-0.5">
                <span className="text-[10px] font-semibold text-purple-400 uppercase tracking-wider">
                  Faculty
                </span>
                {user?.faculty_id && (
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-purple-950/60 border border-purple-800/40 text-purple-300">
                    ID: {user.faculty_id}
                  </span>
                )}
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

