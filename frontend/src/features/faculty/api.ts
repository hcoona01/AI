// API definitions, TanStack Query hooks, and types for Faculty portal features

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../lib/apiClient';
import type { Faculty, Course, Section, Assignment, TimeSlot } from '../../types';

export interface AnonymizedPeerLoad {
  peer_id: string;
  label: string;
  rank: string;
  assigned_hours: number;
  max_limit: number;
  load_ratio: number;
  is_current_user: boolean;
}

export interface AnonymizedLoadComparison {
  term: string;
  faculty_id: string;
  my_load: number;
  my_max_limit: number;
  my_load_ratio: number;
  department_median_load: number;
  department_mean_load: number;
  total_faculty_evaluated: number;
  anonymized_peers: AnonymizedPeerLoad[];
}

export interface ChangeRequest {
  id: string;
  assignment_id: string;
  faculty_id: string;
  section_id: string;
  course_code: string;
  comment: string;
  status: 'pending' | 'approved' | 'rejected';
  admin_response?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PreferencesUpdatePayload {
  unavailable_slots?: string[];
  leave_terms?: string[];
  preferred_course_ids?: string[];
  expertise?: { tag: string; proficiency: number }[];
}

export interface AssignmentExplanation {
  assignment_id: string;
  section_id: string;
  course_code: string;
  course_title: string;
  chosen_faculty: {
    faculty_id: string;
    name: string;
    fit_score: number;
    fit_breakdown: Record<string, number>;
    rule_ids_satisfied: string[];
    rule_ids_violated: string[];
    rationale: string;
  };
  top_alternatives: {
    faculty_id: string;
    name: string;
    rank: string;
    fit_score: number;
    fit_breakdown: Record<string, number>;
    is_eligible: boolean;
    blocked_reasons: string[];
  }[];
  total_candidates_evaluated: number;
}

// ----------------------------------------------------------------------
// Hooks
// ----------------------------------------------------------------------

export const useMyFacultyProfile = (facultyId?: string | null) => {
  return useQuery<Faculty>({
    queryKey: ['myFacultyProfile', facultyId],
    queryFn: async () => {
      const fid = facultyId || 'f-01';
      const resp = await apiClient.get<Faculty>(`/faculty/${encodeURIComponent(fid)}`);
      return resp.data;
    },
    enabled: Boolean(facultyId),
  });
};

export const useMyAssignments = (term: string, facultyId?: string | null) => {
  return useQuery<Assignment[]>({
    queryKey: ['myAssignments', term, facultyId],
    queryFn: async () => {
      const qs = facultyId
        ? `?term=${encodeURIComponent(term)}&faculty_id=${encodeURIComponent(facultyId)}`
        : `?term=${encodeURIComponent(term)}`;
      const resp = await apiClient.get<Assignment[]>(`/assign${qs}`);
      return resp.data;
    },
    enabled: Boolean(term),
  });
};

export const useFacultyCourses = () => {
  return useQuery<Course[]>({
    queryKey: ['courses'],
    queryFn: async () => {
      const resp = await apiClient.get<Course[]>('/courses');
      return resp.data;
    },
  });
};

export const useFacultySections = (term: string) => {
  return useQuery<Section[]>({
    queryKey: ['sections', term],
    queryFn: async () => {
      const resp = await apiClient.get<Section[]>(`/sections?term=${encodeURIComponent(term)}`);
      return resp.data;
    },
    enabled: Boolean(term),
  });
};

export const useFacultyTimeslots = () => {
  return useQuery<TimeSlot[]>({
    queryKey: ['timeslots'],
    queryFn: async () => {
      const resp = await apiClient.get<TimeSlot[]>('/timeslots');
      return resp.data;
    },
  });
};

export const useAssignmentExplanation = (assignmentId: string | null) => {
  return useQuery<AssignmentExplanation>({
    queryKey: ['assignmentExplanation', assignmentId],
    queryFn: async () => {
      if (!assignmentId) throw new Error('No assignment ID provided');
      const resp = await apiClient.get<AssignmentExplanation>(`/assign/explain/${encodeURIComponent(assignmentId)}`);
      return resp.data;
    },
    enabled: Boolean(assignmentId),
  });
};

export const useAnonymizedLoadComparison = (facultyId: string | null, term: string) => {
  return useQuery<AnonymizedLoadComparison>({
    queryKey: ['anonymizedLoadComparison', facultyId, term],
    queryFn: async () => {
      const fid = facultyId || 'f-01';
      const resp = await apiClient.get<AnonymizedLoadComparison>(
        `/faculty/${encodeURIComponent(fid)}/load-comparison?term=${encodeURIComponent(term)}`
      );
      return resp.data;
    },
    enabled: Boolean(facultyId && term),
  });
};

export const useMyChangeRequests = () => {
  return useQuery<ChangeRequest[]>({
    queryKey: ['myChangeRequests'],
    queryFn: async () => {
      const resp = await apiClient.get<ChangeRequest[]>('/faculty/change-requests');
      return resp.data;
    },
  });
};

export const useUpdateFacultyPreferences = (facultyId: string) => {
  const queryClient = useQueryClient();
  return useMutation<
    { success: boolean; faculty: Faculty; pending_optimization: boolean; message: string },
    Error,
    PreferencesUpdatePayload
  >({
    mutationFn: async (payload) => {
      const resp = await apiClient.put(`/faculty/${encodeURIComponent(facultyId)}/preferences`, payload);
      return resp.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['myFacultyProfile', facultyId] });
      void queryClient.invalidateQueries({ queryKey: ['faculty'] });
    },
  });
};

export const useCreateChangeRequest = () => {
  const queryClient = useQueryClient();
  return useMutation<ChangeRequest, Error, { assignment_id: string; comment: string }>({
    mutationFn: async (payload) => {
      const resp = await apiClient.post<ChangeRequest>('/faculty/change-requests', payload);
      return resp.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['myChangeRequests'] });
    },
  });
};

