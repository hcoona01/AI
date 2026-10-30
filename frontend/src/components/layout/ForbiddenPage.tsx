import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { UserRole } from '../../types';

export interface ForbiddenPageProps {
  currentRole?: UserRole;
  requiredRole?: UserRole;
}

export const ForbiddenPage: React.FC<ForbiddenPageProps> = ({
  currentRole,
  requiredRole,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const activeRole = currentRole || user?.role;
  const dashboardLink = activeRole === 'admin' ? '/admin' : '/faculty';

  const handleLogoutAndSwitch = async (): Promise<void> => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-6 text-center">
      <div className="max-w-md w-full bg-slate-900/90 border border-rose-900/30 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mb-6 text-2xl font-mono">
          403
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Access Forbidden</h1>
        <p className="text-sm text-slate-400 mb-6">
          You do not have the required permissions to access this area.
          {requiredRole && (
            <span className="block mt-2 font-mono text-xs text-rose-300">
              Required Role: <strong className="uppercase">{requiredRole}</strong> | Your Role:{' '}
              <strong className="uppercase">{activeRole || 'Unknown'}</strong>
            </span>
          )}
        </p>

        {user && (
          <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-400 mb-6 text-left">
            <div>
              Signed in as: <span className="text-slate-200 font-mono font-medium">{user.email}</span>
            </div>
            {user.faculty_id && (
              <div className="mt-1">
                Linked Faculty ID: <span className="text-purple-300 font-mono">{user.faculty_id}</span>
              </div>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            to={dashboardLink}
            className="flex-1 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition"
          >
            Go to My Dashboard
          </Link>
          <button
            type="button"
            onClick={() => void handleLogoutAndSwitch()}
            className="flex-1 py-2.5 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-sm font-medium transition cursor-pointer"
          >
            Switch Account
          </button>
        </div>
      </div>
    </div>
  );
};

