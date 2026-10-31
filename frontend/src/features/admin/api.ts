// API definitions, TanStack Query hooks, and types for Admin planning features

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../lib/apiClient';
import type {
  Assignment,
  Faculty,
  Course,
  Section,
  ConstraintRule,
  ValidationRequest,
  ValidationResponse,
  Override,
  AuditLogEntry,
  Resource,
  TimeSlot,
} from '../../types';

export interface FairnessSummary {
  term: string;
  gini: number;
  std_dev: number;
  max_min_gap: number;
  mean_load: number;
  faculty_count: number;
  by_rank?: Record<string, {
    gini: number;
    std_dev: number;
    max_min_gap: number;
    mean_load: number;
    faculty_count: number;
  }>;
  faculty_loads: {
    faculty_id: string;
    name: string;
    rank: string;
    assigned_contact_hours: number;
    max_weekly_load_hours: number;
    load_ratio: number;
  }[];
}

export interface ConflictViolation {
  rule_id: string;
  severity: 'error' | 'warning' | 'info';
  entity_ids: string[];
  explanation: string;
  suggested_repairs?: string[];
}

export interface RepairAlternative {
  repair_type: string;
  title: string;
  description: string;
  changes?: Record<string, unknown>[];
  feasible_after_repair: boolean;
  fairness_gini: number;
  mean_fit: number;
  rule_relaxed?: string | null;
}

export interface ConflictsResponse {
  term: string;
  has_hard_violations: boolean;
  hard_violations_count: number;
  soft_violations_count: number;
  violations: ConflictViolation[];
  explanation?: {
    summary: string;
    primary_rule_ids: string[];
    detailed_narrative: string;
    suggested_actions: string[];
  } | null;
  repair_alternatives: RepairAlternative[];
}

export interface ForecastRecord {
  course_id: string;
  course_code: string;
  term: string;
  season: string;
  year: number;
  p10: number;
  p50: number;
  p90: number;
  n_sections: number;
  p90_risk_sections: number;
}

export interface OptimizationJobResult {
  feasible: boolean;
  status: string;
  objective_value?: number | null;
  assignments_count: number;
  solve_time_seconds: number;
  fairness?: {
    gini?: number;
    std_dev?: number;
    max_min_gap?: number;
  };
  fit_summary?: {
    mean_fit?: number;
    min_fit?: number;
    max_fit?: number;
  };
  blocking_rule_ids?: string[];
  explanation?: string;
}

export interface OptimizationJob {
  id: string;
  term: string;
  method: 'cpsat' | 'greedy';
  forecast_mode: 'p50' | 'p90';
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  completed_at?: string | null;
  result?: OptimizationJobResult | null;
  error?: string | null;
}

export interface RunOptimizationPayload {
  term: string;
  method: 'cpsat' | 'greedy';
  forecast_mode: 'p50' | 'p90';
  weights?: Record<string, number>;
  time_limit?: number;
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

export interface OverridePayload {
  assignment_id: string;
  new_faculty_id: string;
  reason: string;
  acknowledge_violations?: boolean;
}

export interface OverrideResponse {
  success: boolean;
  requires_acknowledgement?: boolean;
  message?: string;
  override_id?: string;
  assignment?: Assignment;
  hard_violations?: {
    rule_id: string;
    entity_ids: string[];
    explanation: string;
  }[];
}

// ----------------------------------------------------------------------
// TanStack Query Hooks
// ----------------------------------------------------------------------

export const useFairness = (term: string) => {
  return useQuery<FairnessSummary>({
    queryKey: ['fairness', term],
    queryFn: async () => {
      const resp = await apiClient.get<FairnessSummary>(`/assign/fairness?term=${encodeURIComponent(term)}`);
      return resp.data;
    },
    enabled: Boolean(term),
  });
};

export const useConflicts = (term: string) => {
  return useQuery<ConflictsResponse>({
    queryKey: ['conflicts', term],
    queryFn: async () => {
      const resp = await apiClient.get<ConflictsResponse>(`/assign/conflicts?term=${encodeURIComponent(term)}`);
      return resp.data;
    },
    enabled: Boolean(term),
  });
};

export const useForecasts = (term: string) => {
  return useQuery<ForecastRecord[]>({
    queryKey: ['forecasts', term],
    queryFn: async () => {
      const resp = await apiClient.get<ForecastRecord[]>(`/forecast?term=${encodeURIComponent(term)}`);
      return resp.data;
    },
    enabled: Boolean(term),
  });
};

export const useAssignments = (term: string) => {
  return useQuery<Assignment[]>({
    queryKey: ['assignments', term],
    queryFn: async () => {
      const resp = await apiClient.get<Assignment[]>(`/assign?term=${encodeURIComponent(term)}`);
      return resp.data;
    },
    enabled: Boolean(term),
  });
};

export const useFacultyList = () => {
  return useQuery<Faculty[]>({
    queryKey: ['faculty'],
    queryFn: async () => {
      const resp = await apiClient.get<Faculty[]>('/faculty');
      return resp.data;
    },
  });
};

export const useCoursesList = () => {
  return useQuery<Course[]>({
    queryKey: ['courses'],
    queryFn: async () => {
      const resp = await apiClient.get<Course[]>('/courses');
      return resp.data;
    },
  });
};

export const useSectionsList = (term?: string) => {
  return useQuery<Section[]>({
    queryKey: ['sections', term],
    queryFn: async () => {
      const url = term ? `/sections?term=${encodeURIComponent(term)}` : '/sections';
      const resp = await apiClient.get<Section[]>(url);
      return resp.data;
    },
  });
};

export const useJobStatus = (jobId: string | null) => {
  return useQuery<OptimizationJob>({
    queryKey: ['jobStatus', jobId],
    queryFn: async () => {
      if (!jobId) throw new Error('No job ID provided');
      const resp = await apiClient.get<OptimizationJob>(`/assign/jobs/${jobId}`);
      return resp.data;
    },
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'RUNNING') return 1000;
      return false;
    },
  });
};

