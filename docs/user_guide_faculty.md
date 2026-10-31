# Faculty Portal User Guide: Schedule Review & Availability

This guide provides step-by-step instructions for university faculty members (Professors, Associate Professors, Assistant Professors, and Lecturers) using the **Faculty Workload & Availability Portal**.

---

## 1. Sign In & Privacy Isolation

1. Navigate to `/login` in your web browser.
2. Enter your university email address (e.g., `ada.lovelace@university.edu` or `alan.turing@university.edu`).
3. Click **Send One-Time Passcode (OTP)**.
4. Retrieve the 6-digit verification code from your university email inbox.
5. Enter the code. You will be authenticated and redirected to your personal dashboard at `/faculty`.

> [!IMPORTANT]
> **Privacy & Role-Based Access Control (RBAC)**
> - Faculty members have read access **strictly restricted to their own assignments, preferences, and change requests**.
> - Attempting to view another faculty member's profile or navigate to `/admin` routes will immediately display an `Access Forbidden (403)` page.
> - Departmental workload comparison charts strictly **anonymize all peer faculty identities** (e.g., labeled as `Peer 1 (Associate Professor)`). Other faculty names and emails are never exposed.

---

## 2. My Schedule & Assigned Workload (`/faculty`)

The landing page displays your teaching commitments for the selected academic term:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 👤 Welcome, Prof. Ada Lovelace                       Term: [Fall 2026 ▼]    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Assigned Contact Hours: [■■■■■■■■□□] 9.0h / 12.0h Max                      │
│  Assigned Sections: 3 Sections | Department Median: 9.0h                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  [📅 Weekly Timetable]   [💡 Why I Was Assigned]   [📊 Peer Benchmark]      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Workload Metric Cards
- **Weekly Contact Hours**: Shows your assigned weekly classroom hours against your contractual maximum load limit (`max_weekly_load_hours`).
- **Assigned Sections Count**: Total active lecture and laboratory sections.
- **Department Median Load**: Contextual reference indicating the median workload across all faculty of your rank.

### 2.2 Weekly Timetable Grid
Displays a clean, chronological visual timetable (Monday through Friday, 08:00 to 18:00):
- Color-coded calendar blocks displaying **Course Code**, **Section ID**, **Meeting Times**, and **Assigned Classroom/Lab**.
- Identifies back-to-back classes and scheduled prep intervals.

### 2.3 "Why I Was Assigned" (Explainability Card)
Click on any assigned course section to review the algorithm's justification:
- **Fit Breakdown**: Shows the mathematical scoring breakdown:
  - **Expertise Tag Match (60%)**: Alignment between your research tags and course syllabus tags.
  - **Syllabus Text Similarity (25%)**: TF-IDF match between your teaching history and course description.
  - **Past Continuity (15%)**: Recognition of previous terms you successfully taught this course.
- **Verified Invariants**: Confirms that your assignment satisfies all contractual rules:
  - `✓ HC-01`: Minimum domain proficiency met.
  - `✓ HC-02`: Maximum weekly teaching load respected.
  - `✓ HC-03`: Zero overlapping time clashes.
  - `✓ HC-04`: No assignment during approved leave or blacked-out slots.
  - `✓ HC-05`: Course preparation count within contractual ceiling.
- **Plain-Language Summary**: Transparent narrative explaining why you were selected as the optimal instructor for this section.

### 2.4 Anonymized Peer Load Benchmark
An interactive bar chart comparing your assigned weekly hours against department colleagues:
- Your load is prominently highlighted as **"You"**.
- Peer faculty are listed anonymously by rank only (e.g., `Peer 1 (Professor)`, `Peer 2 (Associate Professor)`).
- A dashed horizontal line indicates the **Department Median**, assuring you of workload equity.

---

## 3. Availability, Blackouts & Course Preferences (`/faculty/preferences`)

Use this page to communicate your scheduling constraints and teaching interests to the department chair before the automated schedule is solved.

### 3.1 Weekly Blackout Timeslot Selector
- An interactive Monday–Friday grid representing all departmental timeslots.
- Click any timeslot button to toggle it between:
  - 🟩 **Available** (Default)
  - ⬛ **Blackout / Unavailable** (e.g., designated research day, recurring committee meeting, or family commitments).
- Any timeslot marked as Blackout will be enforced by the solver as a hard invariant (`HC-04`), preventing the algorithm from scheduling classes during that window.

### 3.2 Approved Sabbatical & Leave Terms
- Check the box for any semester you are scheduled for approved sabbatical, research fellowship, or parental leave.
- Marking a term as Leave ensures the solver will assign 0 courses to you for that entire term (`HC-04`).

### 3.3 Course Teaching Preferences
- Browse the department course catalog.
- Multi-select courses you are enthusiastic to teach in upcoming terms.
- The optimizer rewards assigning preferred courses through soft constraint `SC-03`, increasing your likelihood of receiving your top course selections.

### 3.4 Saving & "Pending Re-Optimization" Status
1. Click **Save Preferences**.
2. A banner appears: **"Preferences Saved — Pending Re-Optimization"**.
3. *Note*: Updating your preferences does not instantly rewrite active semester schedules. Your changes will be factored in automatically when the department chair executes the next optimizer run for that term.

---

## 4. Submitting Assignment Change Requests (`/faculty/requests`)

If unforeseen circumstances prevent you from teaching an assigned section (e.g., medical emergency, grant award buyout, or unexpected schedule conflict):

### 4.1 Submitting a Request
1. Navigate to `/faculty/requests`.
2. Click **Submit New Request**.
3. Select the affected section from your current assignments.
4. Choose the request category:
   - *Time Slot Reschedule Request*
   - *Section Reassignment / Release Request*
   - *Load Reduction Request*
5. Provide a detailed, professional explanation in the **Rationale** textarea.
6. Click **Submit to Department Chair**.

### 4.2 Tracking Request Status
Your request appears in the chronological history table with live status tracking:
- 🟡 **Pending Review**: Request submitted and awaiting department chair review.
- 🟢 **Approved**: Department chair accepted the request; the schedule will be updated in the next solver run or manual override.
- 🔴 **Rejected**: Request declined. View the administrator's review feedback note directly in the table.
