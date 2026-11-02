import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { BrandMark } from '../brand/BrandMark';

export const NotFoundPage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const returnLink = isAuthenticated ? (user?.role === 'admin' ? '/admin' : '/faculty') : '/';

  return (
    <div className="min-h-screen bg-[#f3f6ec] flex flex-col justify-center items-center p-6 text-center">
      <div className="max-w-md w-full bg-white/90 border border-white rounded-[26px] p-8 shadow-[0_30px_60px_rgba(10,20,60,0.1)]">
        <div className="brand justify-center mb-4">
          <BrandMark />
          <span>workload</span>
        </div>
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#e7efcf] text-[#4d6a10] mb-6 text-2xl font-medium">
          404
        </div>

        <h1 className="text-2xl font-medium tracking-tight mb-2">Page not found</h1>
        <p className="text-sm text-slate-400 mb-6">
          The requested route does not exist or has been moved.
        </p>

        <Link to={returnLink} className="btn inline-flex w-full">
          Return to dashboard
        </Link>
      </div>
    </div>
  );
};
