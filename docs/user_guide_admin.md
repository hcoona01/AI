# Department Administrator & Chair User Guide

This guide provides step-by-step instructions for department chairs, academic deans, and administrative planners using the **Faculty Workload Balancing & Course Assignment Cockpit**.

---

## 1. Sign In & Navigation

1. Navigate to `/login` in your web browser.
2. Enter your institutional email address (e.g., `admin@university.edu` or `chair@university.edu`).
3. Click **Send One-Time Passcode (OTP)**.
4. Check your email inbox for the 6-digit verification code.
   *(In local development mode with `OTP_DEV_MODE=true`, the passcode is logged in your backend terminal or retrievable at `/api/v1/auth/dev-otp?email=admin@university.edu`)*.
5. Enter the 6-digit code. Upon verification, you are redirected to the **Department Planning Workspace** at `/admin`.

---

## 2. Cockpit Layout & Global Controls

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ University Faculty Workload Balancing Cockpit             Term: [Fall 2026 ▼] │
├─────────────────────────────────────────────────────────────────────────────┤
│ [📊 Overview] [⚡ Optimizer] [📈 Load View] [📋 Assignments] [🔮 Forecasts] │
│ [⚠️ Conflicts] [⚖️ Rules] [📜 Audit Trail]                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Global Term Selector**: Top right dropdown (`Fall 2026`, `Spring 2027`, `Summer 2027`). Switching terms instantly refetches demand forecasts, course sections, and solver assignments for that planning semester.
- **Role Badge**: Confirms authenticated administrative privileges.

---

## 3. Overview Dashboard (`/admin`)

The Overview tab provides real-time departmental health metrics:

1. **Feasible Status Badge**: Indicates whether current assignments satisfy 100% of institutional hard constraints (`HC-01` through `HC-07`).
2. **Hard Violations Counter**: Number of blocking invariants currently violated (target: 0).
3. **Load Gini Index**: Departmental workload disparity metric ($0.0 = \text{perfect equality}, 1.0 = \text{extreme inequality}$). Values $< 0.15$ indicate high fairness.
4. **Mean Expertise Fit**: Percentage match score across all faculty-section pairings based on course required tags and syllabus text.
5. **Unassigned Sections Counter**: Number of active course sections lacking an assigned instructor.
6. **Scenario Loader**: Dropdown allowing you to instantly load standardized benchmark scenarios (`balanced_baseline`, `tight_capacity`, `infeasible_expertise`, `lab_resource_shortage`) to evaluate system behavior under diverse conditions.

---

## 4. Run Optimizer Panel (`/admin` $\rightarrow$ Optimizer Tab)

The optimizer cockpit enables automated course allocation using mathematical constraint programming:

### Step 1: Select Solver Engine
- **CP-SAT Solver (Google OR-Tools)**: Full constraint programming model. Optimizes multi-objective trade-offs, guarantees hard invariants, and minimizes workload Gini index.
- **Greedy Baseline Heuristic**: Instantaneous sub-10ms greedy assignment. Allocates most-constrained sections first to highest-fit instructors with spare capacity.

### Step 2: Choose Forecast Scenario
- **P50 Expected Demand**: Plans section counts to match median expected enrollments.
- **P90 Surge Stress Mode**: Expands section counts to insulate against 90th-percentile enrollment surges.

### Step 3: Adjust Objective Function Weights
Use the interactive sliders to customize departmental priorities:
- **w1 • SC-01 Expertise Fit (Default: 100)**: Higher weights maximize domain proficiency and syllabus alignment.
- **w2 • SC-02 Workload Fairness (Default: 50)**: Higher weights minimize the gap between the most-loaded and least-loaded faculty.
- **w3 • SC-03 Faculty Preference (Default: 20)**: Penalizes assigning courses faculty explicitly designated as non-preferred.
- **w4 • SC-04 Past-Teaching Continuity (Default: 15)**: Rewards assigning instructors who taught the course in recent terms.

### Step 4: Execute & Monitor
1. Set **Solver CPU Time Limit** (default: `20` seconds).
2. Click **Execute CP-SAT Solver**.
3. A progress banner displays live job status (`QUEUED` $\rightarrow$ `RUNNING` $\rightarrow$ `COMPLETED`).
4. Once completed, a comparison card displays **CP-SAT vs. Baseline** performance metrics (Gini reduction, mean fit, and solve time).

---

## 5. Faculty Load View (`/admin` $\rightarrow$ Load View Tab)

