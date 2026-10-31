# University Faculty Workload & Course Assignment Balancing System

An AI-assisted faculty-allocation system that connects expected course demand prediction, faculty expertise matching, and Google OR-Tools CP-SAT constraint reasoning with quantified fairness metrics (Gini index, standard deviation, max-min load gap).

---

## 1. Monorepo Architecture

```text
faculty-workload-system/
├── backend/                  # FastAPI REST API (Python 3.11, Pydantic v2, <= 512MB RAM)
│   ├── app/
│   │   ├── api/v1/           # API Routers (auth, faculty, courses, assign, health, etc.)
│   │   ├── core/             # Settings (pydantic-settings), structured logging, error handling
│   │   ├── repositories/     # Storage layer (Gist repository & local filesystem fallback)
│   │   ├── schemas/          # Pydantic v2 domain schemas & DTOs
│   │   └── services/         # Business logic, constraint orchestration, audit logging
│   └── tests/                # Pytest unit & integration test suite
├── frontend/                 # Vite + React + TypeScript strict mode
│   └── src/
│       ├── app/              # Router, QueryClient, global providers
│       ├── features/         # Feature modules (home, auth, admin, faculty)
│       └── lib/              # Axios API client (VITE_API_URL), formatters
├── ml/                       # Importable CPU-only ML package
│   ├── artifacts/            # Serialized models (<5MB text format) & metrics JSON
│   ├── fit/                  # TF-IDF & syllabus tag expertise matching
│   ├── forecast/             # LightGBM quantile demand forecasting (P10/P50/P90)
│   ├── optimizer/            # Google OR-Tools CP-SAT solver & greedy baseline
│   └── scripts/train.py      # Offline model training pipeline (`make train`)
├── data/                     # Seed JSON datasets and named boundary fixture scenarios
├── docs/                     # PROJECT_BRIEF, architecture, constraint catalog, progress logs
└── Makefile                  # Unified developer CLI commands
```

---

## 2. Prerequisites

- **Python**: 3.11 or higher (Native Windows / Linux / macOS)
- **Node.js**: 20.x or higher (`npm` 10+)
- **Compute Budget**: **CPU-Only** (No GPU, PyTorch, TensorFlow, or CUDA required). The backend operates within a strict **512 MB RAM** limit.

---

## 3. Quickstart Setup

### Step 1: Environment Configuration
Copy the configuration template and create your local `.env`:
```bash
cp .env.example .env
```
Default non-sensitive development settings are preconfigured (including `STORE_BACKEND=local`, `OTP_DEV_MODE=True`, and `FORECAST_MODE=model`).

### Step 2: Python Backend Environment
Create a Python 3.11 virtual environment and install runtime dependencies:
```bash
python3.11 -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies:
pip install -r backend/requirements.txt
pip install -e ml
```

### Step 3: Frontend Environment
Install the Node.js dependencies:
```bash
cd frontend
npm install
cd ..
```

---

## 4. Running the System

Start the backend and frontend dev servers in separate terminal sessions:

### Terminal 1: FastAPI Backend
```bash
make dev-backend
```
- API Base URL: `http://localhost:8000/api/v1`
- Interactive Swagger Docs: `http://localhost:8000/api/v1/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### Terminal 2: Vite Frontend
```bash
make dev-frontend
```
- Web Application URL: `http://localhost:5173/`

---

## 5. Acceptance Verification

1. Open **`http://localhost:5173/`** in your browser.
2. The landing page calls `GET /api/v1/health` automatically via TanStack Query.
3. Verify that the health badge displays **`BACKEND ONLINE (200 OK)`** along with:
   - **Service Name**: `Faculty Workload Balancing API`
   - **API Version**: `v0.1.0`
   - **Store Backend**: `LOCAL`
   - **Forecast Mode**: `MODEL`
4. Test placeholder navigation routes:
   - `/admin` &rarr; Administrative planning overview and solver configuration
   - `/faculty` &rarr; Faculty personal load and availability submission
   - `/login` &rarr; Passwordless email OTP authentication screen

---

## 6. Developer CLI Commands (`Makefile`)

| Command | Action |
| :--- | :--- |
| `make dev-backend` | Run FastAPI server with auto-reload on port 8000 |
| `make dev-frontend` | Run Vite development server on port 5173 |
| `make test` | Run quick unit and integration tests (< 2 minutes, CPU-only) |
| `make lint` | Run `ruff` and `black` code quality checks |
| `make train` | Run offline LightGBM training pipeline (`ml/scripts/train.py`) |
| `make benchmark-quick` | Run quick solver benchmark (OR-Tools vs. Greedy) |
| `make e2e` | Run frontend production bundle validation |

---

## 7. Interactive Demo Walkthrough Script

Follow these steps to demonstrate each core capability and outcome of the system:

