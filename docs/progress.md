# Engineering Progress Log

## 2026-10-29: Monorepo Scaffolding & Foundational Setup
- **Task Objective**: Initialize repository structure, baseline configuration, and documentation contracts.
- **Changes Implemented**:
  - Authored `docs/PROJECT_BRIEF.md` detailing technical specifications, constraints, and architecture.
  - Authored `AGENTS.md` enforcing compute budget, code layering, and development rules.
  - Authored `docs/architecture.md` with system layers and sequence diagrams.
  - Scaffolded monorepo tree across `backend/`, `frontend/`, `ml/`, `data/`, and `docs/`.
  - Configured root `Makefile`, `.env.example`, `.gitignore`, and `.github/workflows/ci.yml`.
- **Test Results & Verification Status**: Scaffolding validated; all placeholder files created with docstrings and comments.
- **Next Steps / Backlog Items**:
  - Implement seed datasets in `data/seed/`.
  - Implement ML demand forecasting baseline and LightGBM model.
  - Implement FastAPI Gist storage repository and auth/OTP endpoints.

## 2026-10-30: Runnable Scaffold Implementation & Live Health Check
- **Task Objective**: Make the frontend and backend scaffold fully runnable with exact pinned dependencies, CORS, error handling, config management, and live health integration.
- **Changes Implemented**:
  - Configured FastAPI backend: `app.core.config.Settings` using `pydantic-settings`, structured logging in `app.core.logging`, global error handling in `app.core.errors`, and `GET /api/v1/health` endpoint.
  - Configured CORS for Vite dev origins (`http://localhost:5173`, `http://localhost:3000`).
  - Created Python 3.11 virtual environment (`.venv`) and pinned exact runtime dependencies in `backend/requirements.txt` (CPU-only, no pandas, memory budget <= 512MB) and training dependencies in `ml/requirements-train.txt`.
  - Configured frontend with React Router 6, TanStack Query 5, Zod, Axios, Tailwind CSS v4 (`@tailwindcss/vite`), and Recharts.
  - Built Axios API client in `src/lib/apiClient.ts` reading `VITE_API_URL` with auth token interceptors.
  - Implemented application routes with placeholder pages for `/login`, `/admin`, and `/faculty`.
  - Implemented `LandingPage` with real-time polling to `/api/v1/health` displaying connection badge and service metadata.
  - Updated `.env.example` and created local `.env` with all required configuration variables.
  - Updated `Makefile` with targets: `dev-backend`, `dev-frontend`, `test`, `lint`, `train`, `benchmark-quick`, `e2e`.
  - Authored comprehensive `README.md` with step-by-step setup and verification instructions.
- **Test Results & Verification Status**:
  - `pytest backend/tests ml/tests`: 5 passed in 1.86s.
  - `npm run build` in `frontend/`: successfully built TypeScript bundle with zero errors.
  - Browser verification at `http://127.0.0.1:5173/`: live status confirmed showing `BACKEND ONLINE (200 OK)` with service details.
- **Next Steps / Backlog Items**:
  - Seed dataset generation in `data/seed/` (faculty profiles, courses, historical sections).
  - Gist and local repository storage implementation.
  - Passwordless email OTP authentication flow.

