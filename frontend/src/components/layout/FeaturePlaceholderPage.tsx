import React from 'react';
import { Link } from 'react-router-dom';

export interface FeaturePlaceholderPageProps {
  title: string;
  category: string;
  description: string;
  backLink: string;
}

export const FeaturePlaceholderPage: React.FC<FeaturePlaceholderPageProps> = ({
  title,
  category,
  description,
  backLink,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <span className="pill">{category}</span>
          <h1 className="text-2xl font-medium tracking-tight mt-2">{title}</h1>
          <p className="text-sm text-slate-400 mt-1">{description}</p>
        </div>
        <Link to={backLink} className="btn self-start sm:self-auto">
          ← Back to dashboard
        </Link>
      </div>

      <div className="bg-white border border-slate-800 rounded-[22px] p-8 text-center space-y-4">
        <div className="w-12 h-12 mx-auto rounded-xl bg-[#e7efcf] border border-[#d5e0b0] flex items-center justify-center text-[#2c3a10] text-xl">
          ✿
        </div>
        <h2 className="text-lg font-medium">Module scaffold ready</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          The layout shell, role guard, and navigation bindings for{' '}
          <strong className="text-slate-200">{title}</strong> are active. This feature will connect
          to the backend solver and analytics engines in subsequent modules.
        </p>
      </div>
    </div>
  );
};