### Demo 1: Feasible Allocation & CP-SAT vs. Greedy Fairness
1. **Sign in**: Visit `http://localhost:5173/login`, enter `admin@university.edu`, and log in with the dev passcode (`000000` or from `/api/v1/auth/dev-otp?email=admin@university.edu`).
2. **Load Scenario**: On `/admin`, use the **Scenario Loader** dropdown to select **`balanced_baseline`**.
3. **Run Optimizer**:
   - Click the **⚡ Optimizer** tab.
   - Select **Method: CP-SAT Solver**, **Forecast Mode: P50**, and click **Execute CP-SAT Solver**.
4. **Observe Outcome**:
   - Status transitions to **COMPLETED (Feasible)**.
   - Hard Violations: **0**.
   - Notice the **Comparison Card**: CP-SAT achieves a **Load Gini of ~0.07** vs. Greedy's **~0.49**, dramatically evening out workload across faculty.
   - Switch to **📈 Load View** to view the green balanced teaching bars.

---

### Demo 2: Instant Pre-Filter Pruning on Infeasible Scenarios
1. **Load Scenario**: From the scenario selector on `/admin`, choose **`infeasible_expertise`**.
2. **Execute Solver**: Go to **⚡ Optimizer** and click **Execute CP-SAT Solver**.
3. **Observe Outcome**:
   - The engine returns an **immediate infeasibility result in < 10ms** without wasting CPU cycles.
   - Displays the exact blocking rule: **`HC-01: Minimum Proficiency Deficit`** and the unstaffable section.
   - Variable count is pruned to 0, demonstrating Step 1 domain pre-filtering.

---

### Demo 3: Schedule Conflicts & Automated Remediation
1. **Load Scenario**: From the scenario dropdown, select **`time_clash_dense`** or **`tight_capacity`**.
2. **Inspect Violations**:
   - Navigate to the **⚠️ Conflicts** tab.
   - Review the violation cards tagged with **`Hard Invariant (Blocking)`**, citing `HC-03` (Time Slot Overlap) and `HC-02` (Max Load).
3. **Synthesize Repairs**:
   - Click the purple **🛠️ Synthesize Repairs** button.
   - The modal displays 3 automated alternatives with predicted impact:
     - *Relax HC-05 (Increase Course Preparations)*
     - *Inject Adjunct Teaching Capacity*
     - *Reschedule Overlapping Section Timeslot*
   - Click **Apply** on an alternative: the schedule is updated and re-optimization is triggered automatically.

---

### Demo 4: Controlled Human Override with Invariant Acknowledgement
1. **Open Assignments**: On `/admin`, click the **📋 Assignments** tab.
2. **Select Assignment**: Locate any assigned course section and click **Override**.
3. **Choose Replacement Faculty**: Select another instructor from the dropdown.
4. **Observe Live Invariant Check**:
   - If the new instructor exceeds contractual hours or has a schedule clash, a **red warning banner** immediately appears citing the exact rule (e.g., `HC-02: 15.0h exceeds 12.0h limit`).
5. **Complete Override**:
   - Enter an Administrative Justification: *"Chair-approved emergency sabbatical coverage"*.
   - Check the mandatory risk box: `[✓] I acknowledge these violations and force this override`.
   - Click **Apply Override**.
   - The row receives a prominent **Overridden** badge, and the event is permanently recorded in the **📜 Audit Trail**.

---

### Demo 5: Faculty Self-Service & Privacy Boundary
1. **Sign in as Faculty**: Log out and log back in as `ada.lovelace@university.edu`.
2. **Inspect Schedule**:
   - On `/faculty`, view your personal **Weekly Timetable Grid** and assigned contact hours.
   - View the **"Why I Was Assigned"** card showing the 60%/25%/15% fit score breakdown and satisfied rules (`✓ HC-01`, `✓ HC-02`).
3. **Verify Anonymization**:
   - Scroll to the **Department Load Comparison** chart. Confirm your bar is marked **"You"** and all other colleagues are strictly labeled **`Peer 1 (Professor)`**, with zero peer names or emails exposed.
4. **Verify RBAC Protection**:
   - Manually type `http://localhost:5173/admin` into the browser URL bar.
   - Observe immediate block: **`403 Access Forbidden: Administrator access required`**.

---

## 8. Key Architecture & Constraints

- **Explainability**: Every assignment constraint has a unique identifier (e.g., `HC-01_MAX_LOAD`, `SC-01_EXPERTISE_MATCH`). Solver outcomes cite these rule IDs directly.
- **Fairness Metrics**: Load distributions are mathematically evaluated via the **Gini Coefficient**, standard deviation of teaching hours, and max-min section gap.
- **Decoupled Training**: The backend **never** trains ML models. Training runs offline via `make train`, and the backend loads serialized, portable text models (`model.txt`, `< 5 MB`) at startup.
- **Single-Writer Persistence**: State is stored in a private GitHub Gist with optimistic concurrency checks, running in a single-worker container within a 512 MB RAM footprint.