## 2026-10-30: Pydantic v2 Schemas & TypeScript Domain Types
- **Task Objective**: Implement complete Pydantic v2 domain schemas with boundary validation rules and matching TypeScript strict interfaces for all core entities.
- **Changes Implemented**:
  - Implemented modular Pydantic schemas in `backend/app/schemas/`:
    - `common.py`: Enums (`UserRole`, `FacultyRank`, `CourseLevel`, `ResourceType`, `DayOfWeek`, `RuleType`, `AssignmentSource`, `ViolationSeverity`).
    - `user.py`: `User` with email format and faculty role link validation.
    - `faculty.py`: `Faculty` and `FacultyExpertise` with `min_courses <= max_courses`, `max_preparations <= max_courses`, `proficiency` bounds (1-5), and duplicate tag prevention.
    - `course.py`: `Course` with credits/contact hours positivity and `min_proficiency` validation.
    - `section.py`: `Section` with quantile monotonicity (`size_p10 <= size_p50 <= size_p90`).
    - `resource.py`: `Resource` with positive capacity and type classification.
    - `timeslot.py`: `TimeSlot` with 24h `HH:MM` format validation and chronological ordering (`start < end`).
    - `constraint.py`: `ConstraintRule` with non-negative weights and stable `rule_id` convention.
    - `assignment.py`: `Assignment` with normalized fit scores (0.0 to 1.0) and rule satisfaction tracking.
    - `violation.py`: `Violation` with severity classifications, entity tracking, and suggested repairs.
    - `override.py`: `Override` with mandatory non-empty administrative justification and distinct faculty validation.
    - `audit.py`: `AuditLogEntry` for immutable change logging.
  - Created matching strict TypeScript types in `frontend/src/types/index.ts` with zero `any` usage.
  - Authored comprehensive validation test suite in `backend/tests/test_schemas.py` covering positive cases and boundary edge failures across all models.
  - Formatted and linted backend codebase with `black` and `ruff`.
- **Test Results & Verification Status**:
  - `pytest backend/tests ml/tests`: 34 passed in 0.86s (29 new schema tests + health & artifact checks).
  - `npm run build`: TypeScript compiled cleanly with strict mode.
  - `ruff` & `black`: clean with zero errors/warnings.
- **Next Steps / Backlog Items**:
  - Populate seed JSON fixtures in `data/seed/` conforming to the new schemas.
  - Implement Gist and local repository persistence adapters.
  - Wire schemas into FastAPI CRUD routers and service layers.

