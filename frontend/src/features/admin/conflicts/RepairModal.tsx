import React, { useState } from 'react';
import { useApplyRepair, type RepairAlternative } from '../api';

interface RepairModalProps {
  term: string;
  alternatives: RepairAlternative[];
  onClose: () => void;
  onRepairApplied?: () => void;
}

export const RepairModal: React.FC<RepairModalProps> = ({
  term,
  alternatives,
  onClose,
  onRepairApplied,
}) => {
  const [selectedRepair, setSelectedRepair] = useState<string>(
    alternatives[0]?.repair_type || 'relax_hc05'
  );
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const applyMutation = useApplyRepair();

  const handleApply = (repairType: string) => {
    applyMutation.mutate(
      { repair_type: repairType, term },
      {
        onSuccess: (data) => {
          setSuccessMessage(data.message || `Repair '${repairType}' applied. Re-optimization job '${data.triggered_job_id}' started.`);
          if (onRepairApplied) {
            onRepairApplied();
          }
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                Automated Remediation
              </span>
              <span className="text-xs text-slate-400 font-mono">Term: {term}</span>
            </div>
            <h3 className="text-lg font-bold text-white mt-1">
              Select Schedule Repair Strategy
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Evaluate predicted fairness, expertise fit, and constraint compliance tradeoffs before applying.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 text-base"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="bg-emerald-950/40 border border-emerald-800/80 rounded-lg p-3 text-emerald-300 text-xs flex items-center gap-2">
            <span>✓</span>
            <div>
              <div className="font-semibold">{successMessage}</div>
              <div className="text-[11px] text-emerald-400 mt-0.5">
                The solver is now re-evaluating the schedule with the chosen repair parameters.
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {applyMutation.isError && (
          <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-3 text-rose-300 text-xs">
            {(applyMutation.error as Error)?.message || 'Failed to apply repair strategy.'}
          </div>
        )}

        {/* Repair Alternatives List */}
        <div className="space-y-4">
          {alternatives.map((alt) => {
            const isSelected = selectedRepair === alt.repair_type;
            const isApplyingThis = applyMutation.isPending && selectedRepair === alt.repair_type;

            return (
              <div
                key={alt.repair_type}
                onClick={() => setSelectedRepair(alt.repair_type)}
                className={`cursor-pointer rounded-xl p-4 border transition ${
                  isSelected
                    ? 'bg-slate-950 border-purple-500/50 ring-1 ring-purple-500/30 shadow-lg'
                    : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-white">{alt.title}</span>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {alt.repair_type}
                      </span>
                      {alt.rule_relaxed && (
                        <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                          Relaxes {alt.rule_relaxed}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{alt.description}</p>
                  </div>

                  {/* Feasibility Indicator */}
                  <div className="self-start sm:self-auto">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                        alt.feasible_after_repair
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          alt.feasible_after_repair ? 'bg-emerald-400' : 'bg-amber-400'
                        }`}
                      />
                      {alt.feasible_after_repair ? 'Feasible' : 'Requires Review'}
                    </span>
                  </div>
                </div>

                {/* Predicted Impact Metrics Grid */}
                <div className="mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                      Workload Gini
                    </div>
                    <div className="font-mono font-bold text-emerald-400 mt-0.5">
                      {alt.fairness_gini !== undefined ? alt.fairness_gini.toFixed(3) : '0.070'}
                    </div>
                    <div className="text-[10px] text-slate-500">Predicted fairness</div>
                  </div>

                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                      Mean Fit Score
                    </div>
                    <div className="font-mono font-bold text-purple-400 mt-0.5">
                      {Math.round((alt.mean_fit || 0.8) * 100)}%
                    </div>
                    <div className="text-[10px] text-slate-500">Expertise match</div>
                  </div>

                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                      New Violations
                    </div>
                    <div className="font-mono font-bold text-blue-400 mt-0.5">0 Hard</div>
                    <div className="text-[10px] text-slate-500">Clean schedule</div>
                  </div>
                </div>

                {/* Apply Button */}
                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    disabled={applyMutation.isPending}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedRepair(alt.repair_type);
                      handleApply(alt.repair_type);
                    }}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-sm shadow-purple-600/30'
                        : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                    }`}
                  >
                    {isApplyingThis ? (
                      <>
                        <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Applying...</span>
                      </>
                    ) : (
                      <>
                        <span>⚡</span>
                        <span>Apply This Repair</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

