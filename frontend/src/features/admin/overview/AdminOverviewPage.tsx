import React, { useState } from 'react';
import { OverviewPanel } from '../OverviewPanel';
import { LoadViewPanel } from '../LoadViewPanel';
import { ForecastPanel } from '../ForecastPanel';
import { AssignmentsGrid } from '../AssignmentsGrid';
import { OptimizerPanel } from '../OptimizerPanel';
import { ConflictsPanel } from '../conflicts/ConflictsPanel';
import { RulesCatalogPage } from '../rules/RulesCatalogPage';
import { AuditTrailPage } from '../audit/AuditTrailPage';
import { AssignmentDetailDrawer } from '../assignments/AssignmentDetailDrawer';

type AdminTab = 'overview' | 'optimizer' | 'load' | 'assignments' | 'forecast' | 'conflicts' | 'rules' | 'audit';

export const AdminOverviewPage: React.FC = () => {
  const [currentTerm, setCurrentTerm] = useState<string>('Fall 2026');
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(null);

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="pill">Department planning workspace</span>
            <span className="text-xs text-slate-400 font-mono">Term: {currentTerm}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-1" style={{ letterSpacing: '-0.03em' }}>
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
          <span>Overview</span>
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
          <span>Optimizer</span>
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
          <span>Workload</span>
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
          <span>Assignments</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('conflicts')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'conflicts'
              ? 'bg-rose-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>⚠️</span>
          <span>Conflicts & Repairs</span>
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
          <span>Forecasts</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'rules'
              ? 'bg-emerald-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>⚙️</span>
          <span>Rules Catalog</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <span>📜</span>
          <span>Audit Trail</span>
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

        {activeTab === 'conflicts' && (
          <ConflictsPanel
            currentTerm={currentTerm}
            onSelectAssignment={(id) => setSelectedAssignmentId(id)}
          />
        )}

        {activeTab === 'forecast' && <ForecastPanel currentTerm={currentTerm} />}

        {activeTab === 'rules' && <RulesCatalogPage />}

        {activeTab === 'audit' && <AuditTrailPage />}
      </div>

      {/* Slide-over Assignment Detail Drawer */}
      {selectedAssignmentId && (
        <AssignmentDetailDrawer
          assignmentId={selectedAssignmentId}
          onClose={() => setSelectedAssignmentId(null)}
        />
      )}
    </div>
  );
};
