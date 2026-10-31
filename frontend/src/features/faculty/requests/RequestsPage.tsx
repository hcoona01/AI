import React, { useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import {
  useMyChangeRequests,
  useCreateChangeRequest,
  useMyAssignments,
  useFacultyCourses,
  useFacultySections,
} from '../api';

export const RequestsPage: React.FC = () => {
  const { user } = useAuth();
  const currentFacultyId = user?.faculty_id || 'f-01';
  const currentTerm = 'Fall 2026';

  const { data: changeRequests, isLoading: loadingRequests, refetch } = useMyChangeRequests();
  const { data: assignments } = useMyAssignments(currentTerm, currentFacultyId);
  const { data: courses } = useFacultyCourses();
  const { data: sections } = useFacultySections(currentTerm);

  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>('');
  const [comment, setComment] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const createMutation = useCreateChangeRequest();

  const courseMap = new Map(courses?.map((c) => [c.id, c]) || []);
  const sectionMap = new Map(sections?.map((s) => [s.id, s]) || []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignmentId || !comment.trim()) return;

    createMutation.mutate(
      {
        assignment_id: selectedAssignmentId,
        comment: comment.trim(),
      },
      {
        onSuccess: () => {
          setSuccessMessage('Change request submitted to curriculum administration.');
          setSelectedAssignmentId('');
          setComment('');
          void refetch();
          setTimeout(() => setSuccessMessage(null), 4000);
        },
      }
    );
  };

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-500/10 px-2.5 py-0.5 rounded border border-purple-500/20">
            Administrative Dialogue
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">Assignment Change Requests</h1>
          <p className="text-xs text-slate-400">
            Submit comments or modification requests for assigned sections. Administrators receive immediate notifications.
          </p>
        </div>
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div className="bg-emerald-950/40 border border-emerald-800/80 rounded-xl p-3 text-emerald-300 text-xs flex items-center gap-2">
          <span>✓</span>
          <span>{successMessage}</span>
        </div>
      )}

      {/* New Change Request Form Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">
          Submit New Section Modification Request
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Select Assigned Course Section:
            </label>
            <select
              value={selectedAssignmentId}
              onChange={(e) => setSelectedAssignmentId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
            >
              <option value="">-- Choose Assigned Section --</option>
              {assignments?.map((a) => {
                const sec = sectionMap.get(a.section_id);
                const crs = sec ? courseMap.get(sec.course_id) : undefined;
                return (
                  <option key={a.id} value={a.id}>
                    {crs?.code || a.section_id} - Section {sec?.id || a.section_id} ({crs?.title})
                  </option>
                );
              })}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Modification Request & Justification:
            </label>
            <textarea
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="State reason for change (e.g., sabbatical schedule, specialized lab conflict, research grant overlap)..."
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg p-2.5 focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!selectedAssignmentId || !comment.trim() || createMutation.isPending}
              className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-bold uppercase tracking-wider rounded-lg shadow-sm transition"
            >
              {createMutation.isPending ? 'Submitting...' : 'Submit Request to Admin'}
            </button>
          </div>
        </form>
      </div>

      {/* Submitted Requests List */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            My Submitted Change Requests ({changeRequests?.length || 0})
          </h2>
          <span className="text-xs text-slate-400">Chronological history</span>
        </div>

        {loadingRequests && (
          <div className="p-8 text-center text-slate-400 animate-pulse text-xs">
            Loading submitted requests...
          </div>
        )}

        {!loadingRequests && (!changeRequests || changeRequests.length === 0) && (
          <div className="p-8 text-center text-slate-400 text-xs">
            <span className="text-3xl mb-2 block">📋</span>
            <p className="font-semibold text-white">No Change Requests on File</p>
            <p className="text-slate-500 mt-1">
              Submit a request using the form above if you need a schedule adjustment.
            </p>
          </div>
        )}

        {!loadingRequests && changeRequests && changeRequests.length > 0 && (
          <div className="space-y-3">
            {changeRequests.map((cr) => (
              <div
                key={cr.id}
                className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2.5"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-white">
                        {cr.course_code || cr.section_id}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Section: {cr.section_id}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                      Submitted: {new Date(cr.created_at).toLocaleString()} • ID: {cr.id}
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                      cr.status === 'approved'
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : cr.status === 'rejected'
                        ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                        : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                    }`}
                  >
                    {cr.status}
                  </span>
                </div>

                <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 text-slate-300">
                  <span className="text-[11px] font-semibold text-slate-400 block mb-0.5">Your Comment:</span>
                  "{cr.comment}"
                </div>

                {cr.admin_response && (
                  <div className="bg-purple-950/20 border border-purple-800/40 p-3 rounded-lg text-purple-200">
                    <span className="text-[11px] font-semibold text-purple-300 block mb-0.5">Administrator Response:</span>
                    {cr.admin_response}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
