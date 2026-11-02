import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { UserRole } from '../../types';
import { ForbiddenPage } from './ForbiddenPage';

export interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  allowedRoles,
  children,
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div
            className="min-h-screen bg-[#f3f6ec] flex flex-col items-center justify-center p-4"
        role="status"
        aria-live="polite"
      >
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-sm font-medium text-slate-400">
            Verifying institutional credentials...
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <ForbiddenPage currentRole={user.role} requiredRole={allowedRoles[0]} />;
  }

  return children ? <>{children}</> : <Outlet />;
};

