// TypeScript domain interfaces mirroring backend Pydantic v2 schemas
// Strict mode enabled: no 'any' types used

export type UserRole = 'admin' | 'faculty';

export type FacultyRank =
  | 'Professor'
  | 'Associate Professor'
  | 'Assistant Professor'
  | 'Lecturer'
  | 'Adjunct'
  | 'Visiting';

export type CourseLevel = 'undergraduate' | 'graduate' | 'doctoral';

export type ResourceType = 'room' | 'lab';

export type DayOfWeek = 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN';

export type RuleType = 'hard' | 'soft';

export type AssignmentSource = 'solver' | 'baseline' | 'override';

export type ViolationSeverity = 'error' | 'warning' | 'info';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  faculty_id?: string | null;
}

export interface FacultyExpertise {
  tag: string;
  proficiency: number; // 1 to 5
}

export interface Faculty {
  id: string;
  name: string;
  email: string;
  rank: FacultyRank;
  expertise: FacultyExpertise[];
  max_weekly_load_hours: number;
  max_courses: number;
  min_courses: number;
  max_preparations: number;
  unavailable_slots: string[];
  leave_terms: string[];
  preferred_course_ids: string[];
}

export interface Course {
  id: string;
  code: string;
  title: string;
  description: string;
  credits: number;
  contact_hours: number;
  level: CourseLevel;
  required_tags: string[];
  min_proficiency: number;
  is_lab: boolean;
  required_resource_ids: string[];
}

export interface Section {
  id: string;
  course_id: string;
  term: string;
  section_cap: number;
  expected_size: number;
  size_p10: number;
  size_p50: number;
  size_p90: number;
  time_slot_id?: string | null;
}

export interface Resource {
  id: string;
  type: ResourceType;
  capacity: number;
  unavailable_slots: string[];
}

export interface TimeSlot {
  id: string;
  day: DayOfWeek;
  start: string; // 24h format HH:MM
  end: string;   // 24h format HH:MM
}

export interface ConstraintRule {
  rule_id: string;
  type: RuleType;
  description: string;
  weight: number;
  enabled: boolean;
  params: Record<string, unknown>;
}

export interface ValidationScenario {
  faculty: Faculty[];
  courses: Course[];
  sections: Section[];
  resources: Resource[];
  timeslots: TimeSlot[];
  previous_assignments: Assignment[];
}

export interface ValidationRequest {
  assignments: Assignment[];
  scenario: ValidationScenario;
  rule_overrides?: ConstraintRule[] | null;
}

export interface ValidationResponse {
  is_valid: boolean;
  hard_violation_count: number;
  soft_violation_count: number;
  violations: Violation[];
  timestamp: string;
}

export interface ConstraintBatchUpdateRequest {
  rules: ConstraintRule[];
}

export interface Assignment {
  id: string;
  section_id: string;
  faculty_id: string;
  source: AssignmentSource;
  fit_score: number; // 0.0 to 1.0
  fit_breakdown: Record<string, number>;
  rule_ids_satisfied: string[];
  rule_ids_violated: string[];
  run_id: string;
  created_at: string; // ISO 8601 string
}

export interface Violation {
  rule_id: string;
  severity: ViolationSeverity;
  entity_ids: string[];
  explanation: string;
  suggested_repairs: string[];
}

export interface Override {
  id: string;
  assignment_id: string;
  admin_id: string;
  reason: string;
  previous_faculty_id?: string | null;
  new_faculty_id: string;
  constraint_evidence_snapshot: Record<string, unknown>;
  acknowledged_violations: string[];
  timestamp: string; // ISO 8601 string
}

export interface AuditLogEntry {
  id: string;
  actor_id: string;
  action: string;
  entity: string;
  payload: Record<string, unknown>;
  timestamp: string; // ISO 8601 string
}
