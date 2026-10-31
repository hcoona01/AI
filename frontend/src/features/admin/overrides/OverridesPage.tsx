import React, { useState } from 'react';
import { useOverrides, useFacultyList } from '../api';
import type { Override } from '../../../types';

export const OverridesPage: React.FC = () => {
  const { data: overrides, isLoading, isError, error, refetch } = useOverrides();
  const { data: facultyList } = useFacultyList();

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedOverride, setSelectedOverride] = useState<Override | null>(null);

  const facultyMap = new Map(facultyList?.map((f) => [f.id, f]) || []);

  const filteredOverrides = overrides?.filter((o) => {
    if (!searchTerm.trim()) return true;
    const query = searchTerm.toLowerCase();
    const prevFac = facultyMap.get(o.previous_faculty_id || '')?.name.toLowerCase() || '';
    const newFac = facultyMap.get(o.new_faculty_id)?.name.toLowerCase() || '';
    return (
      o.assignment_id.toLowerCase().includes(query) ||
      o.reason.toLowerCase().includes(query) ||
      o.admin_id.toLowerCase().includes(query) ||
      prevFac.includes(query) ||
      newFac.includes(query)
    );
  });

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded border border-amber-500/20">
            Administrative Overrides
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">Manual Assignment Overrides</h1>
          <p className="text-xs text-slate-400">
            Audit history of manual instructor reassignments, mandatory justifications, and preserved constraint evidence.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void refetch()}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition self-start md:self-auto flex items-center gap-1.5"
        >
          <span>↻</span>
          <span>Refresh Records</span>
        </button>
      </div>

      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
        <input
          type="text"
          placeholder="Search overrides by section, instructor name, justification, or admin ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full max-w-md"
        />
        <span className="text-xs text-slate-400">
          Showing {filteredOverrides?.length || 0} override records
        </span>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {isLoading && (
          <div className="p-12 text-center text-slate-400 animate-pulse text-xs">
            Loading override history and snapshots...
          </div>
        )}

        {isError && (
          <div className="p-6 bg-rose-950/40 text-rose-300 text-xs border border-rose-800/60">
            Failed to retrieve override records: {(error as Error)?.message}
          </div>
        )}

        {!isLoading && (!filteredOverrides || filteredOverrides.length === 0) && (
          <div className="p-12 text-center text-slate-400">
            <span className="text-3xl mb-2 block">⚖️</span>
            <p className="font-semibold text-white">No manual overrides recorded</p>
            <p className="text-xs text-slate-500 mt-1">
              All active sections currently reflect pure solver recommendations. Manual overrides will appear here.
            </p>
          </div>
        )}

        {!isLoading && filteredOverrides && filteredOverrides.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Target Assignment</th>
                  <th className="py-3 px-4">Original Instructor</th>
                  <th className="py-3 px-4">Reassigned Instructor</th>
                  <th className="py-3 px-4">Administrative Justification</th>
                  <th className="py-3 px-4 text-right">Evidence Snapshot</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredOverrides.map((ovr) => {
                  const prev = facultyMap.get(ovr.previous_faculty_id || '');
                  const curr = facultyMap.get(ovr.new_faculty_id);

                  return (
                    <tr key={ovr.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 whitespace-nowrap font-mono text-slate-300 text-xs">
                        {new Date(ovr.timestamp).toLocaleString()}
                        <div className="text-[10px] text-slate-500">By: {ovr.admin_id}</div>
                      </td>

                      <td className="py-3 px-4 font-mono font-bold text-white whitespace-nowrap">
                        {ovr.assignment_id}
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="text-slate-400 font-medium">{prev ? prev.name : ovr.previous_faculty_id || 'System'}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{ovr.previous_faculty_id}</div>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="text-blue-300 font-semibold">{curr ? curr.name : ovr.new_faculty_id}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{ovr.new_faculty_id}</div>
                      </td>

                      <td className="py-3 px-4 max-w-sm text-xs text-slate-300 leading-relaxed">
                        <span className="italic">"{ovr.reason}"</span>
                        {ovr.acknowledged_violations && ovr.acknowledged_violations.length > 0 && (
                          <div className="flex items-center gap-1 mt-1">
                            <span className="text-[10px] font-bold text-rose-400 bg-rose-500/10 px-1.5 py-0.2 rounded border border-rose-500/20">
                              Acknowledged: {ovr.acknowledged_violations.join(', ')}
                            </span>
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => setSelectedOverride(ovr)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition"
                        >
                          View Evidence &rarr;
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

      {/* Snapshot Modal */}
      {selectedOverride && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  Evidence Snapshot
                </span>
                <h3 className="text-base font-bold text-white mt-1">Override Evidence Record</h3>
                <p className="text-xs text-slate-400 font-mono">ID: {selectedOverride.id}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedOverride(null)}
                className="text-slate-400 hover:text-white p-1"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-amber-300 max-h-72 overflow-y-auto">
              {JSON.stringify(selectedOverride.constraint_evidence_snapshot, null, 2)}
            </pre>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedOverride(null)}
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
