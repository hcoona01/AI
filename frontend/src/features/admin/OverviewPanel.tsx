import React, { useState } from 'react';
import {
  useFairness,
  useConflicts,
  useAssignments,
  useSectionsList,
  useLoadScenario,
} from './api';
import type { Assignment, Section } from '../../types';

const SCENARIOS = [
  { id: 'balanced_baseline', name: 'Balanced Baseline (Feasible)' },
  { id: 'tight_capacity', name: 'Tight Capacity (98% load)' },
  { id: 'infeasible_expertise', name: 'Infeasible Expertise (HC-01)' },
  { id: 'leave_heavy', name: 'Leave Heavy (30% on leave)' },
  { id: 'single_expert_bottleneck', name: 'Single Expert Bottleneck (HC-02)' },
  { id: 'lab_resource_shortage', name: 'Lab Resource Shortage (HC-07)' },
  { id: 'time_clash_dense', name: 'Time Clash Dense (HC-03)' },
  { id: 'demand_spike', name: 'Demand Spike' },
  { id: 'boundary_exact_limit', name: 'Boundary Exact Limit' },
  { id: 'boundary_zero_capacity', name: 'Boundary Zero Capacity (HC-07)' },
];

interface OverviewProps {
  currentTerm: string;
  onTermChange: (term: string) => void;
  onOpenOptimizer: () => void;
}

