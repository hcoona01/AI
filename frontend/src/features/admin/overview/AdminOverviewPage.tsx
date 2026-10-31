import React, { useState } from 'react';
import { OverviewPanel } from '../OverviewPanel';
import { LoadViewPanel } from '../LoadViewPanel';
import { ForecastPanel } from '../ForecastPanel';
import { AssignmentsGrid } from '../AssignmentsGrid';
import { OptimizerPanel } from '../OptimizerPanel';

type AdminTab = 'overview' | 'optimizer' | 'load' | 'assignments' | 'forecast';

export const AdminOverviewPage: React.FC = () => {
  const [currentTerm, setCurrentTerm] = useState<string>('Fall 2026');
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20">
              Department Planning Workspace
            </span>
            <span className="text-xs text-slate-400 font-mono">Term: {currentTerm}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-1">
            Faculty Workload Balancing & Assignment Cockpit
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            End-to-end curriculum planning: demand quantile forecasting, CP-SAT optimization, and fairness audit.
          </p>
        </div>

        {/* Global Term Selector */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl self-start md:self-auto">
          <label htmlFor="global-term-select" className="text-xs font-semibold text-slate-400 uppercase">
            Term:
          </label>
          <select
            id="global-term-select"
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

      {/* Cockpit Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-1 sm:space-x-2 overflow-x-auto pb-1" aria-label="Planning Tabs">
        <button
          type="button"
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'overview'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>📊</span>
          <span>Overview & KPIs</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('optimizer')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'optimizer'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>⚡</span>
          <span>Run Optimizer</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('load')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'load'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>⚖️</span>
          <span>Workload Balance</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('assignments')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'assignments'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>📋</span>
          <span>Assignments Grid</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('forecast')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'forecast'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>📈</span>
          <span>Demand Forecasts</span>
        </button>
      </div>

      {/* Tab Panels */}
      <div className="pt-2">
        {activeTab === 'overview' && (
          <OverviewPanel
            currentTerm={currentTerm}
            onTermChange={setCurrentTerm}
            onOpenOptimizer={() => setActiveTab('optimizer')}
          />
        )}

        {activeTab === 'optimizer' && (
          <OptimizerPanel
            currentTerm={currentTerm}
            onRunSuccess={() => setActiveTab('overview')}
          />
        )}

        {activeTab === 'load' && <LoadViewPanel currentTerm={currentTerm} />}

        {activeTab === 'assignments' && <AssignmentsGrid currentTerm={currentTerm} />}

        {activeTab === 'forecast' && <ForecastPanel currentTerm={currentTerm} />}
      </div>
    </div>
  );
};