export const useExplainAssignment = (assignmentId: string | null) => {
  return useQuery<AssignmentExplanation>({
    queryKey: ['explainAssignment', assignmentId],
    queryFn: async () => {
      if (!assignmentId) throw new Error('No assignment ID provided');
      const resp = await apiClient.get<AssignmentExplanation>(`/assign/explain/${assignmentId}`);
      return resp.data;
    },
    enabled: Boolean(assignmentId),
  });
};

// ----------------------------------------------------------------------
// Mutations
// ----------------------------------------------------------------------

export const useRunOptimization = () => {
  const queryClient = useQueryClient();
  return useMutation<{ job_id: string; status: string; message: string }, Error, RunOptimizationPayload>({
    mutationFn: async (payload) => {
      const resp = await apiClient.post('/assign/run', payload);
      return resp.data;
    },
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['assignments', variables.term] });
      void queryClient.invalidateQueries({ queryKey: ['fairness', variables.term] });
      void queryClient.invalidateQueries({ queryKey: ['conflicts', variables.term] });
    },
  });
};

export const useApplyRepair = () => {
  const queryClient = useQueryClient();
  return useMutation<{ success: boolean; triggered_job_id: string; message: string }, Error, { repair_type: string; term: string }>({
    mutationFn: async ({ repair_type, term }) => {
      const resp = await apiClient.post('/assign/repair/apply', { repair_type, term });
      return resp.data;
    },
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['assignments', variables.term] });
      void queryClient.invalidateQueries({ queryKey: ['fairness', variables.term] });
      void queryClient.invalidateQueries({ queryKey: ['conflicts', variables.term] });
      void queryClient.invalidateQueries({ queryKey: ['faculty'] });
      void queryClient.invalidateQueries({ queryKey: ['sections'] });
    },
  });
};

export const useExecuteOverride = () => {
  const queryClient = useQueryClient();
  return useMutation<OverrideResponse, Error, OverridePayload>({
    mutationFn: async (payload) => {
      const resp = await apiClient.post<OverrideResponse>('/assign/override', payload);
      return resp.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['assignments'] });
      void queryClient.invalidateQueries({ queryKey: ['fairness'] });
      void queryClient.invalidateQueries({ queryKey: ['conflicts'] });
    },
  });
};

export const useLoadScenario = () => {
  const queryClient = useQueryClient();
  return useMutation<{ name: string; message: string }, Error, string>({
    mutationFn: async (scenarioName) => {
      const resp = await apiClient.post(`/scenarios/load/${encodeURIComponent(scenarioName)}`);
      return resp.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries();
    },
  });
};

export const useAuditLogs = (params?: { entity?: string; actor_id?: string; action?: string; limit?: number }) => {
  return useQuery<AuditLogEntry[]>({
    queryKey: ['auditLogs', params],
    queryFn: async () => {
      const queryParts: string[] = [];
      if (params?.entity) queryParts.push(`entity=${encodeURIComponent(params.entity)}`);
      if (params?.actor_id) queryParts.push(`actor_id=${encodeURIComponent(params.actor_id)}`);
      if (params?.action) queryParts.push(`action=${encodeURIComponent(params.action)}`);
      if (params?.limit) queryParts.push(`limit=${params.limit}`);
      const qs = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
      const resp = await apiClient.get<AuditLogEntry[]>(`/audit${qs}`);
      return resp.data;
    },
  });
};

export const useOverrides = (assignmentId?: string) => {
  return useQuery<Override[]>({
    queryKey: ['overrides', assignmentId],
    queryFn: async () => {
      const qs = assignmentId ? `?assignment_id=${encodeURIComponent(assignmentId)}` : '';
      const resp = await apiClient.get<Override[]>(`/overrides${qs}`);
      return resp.data;
    },
  });
};

export const useConstraints = () => {
  return useQuery<ConstraintRule[]>({
    queryKey: ['constraints'],
    queryFn: async () => {
      const resp = await apiClient.get<ConstraintRule[]>('/constraints');
      return resp.data;
    },
  });
};

export const useUpdateConstraints = () => {
  const queryClient = useQueryClient();
  return useMutation<ConstraintRule[], Error, { rules: ConstraintRule[] }>({
    mutationFn: async ({ rules }) => {
      const resp = await apiClient.put<ConstraintRule[]>('/constraints', { rules });
      return resp.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['constraints'] });
    },
  });
};

export const useValidateAssignments = () => {
  return useMutation<ValidationResponse, Error, ValidationRequest>({
    mutationFn: async (payload) => {
      const resp = await apiClient.post<ValidationResponse>('/constraints/validate', payload);
      return resp.data;
    },
  });
};

export const useResourcesList = () => {
  return useQuery<Resource[]>({
    queryKey: ['resources'],
    queryFn: async () => {
      const resp = await apiClient.get<Resource[]>('/resources');
      return resp.data;
    },
  });
};

export const useTimeslotsList = () => {
  return useQuery<TimeSlot[]>({
    queryKey: ['timeslots'],
    queryFn: async () => {
      const resp = await apiClient.get<TimeSlot[]>('/timeslots');
      return resp.data;
    },
  });
};

