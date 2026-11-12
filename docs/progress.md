# Engineering Progress Log

## 2026-11-12: Login & OTP Page Input Text Visibility Fix
- **Task Objective**: Fix text color of entered email address and OTP digits on `/login` so letters and numbers appear in solid black/dark-ink rather than invisible white.
- **Changes Implemented**:
  - Identified root cause: `--color-slate-900: #ffffff` in Tailwind CSS theme caused `text-slate-900` to render as white text on white inputs.
  - In [`LoginPage.tsx`](file:///e:/AI%20project/frontend/src/features/auth/LoginPage.tsx), changed email input classes to `text-black` with inline `style={{ color: '#121410' }}` and `placeholder:text-slate-500`.
  - In [`OtpStep.tsx`](file:///e:/AI%20project/frontend/src/features/auth/OtpStep.tsx), updated 6-digit OTP passcode input to `text-black` with inline `style={{ color: '#121410' }}` and `placeholder:text-slate-500`.
  - In [`frontend/src/index.css`](file:///e:/AI%20project/frontend/src/index.css), added explicit CSS rules for `input#email` and `input#otp-code` guaranteeing `color: #121410 !important; -webkit-text-fill-color: #121410 !important;` and clearly legible placeholders across all browsers.
- **Test Results & Verification Status**:
  - `npm run build` in `frontend/`: 0 errors.
  - Deployed live to production on Vercel.
- **Next Steps / Backlog Items**:
  - Confirm user verification on live production login page.



## 2026-11-05: Live Database Testing & GitHub Gist Synchronization
- **Task Objective**: Test all database collections and domain entities, create a private GitHub Gist, synchronize all data live to the Gist, and configure the application to support live Gist persistence with optimistic concurrency.
- **Changes Implemented**:
  - Created private GitHub Gist persistence store: [`https://gist.github.com/62907a1fa0dd1bd05513a9b4ffd0a660`](https://gist.github.com/62907a1fa0dd1bd05513a9b4ffd0a660).
  - Synchronized and verified all 12 domain entity files from `data/store`:
    - `users.json` (27 items)
    - `faculty.json` (25 items)
    - `courses.json` (42 items)
    - `sections.json` (62 items)
    - `resources.json` (10 items)
    - `timeslots.json` (20 items)
    - `constraints.json` (12 items)
    - `forecasts.json` (40 items)
    - `assignments.json` (6 items)
    - `overrides.json` (17 items)
    - `audit_log.json` (446 items)
    - `change_requests.json` (16 items)
  - Enhanced [`backend/app/repositories/gist_store.py`](file:///e:/AI%20project/backend/app/repositories/gist_store.py) to manage `change_requests.json` and prefer existing `data/store` records during initial Gist bootstrapping.
  - Authored automated synchronization script [`scripts/sync_to_gist.py`](file:///e:/AI%20project/scripts/sync_to_gist.py) and added `make sync-gist` to [`Makefile`](file:///e:/AI%20project/Makefile).
  - Added [`backend/tests/conftest.py`](file:///e:/AI%20project/backend/tests/conftest.py) ensuring local isolation during fast pytest runs while allowing live Gist persistence during server runtime.
  - Performed live round-trip CRUD and CP-SAT solver optimization verification against GitHub Gist API with verified PATCH writes and ETag concurrency checks.
- **Test Results & Verification Status**:
  - Live round-trip audit entry creation and read-back verified against GitHub Gist `62907a1fa0dd1bd05513a9b4ffd0a660`.
  - Authenticated API test suite verified (`health`, `faculty`, `courses`, `sections`, `assign/run` all passing).
- **Next Steps / Backlog Items**:
  - Set `GIST_TOKEN` and `GIST_ID` on production Render deployment dashboard if continuous remote Gist persistence is desired on Render.



## 2026-11-05: GitHub README LaTeX Delimiter Compatibility Fix
- **Task Objective**: Fix GitHub markdown rendering error (`Missing or unrecognized delimiter for \left`) in Section 4.1 of `README.md`.
- **Changes Implemented**:
  - Replaced problematic `\left\{ ... \middle| ... \right\}` with GitHub-safe `\lbrace ... \mid ... \rbrace` notation.
  - Replaced `\left( ... \right)` in the objective formula with standard mathematical parentheses `( ... )`.
  - Replaced raw inline brace escapes `\{ ... \}` with `\lbrace ... \rbrace` for guaranteed cross-platform KaTeX/MathJax compatibility.
- **Test Results & Verification Status**:
  - Validated formula syntax; eliminates all unrecognized delimiter errors in GitHub's markdown renderer.
- **Next Steps / Backlog Items**:
  - Confirm clean rendering on `https://github.com/hcoona01/AI`.



## 2026-11-05: Comprehensive Professional GitHub README Overhaul
- **Task Objective**: Author an exhaustive, creative, and professional GitHub `README.md` showcasing system architecture, Mermaid diagrams, embedded benchmark performance graphs, complete API reference, ML training methods, mathematical constraint catalog, interactive walkthroughs, and dependency management.
- **Changes Implemented**:
  - Authored a multi-section, beautifully styled [`README.md`](file:///e:/AI%20project/README.md) featuring:
    - High-level architecture and sequence flowcharts using Mermaid syntax.
    - Embedded solver benchmark charts (`docs/img/benchmark_solve_time.png`, `benchmark_tradeoffs.png`, `benchmark_memory.png`).
    - Empirical solver comparison table (CP-SAT vs. Greedy across 10 evaluation fixtures).
    - Detailed LightGBM quantile demand forecasting methodology ($P_{10}, P_{50}, P_{90}$), feature engineering, and offline metrics table.
    - Complete formal constraint catalog (`HC-01` through `HC-07` and `SC-01` through `SC-05`) with mathematical notation.
    - Exhaustive REST API reference covering all 14 subrouters and endpoints.
    - 5-step interactive walkthrough script for administrative, diagnostic, override, and privacy testing.
    - Compute budget compliance rules (CPU-only, $\le 512\text{ MB}$ RAM, no GPU, no pickle).
- **Test Results & Verification Status**:
  - Pytest full suite verified: 233 passed in 58.70s.
  - Formatted and validated markdown structure, badges, tables, and links.
- **Next Steps / Backlog Items**:
  - Keep documentation synchronized with future API endpoint or scenario expansions.



## 2026-11-03: Landing Page Background & Animated Effects on Login / Auth Page
- **Task Objective**: Bring the landing page animated video backdrop, drifting anime clouds, and falling petals with frosted glass effects to `/login` and OTP verification.
- **Changes Implemented**:
  - Integrated [`DashboardBackground`](file:///e:/AI%20project/frontend/src/components/layout/DashboardBackground.tsx) into [`LoginPage.tsx`](file:///e:/AI%20project/frontend/src/features/auth/LoginPage.tsx).
  - Styled login card with semi-translucent frosted glass (`bg-white/90 backdrop-blur-xl border border-white/80 shadow-[0_24px_60px_rgba(40,60,15,0.14)] rounded-[28px]`) so the cherry blossom valley, floating clouds, and swaying petals flow seamlessly around and behind the form.
  - Upgraded inputs, quick-test buttons, and OTP fields in [`OtpStep.tsx`](file:///e:/AI%20project/frontend/src/features/auth/OtpStep.tsx) with matching frosted tactile styling and contrast-compliant typography.
- **Test Results & Verification Status**:
  - `npm run build` in `frontend/`: 0 errors.
  - Git committed and pushed to `origin/main` (`86a469d`).
  - Production deployed to Vercel at `https://pentalyx.vercel.app` (Ready).
- **Next Steps / Backlog Items**:
  - Continue refining UI components based on live user feedback.



## 2026-11-03: Pinned Static Sidebar Scrolling & Statistics Cards Typography Alignment
- **Task Objective**: Pin the dashboard sidebar tabs completely static during vertical page scrolling, and fix vertical alignment and font typography across the KPI statistics boxes (aligning "Infeasible" vs "34", Gini, etc.).
- **Changes Implemented**:
  - **Static Sidebar Lock**:
    - Removed `position: relative` override from `.dashboard-shell .app-aside` in `frontend/src/index.css`.
    - Pinned `<aside>` with `fixed top-0 left-0 bottom-0 z-40 h-screen w-64` in [`AdminLayout.tsx`](file:///e:/AI%20project/frontend/src/components/layout/AdminLayout.tsx) and [`FacultyLayout.tsx`](file:///e:/AI%20project/frontend/src/components/layout/FacultyLayout.tsx).
    - Added `md:pl-64` to `.dashboard-content` so content flows neatly alongside the static sidebar without jumping or shifting on scroll.
  - **KPI Statistics Cards Alignment & Typography**:
    - Added Google Font `Space Grotesk` (weights 500, 600, 700) and `Plus Jakarta Sans` to [`frontend/index.html`](file:///e:/AI%20project/frontend/index.html).
    - Defined `.stat-box`, `.stat-header` (`h-8 flex items-start`), `.stat-value-row` (`h-12 flex items-center`), `.stat-number`, `.stat-badge`, and `.stat-sub` (`h-5 flex items-center`) in [`frontend/src/index.css`](file:///e:/AI%20project/frontend/src/index.css).
    - Updated [`OverviewPanel.tsx`](file:///e:/AI%20project/frontend/src/features/admin/OverviewPanel.tsx) KPI cards: "Schedule Feasibility" (`⚠️ Infeasible`), "Hard Violations" (`34`), "Workload Fairness" (`0.900`), "Mean Expertise Fit" (`77.0%`), and "Unassigned Sections" (`24 / 25`) now share identical 48px vertically centered rows and tabular Space Grotesk typography with zero baseline drift.
    - Updated secondary stat cards in [`ConflictsPanel.tsx`](file:///e:/AI%20project/frontend/src/features/admin/conflicts/ConflictsPanel.tsx), [`ForecastPanel.tsx`](file:///e:/AI%20project/frontend/src/features/admin/ForecastPanel.tsx), and [`MyLoadPage.tsx`](file:///e:/AI%20project/frontend/src/features/faculty/myload/MyLoadPage.tsx) with `.stat-number`.
- **Test Results & Verification Status**:
  - `npm run build` in `frontend/`: 0 errors, successful production bundle.
  - Git committed and pushed to `origin/main` (`03979a5`).
  - Production deployed to Vercel at `https://pentalyx.vercel.app` (Ready).
- **Next Steps / Backlog Items**:
  - Monitor user feedback on mobile vs desktop responsiveness and stat clarity.



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
  - Wire Gist and local repository storage backend into FastAPI routers and domain services.

## 2026-10-30: Data Persistence & Repository Layer (`backend/app/repositories`)
- **Task Objective**: Implement `backend/app/repositories` as the sole data-access layer for the monorepo, supporting both private GitHub Gist and local JSON storage with identical interfaces, optimistic concurrency, caching, rate-limit backoff, and full test coverage.
- **Changes Implemented**:
  - Authored [`backend/app/repositories/base.py`](file:///e:/AI%20project/backend/app/repositories/base.py):
    - `BaseStore` abstract contract (`read_file`, `write_file`, `get_file_metadata`).
    - Generic `Repository[T]` with `get_all`, `get(id)`, `upsert(item)`, `delete(id)`, and `bulk_replace(items)`. Supports typed Pydantic v2 deserialization, custom `id_field`, and per-file async locking.
  - Implemented [`backend/app/repositories/local_store.py`](file:///e:/AI%20project/backend/app/repositories/local_store.py):
    - JSON-backed filesystem storage with atomic file writing via temporary replacements.
    - Deterministic version calculation using file `mtime_ns` and content SHA-256 digest.
    - Optimistic concurrency control detecting external file changes and raising `ConflictError` (`HTTP 409`).
    - In-memory TTL cache with force refresh support.
    - Automatic seeding from `data/seed` for offline development.
  - Implemented [`backend/app/repositories/gist_store.py`](file:///e:/AI%20project/backend/app/repositories/gist_store.py):
    - Async `httpx.AsyncClient` communicating with GitHub Gists API (`https://api.github.com/gists`).
    - Automatic creation of private GitHub Gist with all 11 managed files when `GIST_ID` is empty, printing the new Gist ID.
    - Truncated file handling (>1MB): detects `truncated: true` and fetches complete payload from `raw_url`.
    - GitHub rate-limit detection: inspects `X-RateLimit-Remaining` and `X-RateLimit-Reset`, raising structured `RateLimitError` (`HTTP 403`).
    - HTTP ETag conditional caching (`If-None-Match` -> `304 Not Modified`).
    - In-memory TTL cache preventing redundant API traffic.
    - Optimistic concurrency: monitors Gist `updated_at`, re-fetches and retries once upon collision, raising `ConflictError` (`HTTP 409`) on persistent conflict.
    - Per-file async write lock preventing concurrent in-process race conditions.
  - Configured [`backend/app/repositories/__init__.py`](file:///e:/AI%20project/backend/app/repositories/__init__.py):
    - Factory function `get_store()` selecting `LocalStore` or `GistStore` based on `STORE_BACKEND`.
    - Typed repository factory accessors for all 11 managed entities (`User`, `Faculty`, `Course`, `Section`, `Resource`, `TimeSlot`, `ConstraintRule`, `Assignment`, `Override`, `AuditLogEntry`, `forecasts`).
  - Added [`RateLimitError`](file:///e:/AI%20project/backend/app/core/errors.py) to global error handling hierarchy.
  - Authored comprehensive test suites:
    - [`backend/tests/test_local_store.py`](file:///e:/AI%20project/backend/tests/test_local_store.py): 6 tests covering CRUD, bulk replace, custom ID fields, optimistic concurrency conflicts, TTL caching, and 10 concurrent async writes.
    - [`backend/tests/test_gist_store.py`](file:///e:/AI%20project/backend/tests/test_gist_store.py): 5 tests with mocked `httpx.MockTransport` covering standard fetch/patch, ETag 304, in-memory TTL caching, >1MB truncated file `raw_url` fallback, 403 rate-limit handling, 409 optimistic concurrency conflict and retry, and private Gist auto-creation.
- **Test Results & Verification Status**:
  - `pytest backend/tests ml/tests`: 112 passed in 1.62s.
  - `ruff` & `black`: 100% compliant across `backend/` and `ml/`.
  - Frontend build: `npm run build` clean in 3.15s.
- **Next Steps / Backlog Items**:
  - Implement ML course demand forecaster (`ml/forecast/model.py`, LightGBM training script).
  - Implement OR-Tools CP-SAT assignment optimizer and heuristics (`backend/app/services/solver.py`).
  - Implement passwordless OTP authentication service and email verification router.

## 2026-10-30: Seed Store Utility, Role-Enforced CRUD Routers, & Scenario Loading
- **Task Objective**: Build `scripts/seed_store.py` for idempotent/reset persistence seeding, implement CRUD routers and domain services for `faculty`, `courses`, `sections`, `resources`, and `timeslots` with role-aware privacy and admin write locks, create scenario loading endpoint `POST /api/v1/scenarios/load/{name}`, and record immutable audit logs on every write mutation.
- **Changes Implemented**:
  - Created [`scripts/seed_store.py`](file:///e:/AI%20project/scripts/seed_store.py):
    - Idempotent seeding by default; supports `--reset` to atomically bulk-replace collections.
    - Loads all 7 core collections (`users`, `faculty`, `courses`, `sections`, `resources`, `timeslots`, `constraints`) into configured store (`local` or `gist`).
    - Records audit log event `STORE_SEEDED` in `audit_log.json`.
  - Implemented Domain Services in `backend/app/services/`:
    - [`audit_service.py`](file:///e:/AI%20project/backend/app/services/audit_service.py): `AuditService` logging immutable events and querying history by entity, actor, and action.
    - [`faculty_service.py`](file:///e:/AI%20project/backend/app/services/faculty_service.py): Role-aware querying (admins view directory; faculty view own profile only; 403 on other profiles) and admin-only CRUD with `FACULTY_CREATED`, `FACULTY_UPDATED`, `FACULTY_DELETED` audit logging.
    - [`course_service.py`](file:///e:/AI%20project/backend/app/services/course_service.py): Shared course catalog reads and admin-only CRUD with `COURSE_CREATED`, `COURSE_UPDATED`, `COURSE_DELETED` audit logging.
    - [`section_service.py`](file:///e:/AI%20project/backend/app/services/section_service.py): Section reads with term filtering and admin-only CRUD with `SECTION_CREATED`, `SECTION_UPDATED`, `SECTION_DELETED` audit logging.
    - [`resource_service.py`](file:///e:/AI%20project/backend/app/services/resource_service.py): Shared lecture halls and labs catalog with admin-only CRUD with `RESOURCE_CREATED`, `RESOURCE_UPDATED`, `RESOURCE_DELETED` audit logging.
    - [`timeslot_service.py`](file:///e:/AI%20project/backend/app/services/timeslot_service.py): Weekly scheduling grid management with admin-only CRUD with `TIMESLOT_CREATED`, `TIMESLOT_UPDATED`, `TIMESLOT_DELETED` audit logging.
    - [`scenario_service.py`](file:///e:/AI%20project/backend/app/services/scenario_service.py): Reads evaluation fixtures from `/data/fixtures/{name}.json`, validates Pydantic models, executes atomic bulk replacement across the store, and logs `SCENARIO_LOADED` audit entry.
  - Implemented Routers in `backend/app/api/v1/`:
    - [`faculty.py`](file:///e:/AI%20project/backend/app/api/v1/faculty.py): `GET /api/v1/faculty`, `GET /api/v1/faculty/{id}`, `POST`, `PUT`, `DELETE`.
    - [`courses.py`](file:///e:/AI%20project/backend/app/api/v1/courses.py): `GET /api/v1/courses`, `GET /api/v1/courses/{id}`, `POST`, `PUT`, `DELETE`.
    - [`sections.py`](file:///e:/AI%20project/backend/app/api/v1/sections.py): `GET /api/v1/sections?term=...`, `GET /api/v1/sections/{id}`, `POST`, `PUT`, `DELETE`.
    - [`resources.py`](file:///e:/AI%20project/backend/app/api/v1/resources.py): `GET /api/v1/resources`, `GET /api/v1/resources/{id}`, `POST`, `PUT`, `DELETE`.
    - [`timeslots.py`](file:///e:/AI%20project/backend/app/api/v1/timeslots.py): `GET /api/v1/timeslots`, `GET /api/v1/timeslots/{id}`, `POST`, `PUT`, `DELETE`.
    - [`scenarios.py`](file:///e:/AI%20project/backend/app/api/v1/scenarios.py): `POST /api/v1/scenarios/load/{name}` (admin-only).
    - [`audit.py`](file:///e:/AI%20project/backend/app/api/v1/audit.py): `GET /api/v1/audit` (admin-only with filtering).
    - Aggregated all subrouters in [`backend/app/api/v1/__init__.py`](file:///e:/AI%20project/backend/app/api/v1/__init__.py).
  - Configured Security & RBAC in [`backend/app/core/security.py`](file:///e:/AI%20project/backend/app/core/security.py):
    - `get_current_user` supporting JWT Bearer tokens and testing headers (`X-User-Role`, `X-User-Id`, `X-Faculty-Id`).
    - RBAC guards `require_admin` and `require_authenticated`.
  - Configured Storage Separation:
    - Pointed runtime `LOCAL_DATA_DIR` to `data/store`, protecting `data/seed` as pristine source of truth.
  - Comprehensive Test Suite in [`backend/tests/test_api_crud_and_rbac.py`](file:///e:/AI%20project/backend/tests/test_api_crud_and_rbac.py):
    - Role-aware faculty profile isolation (faculty reading other profile -> 403 Forbidden).
    - Shared reference data accessibility across all authenticated roles.
    - Strict rejection of write operations by faculty (403 Forbidden).
    - Admin CRUD execution and verification of audit trail entries.
    - Scenario fixture loading (`POST /api/v1/scenarios/load/{name}`), audit confirmation, and 403/404 validations.
- **Test Results & Verification Status**:
  - `pytest backend/tests ml/tests`: 117 passed in 2.15s.
  - `ruff` & `black`: 100% compliant across `backend/`, `ml/`, and `scripts/`.
  - Frontend build: `npm run build` clean in 3.08s.
- **Next Steps / Backlog Items**:
  - Implement course demand forecasting pipeline with LightGBM.
  - Implement OR-Tools CP-SAT optimizer for assignment balance and repair heuristics.
  - Build frontend pages connecting to the new CRUD APIs.



## 2026-10-30: Passwordless Email OTP Authentication & Session Lifecycle
- **Task Objective**: Implement secure passwordless Email OTP authentication, in-memory salted-hash persistence with attempt tracking, rate-limiting, JWT session lifecycle (15-min access token + httpOnly refresh cookie), profile endpoint, RBAC dependencies, and test suite.
- **Changes Implemented**:
  - Auth Schemas in [`backend/app/schemas/auth.py`](file:///e:/AI%20project/backend/app/schemas/auth.py):
    - `OTPRequest`, `OTPVerifyRequest` (strict 6-digit regex), `OTPResponse`, `TokenResponse`, `RefreshTokenRequest`, `MessageResponse`.
  - In-Memory OTP Service in [`backend/app/services/otp_service.py`](file:///e:/AI%20project/backend/app/services/otp_service.py):
    - Generates 6-digit OTP using Python `secrets`.
    - Persists ONLY a 16-byte random salt and SHA-256 salted hash with a 5-minute TTL in an in-memory dictionary (never in Gist or disk).
    - Max 5 verification attempts per code; constant-time hash comparison via `secrets.compare_digest`.
    - Strictly single-use (record purged immediately upon successful verification).
    - Account lockout upon 5 wrong attempts (record purged).
    - Rate limiting: max 3 requests per email and per client IP per 10 minutes (returns HTTP 429).
    - Console logging dispatch in `OTP_DEV_MODE=True`, SMTP dispatch via `smtplib` in production mode.
  - Auth Service in [`backend/app/services/auth_service.py`](file:///e:/AI%20project/backend/app/services/auth_service.py):
    - `request_otp`: Validates rate limits and generates OTP only if user exists, returning identical generic response to prevent account enumeration.
    - `verify_otp`: Verifies OTP, looks up user, and generates 15-minute access token and 7-day refresh token.
    - `refresh_session`: Validates refresh token JWT claim and issues renewed token pair.
  - Security Dependencies & Token Helpers in [`backend/app/core/security.py`](file:///e:/AI%20project/backend/app/core/security.py):
    - `create_access_token` (15-minute default) and `create_refresh_token` (7-day default) with token type claims.
    - `get_current_user` validating Bearer access tokens (rejecting refresh tokens) or testing headers, raising 401 Unauthorized for unauthenticated requests.
    - RBAC guards `require_admin`, `require_faculty`, and privacy helper `verify_faculty_access` (ensuring faculty can only access their own `faculty_id`).
  - Auth & Profile Routers:
    - [`backend/app/api/v1/auth.py`](file:///e:/AI%20project/backend/app/api/v1/auth.py): `POST /auth/request-otp`, `POST /auth/verify-otp`, `POST /auth/refresh`, `POST /auth/logout` (with httpOnly, SameSite cookie handling).
    - [`backend/app/api/v1/me.py`](file:///e:/AI%20project/backend/app/api/v1/me.py): `GET /me` returning current user profile.
    - Mounted in [`backend/app/api/v1/__init__.py`](file:///e:/AI%20project/backend/app/api/v1/__init__.py) and [`backend/app/main.py`](file:///e:/AI%20project/backend/app/main.py) to support both `/api/v1/auth/*` and `/auth/*` as well as `/me` and `/api/v1/me`.
  - Config & Environment:
    - Updated `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `OTP_CODE_TTL_MINUTES=5`, and `REFRESH_TOKEN_EXPIRE_DAYS=7` in [`backend/app/core/config.py`](file:///e:/AI%20project/backend/app/core/config.py), [`.env.example`](file:///e:/AI%20project/.env.example), and [`.env`](file:///e:/AI%20project/.env).
    - Seeded user store contains 1 admin, 1 department chair, and 25 faculty users matching faculty dataset.
  - Comprehensive Test Suite in [`backend/tests/test_auth.py`](file:///e:/AI%20project/backend/tests/test_auth.py):
    - Verified generic response preventing account enumeration.
    - Verified rate limits (429 on 4th request within 10m for email and IP).
    - Verified successful verification, 15-minute token, and httpOnly refresh cookie.
    - Verified single-use rejection on immediate reuse.
    - Verified rejection of expired OTP codes.
    - Verified lockout and record purge after 5 failed attempts.
    - Verified session refresh and cookie clearing on logout.
    - Verified `GET /me` (401 unauth, 200 for faculty and admin).
    - Verified 403 Forbidden for faculty JWT on admin routes.
    - Verified `verify_faculty_access` helper behavior.
- **Test Results & Verification Status**:
  - `pytest backend/tests`: 113 passed in 13.62s.
  - `ruff` & `black`: 100% compliant across backend codebase.
- **Next Steps / Backlog Items**:
  - Wire frontend auth flow (`LoginPage`, `OtpStep`) to `/auth/request-otp` and `/auth/verify-otp`.
  - Implement ML demand forecasting and OR-Tools optimization engine.

## 2026-10-30: Frontend Passwordless Authentication Flow & Dashboard Shells
- **Task Objective**: Build complete frontend authentication flow with 2-step OTP login, in-memory token state, silent cookie refresh, route guards, 403/404 error pages, and responsive layout shells for Admin and Faculty dashboards.
- **Changes Implemented**:
  - API Client Updates in [`frontend/src/lib/apiClient.ts`](file:///e:/AI%20project/frontend/src/lib/apiClient.ts):
    - Configured `withCredentials: true` for httpOnly refresh cookies.
    - Implemented in-memory access token storage via closure (`setAccessToken`, `getAccessToken`), completely eliminating `localStorage`.
    - Request interceptor attaching `Authorization: Bearer <inMemoryToken>`.
    - Added typed methods: `requestOtpApi`, `verifyOtpApi`, `refreshSessionApi`, `logoutApi`, `fetchCurrentUserApi`.
  - Auth State Context in [`frontend/src/features/auth/AuthContext.tsx`](file:///e:/AI%20project/frontend/src/features/auth/AuthContext.tsx) & [`frontend/src/hooks/useAuth.ts`](file:///e:/AI%20project/frontend/src/hooks/useAuth.ts):
    - `AuthProvider` maintaining `user`, `accessToken`, `isAuthenticated`, `isLoading`, and `error` in memory.
    - Silent refresh on page load calling `/auth/refresh` with cookies.
    - `requestOtp`, `verifyOtp`, and `logout` (clearing queries and memory tokens).
  - 2-Step Login UI:
    - [`frontend/src/features/auth/LoginPage.tsx`](file:///e:/AI%20project/frontend/src/features/auth/LoginPage.tsx): Step 1 email input with Zod validation, accessible aria attributes, loading spinners, inline errors, quick-fill test account pills (`admin@university.edu`, `alan.turing@university.edu`), and role-based redirect upon login.
    - [`frontend/src/features/auth/OtpStep.tsx`](file:///e:/AI%20project/frontend/src/features/auth/OtpStep.tsx): Step 2 6-digit numeric OTP input with 60-second countdown resend cooldown timer, automatic submit upon 6th digit, dev-mode console hint banner, inline error alert, and "Change Email" action.
  - Route Guards & Error Pages:
    - [`frontend/src/components/layout/ProtectedRoute.tsx`](file:///e:/AI%20project/frontend/src/components/layout/ProtectedRoute.tsx): Checks session loading state, redirects unauthenticated users to `/login`, and blocks unauthorized roles with 403 Forbidden page.
    - [`frontend/src/components/layout/ForbiddenPage.tsx`](file:///e:/AI%20project/frontend/src/components/layout/ForbiddenPage.tsx): Accessible 403 page with clear role explanations, "Go to My Dashboard" button, and "Switch Account" action.
    - [`frontend/src/components/layout/NotFoundPage.tsx`](file:///e:/AI%20project/frontend/src/components/layout/NotFoundPage.tsx): Accessible 404 page returning to dashboard.
  - Dashboard Shells & Navigation:
    - [`frontend/src/components/layout/AdminLayout.tsx`](file:///e:/AI%20project/frontend/src/components/layout/AdminLayout.tsx): Admin console sidebar (Overview, Assignments, Forecasts, Faculty, Courses, Constraints, Scenarios, Audit) with active state highlighting, mobile responsive drawer, and topbar with user badge and Sign Out button.
    - [`frontend/src/components/layout/FacultyLayout.tsx`](file:///e:/AI%20project/frontend/src/components/layout/FacultyLayout.tsx): Faculty portal sidebar (Schedule, Availability, Expertise, Courses) and topbar with user email, faculty ID, and Sign Out button.
    - [`frontend/src/components/layout/FeaturePlaceholderPage.tsx`](file:///e:/AI%20project/frontend/src/components/layout/FeaturePlaceholderPage.tsx): Placeholder components for upcoming feature views.
    - Updated [`frontend/src/app/router.tsx`](file:///e:/AI%20project/frontend/src/app/router.tsx) with nested route structure.
- **Test Results & Verification Status**:
  - `npm --prefix frontend run build`: TypeScript compiled and Vite production build succeeded with zero errors (163 modules transformed in 4.68s).
  - Integration acceptance test verified:
    - Admin login via OTP -> lands on `/admin`, prevented from unauthorized faculty reads (403).
    - Faculty login via OTP -> lands on `/faculty`, prevented from admin operations (403).
    - Silent refresh and logout verified.
  - Backend tests: 113 tests passing cleanly in `pytest backend/tests`.
- **Next Steps / Backlog Items**:
  - Implement LightGBM quantile regression demand forecasting offline pipeline (`make train`).
  - Implement OR-Tools CP-SAT solver service for section-to-faculty balancing.

## 2026-10-31: Section Demand Forecaster (Quantile Regression & Precomputed Inference)
- **Task Objective**: Build the CPU-only section-demand forecaster in `/ml/forecast` with offline training (`make train`), quantile regression (P10, P50, P90), baselines comparison, portable text serialization, backend inference endpoints, and comprehensive unit tests.
- **Changes Implemented**:
  - Baseline Demand Heuristics ([`ml/forecast/baselines.py`](file:///e:/AI%20project/ml/forecast/baselines.py)):
    - `seasonal_naive`: Returns historical enrollment from the most recent identical season.
    - `moving_average_3`: Computes mean enrollment across the prior 3 observed terms.
    - `evaluate_baseline`: Measures MAE and RMSE on held-out validation records using strictly prior context.
  - LightGBM Quantile Regressors ([`ml/forecast/model.py`](file:///e:/AI%20project/ml/forecast/model.py)):
    - Feature pipeline engineering 10 lightweight features: `credits`, `is_lab`, `is_elective`, `level_enc`, `lag1_enrolled`, `lag2_enrolled`, `rolling3_mean`, `term_index_norm`, `season_enc`, `prereq_cohort_size`.
    - Downcasts data structures to `float32` for strict memory efficiency.
    - Trains 3 LightGBM quantile regressors ($\alpha \in \{0.1, 0.5, 0.9\}$) with `n_jobs=1`, `num_leaves=15`, `n_estimators=150`, fixed `random_state=42`.
  - Metrics & Evaluation ([`ml/forecast/evaluate.py`](file:///e:/AI%20project/ml/forecast/evaluate.py)):
    - Computes MAE, RMSE, WAPE, and P10-P90 interval coverage.
  - Inference & Monotonicity Enforcement ([`ml/forecast/predict.py`](file:///e:/AI%20project/ml/forecast/predict.py)):
    - Loads native LightGBM text models (`.txt`, never pickle).
    - Enforces strict quantile monotonicity ($P_{10} \le P_{50} \le P_{90}$) by sorting per row.
    - Converts demand to sections: $\text{n\_sections} = \lceil P_{50} / \text{section\_cap} \rceil$ and $\text{p90\_risk\_sections} = \lceil P_{90} / \text{section\_cap} \rceil$.
  - Offline Training Script ([`ml/scripts/train.py`](file:///e:/AI%20project/ml/scripts/train.py)):
    - Executed via `make train` (or `python ml/scripts/train.py`), finishing in ~0.3s on CPU.
    - Time-ordered split: Terms 1-7 for training (280 records), Terms 8-9 for validation (80 records).
    - Produces artifacts in `ml/artifacts/`: `forecast_p10.txt` (228 KB), `forecast_p50.txt` (226 KB), `forecast_p90.txt` (226 KB), `feature_config.json` (<1 KB), `metrics.json` (~1 KB, SHA-256 hash `43fe3034...`), `precomputed_forecasts.json` (28 KB). All files $< 0.25$ MB, well under the 5 MB threshold.
  - Backend Integration:
    - Domain schemas in [`backend/app/schemas/forecast.py`](file:///e:/AI%20project/backend/app/schemas/forecast.py) (`ForecastRecord`, `ForecastRunResponse`).
    - Service layer in [`backend/app/services/forecast_service.py`](file:///e:/AI%20project/backend/app/services/forecast_service.py):
      - `FORECAST_MODE=model`: Loads text artifacts and computes quantiles on demand. Never trains models. Returns HTTP 503 if artifacts are missing, advising the user to run `make train`.
      - `FORECAST_MODE=precomputed`: Reads `precomputed_forecasts.json` without importing `lightgbm`, preserving the 512 MB memory budget.
      - Updates matching `Section` instances in `sections.json` (`size_p10`, `size_p50`, `size_p90`).
      - Emits audit event `FORECAST_RUN`.
    - API router in [`backend/app/api/v1/forecast.py`](file:///e:/AI%20project/backend/app/api/v1/forecast.py):
      - `POST /api/v1/forecast/run` (admin only).
      - `GET /api/v1/forecast` (authenticated, query param `term`).
      - Registered in [`backend/app/api/v1/__init__.py`](file:///e:/AI%20project/backend/app/api/v1/__init__.py).
  - Documentation:
    - Authored [`docs/model_card.md`](file:///e:/AI%20project/docs/model_card.md) covering training data, features, hyperparameters, validation metrics (MAE 4.34 vs baseline 4.51/12.05), operational modes, limitations, and retraining workflow.
  - Tests:
    - Unit & validation tests in [`ml/tests/test_artifacts.py`](file:///e:/AI%20project/ml/tests/test_artifacts.py): artifact existence, file size limits (<5MB), JSON schemas, monotonicity, section conversion, baselines, determinism, 503 guard on missing artifacts, and precomputed mode without `lightgbm`.
    - Integration tests in [`backend/tests/test_forecast_api.py`](file:///e:/AI%20project/backend/tests/test_forecast_api.py): RBAC checks (403 for faculty, 401 unauth, 200 for admin), query by term, and 503 error handling.
- **Test Results & Verification Status**:
  - `python ml/scripts/train.py`: offline training finished in 0.3s; all 6 artifacts created and verified $< 5$ MB.
  - `pytest ml/tests backend/tests`: 150 passed in 4.96s (100% pass rate).
- **Next Steps / Backlog Items**:
  - Implement faculty-course matching & expertise similarity scoring (TF-IDF & domain tag overlap).
  - Implement OR-Tools CP-SAT multi-objective optimization assignment solver.


## 2026-10-31: Faculty-to-Course Expertise Fit Scoring Pipeline
- **Task Objective**: Implement `/ml/fit/scoring.py` with multi-component expertise fit scoring in $[0.0, 1.0]$, runtime TF-IDF text similarity, explainable breakdown dictionary, independent HC-01 feasibility gating, and vectorized full-matrix evaluation in `float32`.
- **Changes Implemented**:
  - Fit Scoring Pipeline ([`ml/fit/scoring.py`](file:///e:/AI%20project/ml/fit/scoring.py)):
    - Formulated 3-component weighted score:
      $$\text{fit}(f, c) = 0.60 \times M_{\text{tag}} + 0.25 \times M_{\text{tfidf}} + 0.15 \times M_{\text{past}}$$
    - $M_{\text{tag}}$: Normalized mean proficiency ($\text{proficiency}/5.0$) across course required tags (with optional tag weights; 1.0 if no tags required).
    - $M_{\text{tfidf}}$: Dynamic runtime TF-IDF vectorization and cosine similarity between faculty profile text (name, rank, expertise tags, past courses) and course syllabus text (code, title, description, tags). Never pickled.
    - $M_{\text{past}}$: Historical past-teaching bonus, scaled and capped at `past_teaching_cap` (default 2 terms).
    - Explainable UI breakdown dictionary returning component scores, weighted values, tag details, times taught, and HC-01 compliance evidence.
    - `FitResult` interface supporting float conversion, tuple unpacking `(score, breakdown)`, attribute access, and subscripting.
    - Hard constraint filter `check_hc01`: Assesses whether faculty proficiency $\ge$ course `min_proficiency` across all required tags as an independent gate (not subtracted from fit score).
    - Vectorized full matrix evaluation:
      - `compute_fit_matrix`: Fits TF-IDF on combined corpus at runtime, computes sparse cosine product, and aggregates tag and past-teaching matrices into an $(N, M)$ `float32` ndarray in $[0.0, 1.0]$.
      - `compute_hc01_mask`: Produces an $(N, M)$ boolean feasibility mask for HC-01.
  - Subpackage Exports ([`ml/fit/__init__.py`](file:///e:/AI%20project/ml/fit/__init__.py)):
    - Exported `fit`, `check_hc01`, `compute_fit_matrix`, `compute_hc01_mask`, and `FitResult`.
  - Comprehensive Unit Tests ([`ml/tests/test_fit_scoring.py`](file:///e:/AI%20project/ml/tests/test_fit_scoring.py)):
    - Hand-computed exact numerical test verifying tag match, past teaching bonus, and dynamic TF-IDF breakdown.
    - Past-teaching bonus scaling and capping validation ($0 \to 0.0$, $1 \to 0.50$, $2 \to 1.00$, $5 \to 1.00$).
    - HC-01 independence test verifying deficient proficiency fails feasibility without distorting continuous score.
    - Missing tag handling ($0/5$ proficiency) and course without required tags ($1.0$ tag match).
    - Disjoint vocabulary test yielding $0.0$ TF-IDF score.
    - Pydantic v2 domain model (`Faculty`, `Course`) and raw dictionary compatibility.
    - Vectorized `compute_fit_matrix` shape $(10, 5)$, `float32` dtype, and $[0.0, 1.0]$ bounds.
    - Vectorized `compute_hc01_mask` shape and boolean accuracy.
- **Test Results & Verification Status**:
  - `pytest ml/tests/test_fit_scoring.py`: 9 passed in 2.50s.
  - `pytest ml/tests backend/tests`: 159 passed in 6.56s (100% pass rate).
- **Next Steps / Backlog Items**:
  - Implement Google OR-Tools CP-SAT multi-objective optimization assignment solver integrating demand quantiles, expertise fit matrix, and hard/soft constraints.

## 2026-11-01: Optimizer Suite — Tests, Fixes & Validation

- **Task Objective**: Implement and fully validate the `/ml/optimizer` package — CP-SAT solver, greedy baseline, fairness metrics, infeasibility explanation, repair alternatives — with a comprehensive pytest suite covering all 10 evaluation fixtures.

### Changes Implemented

#### `ml/optimizer/cpsat.py`
- **STEP 1 pre-filtering** (`prefilter_eligible_pairs`): Builds eligible set E of `(faculty, section)` pairs by removing HC-01 (proficiency), HC-04 (leave/unavailability), and HC-07 (resource) violations before model creation. Logs avoided variable count.
- **STEP 2 short-circuit**: If any section has zero eligible faculty, returns immediate `INFEASIBLE` `SolveResult` naming the section and blocking rule IDs.
- **CP-SAT constraints**: HC-02 (load hours + max courses), HC-03 (time clash grouped by slot), HC-05 (max distinct preparations via auxiliary y-vars), HC-06 (exactly one faculty per section). All enforced via assumption literals for minimal conflict core extraction.
- **Objective**: `w1*sum(fit*x) - w2*fairness_gap - w3*pref_miss + w4*continuity` with integer-scaled coefficients (`SCALE_FACTOR=1000`). Weights from `rule_weights` dict (overridable).
- **Solver config**: `num_workers=1`, configurable time limit (default 20s), configurable `random_seed`.
- **Benchmark fields returned**: `solve_time_seconds`, `status`, `objective_value`, `objective_bound`, `variable_count`, `variables_avoided`, `peak_memory_mb` (via `tracemalloc`).
- **P50/P90 demand profiles**: `demand_profile` parameter selects `size_p50` or `size_p90` for HC-07 capacity checks.

#### `ml/optimizer/greedy.py`
- Same interface as CP-SAT. Pre-filters identically (HC-01, HC-04, HC-07).
- Orders sections by most-constrained first (fewest eligible candidates, then contact hours descending).
- Selects highest fit + spare capacity candidate respecting dynamic HC-02, HC-03, HC-05 checks.

#### `ml/optimizer/fairness.py`
- `compute_gini`: Vectorised Gini coefficient via sorted rank formula.
- `compute_standard_deviation`: Sample std-dev (`ddof=1`).
- `compute_max_min_gap`: `max - min` of loads.
- `compute_fairness_summary`: Overall + per-rank breakdown dict.

#### `ml/optimizer/explain.py`
- `generate_explanation(solve_result, faculty, courses, sections, ...)` → `ExplanationResult`.
- For feasible results: trivial pass-through.
- For infeasible: re-runs `prefilter_eligible_pairs`, maps per-section zero-eligible counts to rule IDs, combines with assumption-literal conflict core, generates per-rule narrative paragraphs and suggested repair actions.
- Signature now accepts `previous_assignments` (ignored) for interface consistency.

#### `ml/optimizer/repair.py`
- `generate_repairs(...)` → `list[RepairAlternative]` (up to `max_repairs=3`).
- Four repair strategies: `relax_hc05` (increase prep limits), `add_adjunct` (inject a new faculty member with full expertise), `move_timeslot` (shift colliding section), `expand_facility` (upgrade resource capacity; only generated when HC-07 is blocking).
- Each is re-solved with a 5s CP-SAT limit. Results ranked by (feasibility restored, mean fit, -Gini).

#### `ml/optimizer/__init__.py`
- Exports all public symbols.

#### `ml/tests/test_optimizer.py` *(new, 46 tests)*
- **Fixture feasibility (CP-SAT)**: 10 parametrised cases covering all fixtures. `leave_heavy` correctly marked FEASIBLE by optimizer (7/10 faculty are available; the fixture's "infeasibility" in `test_datagen.py` is about the *pre-supplied* on-leave assignments tested by `ConstraintEngine`, not the optimizer's search).
- **Fixture feasibility (Greedy)**: Same 10 cases.
- **Reproducibility**: Two identical `seed=42` runs on `balanced_baseline` produce identical `objective_value` and `mean_fit`.
- **Pre-filter variable reduction**: Verified on `balanced_baseline` (14 of 25 pairs pruned via HC-01). `leave_heavy` prunes exactly 9 pairs (3 on-leave × 3 sections). `tight_capacity` correctly avoids 0 pairs (all eligible).
- **Fairness metrics**: Unit tests for Gini (equality=0, extreme inequality>0.5, empty, single), std-dev (homogeneous=0, known sample), max-min gap (zero, known value, empty).
- **Fairness in result**: CP-SAT `SolveResult.fairness` carries all required keys with Gini ∈ [0,1].
- **Explanation**: Feasible → trivial result; infeasible HC-01 → `HC-01` in `primary_rule_ids`; infeasible HC-07 → `HC-07` in `primary_rule_ids`.
- **Repair**: Feasible → empty list; infeasible → ≥1 `RepairAlternative`; HC-07 → `expand_facility` present; `max_repairs` respected.
- **Benchmark fields**: All mandatory fields present and non-negative; feasible result has non-None `objective_value` and `objective_bound`.
- **P50/P90 profiles**: Both run without error on `leave_heavy` (resource-free fixture).
- **Infeasible result diagnostics**: At least one of `blocking_rule_ids` or `conflicts` is non-empty.

### Test Results & Verification Status

```
ml/tests/test_artifacts.py    18 passed
ml/tests/test_datagen.py      14 passed
ml/tests/test_fit_scoring.py   9 passed
ml/tests/test_optimizer.py    46 passed
─────────────────────────────────────
Total                          87 passed  in 11.20s  (0 failed)
```

All tests green. Full suite runs in ~11 seconds, well inside the 2-minute local budget.

### Next Steps / Backlog Items
- Add backend API endpoint `/api/v1/optimize` (POST) that invokes `solve_cpsat` or `solve_greedy` based on a query parameter, serialises `SolveResult` to JSON, and guards with `require_admin`.
- Wire `generate_explanation` and `generate_repairs` into the API response so the frontend can render conflict narratives and repair options.
- Frontend: Build the assignment dashboard pages (`/admin/optimize`, `/admin/assignments`) consuming the optimizer endpoints.
- Benchmark table: Record solve time and memory for all 10 fixtures at default 20s limit.

## 2026-11-01: Solver Benchmarking Suite & Trade-Off Documentation

- **Task Objective**: Implement `/ml/benchmark/run_benchmark.py` with `--profile` (`quick` vs `full`), record performance metrics across CP-SAT and greedy baseline, render `/docs/benchmark.md` and comparison charts in `/docs/img/`, and validate execution speed (< 2 minutes) and schema integrity.

### Changes Implemented

#### `ml/benchmark/run_benchmark.py`
- Built benchmarking CLI with `--profile` argument (`quick` default, `full` optional).
  - **`quick`**: 3 representative fixtures (`balanced_baseline`, `tight_capacity`, `single_expert_bottleneck`), P50 only, 1 seed (42), 10s time limit. Runs in ~1 second.
  - **`full`**: All 10 fixtures, P50 and P90 demand profiles, 3 seeds (42, 123, 999), 30s time limit.
- Metrics recorded per run: feasibility, status, objective value, mean/min/max fit score, workload Gini coefficient, load standard deviation, max-min workload gap, number of hard constraint violations (via `ConstraintEngine`), solve time (seconds), variable count, variables avoided by pre-filter, and peak memory in MB (via `tracemalloc`).
- Serializes complete benchmark report to `/ml/artifacts/benchmark_<profile>.json`.
- Generates 3 visualization figures under `/docs/img/`:
  - `benchmark_solve_time.png`: Execution time comparison (log scale).
  - `benchmark_tradeoffs.png`: Dual plot of Expertise Fit score vs. Workload Fairness (Gini index).
  - `benchmark_memory.png`: Peak memory footprint vs. 512 MB memory ceiling.
- Renders `/docs/benchmark.md` with:
  - Markdown comparison table across scenarios.
  - Trade-off analysis detailing strengths and weaknesses of each solver.
  - Computational effort summary confirming CPU-only and < 512 MB compliance.
  - "Selected approach and rationale" section documenting when CP-SAT is mandatory (fairness, feasibility guarantees) and where Greedy is competitive (instant UI feedback, tight uniform capacity).

#### `ml/tests/test_benchmark.py`
- Added 3 unit tests verifying:
  - `test_quick_benchmark_finishes_under_two_minutes`: Asserts complete run completes in < 120s (actual: ~1.1s).
  - `test_benchmark_json_schema`: Validates metadata and runs schema, required fields, and boundary invariants.
  - `test_benchmark_docs_and_images_generated`: Validates generated markdown sections and non-empty PNG charts.

### Test Results & Verification Status
- `ml/tests/test_benchmark.py`: 3/3 passed.
- Entire ML test suite (`ml/tests/`): **90 passed in 10.76s** (0 failed).

### Next Steps / Backlog Items
- Wire the benchmark results and optimizer routines into the backend FastAPI service (`POST /api/v1/optimize`).
- Connect frontend dashboard to visualize solver trade-offs and repair options.

## 2026-11-01: Backend Optimization Service, Endpoints & Override Management

- **Task Objective**: Expose the CP-SAT/Greedy optimizer through backend REST endpoints with asynchronous background execution, single-active-job RAM guard, explainability, fairness calculations, conflict diagnosis, repair application, and auditable human overrides.

### Changes Implemented

#### `backend/app/services/assignment_service.py`
- Built `AssignmentService` managing:
  - `start_optimization_job`: Asynchronously triggers CP-SAT or Greedy allocation in a background worker thread (`asyncio.to_thread`), enforcing strict single-active-job protection (raises `409 Conflict` if another job is running).
  - `get_job`: In-memory status polling for job progress, durations, objective values, fairness summary, and error tracking.
  - Assignment persistence: Validates solver outputs against `ConstraintEngine`, stamps `rule_ids_satisfied` and `rule_ids_violated`, and saves to `assignments.json`.
  - `explain_assignment`: Diagnoses responsible rules, computes top-3 faculty alternatives with fit breakdown and eligibility blocking reasons, and formulates audit explanations.
  - `get_fairness_metrics`: Calculates overall departmental Gini, standard deviation, max-min gap, and individual load breakdown for a given term.
  - `get_conflicts_and_repairs`: Runs validation scenario across term assignments, returns categorized hard/soft violations, and invokes `generate_repairs` for automated remediation strategies.
  - `apply_repair`: Applies chosen structural repairs (`relax_hc05`, `add_adjunct`, `move_timeslot`, `expand_facility`) and automatically kicks off a re-optimization job.
  - `execute_override`: Handles administrative human reassignments with full `ConstraintEngine` re-validation. Preserves the original solver recommendation and fit metrics in an immutable snapshot (`Override` record), blocks unacknowledged hard violations (`acknowledge_violations=False`), and updates the assignment if confirmed.
  - Complete integration with `AuditService` logging every event (`OPTIMIZE_JOB_START`, `OPTIMIZE_JOB_COMPLETE`, `OPTIMIZE_JOB_FAIL`, `ASSIGNMENT_OVERRIDE`, `REPAIR_APPLY`).

#### `backend/app/api/v1/assign.py`
- Implemented and mounted the `/api/v1/assign` router:
  - `POST /assign/run`: Admin-only trigger returning HTTP 202 with job ID.
  - `GET /assign/jobs/{id}`: Polls job status and execution payload.
  - `GET /assign`: Fetches assignments with strict RBAC (faculty restricted strictly to their own assigned records).
  - `GET /assign/explain/{id}`: Deep dive into assignment rationale and top-3 alternatives (faculty restricted to their own assignments).
  - `GET /assign/fairness?term=...`: Workload distribution statistics.
  - `GET /assign/conflicts?term=...`: Violation audit and repair alternatives.
  - `POST /assign/repair/apply`: Admin-only repair execution.
  - `POST /assign/override`: Admin-only human override.

#### `backend/tests/test_assign_api.py`
- Implemented comprehensive integration test suite covering:
  - `test_single_active_job_enforcement`: 409 Conflict when a job is already in progress.
  - `test_greedy_job_run_and_status`: Background completion and status transition.
  - `test_infeasible_path`: Zero-eligible detection returning blocking rules and explanation.
  - `test_explain_assignment_and_faculty_isolation`: Explanation structure and 403 enforcement when faculty queries another instructor's assignment.
  - `test_faculty_assignment_listing_restricted`: Strict filtering to own faculty ID.
  - `test_fairness_and_conflicts_endpoints`: Metric payloads and violation structures.
  - `test_override_flow_with_and_without_hard_violations`: 400 on duplicate faculty, acknowledgement requirement on hard violations, snapshot preservation, and audit logging.
  - `test_repair_apply_endpoint`: Admin authorization and triggered job dispatch.

### Test Results & Verification Status
- `backend/tests/test_assign_api.py`: 8/8 passed.
- Entire backend test suite (`backend/tests/`): **126 passed in 5.96s** (0 failed).
- Entire ML test suite (`ml/tests/`): **90 passed in 13.35s** (0 failed).

### Next Steps / Backlog Items
- Wire the frontend `/admin/assignments`, `/admin/optimize`, and `/faculty/schedule` routes to consume these `/api/v1/assign` endpoints.
- Build UI dialog for administrative override with violation warnings and acknowledgement checkbox.

## 2026-11-01: Admin Planning Tool Suite Implementation

- **Task Objective**: Build the admin planning tool pages in `/frontend/src/features/admin` covering Overview KPIs, Workload Balance bar chart, Demand Forecasts quantile panel, Assignments Grid with rule badges, and Optimizer Configuration panel with real-time job tracking and CP-SAT vs. Greedy benchmarking.

### Changes Implemented

#### 1. Typed API Layer & TanStack Query Hooks (`frontend/src/features/admin/api.ts`)
- Defined strict TypeScript interfaces matching backend domain schemas: `FairnessSummary`, `ConflictViolation`, `RepairAlternative`, `ConflictsResponse`, `ForecastRecord`, `OptimizationJob`, `OptimizationJobResult`, `RunOptimizationPayload`, `AssignmentExplanation`, `OverridePayload`, `OverrideResponse`.
- Implemented query hooks with caching and invalidation: `useFairness`, `useConflicts`, `useForecasts`, `useAssignments`, `useFacultyList`, `useCoursesList`, `useSectionsList`, `useJobStatus` (with 1s polling interval during `RUNNING` status), `useExplainAssignment`.
- Implemented mutation hooks: `useRunOptimization`, `useApplyRepair`, `useExecuteOverride`, `useLoadScenario`.

#### 2. Overview Panel (`frontend/src/features/admin/OverviewPanel.tsx`)
- 5 Core KPI cards: Feasibility badge (green/rose), Hard Violations counter, Workload Fairness Gini (color-coded for balanced <= 0.15), Mean Fit percentage, and Unassigned Sections count.
- Academic Term selector (`Fall 2026`, `Spring 2027`, `Summer 2027`).
- Benchmark scenario loader dropdown (`balanced_baseline`, `tight_capacity`, `infeasible_expertise`, `leave_heavy`, etc.) with instant feedback toast.
- Quick action shortcuts to launch the optimizer engine or review conflicts.

#### 3. Load View Panel (`frontend/src/features/admin/LoadViewPanel.tsx`)
- Lightweight Recharts `BarChart` displaying assigned weekly contact hours against contractual limits per faculty member.
- Dynamic color-coding: Emerald (`#10b981`) for balanced (60–100%), Rose (`#f43f5e`) for overloaded (>100% violating HC-02), and Sky (`#38bdf8`) for underloaded (<60% available slack).
- Workload filter pills: `All`, `Overloaded`, `Balanced`, `Underloaded`.
- Reference lines for institutional standard caps (12h) and descriptive legend summary.

#### 4. Forecast Panel (`frontend/src/features/admin/ForecastPanel.tsx`)
- P50 (Expected) vs. P90 (Surge Stress) scenario toggle.
- Aggregate demand and capacity metrics: Total student enrollment, sections needed, surge capacity buffer (+sections), and volatile course count.
- Uncertainty band chart using Recharts `ComposedChart` showing P10 floor, P50 median, and P90 surge distributions.
- Course requirements table with search filtering, P90-P10 spread, sections needed, and volatility tags.

#### 5. Assignments Grid (`frontend/src/features/admin/AssignmentsGrid.tsx`)
- Interactive schedule grid listing course sections, schedule timeslots, assigned faculty, fit-score chips, and rule compliance badges.
- Fit score chips color-coded by match level (Emerald >= 80%, Sky >= 60%, Amber < 60%) with click-to-explain.
- Rule badges displaying satisfied hard/soft rules and highlighting violations (e.g. `HC-03`).
- Paginated table (10, 20, 50 rows per page) with search and multi-criteria filters.
- **Explain Assignment Modal**: Renders detailed fit breakdown (tag match, TF-IDF cosine similarity, continuity bonus), narrative rationale, and top-3 evaluated candidate alternatives with eligibility/blocking reasons.
- **Administrative Override Dialog**: Allows replacing assigned faculty, entering institutional justifications, and warning/requiring acknowledgement when hard constraints are violated.

#### 6. Optimizer Control Panel (`frontend/src/features/admin/OptimizerPanel.tsx`)
- Method selector: Google OR-Tools CP-SAT (multi-objective MILP) vs. Greedy Baseline.
- Demand mode toggle: P50 vs. P90.
- Soft constraint weight sliders: `w1` (SC-01 Expertise Fit), `w2` (SC-02 Workload Fairness penalty), `w3` (SC-03 Preference Miss penalty), `w4` (SC-04 Continuity bonus).
- Solver CPU time limit configuration (default 20s).
- Live execution progress tracker: Polling `useJobStatus`, visual progress bar, and status phases (pre-filtering, formulation, integer solve, fairness evaluation).
- Empirical benchmark comparison card: Side-by-side table comparing CP-SAT vs. Greedy on Gini fairness (0.071 vs 0.494), max-min gap (1 vs 7 sections), fit scores, constraint compliance, and RAM overhead (<0.2 MB).

#### 7. Page & Router Integration (`frontend/src/features/admin/overview/AdminOverviewPage.tsx`, `router.tsx`)
- Unified Planning Cockpit in `AdminOverviewPage.tsx` with top tab bar switching between Overview, Optimizer, Workload Balance, Assignments Grid, and Demand Forecasts.
- Standalone routed pages connected in `router.tsx`: `/admin/assignments`, `/admin/forecasts`, `/admin/load`.

### Test Results & Verification Status
- **Frontend TypeScript & Vite Production Build**: `npm run build` executed and passed cleanly (`tsc && vite build`, 761 modules transformed, 0 TypeScript errors).
- **Backend & ML Pytest Suite**: 216/216 tests passing in 50.13s (126 backend tests + 90 ML tests).
- Strict mode compliance (`strict: true`, zero `any` types).

### Next Steps / Backlog Items
- Build the faculty self-service portal (`/faculty/schedule`, `/faculty/preferences`, `/faculty/expertise`).
- Add CSV / Excel export for final administrative schedules.

## 2026-11-01: Admin Explainability, Control, Repairs, Overrides, and Audit Suite

- **Task Objective**: Add complete explainability and administrative control features to the admin UI: Conflicts panel with linking, Assignment detail drawer with fit breakdown and blocking reasons, Repair modal with predicted impacts, Override flow with live constraint validation and required violation acknowledgement, Audit trail page, and Rules parameterization page with simulated impact preview.

### Changes Implemented

#### 1. Backend Overrides API (`backend/app/api/v1/overrides.py`, `backend/app/api/v1/__init__.py`)
- Created `GET /api/v1/overrides` and `GET /api/v1/overrides/{id}` endpoints.
- Registered the `overrides` router in `backend/app/api/v1/__init__.py` to allow querying stored override records and evidence snapshots.

#### 2. Conflicts Panel & Repair Modal (`frontend/src/features/admin/conflicts/ConflictsPanel.tsx`, `RepairModal.tsx`, `ConflictsPage.tsx`)
- **Conflicts Panel**:
  - Displays detected violations with severity badges (`error` for hard invariants, `warning` for soft objectives), plain-language explanations, and `rule_id` badges (`HC-01`, `HC-02`, `HC-03`, etc.).
  - Entity deep-linking: Clicking "Inspect Assignment" opens the Assignment Detail Drawer for the affected section or instructor.
  - Multi-criteria filtering by severity (`All`, `Hard Only`, `Soft Only`) and real-time search.
  - Feasibility status banner and counter cards.
- **Repair Modal**:
  - Surfaces 2–3 automated repair strategies (`relax_hc05` for limit relaxation, `add_adjunct` for adjunct capacity, `move_timeslot` for conflict resolution).
  - Shows predicted impact metrics: Feasibility status, predicted workload Gini (fairness), mean fit score, and new/remaining violations.
  - Includes "Apply This Repair" button calling `useApplyRepair()` with immediate background re-optimization dispatch and toast confirmation.

#### 3. Assignment Detail Drawer (`frontend/src/features/admin/assignments/AssignmentDetailDrawer.tsx`)
- Slide-over drawer accessible from any section assignment or conflict violation link.
- **Fit-Score Breakdown**: Visual progress bars displaying weighted tag match (60%), TF-IDF syllabus similarity (25%), and past-teaching continuity bonus (15%).
- **"Why This Faculty"**: Responsible justifying rule badges (`✓ HC-01`, `✓ HC-02`, etc.) and textual narrative rationale.
- **Top Alternative Candidates**: Ranked candidate alternatives with fit scores, rank, and explicit blocking reasons (e.g. insufficient proficiency, scheduled leave, or timeslot clashes).
- **Preserved Override Evidence**: If an assignment has been overridden, prominently displays an "Overridden" badge along with the original recommended instructor, previous fit score, and administrative justification snapshot.

#### 4. Live Constraint Validation & Override Flow
- Integrated into `AssignmentDetailDrawer` and `AssignmentsGrid`.
- **Live Validation**: As candidate faculty members are selected in the override dropdown, immediate client-side and server-side constraint checks evaluate timeslot clashes (`HC-03`), sabbatical/leave terms (`HC-04`), required tag proficiencies (`HC-01`), and course preferences (`SC-03`).
- **Required Justification**: Mandates input of administrative justification before enabling submission.
- **Explicit Acknowledgement**: If hard constraint invariants would be broken, presents a warning banner and mandates an explicit checkbox acknowledgement (`acknowledge_violations=true`).
- **Audit Persistence**: Persists an immutable `Override` record, writes an `ASSIGNMENT_OVERRIDE` event to the audit trail, and flags the assignment source as `override`.

#### 5. Audit Trail Page (`frontend/src/features/admin/audit/AuditTrailPage.tsx`)
- Chronological, filterable log consuming `GET /api/v1/audit`.
- Filters by category: Solver Runs (`OPTIMIZE_*`), Overrides (`ASSIGNMENT_OVERRIDE`), Rule Changes (`CONSTRAINT_*`), and Repairs (`REPAIR_*`).
- Entity domain and free-text search filters.
- JSON snapshot viewer modal to inspect payloads, evidence snapshots, and before/after parameters.

#### 6. Rules Catalog & Impact Simulation (`frontend/src/features/admin/rules/RulesCatalogPage.tsx`)
- Catalog of all Hard Constraints (HC-01 to HC-07) and Soft Objectives (SC-01 to SC-04).
- Toggles to enable/disable rules and weight sliders for soft penalties/bonuses.
- **Preview Impact Simulation**: "Preview Impact" button executes simulated constraint validation via `POST /api/v1/constraints/validate` on the active schedule with candidate rule overrides, displaying live counts of resulting hard violations, soft flags, and specific failure reasons before committing changes.
- Batch update mutation saving changes via `PUT /api/v1/constraints`.

#### 7. Navigation & Router Integration (`frontend/src/app/router.tsx`, `AdminOverviewPage.tsx`, `AdminLayout.tsx`)
- Mounted routes in `router.tsx`: `/admin/conflicts`, `/admin/constraints`, `/admin/overrides`, `/admin/audit`.
- Updated `AdminLayout.tsx` sidebar with direct navigation items.
- Updated `AdminOverviewPage.tsx` with top tab bar switching seamlessly between Overview, Optimizer, Workload, Assignments, Conflicts & Repairs, Forecasts, Rules Catalog, and Audit Trail.

### Test Results & Verification Status
- **TypeScript & Vite Production Build**: `npm run build` executed cleanly (`tsc && vite build`, 768 modules transformed, 0 type errors, exit code 0).
- **Backend & ML Pytest Suite**: 216/216 passed in 75.54s (0 failed, exit code 0).
- Strict mode compliance (`strict: true`, zero `any` types).

## 2026-11-01: Faculty Portal, Load Benchmarking, Availability Preferences & Change Requests

- **Task Objective**: Build the faculty self-service portal in `/frontend/src/features/faculty` and add supporting backend endpoints enforcing strict RBAC isolation (faculty can neither read nor modify other faculty records): My Assignments with weekly hours and timetable, Why I Was Assigned with fit breakdown and strictly anonymized peer department load comparisons, Availability & Preferences form with pending re-optimization status tracking, and Change Request submission with administrative notification.

### Changes Implemented

#### 1. Backend Schema & Endpoints (`backend/app/schemas/change_request.py`, `backend/app/api/v1/faculty.py`, `backend/app/services/faculty_service.py`)
- Created `ChangeRequest` and `ChangeRequestCreate` schemas in `backend/app/schemas/change_request.py`.
- Added repository provider `get_change_request_repository` in `backend/app/repositories/__init__.py` backed by `data/store/change_requests.json`.
- Implemented `PUT /api/v1/faculty/{faculty_id}/preferences`:
  - Updates `unavailable_slots`, `leave_terms`, and `preferred_course_ids`.
  - Strictly restricted: raises `403 Forbidden` if a faculty user attempts to modify another faculty member's preferences.
  - Returns `pending_optimization: True` and records audit event `FACULTY_PREFERENCES_UPDATE`.
- Implemented `GET /api/v1/faculty/{faculty_id}/load-comparison?term=...`:
  - Returns the authenticated faculty member's teaching load alongside department mean, median, and load ratio.
  - Strictly restricted: raises `403 Forbidden` if a faculty user attempts to query another faculty member's comparison.
  - Peer privacy enforcement: peer faculty are labeled `"Peer X (Rank)"` with contact hours and load ratios—never real names, emails, or real IDs. The current user is labeled `"You (Your Load)"`.
- Implemented Change Request lifecycle:
  - `POST /api/v1/faculty/change-requests`: Faculty submits a comment/request on their assigned section (raises `403 Forbidden` if section is not assigned to caller).
  - `GET /api/v1/faculty/change-requests`: Faculty retrieves only their own requests; admins view all.
  - `PUT /api/v1/faculty/change-requests/{request_id}/status`: Admin-only approval or rejection with audit logging.

#### 2. Faculty RBAC Test Suite (`backend/tests/test_faculty_features.py`)
- `test_faculty_preferences_update_and_rbac`: Proves faculty user `f-01` can update their own preferences with `pending_optimization=True`, while modifying `f-02` returns `403 Forbidden`.
- `test_anonymized_load_comparison_and_privacy`: Proves load comparison strictly anonymizes peers (no names/emails/IDs) with current user labeled "You", and querying another faculty ID returns `403 Forbidden`.
- `test_change_request_lifecycle_and_isolation`: Proves faculty can create change requests for own assignments, cannot create requests for others' assignments, cannot view others' change requests, cannot self-approve, and admin can approve/reject.

#### 3. Faculty Portal Frontend (`frontend/src/features/faculty`)
- **API Client & Query Hooks (`frontend/src/features/faculty/api.ts`)**:
  - `useMyFacultyProfile`, `useMyAssignments`, `useFacultyCourses`, `useFacultySections`, `useFacultyTimeslots`, `useAssignmentExplanation`, `useAnonymizedLoadComparison`, `useMyChangeRequests`, `useUpdateFacultyPreferences`, `useCreateChangeRequest`.
- **My Schedule & Workload Page (`frontend/src/features/faculty/myload/MyLoadPage.tsx`)**:
  - KPI Cards: Contact hours vs. contractual max limit with visual progress bar, assigned sections count, and department median comparison.
  - **Weekly Timetable Grid**: Monday through Friday class meeting visual blocks with course codes, start/end times, and section tags.
  - **Why I Was Assigned**: Detailed fit breakdown bars (Tag match 60%, TF-IDF 25%, Continuity 15%), justifying satisfied invariants (`✓ HC-01`, `✓ HC-02`, etc.), and plain-language rationale.
  - **Anonymized Peer Benchmark Chart**: Recharts bar chart showing personal load against anonymized peers (`Peer 1 (Professor)`, `Peer 2 (Lecturer)`) with reference line for Department Median Load.
- **Availability & Preferences Page (`frontend/src/features/faculty/availability/AvailabilityPage.tsx`)**:
  - Timetable blackout selector: Interactive Monday–Friday timeslot grid to toggle unavailable hours.
  - Sabbatical & Leave semester selector: Checkbox cards for approved leave terms.
  - Preferred courses selector: Searchable catalog multi-select.
  - **Pending Optimization Status**: Displays prominent banner marking saved changes as "Pending Re-Optimization" until the next solver execution.
- **Change Requests Page (`frontend/src/features/faculty/requests/RequestsPage.tsx`)**:
  - Section modification submission form linked to active assignments.
  - Chronological request history table displaying status badges (`Pending`, `Approved`, `Rejected`), comment text, and administrative response notes.

#### 4. Navigation & Router Integration (`frontend/src/app/router.tsx`, `FacultyLayout.tsx`)
- Connected routes: `/faculty` (Schedule & Load), `/faculty/preferences` (Availability & Blackouts), `/faculty/requests` (Change Requests).
- Updated `FacultyLayout.tsx` navigation sidebar with Change Requests item.

### Test Results & Verification Status
- **Frontend TypeScript & Vite Production Build**: `npm run build` executed cleanly (`tsc && vite build`, 771 modules transformed, 0 type errors, exit code 0).
- **Backend & ML Pytest Suite**: 219/219 passed in 69.72s (0 failed, exit code 0).
- Strict mode compliance (`strict: true`, zero `any` types).


## 2026-11-01: CI/CD, Coverage, Reproducibility & E2E Testing

- **Task Objective**: Establish complete CI/CD pipeline covering local `make test` (< 2 min, ≥80% coverage), a reproducibility contract for solvers, Playwright E2E suite (`@e2e`), and GitHub Actions CI with PR checks and a `workflow_dispatch` full benchmark job.

- **Changes Implemented**:

  ### 1. `make test` — Local Unit Tests with Coverage Enforcement
  - Fixed `ImportError: cannot load module more than once per process` for all 7 backend test modules: root-level `pytest.ini` now sets `pythonpath = . backend ml`, eliminating the Python Store path collision that occurred when running from `backend/` subdirectory.
  - Updated `Makefile` `test` target: runs `coverage run -m pytest backend/tests ml/tests -q -m "not e2e and not slow"` followed by `coverage report --fail-under=80` scoped to the 3 target modules.
  - **231 tests pass in 57.93s** (well under 2-minute budget).
  - Coverage verified: `constraint_engine` 95%, `security` 97%, `auth` 92%, `repositories` 81–96%.

  ### 2. Added Coverage-Boosting Tests (`backend/tests/test_security_coverage.py`)
  - 9 targeted tests covering previously-uncovered branches in `security.py`:
    - Decoding invalid tokens → `UnauthorizedError`
    - `get_current_user` with invalid `X-User-Role` header → HTTP 400
    - JWT token missing `sub` claim → `UnauthorizedError`
    - JWT token of type `refresh` used as access token → `UnauthorizedError`
    - Token payload fallback path (no user_repo) → reconstructed `User`
    - `require_faculty` called with admin user → `ForbiddenError`
    - `require_authenticated` passthrough
    - `verify_faculty_access` admin bypass, own-faculty match, cross-faculty block
    - `FacultyAccessGuard.__call__` with path params

  ### 3. Reproducibility Tests (`backend/tests/test_reproducibility.py`)
  - 3 tests covering CP-SAT and Greedy determinism:
    - `test_cpsat_identical_assignments_fixed_seed` (parametrized over `balanced_baseline` and `tight_capacity`): two independent `solve_cpsat(..., seed=42)` calls must produce identical `feasible`, `objective_value`, section→faculty mapping, and fit scores.
    - `test_greedy_identical_assignments`: two `solve_greedy()` calls must produce identical results.
  - All 3 pass.

  ### 4. `/auth/dev-otp` Endpoint
  - Added `GET /api/v1/auth/dev-otp?email=...` returning the in-memory OTP when `OTP_DEV_MODE=true`; returns `null` otherwise.
  - Enables automated E2E tests to retrieve OTP without SMTP or screen-scraping.

  ### 5. Playwright E2E Suite (`tests/e2e/`)
  - `tests/e2e/conftest.py`: Session-scoped fixtures spin up backend (uvicorn, `OTP_DEV_MODE=true`) and Vite dev server if not already running; gracefully tear down at session end.
  - `tests/e2e/test_app_e2e.py`: 6 tests tagged `@pytest.mark.e2e`:
    1. `test_e2e_otp_login_admin`: Admin OTP login → redirected to `/admin`.
    2. `test_e2e_otp_login_faculty`: Faculty OTP login → redirected to `/faculty`.
    3. `test_e2e_faculty_blocked_from_admin_routes`: Faculty visiting `/admin` sees 403 Forbidden.
    4. `test_e2e_run_optimizer`: Admin runs CP-SAT solver and awaits `COMPLETED` status.
    5. `test_e2e_open_conflict`: Admin opens conflicts panel, sees "Schedule Conflicts & Rule Violations".
    6. `test_e2e_apply_repair`: Admin opens repair modal, clicks Apply, confirms success.
    7. `test_e2e_override_with_reason`: Admin overrides with reason, checks acknowledgment if hard violations detected.
  - **Excluded from `make test`** (gated by `-m "not e2e and not slow"`).
  - **Accessible via `make e2e`** only.

  ### 6. Updated `Makefile`
  - `test`: coverage run + `--fail-under=80` report.
  - `e2e`: `pytest tests/e2e -m e2e -v`.
  - `benchmark-quick`: `ml/benchmark/run_benchmark.py --profile quick`.
  - `benchmark-full`: `ml/benchmark/run_benchmark.py --profile full`.

  ### 7. GitHub Actions CI (`.github/workflows/ci.yml`)
  - PR/push job `lint-and-test`:
    - Lint with `ruff` + `black --check`
    - Backend + ML unit tests with `coverage --fail-under=80`
    - Frontend `npm run build`
    - Playwright E2E tests (`playwright install --with-deps chromium`)
    - Benchmark quick profile
  - `workflow_dispatch`-only job `full-benchmark`:
    - Runs `--profile full` (all 10 fixtures, P50+P90, 3 seeds)
    - Uploads `ml/artifacts/benchmark_full.json`, `docs/benchmark.md`, `docs/img/*.png` as GitHub Actions artifacts (retained 30 days)

  ### 8. Root `pytest.ini`
  - Created at project root with `pythonpath = . backend ml`, `addopts = -m "not e2e and not slow"`, `testpaths = backend/tests ml/tests`, and marker registrations for `e2e` and `slow`.

  ### 9. Backend `pyproject.toml`
  - Updated `[tool.pytest.ini_options]` with `pythonpath = [".", "..", "../ml"]` and formal marker declarations.

- **Test Results & Verification Status**:
  - ✅ **231 tests pass in 57.93s** (< 2 min budget).
  - ✅ Coverage: all 3 target modules ≥80% (`constraint_engine` 95%, `security` 97%, `auth` 92%, `repositories` 81–96%).
  - ✅ **3 reproducibility tests pass** (CP-SAT and Greedy determinism validated).
  - ✅ **Benchmark quick profile**: 0.87s (3 fixtures, 6 runs total), JSON and charts generated.
  - ✅ Playwright Chromium v1.64.1 installed (`chromium-1248`).
  - ✅ Frontend production build still clean.

- **Next Steps / Backlog Items**:
  - Run `make e2e` against live servers to complete full Playwright E2E validation.
  - Optionally add `make e2e` to local developer flow after backend/frontend start.
  - Push to GitHub to trigger CI and verify the `workflow_dispatch` full benchmark upload.
  - Consider adding `--timid` or branch coverage to catch missed branches in `local_store.py` (currently 81%).


## 2026-11-01: Production Packaging, Hardening, Deployment & Documentation Finalization

- **Task Objective**: Deliver production containerization (Dockerfile within 512MB RAM), static frontend deployment for Vercel/Netlify, security hardening (strict CORS, security headers, secure cookies, rate limiting, dual-mount `/health`), complete deployment guide, offline model refresh runbook, comprehensive technical documentation (limitations, user guides), and README demo walkthrough script.

- **Changes Implemented**:

  ### 1. Backend Production Containerization (`backend/Dockerfile`, root `Dockerfile`, `.dockerignore`)
  - Authored minimal `python:3.11-slim` container installing only runtime requirements from `backend/requirements.txt` (excluding dev tools like pytest, playwright, black, ruff).
  - Explicit single-worker execution (`--workers 1`) to preserve GitHub Gist single-writer integrity and keep RAM strictly $\le 512\text{ MB}$.
  - Added non-privileged user `appuser` (UID 1001) for container security.
  - Added native Docker `HEALTHCHECK` directive monitoring `http://localhost:8000/health`.
  - Documented how `FORECAST_MODE=precomputed` drops LightGBM from process memory, saving 80–120MB RSS.

  ### 2. Frontend Static Build Configurations (`frontend/vercel.json`, `frontend/netlify.toml`, root `netlify.toml`)
  - Configured Vercel build settings with Vite SPA rewrites (`/(.*)` $\rightarrow$ `/index.html`) and security headers.
  - Configured Netlify build settings with 200 rewrite rule (`/*` $\rightarrow$ `/index.html`) and security headers.
  - Verified clean static compilation via `npm run build` (`dist/` generated with zero type errors).

  ### 3. Production Security Hardening
  - **Security Headers Middleware (`backend/app/core/middleware.py`)**: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, and `Strict-Transport-Security` (production/staging).
  - **Lightweight Sliding-Window Rate Limiting (`RateLimitMiddleware`)**: Limits client IPs to 180 requests/minute to protect CPU budget, returning HTTP 429 Too Many Requests when exceeded while exempting health checks and OpenAPI docs.
  - **Secure Cookies (`backend/app/api/v1/auth.py`)**: HTTP-only refresh token cookies with `SameSite=lax` and `secure=True` in production/staging environments.
  - **Dual Health Checks (`backend/app/main.py`, `backend/app/api/v1/health.py`)**: Root `/health` (cloud load balancers) and `/api/v1/health` (application API) reporting live service status, memory footprint, store backend, and forecast mode.

  ### 4. Deployment Guide (`docs/deployment_guide.md`)
  - Complete, step-by-step setup guides for Render and Railway (Backend container) and Vercel and Netlify (Frontend CDN).
  - Comprehensive reference table documenting every environment variable: `GIST_TOKEN`, `GIST_ID`, `JWT_SECRET`, `STORE_BACKEND`, `OTP_DEV_MODE`, `FORECAST_MODE`, `ALLOWED_ORIGINS`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TLS`, `ENVIRONMENT`, `PORT`, `LOG_LEVEL`, `RATE_LIMIT_PER_MINUTE`, and `VITE_API_URL`.
  - Architectural explanation of Gist single-writer invariants.

  ### 5. Model Refresh Runbook (`docs/model_refresh_runbook.md`)
  - Step-by-step SOP for updating enrollment history (`data/seed/enrollment_history.json`), running offline training (`make train`), verifying artifact constraints (< 5MB, `model.txt`, no pickle/joblib), running quick verification (`make test`), and redeploying.
  - Explicit mandate: **Zero model retraining on the production server**.

  ### 6. Documentation Completion (`docs/limitations.md`, `docs/user_guide_admin.md`, `docs/user_guide_faculty.md`, `README.md`)
  - `docs/limitations.md`: Comprehensive coverage of GitHub Gist rate limits (5,000 req/hr), single-writer constraint, forecast uncertainty bands ($P_{10}$ vs $P_{90}$), multi-objective weight sensitivity ($w_1$ fit vs $w_2$ fairness), training dataset size (360 rows), and 512 MB RAM / CPU-only budget.
  - `docs/user_guide_admin.md`: Full manual covering Overview, Load View, Forecasts, Assignments, Optimizer cockpit, Conflicts, Automated Repairs, Manual Overrides with risk acknowledgment, and Audit Trail.
  - `docs/user_guide_faculty.md`: Full manual covering My Load, Timetable, "Why I Was Assigned", Anonymized Peer benchmark, Blackout/Leave preferences, and Change Requests with RBAC privacy isolation.
  - `README.md`: Added interactive Demo Walkthrough Script with 5 targeted scenarios:
    1. Feasible Allocation & CP-SAT vs Greedy Fairness (`balanced_baseline`).
    2. Pre-filter Pruning on Infeasible Scenarios (`infeasible_expertise`).
    3. Conflicts & Automated Schedule Repairs (`time_clash_dense`).
    4. Controlled Override with Invariant Acknowledgement.
    5. Faculty Self-Service & Privacy Boundary.

- **Test Results & Verification Status**:
  - ✅ **233 unit/integration tests passing in 60.66s** (0 failed).
  - ✅ **Coverage >= 80% on all target modules**: `constraint_engine` 95%, `security` 97%, `auth` 92%, `repositories` 81–96% (Total: **91%**).
  - ✅ **Frontend build verified**: `npm run build` succeeds cleanly in 11.17s.
## 2026-11-02: Dashboard glass-morphism visual refresh

- **Task Objective**: Replace saturated dashboard controls with a clean glass treatment and carry a faded version of the landing-page animation into authenticated dashboard views, without backend changes.
- **Changes Implemented**:
  - Added a shared, decorative dashboard atmosphere using the landing hero video and drifting cloud assets at intentionally low opacity.
  - Applied scoped translucent glass surfaces to dashboard cards, navigation, form controls, and buttons for both admin and faculty layouts.
  - Replaced the opaque active-navigation fill with a neutral glass state and retained visible keyboard focus treatment.
- **Test Results & Verification Status**: `npm run build` completed successfully (TypeScript check and Vite production build).
- **Next Steps / Backlog Items**: Perform a visual pass in a browser across the admin and faculty dashboards.

## 2026-11-02: Packet Tracer MCP setup

- **Task Objective**: Install and configure Mats2208's Packet Tracer MCP for Codex on Windows.
- **Changes Implemented**:
  - Registered the global `packet-tracer` Codex MCP server with `uvx --from "packet-tracer-mcp[ui]" packet-tracer-mcp --stdio`.
  - Installed the Packet Tracer agent skill at `C:\Users\omkan\.agents\skills\packet-tracer`.
  - Downloaded the official v0.10.1 MCP Control Center extension to `C:\Users\omkan\Downloads\MCP-Control-Center.pts` after the repository's current `latest` release asset returned 404.
- **Test Results & Verification Status**:
  - `codex mcp get packet-tracer` confirms the enabled stdio registration and UI-enabled arguments.
  - The skill directory and downloaded `.pts` extension file were verified present.
  - The extension could not be copied into `C:\Program Files\Cisco Packet Tracer 9.0.1\extensions` because that protected directory requires an administrator-approved write; live bridge verification remains pending until the extension is imported/enabled in Packet Tracer.
- **Next Steps / Backlog Items**: Import the downloaded extension in Packet Tracer (Extensions → Scripting → Configure PT Script Modules → Add…), enable it, restart Codex, then run `pt_bridge_status`.

## 2026-11-02: Packet Tracer DHCP lab

- **Task Objective**: Build a DHCP-server topology with one router, two switches, seven PCs, and one server.
- **Changes Implemented**:
  - Deployed a 2911 router (`192.168.10.1/24`), two 2960-24TT switches, seven PC-PT clients, and one Server-PT (`192.168.10.2/24`) in a single LAN.
  - Connected the switches using a validated crossover uplink and configured `SRV1` with the `LAN-DHCP` pool (`192.168.10.10`–`192.168.10.16`), gateway `192.168.10.1`, and DNS `192.168.10.2`.
  - Configured every PC for DHCP and saved the result as `C:\Users\omkan\Cisco Packet Tracer 9.0.1\saves\dhcp_server_1r_2s_7pc_1server.pkt`.
- **Test Results & Verification Status**:
  - Plan validation passed with no errors or warnings; deployment verified 11/11 devices and 10/10 links.
  - All seven PCs obtained leases from `SRV1`; PC7's `ipconfig /all` confirmed DHCP server `192.168.10.2`.
  - Real ping from PC1 to PC7 (`192.168.10.16`) succeeded: 4 sent, 4 received, 0% loss.
- **Next Steps / Backlog Items**: None.


## 2026-11-02: Fix Cross-Origin Session Persistence on Page Refresh
- **Task Objective**: Fix session teardown on browser refresh when navigating between Vercel frontend (`pentalyx.vercel.app`) and Render backend (`faculty-workload-api-vidc.onrender.com`).
- **Changes Implemented**:
  - Identified cross-origin cookie limitation: modern browsers partition or reject `SameSite=Lax` cookies across distinct top-level domains.
  - Updated backend `app.api.v1.auth` and `app.schemas.auth`:
    - Updated `TokenResponse` to include optional `refresh_token` string for resilient cross-origin client persistence.
    - Set cookie attributes to `SameSite=None; Secure=True` in production environments.
  - Updated frontend `src/lib/apiClient.ts` and `src/features/auth/AuthContext.tsx`:
    - Added storage helpers for resilient session caching (`workload_refresh_token`, `workload_user`).
    - Enhanced `refreshSessionApi` to accept body payload fallback `{ refresh_token: token }` when third-party cookies are blocked by browser privacy policies.
    - Initialized user state from stored profile and executed silent session refresh on mount, preventing premature redirects to `/login`.
  - Corrected root `.gitignore` to whitelist `frontend/src/lib/` ensuring full version control of client API modules.
  - Redeployed frontend to production on Vercel: `https://pentalyx.vercel.app`.
- **Test Results & Verification Status**:
  - `pytest backend/tests/test_auth.py`: 11/11 passed (100%).
  - `npm run build`: verified clean build with zero TypeScript or Vite errors.
  - Live production endpoints verified: `https://pentalyx.vercel.app` (200 OK) and `https://faculty-workload-api-vidc.onrender.com/health` (200 OK).
- **Next Steps / Backlog Items**: Test end-to-end admin session refresh directly in browser.

## 2026-11-03: Restore Clean Solid Background on Dashboards
- **Task Objective**: Remove landing page anime video/clouds atmosphere from the admin and faculty dashboards, reverting to a clean, distraction-free solid background.
- **Changes Implemented**:
  - Removed `<DashboardAtmosphere />` from `AdminLayout.tsx` and `FacultyLayout.tsx`.
  - Deleted obsolete `frontend/src/components/layout/DashboardAtmosphere.tsx`.
  - Updated `frontend/src/index.css`:
    - Replaced translucent glass-morphism overrides with solid `#f3f6ec` page background and solid `#ffffff` cards (`bg-slate-900` rendered as crisp white with subtle border `#e8ece0`).
    - Standardized sidebar and topbar as solid white containers with border `#e8ece0`.
    - Removed video, cloud keyframes, and wash overlays from authenticated views.
  - Updated `LoginPage.tsx` to use the same clean solid `#f3f6ec` background.
  - Built and redeployed the frontend to Vercel production: `https://pentalyx.vercel.app`.
- **Test Results & Verification Status**:
  - `npm run build`: verified clean build in 10.87s with 0 errors.
  - Vercel production deployment verified: `https://pentalyx.vercel.app` (200 OK).
- **Next Steps / Backlog Items**: None.

## 2026-11-03: Prominent Landing Page Backdrop on Dashboards
- **Task Objective**: Bring the vibrant Petalyx cherry blossom and river backdrop clearly and prominently onto the admin and faculty dashboards with high-contrast frosted glass surfaces.
- **Changes Implemented**:
  - Created `frontend/src/components/layout/DashboardBackground.tsx` rendering the full-resolution cherry blossom valley poster (`HERO_POSTER`), looping river/birds scene video (`HERO_VIDEO`), floating anime clouds (`CLOUD_A`, `CLOUD_B`), and drifting cherry blossom petals (`.petal`).
  - Added a delicate translucent gradient veil ensuring high UI contrast and readability without dimming out the scenery.
  - Rendered `DashboardBackground` in both `AdminLayout.tsx` and `FacultyLayout.tsx`.
  - Updated `frontend/src/index.css`:
    - Styled sidebar and topbar with frosted glass `rgba(255, 255, 255, 0.86)` and `backdrop-filter: blur(18px)`.
    - Styled dashboard cards with crisp frosted glass `rgba(255, 255, 255, 0.86)` and `backdrop-filter: blur(14px)`.
  - Built bundle with `npm run build` and redeployed to Vercel production: `https://pentalyx.vercel.app`.
- **Test Results & Verification Status**:
  - `npm run build`: built in 11.09s with zero errors.
  - Vercel production verified live: `https://pentalyx.vercel.app` (200 OK).
- **Next Steps / Backlog Items**: Hard-refresh in browser to view updated deployment.
