import React, { useState } from 'react';
import { ForecastPanel } from '../ForecastPanel';

export const ForecastPage: React.FC = () => {
  const [currentTerm, setCurrentTerm] = useState<string>('Fall 2026');

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20">
            Machine Learning Demand Forecasts
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">Course Enrollment Forecasts</h1>
          <p className="text-xs text-slate-400">
            Quantile regression projections (P10 conservative floor, P50 expected, P90 surge stress)
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl self-start md:self-auto">
          <label htmlFor="forecast-term-select" className="text-xs font-semibold text-slate-400 uppercase">
            Term:
          </label>
          <select
            id="forecast-term-select"
            value={currentTerm}
            onChange={(e) => setCurrentTerm(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-white text-xs font-medium rounded-lg px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="Fall 2026">Fall 2026</option>
            <option value="Spring 2027">Spring 2027</option>
            <option value="Summer 2027">Summer 2027</option>
          </select>
        </div>
      </div>

      <ForecastPanel currentTerm={currentTerm} />
    </div>
  );
};
