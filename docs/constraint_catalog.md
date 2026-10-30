# Constraint Catalog & Rule Specification

This document serves as the authoritative catalog of all assignment constraints, validation checkers, and objective components evaluated by the University Faculty Workload and Course Assignment Balancing System.

---

## 1. Overview & Explainability Principles

Every assignment restriction, contractual obligation, and optimization objective is associated with a permanent, standardized **`rule_id`**.
- **Hard Constraints (`HC-xx`)**: Strict feasibility rules that cannot be violated under automated solver runs. Violations are designated with severity `error` and prevent schedule certification without an explicit, recorded administrative override.
- **Soft Constraints (`SC-xx`)**: Optimization objectives and preferences penalized by customizable weights. Violations are designated with severity `warning` or `info`.
- **Explainability Contract**: Whenever a hard constraint is broken or a soft objective is penalized, the constraint engine emits a structured [`Violation`](file:///e:/AI%20project/backend/app/schemas/violation.py) object containing:
  - Exact `rule_id`
  - Severity level (`error`, `warning`, `info`)
  - Impacted entity IDs (faculty, course, section, resource)
  - Plain-language explanation citing limits and observed values
  - Actionable suggested repairs

---

## 2. Summary Catalog

| Rule ID | Type | Default Weight | Description | Configurable Parameters |
| :--- | :---: | :---: | :--- | :--- |
| **`HC-01`** | Hard | 1.0 | Faculty proficiency $\ge$ course `min_proficiency` on all required syllabus tags | `{"strict": true}` |
| **`HC-02`** | Hard | 1.0 | Total assigned weekly contact hours $\le$ faculty `max_weekly_load_hours` | `{"allow_overload": false, "max_overload_hours": 0.0}` |
| **`HC-03`** | Hard | 1.0 | No overlapping time slots or time intervals for the same faculty member | `{}` |
| **`HC-04`** | Hard | 1.0 | No assignment during approved leave terms or designated unavailable time slots | `{}` |
| **`HC-05`** | Hard | 1.0 | Number of distinct course preparations $\le$ faculty `max_preparations` | `{}` |
| **`HC-06`** | Hard | 1.0 | Every active course section must have exactly one faculty member assigned | `{}` |
| **`HC-07`** | Hard | 1.0 | Required resources exist, are available during the section time slot, and capacity $\ge$ expected size | `{"check_capacity": true}` |
| **`SC-01`** | Soft | 3.0 | Maximize faculty expertise fit score with course content | `{"min_acceptable_fit": 0.6}` |
| **`SC-02`** | Soft | 2.0 | Minimize teaching load imbalance across faculty of equal rank | `{"max_discrepancy_hours": 3.0}` |
| **`SC-03`** | Soft | 1.5 | Honor faculty explicit course preferences whenever feasible | `{"penalty_per_unpreferred": 1.0}` |
| **`SC-04`** | Soft | 1.0 | Maintain pedagogical continuity with previous term instructors | `{"reward_continuity": 1.0}` |
| **`SC-05`** | Soft | 2.5 | Respect faculty contractual minimum course assignment floor (`min_courses`) | `{}` |

---

## 3. Hard Constraints Specification (`HC-xx`)

### HC-01: Faculty Expertise & Minimum Proficiency
- **Rule Formulation**:
  $$\forall \text{ section } s \text{ of course } c \text{ assigned to faculty } f, \quad \forall t \in c.\text{required\_tags}: \quad f.\text{proficiency}(t) \ge c.\text{min\_proficiency}$$
- **Explanation Template**:
  `"{faculty.name} does not meet required min proficiency {req_p} for tag '{tag}' in course {course.code} (proficiency: {curr_p}) (HC-01)"`
- **Suggested Repairs**:
  1. Reassign section $s$ to an instructor possessing proficiency $\ge \text{req\_p}$ in tag $t$.
  2. Adjust required proficiency threshold for course $c$.

### HC-02: Maximum Weekly Teaching Load
- **Rule Formulation**:
  $$\forall f \in \text{Faculty}, \quad \sum_{s \in \text{Assigned}(f)} \text{course}(s).\text{contact\_hours} \le f.\text{max\_weekly\_load\_hours}$$
- **Explanation Template**:
  `"{faculty.name} is assigned {total_load}h/week; the limit is {faculty.max_weekly_load_hours}h (HC-02)"`
- **Suggested Repairs**:
  1. Unassign one or more sections from faculty member to reduce load below the limit.
  2. Grant an administrative overload exception and record rationale.

### HC-03: No Schedule / Time Slot Overlap
- **Rule Formulation**:
  $$\forall s_1, s_2 \in \text{Assigned}(f), \quad s_1 \ne s_2 \implies s_1.\text{time\_slot} \cap s_2.\text{time\_slot} = \emptyset$$
- **Explanation Template**:
  `"{faculty.name} is assigned overlapping sections {s1.id} and {s2.id} in time slot {time_slot_id} (HC-03)"`
- **Suggested Repairs**:
  1. Reschedule section $s_2$ to a non-conflicting time slot.
  2. Reassign section $s_2$ to another instructor.

### HC-04: Availability & Sabbatical Leave
- **Rule Formulation**:
  $$\forall s \in \text{Assigned}(f): \quad s.\text{term} \notin f.\text{leave\_terms} \quad \land \quad s.\text{time\_slot\_id} \notin f.\text{unavailable\_slots}$$
- **Explanation Template**:
  `"{faculty.name} is on approved leave during term {term} and cannot be assigned section {section.id} (HC-04)"` or
  `"{faculty.name} has designated time slot '{slot}' as unavailable for section {section.id} (HC-04)"`
- **Suggested Repairs**:
  1. Reassign section to an active, available faculty member.
  2. Move section to a time slot when faculty member is available.

### HC-05: Maximum Course Preparations
- **Rule Formulation**:
  $$\forall f \in \text{Faculty}, \quad \left| \{ s.\text{course\_id} \mid s \in \text{Assigned}(f) \} \right| \le f.\text{max\_preparations}$$
- **Explanation Template**:
  `"{faculty.name} is assigned {count} distinct course preparations ({course_list}); the limit is {max_preparations} (HC-05)"`
- **Suggested Repairs**:
  1. Consolidate multiple sections of the same course under this instructor.
  2. Reassign sections of distinct courses to alternative instructors.

### HC-06: Complete Section Coverage (Single Instructor)
- **Rule Formulation**:
  $$\forall s \in \text{Sections}, \quad \left| \{ f \mid (s, f) \in \text{Assignments} \} \right| = 1$$
- **Explanation Template**:
  `"Section {section.id} ({course_code}) is unassigned (HC-06)"` or
  `"Section {section.id} ({course_code}) has {count} instructors assigned: {names} (HC-06)"`
- **Suggested Repairs**:
  1. Assign an eligible faculty member to unassigned section.
  2. Remove duplicate assignments.

### HC-07: Facility & Resource Capacity Feasibility
- **Rule Formulation**:
  $$\forall s \in \text{Sections}, \quad \forall r \in \text{course}(s).\text{required\_resources}: \quad s.\text{time\_slot} \notin r.\text{unavailable\_slots} \quad \land \quad r.\text{capacity} \ge s.\text{expected\_size}$$
- **Explanation Template**:
  `"Facility '{resource.id}' capacity ({capacity}) is insufficient for section {section.id} expected enrollment ({expected_size}) (HC-07)"`
- **Suggested Repairs**:
  1. Relocate section to a facility with capacity $\ge \text{expected\_size}$.
  2. Split the section into smaller cohorts.

---

## 4. Soft Constraints Specification (`SC-xx`)

### SC-01: Maximize Expertise Fit Score
- **Objective Component**:
  $$\text{Maximize } \sum_{a \in \text{Assignments}} w_{\text{SC-01}} \cdot a.\text{fit\_score}$$
- **Explanation Template**:
  `"Assignment of {faculty.name} to section {section.id} has sub-optimal expertise fit score {fit_score} < threshold {threshold} (SC-01)"`

### SC-02: Minimize Load Imbalance
- **Objective Component**:
  $$\text{Minimize } \sum_{\text{rank}} w_{\text{SC-02}} \cdot \left( \max_{f \in \text{rank}} \text{load}(f) - \min_{f \in \text{rank}} \text{load}(f) \right)$$
- **Explanation Template**:
  `"Load imbalance of {gap}h between {fac1} ({load1}h) and {fac2} ({load2}h) exceeds tolerance {max_gap}h among {rank} faculty (SC-02)"`

### SC-03: Honor Course Preferences
- **Objective Component**:
  $$\text{Minimize } \sum_{a=(s, f)} w_{\text{SC-03}} \cdot \mathbb{I}[s.\text{course\_id} \notin f.\text{preferred\_course\_ids}]$$
- **Explanation Template**:
  `"{faculty.name} is assigned section {section.id} ({course.code}), which is outside their preferred courses list ({preferred_codes}) (SC-03)"`

### SC-04: Pedagogical Continuity
- **Objective Component**:
  $$\text{Maximize } \sum_{a=(s, f)} w_{\text{SC-04}} \cdot \mathbb{I}[f \in \text{PreviousInstructors}(s.\text{course\_id})]$$
- **Explanation Template**:
  `"Course {course.code} (section {section.id}) was previously taught by {prev_name}, but currently assigned to {curr_name} (SC-04)"`

### SC-05: Respect Minimum Course Floor
- **Objective Component**:
  $$\text{Minimize } \sum_{f \in \text{Faculty}} w_{\text{SC-05}} \cdot \max(0, f.\text{min\_courses} - |\text{Assigned}(f)|)$$
- **Explanation Template**:
  `"{faculty.name} is assigned {assigned} courses; contractual minimum is {min_courses} (SC-05)"`

---

## 5. REST API Integration

### Retrieve Rule Catalog
```http
GET /api/v1/constraints
```

### Update Rule Weights / States (Admin Only)
```http
PUT /api/v1/constraints
Headers:
  X-User-Role: admin
Content-Type: application/json

{
  "rules": [
    {
      "rule_id": "SC-01",
      "type": "soft",
      "description": "Maximize faculty expertise fit score with course content",
      "weight": 5.0,
      "enabled": true,
      "params": {
        "min_acceptable_fit": 0.7
      }
    }
  ]
}
```

### Evaluate Assignments Against Scenario
```http
POST /api/v1/constraints/validate
Content-Type: application/json

{
  "assignments": [...],
  "scenario": {
    "faculty": [...],
    "courses": [...],
    "sections": [...],
    "resources": [...],
    "timeslots": [...]
  }
}
```
Response:
```json
{
  "is_valid": false,
  "hard_violation_count": 1,
  "soft_violation_count": 2,
  "violations": [
    {
      "rule_id": "HC-02",
      "severity": "error",
      "entity_ids": ["f-1", "s-101", "s-102"],
      "explanation": "Dr. Alan Turing is assigned 14h/week; the limit is 12h (HC-02)",
      "suggested_repairs": [
        "Unassign one or more sections from Dr. Alan Turing to reduce load by 2h",
        "Grant administrative overload exception for Dr. Alan Turing"
      ]
    }
  ]
}
```