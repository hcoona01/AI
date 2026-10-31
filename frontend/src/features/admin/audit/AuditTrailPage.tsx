import React, { useState, useMemo } from 'react';
import { useAuditLogs } from '../api';
import type { AuditLogEntry } from '../../../types';

export const AuditTrailPage: React.FC = () => {
  const [entityFilter, setEntityFilter] = useState<string>('');
  const [actionCategory, setActionCategory] = useState<'all' | 'runs' | 'overrides' | 'rules' | 'repairs'>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [limit, setLimit] = useState<number>(100);

  // Selected entry for JSON inspector modal
  const [inspectedLog, setInspectedLog] = useState<AuditLogEntry | null>(null);

  const { data: logs, isLoading, isError, error, refetch } = useAuditLogs({
    entity: entityFilter || undefined,
    limit,
  });

  // Filtered logs
  const filteredLogs = useMemo(() => {
    if (!logs) return [];

    return logs.filter((log: AuditLogEntry) => {
      // Category filter
      if (actionCategory === 'runs' && !log.action.startsWith('OPTIMIZE_')) return false;
      if (actionCategory === 'overrides' && log.action !== 'ASSIGNMENT_OVERRIDE') return false;
      if (actionCategory === 'rules' && !log.action.includes('CONSTRAINT') && !log.action.includes('RULE')) return false;
      if (actionCategory === 'repairs' && !log.action.startsWith('REPAIR_')) return false;

      // Text search
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchesAction = log.action.toLowerCase().includes(query);
        const matchesActor = log.actor_id.toLowerCase().includes(query);
        const matchesEntity = log.entity.toLowerCase().includes(query);
        const matchesPayload = JSON.stringify(log.payload).toLowerCase().includes(query);

        if (!matchesAction && !matchesActor && !matchesEntity && !matchesPayload) {
          return false;
        }
      }

      return true;
    });
  }, [logs, actionCategory, searchTerm]);

  // Action Badge Color Helper
  const getActionBadge = (action: string) => {
    if (action.startsWith('OPTIMIZE_')) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/15 text-blue-300 border border-blue-500/30">
          ⚡ {action}
        </span>
      );
    }
    if (action === 'ASSIGNMENT_OVERRIDE') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
          ⚠️ {action}
        </span>
      );
    }
    if (action.startsWith('REPAIR_')) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">
          🛠️ {action}
        </span>
      );
    }
    if (action.includes('CONSTRAINT') || action.includes('RULE')) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
          ⚖️ {action}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
        {action}
      </span>
    );
  };

  // Human-readable summary generator
  const getSummary = (log: AuditLogEntry) => {
    const p = log.payload || {};
    if (log.action === 'ASSIGNMENT_OVERRIDE') {
      return (
        <span>
          Reassigned section <strong className="text-white font-mono">{String(p.section_id || '')}</strong> from{' '}
          <span className="text-slate-400 font-mono">{String(p.previous_faculty_id || 'unassigned')}</span> to{' '}
          <strong className="text-blue-300 font-mono">{String(p.new_faculty_id || '')}</strong>. Reason: "
          <span className="italic text-slate-300">{String(p.reason || '')}</span>"
        </span>
      );
    }
    if (log.action === 'OPTIMIZE_JOB_START') {
      return (
        <span>
          Started background optimization job for term{' '}
          <strong className="text-white">{String(p.term || '')}</strong> using{' '}
          <strong className="text-blue-300 uppercase">{String(p.method || 'cpsat')}</strong> ({String(p.forecast_mode || 'p50')}).
        </span>
      );
    }
    if (log.action === 'OPTIMIZE_JOB_COMPLETE') {
      return (
        <span>
          Optimization completed: <strong className="text-emerald-400">{String(p.assignments_count || 0)} sections</strong> assigned in{' '}
          <span className="font-mono">{Number(p.solve_time_seconds || 0).toFixed(2)}s</span> (Feasible: {String(p.feasible)}).
        </span>
      );
    }
    if (log.action === 'REPAIR_APPLY') {
      return (
        <span>
          Applied automated repair strategy <strong className="text-purple-300">{String(p.repair_type || '')}</strong> for term{' '}
          <strong className="text-white">{String(p.term || '')}</strong>.
        </span>
      );
    }
    if (log.action === 'CONSTRAINT_UPDATE') {
      return (
        <span>
          Batch updated constraint catalog rules ({String(p.updated_rules_count || 'several')} rules modified).
        </span>
      );
    }
    return <span className="text-slate-400">{JSON.stringify(log.payload).slice(0, 90)}...</span>;
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20">
            Compliance & Provenance
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">Audit Trail & Activity Log</h1>
          <p className="text-xs text-slate-400">
            Immutable chronological record of optimization solver runs, human overrides, repairs, and rule reweightings.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void refetch()}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition self-start md:self-auto flex items-center gap-1.5"
        >
          <span>↻</span>
          <span>Refresh Trail</span>
        </button>
      </div>

      {/* Filter and Control Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="flex items-center gap-2 flex-1">
          <input
            type="text"
            placeholder="Search audit trail by actor, action, section, or keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full max-w-md"
          />
        </div>

        {/* Action Category Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={() => setActionCategory('all')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              actionCategory === 'all'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            All Events
          </button>
          <button
            type="button"
            onClick={() => setActionCategory('runs')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              actionCategory === 'runs'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            Solver Runs
          </button>
          <button
            type="button"
            onClick={() => setActionCategory('overrides')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              actionCategory === 'overrides'
                ? 'bg-amber-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            Overrides
          </button>
          <button
            type="button"
            onClick={() => setActionCategory('rules')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              actionCategory === 'rules'
                ? 'bg-emerald-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            Rule Changes
          </button>
          <button
            type="button"
            onClick={() => setActionCategory('repairs')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              actionCategory === 'repairs'
                ? 'bg-purple-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-950'
            }`}
          >
            Repairs
          </button>
        </div>

        {/* Entity and Limit Controls */}
        <div className="flex items-center gap-2">
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-2.5 py-1"
          >
            <option value="">All Entities</option>
            <option value="assignment">Assignments</option>
            <option value="constraint">Constraints</option>
            <option value="user">Users</option>
          </select>

          <span className="text-[11px] text-slate-400">Limit:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-2 py-1"
          >
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {isLoading && (
          <div className="p-12 text-center text-slate-400 animate-pulse text-xs">
            Loading immutable audit trail entries...
          </div>
        )}

        {isError && (
          <div className="p-6 bg-rose-950/40 text-rose-300 text-xs border border-rose-800/60">
            Failed to retrieve audit log entries: {(error as Error)?.message}
          </div>
        )}

        {!isLoading && filteredLogs.length === 0 && (
          <div className="p-12 text-center text-slate-400">
            <span className="text-3xl mb-2 block">📜</span>
            <p className="font-semibold text-white">No audit entries found</p>
            <p className="text-xs text-slate-500 mt-1">
              Events will be appended automatically as administrators run solvers, apply repairs, and execute overrides.
            </p>
          </div>
        )}

        {!isLoading && filteredLogs.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Action Code</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Audit Summary & Details</th>
                  <th className="py-3 px-4 text-right">Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredLogs.map((log: AuditLogEntry) => {
                  const dateObj = new Date(log.timestamp);
                  return (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition">
                      {/* Timestamp */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="font-mono text-slate-200 text-xs">
                          {dateObj.toLocaleDateString()} {dateObj.toLocaleTimeString()}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          {log.id.slice(0, 12)}...
                        </div>
                      </td>

                      {/* Actor */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="font-mono text-white font-semibold text-xs">{log.actor_id}</div>
                        <span className="text-[10px] uppercase font-bold text-blue-400">Administrator</span>
                      </td>

                      {/* Action Code Badge */}
                      <td className="py-3 px-4 whitespace-nowrap">{getActionBadge(log.action)}</td>

                      {/* Target Entity */}
                      <td className="py-3 px-4 whitespace-nowrap font-mono text-slate-400">
                        <span className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px]">
                          {log.entity}
                        </span>
                      </td>

                      {/* Summary */}
                      <td className="py-3 px-4 max-w-md text-xs leading-relaxed text-slate-300">
                        {getSummary(log)}
                      </td>

                      {/* Inspect JSON Payload Button */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => setInspectedLog(log)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition"
                        >
                          View Snapshot &rarr;
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* JSON Payload Inspector Modal */}
      {inspectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                  {inspectedLog.action}
                </span>
                <h3 className="text-base font-bold text-white mt-1">Audit Record Snapshot</h3>
                <p className="text-xs text-slate-400 font-mono">
                  ID: {inspectedLog.id} • {new Date(inspectedLog.timestamp).toISOString()}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setInspectedLog(null)}
                className="text-slate-400 hover:text-white p-1"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-emerald-400 overflow-x-auto">
                {JSON.stringify(inspectedLog, null, 2)}
              </pre>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={() => setInspectedLog(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
