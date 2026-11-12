import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLoadScenario } from '../api';

interface ScenarioDefinition {
  id: string;
  name: string;
  expectedFeasible: boolean;
  category: 'Equilibrium' | 'Stress' | 'Infeasible' | 'Boundary';
  constraintTested: string;
  description: string;
  diagnosticReason: string;
  badgeColor: string;
}

const BENCHMARK_SCENARIOS: ScenarioDefinition[] = [
  {
    id: 'balanced_baseline',
    name: 'Balanced Baseline',
    expectedFeasible: true,
    category: 'Equilibrium',
    constraintTested: 'All Constraints Satisfied',
    description: 'Standard balanced department scenario with adequate faculty capacity, clean expertise matches, and non-conflicting time slots.',
    diagnosticReason: 'Optimal baseline distribution where all sections are assigned with zero hard violations and low Gini coefficient.',
    badgeColor: 'bg-emerald-100 text-emerald-900 border-emerald-200',
  },
  {
    id: 'tight_capacity',
    name: 'Tight Capacity (98% Load)',
    expectedFeasible: true,
    category: 'Stress',
    constraintTested: 'HC-02 (Teaching Capacity)',
    description: 'Zero-slack department environment where total required contact hours push department capacity to 98%.',
    diagnosticReason: 'Feasible but tightly constrained; minimal slack for load balancing or faculty preferences.',
    badgeColor: 'bg-amber-100 text-amber-900 border-amber-200',
  },
  {
    id: 'infeasible_expertise',
    name: 'Infeasible Expertise Qualification',
    expectedFeasible: false,
    category: 'Infeasible',
    constraintTested: 'HC-01 (Expertise Qualification)',
    description: 'Course catalog requires specialized competency that no available faculty member possesses.',
    diagnosticReason: 'Immediate solver infeasibility: Course section requires Quantum Algorithms proficiency >= 5, but maximum available faculty proficiency is 0.',
    badgeColor: 'bg-rose-100 text-rose-900 border-rose-200',
  },
  {
    id: 'leave_heavy',
    name: 'Leave Heavy (30% on Sabbatical)',
    expectedFeasible: false,
    category: 'Infeasible',
    constraintTested: 'HC-04 (Sabbatical / Leave)',
    description: 'High proportion of faculty members on sabbatical or research leave during the active term.',
    diagnosticReason: 'Infeasible due to HC-04: 30% of faculty members are on leave in Fall 2026, causing direct sabbatical violations upon assignment.',
    badgeColor: 'bg-rose-100 text-rose-900 border-rose-200',
  },
  {
    id: 'single_expert_bottleneck',
    name: 'Single Expert Bottleneck',
    expectedFeasible: false,
    category: 'Infeasible',
    constraintTested: 'HC-02 & HC-05 (Load & Prep Ceiling)',
    description: 'A single instructor is the only qualified teacher for multiple mandatory course sections.',
    diagnosticReason: 'Infeasible due to HC-02 and HC-05: Single expert is the only qualified instructor for 5 distinct courses, violating max load (15h > 12h) and max preparations (5 > 2).',
    badgeColor: 'bg-rose-100 text-rose-900 border-rose-200',
  },
  {
    id: 'lab_resource_shortage',
    name: 'Lab Facility Resource Shortage',
    expectedFeasible: false,
    category: 'Infeasible',
    constraintTested: 'HC-07 (Facility Capacity)',
    description: 'Specialized hardware laboratory room lacks physical seating capacity for class enrollments.',
    diagnosticReason: 'Infeasible due to HC-07: Specialized lab facility capacity (15 seats) cannot accommodate section expected enrollment (40 students).',
    badgeColor: 'bg-rose-100 text-rose-900 border-rose-200',
  },
  {
    id: 'time_clash_dense',
    name: 'Dense Time Slot Clash',
    expectedFeasible: false,
    category: 'Infeasible',
    constraintTested: 'HC-03 (Time Slot Conflict)',
    description: 'High collision density where essential sections share the exact same temporal slot.',
    diagnosticReason: 'Infeasible due to HC-03: Two course sections assigned to the same instructor share the exact same time slot TS-CLASH.',
    badgeColor: 'bg-rose-100 text-rose-900 border-rose-200',
  },
  {
    id: 'demand_spike',
    name: 'Demand Quantile Spike (P90)',
    expectedFeasible: true,
    category: 'Stress',
    constraintTested: 'SC-03 (Quantile Buffer Risk)',
    description: 'Extreme enrollment volatility where 90th percentile demand triples median forecast.',
    diagnosticReason: 'Feasible under P50 expected demand (40 students), but demonstrates an extreme demand spike where P90 (120 students) triples P50, testing capacity risk planning.',
    badgeColor: 'bg-blue-100 text-blue-900 border-blue-200',
  },
  {
    id: 'boundary_exact_limit',
    name: 'Exact Boundary Capacity Limit',
    expectedFeasible: true,
    category: 'Boundary',
    constraintTested: 'HC-02 & HC-05 (Boundary Stress)',
    description: 'Mathematical boundary test where all instructors hit exactly 100.0% of contractual ceilings.',
    diagnosticReason: 'Feasible on boundary: Faculty load exactly equals max_weekly_load_hours (12.0h), max_courses (3), and max_preparations (2) with zero slack.',
    badgeColor: 'bg-purple-100 text-purple-900 border-purple-200',
  },
  {
    id: 'boundary_zero_capacity',
    name: 'Boundary Zero Capacity Edge',
    expectedFeasible: false,
    category: 'Boundary',
    constraintTested: 'HC-07 (Edge Condition)',
    description: 'Edge case test with zero or minimal resource capacity and empty term constraints.',
    diagnosticReason: 'Infeasible due to HC-07: Resource has capacity (1) that fails to accommodate section expected enrollment (25), alongside empty term verification.',
    badgeColor: 'bg-rose-100 text-rose-900 border-rose-200',
  },
];