## 2026-10-30: Rule Catalog, Constraint Reasoning Engine, & Validation API
- **Task Objective**: Implement the complete rule catalog seeded into `constraints.json`, independent checker engine in `backend/app/services/constraint_engine.py`, REST API endpoints, documentation in `docs/constraint_catalog.md`, and test suites.
- **Changes Implemented**:
  - Seeded [`data/seed/constraints.json`](file:///e:/AI%20project/data/seed/constraints.json) with 12 complete hard (`HC-01` through `HC-07`) and soft (`SC-01` through `SC-05`) constraint definitions.
  - Developed [`backend/app/services/constraint_engine.py`](file:///e:/AI%20project/backend/app/services/constraint_engine.py):
    - Independent checker methods for all 12 constraints with plain-language explanations and suggested remediation actions.
    - Dynamic rule loading, saving, enabling/disabling, and weight overrides.
    - Robust lookup maps for high-performance scenario evaluations.
  - Implemented REST API in [`backend/app/api/v1/constraints.py`](file:///e:/AI%20project/backend/app/api/v1/constraints.py):
    - `GET /api/v1/constraints`: Retrieves active rule catalog.
    - `PUT /api/v1/constraints`: Admin-only batch rule update with RBAC role enforcement.
    - `POST /api/v1/constraints/validate`: Validates assignments against a scenario and outputs structured `ValidationResponse`.
  - Authored comprehensive documentation in [`docs/constraint_catalog.md`](file:///e:/AI%20project/docs/constraint_catalog.md).
  - Created test suites:
    - [`backend/tests/test_constraint_engine.py`](file:///e:/AI%20project/backend/tests/test_constraint_engine.py): At least 2 passing and 2 failing tests per rule (49 tests).
    - [`backend/tests/test_api_constraints.py`](file:///e:/AI%20project/backend/tests/test_api_constraints.py): End-to-end endpoint tests for list, admin update, faculty 403, and validate (4 tests).
- **Test Results & Verification Status**:
  - `pytest backend/tests ml/tests`: 87 passed in 4.46s (100% test pass rate).
  - `npm run build`: Frontend build verified with zero errors.
  - `ruff` & `black`: 100% clean across `backend` and `ml`.
## 2026-10-30: Seed Data Generator & 10 Named Evaluation Fixtures
- **Task Objective**: Build `ml/datagen.py` with seeded deterministic RNG, generating realistic base seed data in `data/seed/` and 10 evaluation fixtures in `data/fixtures/` (each under 1 MB), with complete CLI and automated test suite.
- **Changes Implemented**:
  - Implemented [`ml/datagen.py`](file:///e:/AI%20project/ml/datagen.py):
    - Seeded random generation (`seed=42`) with reproducible pseudo-random numbers.
    - Base scenario generator: 25 faculty across ranks, 40 courses across computing subdisciplines, 60 sections across 3 academic terms (Fall 2026, Spring 2027, Summer 2027), 10 facilities (6 lecture halls and 4 specialized labs), and a 20-slot weekly timeslot grid.
    - 3-year historical course enrollment generator (9 terms, 360 records) in [`data/seed/enrollment_history.json`](file:///e:/AI%20project/data/seed/enrollment_history.json) with underlying upward secular trend (+3.5%/yr), term seasonality (Fall peak, Spring moderate, Summer elective dip), Gaussian noise, and stochastic demand shock outliers (+35% to +60%).
    - Built 10 named evaluation fixtures in [`data/fixtures/`](file:///e:/AI%20project/data/fixtures/) with explicit `expected_outcome` (feasibility flag and plain-language reason):
      1. `balanced_baseline`: Feasible standard department distribution.
      2. `tight_capacity`: Feasible tight scenario with demand at ~98% of aggregate faculty capacity.
      3. `infeasible_expertise`: Infeasible due to `HC-01` (exotic course requiring Quantum Algorithms min proficiency 5).
      4. `leave_heavy`: Infeasible due to `HC-04` (30% faculty on sabbatical leave in a single term).
      5. `single_expert_bottleneck`: Infeasible due to `HC-02`/`HC-05` (only one qualified instructor for 5 distinct courses).
      6. `lab_resource_shortage`: Infeasible due to `HC-07` (lab capacity lower than cohort size).
      7. `time_clash_dense`: Infeasible due to `HC-03` (two sections assigned to the same faculty with overlapping slots).
      8. `demand_spike`: Feasible under nominal plan with extreme P90 spike for elasticity testing.
      9. `boundary_exact_limit`: Feasible boundary test where weekly load exactly equals `max_weekly_load_hours`.
      10. `boundary_zero_capacity`: Infeasible boundary test with empty summer term and undersized capacity.
    - Master aggregator file [`data/fixtures/scenarios.json`](file:///e:/AI%20project/data/fixtures/scenarios.json).
    - CLI entrypoint: `python -m ml.datagen --scenario all --seed 42`.
  - Built comprehensive test suite in [`ml/tests/test_datagen.py`](file:///e:/AI%20project/ml/tests/test_datagen.py):
    - `test_datagen_determinism`: Validates identical outputs for identical seeds, and divergent distributions for different seeds.
    - `test_seed_files_exist_and_under_size_limit`: Confirms all files exist and are strictly `< 1 MB` (actual max is ~114 KB).
    - `test_seed_schema_validation`: Validates every seed JSON against Pydantic v2 schemas (`User`, `Faculty`, `Course`, `Section`, `Resource`, `TimeSlot`).
    - `test_evaluation_fixtures`: Parametrized test evaluating all 10 fixtures through `ConstraintEngine().validate()` and confirming hard violation status matches `expected_outcome['feasible']` and expected rule violation IDs.
    - `test_scenarios_aggregate_json`: Verifies integrity of the master scenario index.
- **Test Results & Verification Status**:
  - `pytest ml/tests backend/tests`: 101 tests passed in 0.93s.
  - `npm run build`: Frontend build passed cleanly (TypeScript check + Vite bundle in 3.15s).
  - `ruff` & `black`: 100% compliant across backend and ml directories.
  - All file sizes well within compute budget (< 120 KB per file, aggregate JSON storage ~500 KB).
- **Next Steps / Backlog Items**:
  - Implement time-series & LightGBM course enrollment forecasting models (`ml/models/forecaster.py`, `ml/scripts/train.py`).
  - Implement OR-Tools CP-SAT solver and greedy baseline heuristics (`backend/app/services/solver.py`).
  - Wire Gist and local repository storage backend.


