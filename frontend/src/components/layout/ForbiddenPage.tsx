import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { UserRole } from '../../types';
import { BrandMark } from '../brand/BrandMark';

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
    <div className="min-h-screen bg-[#f3f6ec] flex flex-col justify-center items-center p-6 text-center">
      <div className="max-w-md w-full bg-white/90 border border-white rounded-[26px] p-8 shadow-[0_30px_60px_rgba(10,20,60,0.1)]">
        <div className="brand justify-center mb-4">
          <BrandMark />
          <span>workload</span>
        </div>
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#e7efcf] text-[#4d6a10] mb-6 text-2xl font-medium">
          403
        </div>

        <h1 className="text-2xl font-medium tracking-tight mb-2">Access forbidden</h1>
        <p className="text-sm text-slate-400 mb-6">
          You do not have the required permissions to access this area.
          {requiredRole && (
            <span className="block mt-2 font-mono text-xs text-rose-600">
              Required role: <strong className="uppercase">{requiredRole}</strong> | Your role:{' '}
              <strong className="uppercase">{activeRole || 'Unknown'}</strong>
            </span>
          )}
        </p>

        {user && (
          <div className="p-3 bg-[#f3f6ec] border border-slate-800 rounded-2xl text-xs text-slate-400 mb-6 text-left">
            <div>
              Signed in as: <span className="text-slate-200 font-mono font-medium">{user.email}</span>
            </div>
            {user.faculty_id && (
              <div className="mt-1">
                Linked faculty ID: <span className="font-mono">{user.faculty_id}</span>
              </div>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <Link to={dashboardLink} className="btn flex-1">
            Go to my dashboard
          </Link>
          <button
            type="button"
            onClick={() => void handleLogoutAndSwitch()}
            className="flex-1 py-2.5 px-4 rounded-full border border-slate-700 text-sm font-medium cursor-pointer"
          >
            Switch account
          </button>
        </div>
      </div>
    </div>
  );
};