export const ScenariosPage: React.FC = () => {
  const navigate = useNavigate();
  const loadScenarioMutation = useLoadScenario();

  const [filterType, setFilterType] = useState<'all' | 'feasible' | 'infeasible'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loadedScenario, setLoadedScenario] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLoadScenario = (scenarioId: string, scenarioName: string) => {
    setErrorMessage(null);
    loadScenarioMutation.mutate(scenarioId, {
      onSuccess: () => {
        setLoadedScenario(scenarioId);
        setSuccessMessage(`Successfully loaded evaluation scenario: "${scenarioName}" into active storage.`);
        setTimeout(() => setSuccessMessage(null), 6000);
      },
      onError: (err) => {
        setErrorMessage(`Failed to load scenario fixture: ${err.message}`);
      },
    });
  };

  const filteredScenarios = BENCHMARK_SCENARIOS.filter((sc) => {
    if (filterType === 'feasible' && !sc.expectedFeasible) return false;
    if (filterType === 'infeasible' && sc.expectedFeasible) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchName = sc.name.toLowerCase().includes(q);
      const matchConstraint = sc.constraintTested.toLowerCase().includes(q);
      const matchDesc = sc.description.toLowerCase().includes(q);
      const matchReason = sc.diagnosticReason.toLowerCase().includes(q);
      if (!matchName && !matchConstraint && !matchDesc && !matchReason) return false;
    }
    return true;
  });

  const feasibleCount = BENCHMARK_SCENARIOS.filter((s) => s.expectedFeasible).length;
  const infeasibleCount = BENCHMARK_SCENARIOS.filter((s) => !s.expectedFeasible).length;

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="pill">Solver Diagnostics & Verification</span>
            <span className="text-xs text-slate-500 font-mono">10 Evaluation Fixtures</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-1" style={{ letterSpacing: '-0.03em' }}>
            Benchmark Scenarios & Stress Tests
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Preconfigured institutional scenarios for evaluating CP-SAT feasibility, constraint diagnostics, and repair heuristics.
          </p>
        </div>
      </div>

      {/* Overview Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">🧪</span>
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Reproducible Optimization Evaluation Suite
          </h2>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          Loading a benchmark scenario injects a carefully structured dataset of faculty members, curriculum courses, sections, and constraints directly into the active store. You can then navigate to the <strong>Optimizer Panel</strong> to run the Google OR-Tools CP-SAT solver and observe solver feasibility certificates, diagnostic violation explanations, and automated repair suggestions.
        </p>
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-300 rounded-xl p-4 shadow-sm flex items-center justify-between gap-3 text-xs text-emerald-900">
          <div className="flex items-center gap-2">
            <span className="text-emerald-600 text-base font-bold">✓</span>
            <span>{successMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => navigate('/admin')}
            className="btn text-xs px-3 py-1 bg-emerald-700 hover:bg-emerald-800 text-white"
          >
            Open Optimizer & Dashboard →
          </button>
        </div>
      )}

      {/* Error Notification */}
      {errorMessage && (
        <div className="bg-rose-50 border border-rose-300 rounded-xl p-4 shadow-sm flex items-center gap-2 text-xs text-rose-900">
          <span className="text-rose-600 font-bold">⚠️</span>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Feasibility Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <button
            type="button"
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterType === 'all'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            All Scenarios ({BENCHMARK_SCENARIOS.length})
          </button>
          <button
            type="button"
            onClick={() => setFilterType('feasible')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterType === 'feasible'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Feasible ({feasibleCount})
          </button>
          <button
            type="button"
            onClick={() => setFilterType('infeasible')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterType === 'infeasible'
                ? 'bg-emerald-800 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Infeasible ({infeasibleCount})
          </button>
        </div>

        {/* Search */}
        <div className="w-full sm:w-64">
          <input
            type="text"
            placeholder="Search scenarios or rules..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs px-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
          />
        </div>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredScenarios.map((sc) => {
          const isCurrentlyLoaded = loadedScenario === sc.id;
          const isPendingThis = loadScenarioMutation.isPending && loadScenarioMutation.variables === sc.id;

          return (
            <div
              key={sc.id}
              className={`bg-slate-900 border rounded-xl p-5 shadow-sm transition flex flex-col justify-between ${
                isCurrentlyLoaded
                  ? 'border-emerald-500 ring-2 ring-emerald-200'
                  : 'border-slate-800 hover:shadow-md'
              }`}
            >
              <div>
                {/* Header: Name, Feasibility Pill, Constraint Tag */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-300">
                        {sc.id}
                      </span>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border ${sc.badgeColor}`}>
                        {sc.category}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mt-2 leading-snug">
                      {sc.name}
                    </h3>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border ${
                      sc.expectedFeasible
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                        : 'bg-rose-50 text-rose-800 border-rose-300'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        sc.expectedFeasible ? 'bg-emerald-600' : 'bg-rose-600'
                      }`}
                    />
                    {sc.expectedFeasible ? 'Feasible' : 'Infeasible'}
                  </span>
                </div>

                {/* Constraint Tested Badge */}
                <div className="mt-2.5">
                  <span className="inline-block text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    Rule Tested: <strong className="text-slate-900 font-mono">{sc.constraintTested}</strong>
                  </span>
                </div>

                {/* Scenario Description */}
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  {sc.description}
                </p>

                {/* Diagnostic Expected Outcome */}
                <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                  <div className="text-[10px] uppercase font-semibold text-slate-500">Diagnostic Mechanism</div>
                  <div className="text-[11px] text-slate-700 mt-0.5">{sc.diagnosticReason}</div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-5 pt-3 border-t border-slate-200 flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400">
                  Fixture: data/fixtures/{sc.id}.json
                </span>

                <button
                  type="button"
                  disabled={loadScenarioMutation.isPending}
                  onClick={() => handleLoadScenario(sc.id, sc.name)}
                  className={`btn text-xs px-3.5 py-1.5 flex items-center gap-1.5 ${
                    isCurrentlyLoaded
                      ? 'bg-emerald-700 hover:bg-emerald-800 text-white'
                      : ''
                  }`}
                >
                  {isPendingThis ? (
                    <>
                      <span className="animate-spin text-sm">⏳</span>
                      <span>Loading...</span>
                    </>
                  ) : isCurrentlyLoaded ? (
                    <>
                      <span>✓</span>
                      <span>Active in Store</span>
                    </>
                  ) : (
                    <>
                      <span>⚡</span>
                      <span>Load Fixture</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
export default ScenariosPage;
