import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';

export const NotFoundPage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const returnLink = isAuthenticated ? (user?.role === 'admin' ? '/admin' : '/faculty') : '/';

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-6 text-center">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-6 text-2xl font-mono">
          404
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Page Not Found</h1>
        <p className="text-sm text-slate-400 mb-6">
          The requested route does not exist or has been moved.
        </p>

        <Link
          to={returnLink}
          className="inline-block w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
};

