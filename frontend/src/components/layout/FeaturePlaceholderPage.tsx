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
          <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md border border-blue-500/20">
            {category}
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-2">{title}</h1>
          <p className="text-sm text-slate-400 mt-1">{description}</p>
        </div>
        <Link
          to={backLink}
          className="self-start sm:self-auto px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition"
        >
          &larr; Back to Dashboard
        </Link>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center space-y-4">
        <div className="w-12 h-12 mx-auto rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-400 text-xl font-mono">
          ⚙️
        </div>
        <h2 className="text-lg font-semibold text-white">Module Scaffold Ready</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          The layout shell, role guard, and navigation bindings for{' '}
          <strong className="text-slate-200">{title}</strong> are active. This feature will connect
          to the backend solver and analytics engines in subsequent modules.
        </p>
      </div>
    </div>
  );
};

