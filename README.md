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

## 7. Key Architecture & Constraints

- **Explainability**: Every assignment constraint has a unique identifier (e.g., `HC-01_MAX_LOAD`, `SC-01_EXPERTISE_MATCH`). Solver outcomes cite these rule IDs directly.
- **Fairness Metrics**: Load distributions are mathematically evaluated via the **Gini Coefficient**, standard deviation of teaching hours, and max-min section gap.
- **Decoupled Training**: The backend **never** trains ML models. Training runs offline via `make train`, and the backend loads serialized, portable text models (`model.txt`, `< 5 MB`) at startup.