export const OverviewPanel: React.FC<OverviewProps> = ({
  currentTerm,
  onTermChange,
  onOpenOptimizer,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [scenarioSuccess, setScenarioSuccess] = useState<string | null>(null);

  const { data: fairness, isLoading: loadingFairness } = useFairness(currentTerm);
  const { data: conflicts, isLoading: loadingConflicts } = useConflicts(currentTerm);
  const { data: assignments, isLoading: loadingAssignments } = useAssignments(currentTerm);
  const { data: sections, isLoading: loadingSections } = useSectionsList(currentTerm);

  const loadScenarioMutation = useLoadScenario();

  const handleScenarioLoad = () => {
    if (!selectedScenario) return;
    loadScenarioMutation.mutate(selectedScenario, {
      onSuccess: () => {
        setScenarioSuccess(`Successfully loaded scenario: ${selectedScenario}`);
        setTimeout(() => setScenarioSuccess(null), 4000);
      },
    });
  };

  // KPI calculations
  const totalSections = sections?.length ?? 0;
  const assignedSectionIds = new Set(assignments?.map((a: Assignment) => a.section_id) ?? []);
  const unassignedCount = sections ? sections.filter((s: Section) => !assignedSectionIds.has(s.id)).length : 0;

  const hardViolationsCount = conflicts?.hard_violations_count ?? 0;
  const isFeasible = hardViolationsCount === 0 && unassignedCount === 0;

  const meanFit =
    assignments && assignments.length > 0
      ? assignments.reduce((acc: number, a: Assignment) => acc + (a.fit_score || 0), 0) / assignments.length
      : 0;

  const loadGini = fairness?.gini ?? 0;

  return (
    <div className="space-y-6">
      {/* Controls Bar: Term selector + Scenario loader */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Term Selector */}
        <div className="flex items-center gap-3">
          <label htmlFor="term-select" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Academic Term:
          </label>
          <select
            id="term-select"
            value={currentTerm}
            onChange={(e) => onTermChange(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-white text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
          >
            <option value="Fall 2026">Fall 2026</option>
            <option value="Spring 2027">Spring 2027</option>
            <option value="Summer 2027">Summer 2027</option>
          </select>
        </div>

        {/* Scenario Loader Dropdown */}
        <div className="flex items-center gap-2">
          <select
            aria-label="Evaluation Scenario"
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-xs"
          >
            <option value="">-- Load Evaluation Scenario --</option>
            {SCENARIOS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleScenarioLoad}
            disabled={!selectedScenario || loadScenarioMutation.isPending}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition cursor-pointer"
          >
            {loadScenarioMutation.isPending ? 'Loading...' : 'Load Scenario'}
          </button>
        </div>
      </div>

      {scenarioSuccess && (
        <div className="bg-emerald-950/60 border border-emerald-700/50 text-emerald-300 px-4 py-2.5 rounded-lg text-xs flex items-center justify-between">
          <span>{scenarioSuccess}</span>
          <button type="button" onClick={() => setScenarioSuccess(null)} className="text-emerald-400 hover:text-white">
            ✕
          </button>
        </div>
      )}

      {loadScenarioMutation.isError && (
        <div className="bg-rose-950/60 border border-rose-700/50 text-rose-300 px-4 py-2.5 rounded-lg text-xs">
          Error loading scenario: {loadScenarioMutation.error?.message}
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Feasibility Status */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Schedule Feasibility
          </div>
          <div className="my-2">
            {loadingConflicts || loadingSections ? (
              <span className="text-sm text-slate-500 animate-pulse">Checking...</span>
            ) : isFeasible ? (
              <span className="inline-flex items-center gap-1.5 text-2xl font-bold text-emerald-400">
                <span>✅</span> Feasible
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-2xl font-bold text-rose-400">
                <span>⚠️</span> Infeasible
              </span>
            )}
          </div>
          <div className="text-[11px] font-mono text-slate-400">
            {isFeasible ? 'All hard constraints satisfied' : `${hardViolationsCount} active violation(s)`}
          </div>
        </div>

        {/* Card 2: Hard Violations */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Hard Violations (HC)
          </div>
          <div className="my-2 text-3xl font-extrabold text-white">
            {loadingConflicts ? (
              <span className="text-sm text-slate-500">...</span>
            ) : (
              <span className={hardViolationsCount > 0 ? 'text-rose-400' : 'text-emerald-400'}>
                {hardViolationsCount}
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-400">
            {hardViolationsCount === 0 ? 'Zero constraint breaches' : 'Immediate planner attention needed'}
          </div>
        </div>

        {/* Card 3: Workload Gini */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Workload Fairness (Gini)
          </div>
          <div className="my-2 text-3xl font-extrabold text-white">
            {loadingFairness ? (
              <span className="text-sm text-slate-500">...</span>
            ) : (
              <span className={loadGini <= 0.15 ? 'text-emerald-400' : loadGini <= 0.3 ? 'text-amber-400' : 'text-rose-400'}>
                {loadGini.toFixed(3)}
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-400">
            {loadGini <= 0.15 ? 'Highly balanced' : loadGini <= 0.3 ? 'Moderate disparity' : 'High load imbalance'}
          </div>
        </div>

        {/* Card 4: Mean Fit */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Mean Expertise Fit
          </div>
          <div className="my-2 text-3xl font-extrabold text-blue-400">
            {loadingAssignments ? (
              <span className="text-sm text-slate-500">...</span>
            ) : (
              `${(meanFit * 100).toFixed(1)}%`
            )}
          </div>
          <div className="text-[11px] text-slate-400">
            Syllabus match & tag score
          </div>
        </div>

        {/* Card 5: Unassigned Sections */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Unassigned Sections
          </div>
          <div className="my-2 text-3xl font-extrabold text-white">
            {loadingSections || loadingAssignments ? (
              <span className="text-sm text-slate-500">...</span>
            ) : (
              <span className={unassignedCount > 0 ? 'text-amber-400' : 'text-emerald-400'}>
                {unassignedCount} <span className="text-xs font-normal text-slate-400">/ {totalSections}</span>
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-400">
            {unassignedCount === 0 ? 'All sections staffed' : `${unassignedCount} section(s) need instructor`}
          </div>
        </div>
      </div>

      {/* Fast Action Banner */}
      <div className="bg-gradient-to-r from-blue-950/40 via-slate-900 to-indigo-950/40 border border-blue-900/40 rounded-xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white">Mathematical Course Allocation Optimizer</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Execute Google OR-Tools CP-SAT or deterministic Greedy heuristic to satisfy contractual load, time clashes, and preparation limits.
          </p>
        </div>
        <button
          type="button"
          onClick={onOpenOptimizer}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow-md shadow-blue-600/30 transition cursor-pointer flex items-center gap-2 whitespace-nowrap"
        >
          <span>⚡ Open Optimizer Panel</span>
        </button>
      </div>
    </div>
  );
};