Visualizes teaching hour distribution across the department:
- **Interactive Bar Chart**: Displays assigned weekly contact hours per faculty member compared against their contractual maximum limit (`max_weekly_load_hours`).
- **Color Coding**:
  - 🟢 **Balanced (Emerald)**: Assigned hours within contractual bounds.
  - 🔴 **Overload (Rose)**: Assigned hours exceed maximum limit (violates `HC-02`).
  - 🟡 **Underload (Amber)**: Assigned hours below contractual minimum floor (violates `SC-05`).
- **Department Median Reference Line**: Dashed horizontal indicator highlighting median teaching load across faculty of equal rank.

---

## 6. Demand Forecasts Panel (`/admin` $\rightarrow$ Forecasts Tab)

Provides probabilistic enrollment projections:
- **Quantile Bands**: Displays $P_{10}$ (conservative bound), $P_{50}$ (median expectation), and $P_{90}$ (surge ceiling) for every course in the catalog.
- **Calculated Section Needs**: Automatic translation of enrollment projections into recommended section counts based on course classroom caps:
  $$\text{Sections Needed} = \lceil P_{50} / \text{section\_cap} \rceil$$
- **Risk Indicator**: Highlights courses with high quantile spread ($P_{90} - P_{10} > 25$), indicating high enrollment volatility.

---

## 7. Assignments Grid & Manual Overrides (`/admin` $\rightarrow$ Assignments Tab)

### 7.1 Inspecting Assignments
- Search by course code, title, or instructor name.
- Filter by rule compliance (`All`, `Clean`, `Violated`).
- Each row displays: Course Code, Section ID, Assigned Faculty, Schedule Timeslot, Fit Score Chip, and Satisfied Constraint Badges (`✓ HC-01`, `✓ HC-02`, etc.).

### 7.2 Assignment Detail Drawer
Click **Explain** on any assignment row to open the Explainability Drawer:
- **Fit Breakdown**: Shows individual contribution of Tag Match (60%), TF-IDF (25%), and Continuity (15%).
- **Why This Faculty Won**: Plain-language justification explaining why this instructor was selected.
- **Top Alternative Candidates**: Ranks the runner-up faculty with their fit scores and notes which constraints blocked them (e.g., `Blocked by HC-03 time clash` or `Blocked by HC-02 max load`).

### 7.3 Executing a Controlled Manual Override
When departmental circumstances require overriding the automated recommendation:
1. Click **Override** on the target assignment row.
2. Select a replacement faculty member from the dropdown.
3. Enter a mandatory **Administrative Justification** (e.g., *"Emergency replacement due to medical leave; department chair approved overload"*).
4. **Live Invariant Checking**: The system re-validates the proposed assignment against all hard constraints.
5. If a hard constraint is broken (e.g., `HC-02` overload or `HC-03` schedule clash), a prominent red warning banner appears detailing the exact violations.
6. Check the mandatory acknowledgment box:
   `[✓] I acknowledge these violations and force this override`
7. Click **Apply Override**.
8. The assignment is tagged with an immutable **Overridden** badge. The original solver recommendation and justification are preserved in the audit log.

---

## 8. Schedule Conflicts & Automated Repairs (`/admin` $\rightarrow$ Conflicts Tab)

When a schedule has constraint violations:
1. Navigate to the **Conflicts** tab.
2. Review violations sorted by severity:
   - 🔴 **Hard Invariant (Blocking)**: Must be remediated or explicitly overridden.
   - 🟡 **Soft Warning**: Advisory penalty.
3. Click **Synthesize Repairs** to open the remediation modal.
4. The system evaluates 2–3 automated repair strategies:
   - *Relax HC-05 (Increase Course Preparations Limit)*
   - *Inject Adjunct Teaching Capacity*
   - *Reschedule Overlapping Section Timeslot (Resolve HC-03)*
5. Each alternative displays its predicted impact on **Workload Gini**, **Mean Fit**, and **New Violations**.
6. Select an alternative and click **Apply Repair** to automatically update constraints and trigger re-optimization.

---

## 9. Audit Trail (`/admin` $\rightarrow$ Audit Tab)

Maintains an immutable chronological record of all administrative actions:
- **Logged Events**: Optimization runs, manual overrides, repair applications, and rule weight changes.
- **Event Metadata**: Timestamp (UTC), Actor identity (`user_id`), Event category, Section/Faculty IDs, Reason text, and Evidence snapshot.
- Search and filter by user ID, term, or action category.
