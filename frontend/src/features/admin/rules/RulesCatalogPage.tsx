import React, { useState, useEffect } from 'react';
import {
  useConstraints,
  useUpdateConstraints,
  useValidateAssignments,
  useAssignments,
  useFacultyList,
  useCoursesList,
  useSectionsList,
  useResourcesList,
  useTimeslotsList,
} from '../api';
import type { ConstraintRule, ValidationResponse, ValidationScenario } from '../../../types';

export const RulesCatalogPage: React.FC = () => {
  const { data: serverRules, isLoading: loadingRules, error: errorRules } = useConstraints();
  const updateMutation = useUpdateConstraints();
  const validateMutation = useValidateAssignments();

  // Supplementary data for live validation simulation
  const { data: assignments } = useAssignments('Fall 2026');
  const { data: faculty } = useFacultyList();
  const { data: courses } = useCoursesList();
  const { data: sections } = useSectionsList();
  const { data: resources } = useResourcesList();
  const { data: timeslots } = useTimeslotsList();

  // Local editable rules copy
  const [localRules, setLocalRules] = useState<ConstraintRule[]>([]);
  const [isDirty, setIsDirty] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Simulation results
  const [simulationResult, setSimulationResult] = useState<ValidationResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'hard' | 'soft'>('all');

  useEffect(() => {
    if (serverRules && localRules.length === 0) {
      setLocalRules(serverRules);
    }
  }, [serverRules, localRules.length]);

  const handleToggleEnabled = (ruleId: string) => {
    setLocalRules((prev) =>
      prev.map((r) => (r.rule_id === ruleId ? { ...r, enabled: !r.enabled } : r))
    );
    setIsDirty(true);
    setSimulationResult(null);
  };

  const handleWeightChange = (ruleId: string, weight: number) => {
    setLocalRules((prev) =>
      prev.map((r) => (r.rule_id === ruleId ? { ...r, weight } : r))
    );
    setIsDirty(true);
    setSimulationResult(null);
  };

  const handleReset = () => {
    if (serverRules) {
      setLocalRules(serverRules);
      setIsDirty(false);
      setSimulationResult(null);
    }
  };

  const handleSave = () => {
    updateMutation.mutate(
      { rules: localRules },
      {
        onSuccess: () => {
          setIsDirty(false);
          setSaveSuccess('Constraint catalog and weights successfully updated.');
          setTimeout(() => setSaveSuccess(null), 4000);
        },
      }
    );
  };

  const handlePreviewImpact = () => {
    if (!assignments || !faculty || !courses || !sections || !resources || !timeslots) {
      return;
    }

    const scenario: ValidationScenario = {
      faculty,
      courses,
      sections,
      resources,
      timeslots,
      previous_assignments: [],
    };

    validateMutation.mutate(
      {
        assignments,
        scenario,
        rule_overrides: localRules,
      },
      {
        onSuccess: (data) => {
          setSimulationResult(data);
        },
      }
    );
  };

  const filteredRules = localRules.filter((r) => {
    if (activeTab === 'hard') return r.type === 'hard' || r.rule_id.startsWith('HC');
    if (activeTab === 'soft') return r.type === 'soft' || r.rule_id.startsWith('SC');
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">
            Rules Engine & Parameterization
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">Constraint Rules Catalog</h1>
          <p className="text-xs text-slate-400">
            Enable or disable institutional invariants, adjust soft objective weights, and simulate impact on current assignments.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
          <button
            type="button"
            disabled={validateMutation.isPending}
            onClick={handlePreviewImpact}
            className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm transition"
          >
            {validateMutation.isPending ? (
              <>
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Simulating...</span>
              </>
            ) : (
              <>
                <span>🔮</span>
                <span>Preview Impact</span>
              </>
            )}
          </button>

          {isDirty && (
            <>
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
              >
                Reset
              </button>
              <button
                type="button"
                disabled={updateMutation.isPending}
                onClick={handleSave}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold uppercase tracking-wider rounded-lg shadow-sm transition"
              >
                {updateMutation.isPending ? 'Saving...' : 'Save Rules'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Success Alert */}
      {saveSuccess && (
        <div className="bg-emerald-950/40 border border-emerald-800/80 rounded-xl p-3 text-emerald-300 text-xs flex items-center gap-2">
          <span>✓</span>
          <span>{saveSuccess}</span>
        </div>
      )}

      {/* SIMULATED IMPACT PREVIEW BANNER */}
      {simulationResult && (
        <div className="bg-slate-950 border border-purple-500/40 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-purple-300 uppercase tracking-wider">
                🔮 Simulation Impact Assessment:
              </span>
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                  simulationResult.is_valid
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    simulationResult.is_valid ? 'bg-emerald-400' : 'bg-rose-400'
                  }`}
                />
                {simulationResult.is_valid ? 'Feasible Schedule' : 'Schedule Infeasible'}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setSimulationResult(null)}
              className="text-slate-400 hover:text-white text-xs"
            >
              Dismiss
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] uppercase block">Hard Violations</span>
              <span
                className={`font-mono text-xl font-bold ${
                  simulationResult.hard_violation_count > 0 ? 'text-rose-400' : 'text-emerald-400'
                }`}
              >
                {simulationResult.hard_violation_count}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">
                {simulationResult.hard_violation_count > 0
                  ? 'Would cause solver to fail or require repairs'
                  : 'All hard invariants satisfied'}
              </span>
            </div>

            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] uppercase block">Soft Optimization Flags</span>
              <span className="font-mono text-xl font-bold text-amber-400">
                {simulationResult.soft_violation_count}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Preferences & balance trade-offs</span>
            </div>

            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] uppercase block">Modified Active Rules</span>
              <span className="font-mono text-xl font-bold text-purple-400">
                {localRules.filter((r) => r.enabled).length} / {localRules.length}
              </span>
              <span className="text-[10px] text-slate-500 block mt-0.5">Active constraint evaluators</span>
            </div>
          </div>

          {simulationResult.violations.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-slate-800">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Detected Impact Violations:
              </span>
              <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
                {simulationResult.violations.map((v, i) => (
                  <div
                    key={i}
                    className="p-2 rounded bg-slate-900 border border-slate-800 text-xs flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-[11px] px-1.5 py-0.5 rounded bg-slate-950 text-white">
                        {v.rule_id}
                      </span>
                      <span className="text-slate-300">{v.explanation}</span>
                    </div>
                    <span className="text-[10px] uppercase font-bold text-slate-500">
                      {v.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Rules Navigation Filter Tabs */}
      <div className="flex items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-xl p-3">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              activeTab === 'all'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            All Constraints ({localRules.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('hard')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              activeTab === 'hard'
                ? 'bg-rose-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            Hard Invariants (HC)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('soft')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              activeTab === 'soft'
                ? 'bg-emerald-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            Soft Objectives (SC)
          </button>
        </div>

        <span className="text-xs text-slate-400">
          {localRules.filter((r) => r.enabled).length} of {localRules.length} rules enabled
        </span>
      </div>

      {/* Rules List Grid */}
      {loadingRules && (
        <div className="p-12 text-center text-slate-400 animate-pulse text-xs">
          Loading constraint rules and configuration parameters...
        </div>
      )}

      {errorRules && (
        <div className="p-6 bg-rose-950/40 text-rose-300 text-xs border border-rose-800/60 rounded-xl">
          Failed to load constraint rules: {(errorRules as Error)?.message}
        </div>
      )}

      <div className="space-y-3">
        {filteredRules.map((rule) => {
          const isHard = rule.type === 'hard' || rule.rule_id.startsWith('HC');

          return (
            <div
              key={rule.rule_id}
              className={`bg-slate-900/90 border rounded-xl p-4 transition ${
                rule.enabled ? 'border-slate-800' : 'border-slate-800/40 opacity-60 bg-slate-950/30'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Left: Info */}
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono font-bold text-xs text-white px-2 py-0.5 rounded bg-slate-950 border border-slate-700">
                      {rule.rule_id}
                    </span>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        isHard
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {isHard ? 'Hard Constraint (HC)' : 'Soft Objective (SC)'}
                    </span>
                    {!rule.enabled && (
                      <span className="text-[10px] uppercase font-bold text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
                        Disabled
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-200 font-medium">{rule.description}</p>

                  {/* Rule Parameters if any */}
                  {rule.params && Object.keys(rule.params).length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">
                        Parameters:
                      </span>
                      {Object.entries(rule.params).map(([k, v]) => (
                        <span
                          key={k}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800"
                        >
                          {k}: <strong className="text-slate-200">{String(v)}</strong>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right: Controls (Enable toggle & Weight slider) */}
                <div className="flex items-center gap-4 self-end md:self-center">
                  {/* Soft Constraint Weight Slider */}
                  {!isHard && (
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs text-slate-400 font-medium">Weight:</span>
                      <input
                        type="range"
                        min="0"
                        max="200"
                        step="5"
                        disabled={!rule.enabled}
                        value={rule.weight}
                        onChange={(e) => handleWeightChange(rule.rule_id, Number(e.target.value))}
                        className="w-24 accent-emerald-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer disabled:opacity-30"
                      />
                      <span className="font-mono text-xs font-bold text-emerald-400 w-8 text-right">
                        {rule.weight}
                      </span>
                    </div>
                  )}

                  {/* Enable / Disable Toggle Button */}
                  <button
                    type="button"
                    onClick={() => handleToggleEnabled(rule.rule_id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition ${
                      rule.enabled
                        ? 'bg-slate-800 hover:bg-slate-700 text-white'
                        : 'bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 border border-rose-800/60'
                    }`}
                  >
                    {rule.enabled ? 'Enabled' : 'Disabled'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
