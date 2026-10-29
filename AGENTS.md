# Agent & Workspace Rules (`AGENTS.md`)

These operating guidelines are mandatory for all AI agents, engineers, and automated tasks operating in this workspace.

---

## 1. Mandatory Starting & Scoping Rules

1. **Required Context Ingestion**:
   - Always read [`AGENTS.md`](file:///e:/AI%20project/AGENTS.md) and [`docs/PROJECT_BRIEF.md`](file:///e:/AI%20project/docs/PROJECT_BRIEF.md) before starting any task.
2. **Strict Scope Discipline**:
   - Do **NOT** start work outside the explicit scope of the current prompt.
   - Do not generate speculative or unprompted boilerplate across unrelated subsystems.

---

## 2. Architectural & Code Quality Standards

### 2.1 Backend (FastAPI + Python 3.11)
- **Strict Layering**: Follow `api (routers) -> services -> repositories`.
  - **Routers**: Pure HTTP translation, parameter validation, status codes, dependency injection. Zero business logic.
  - **Services**: Business logic, workflow orchestration, optimization triggering, fairness calculations.
  - **Repositories**: Direct data access, GitHub Gist API operations, schema persistence.
- **Type Safety**: Explicit type hints across all functions, arguments, and return values. Pydantic v2 models for DTOs and domain entities.
- **Code Style & Linting**: Formatted with `black`, linted with `ruff`.
- **Testing**: Comprehensive tests written with `pytest`. Mock Gist calls and external network interactions in unit/service tests.

### 2.2 Frontend (React + TypeScript + Vite)
- **Structure**: Feature-based directory organization (e.g., `src/features/assignments`, `src/features/forecasts`, `src/features/faculty`).
- **Server State**: TanStack Query (React Query) for all API fetching, caching, and mutations.
- **Navigation & Routing**: React Router.
- **Validation**: Zod schemas for all forms, client-side input validations, and API contract parsing.
- **TypeScript Strictness**: Strict mode enabled (`strict: true`). Absolute ban on the `any` type—use unknown, generics, or precise union types.
- **Accessibility & Design**: Accessible semantic HTML elements (`aria-*` where appropriate, keyboard navigation), responsive layouts, modern design tokens, and no generic placeholders.

### 2.3 Security & Secret Management
- **Zero Secret Exposure**: Never commit secrets, GitHub Personal Access Tokens (PAT), or private keys to version control.
- **Environment Documentation**: Keep [`/.env.example`](file:///e:/AI%20project/.env.example) continuously updated with all required configuration keys and non-sensitive defaults.

---

## 3. Compute Budget Rules (No GPU & Strict RAM Budget)

The host system operates with **NO GPU** and strictly limited RAM. All code and workflows must comply with these constraints:

1. **CPU-Only Dependencies**:
   - Absolutely no GPU frameworks (no `torch`, `tensorflow`, `jax`, `cuda`).
   - Use only lightweight, CPU-efficient libraries (`scikit-learn`, `lightgbm`, `ortools`, `numpy`, `pandas`).
2. **Strict Training vs. Inference Decoupling**:
   - The backend server **NEVER** trains models.
   - Model training is exclusively performed offline via the local script `make train` (`python ml/scripts/train.py`).
   - The backend server only loads precomputed, small artifacts at startup or on demand.
3. **Portable, Safe Model Serialization**:
   - LightGBM models must be saved in the native text format (`booster.save_model("model.txt")`).
   - Metadata, metrics, feature mappings, and configs must be serialized as human-readable `.json`.
   - **Never** use `pickle` or `joblib` for model persistence.
4. **Artifact Size Limit**:
   - All artifacts committed to `/ml/artifacts` must remain strictly `< 5 MB` per file.
5. **Memory-Efficient Data Structures**:
   - Optimize pandas/numpy dtypes: downcast floats to `float32`, integers to `int32`/`int16`, and strings to `category`.
   - No deep learning, large embedding models, or transformer architectures.
6. **Constrained LightGBM Hyperparameters**:
   - `n_jobs=1`
   - `num_leaves <= 15`
   - `n_estimators <= 300`
   - Fixed `random_state` for deterministic, reproducible behavior.
7. **Constrained Google OR-Tools CP-SAT Settings**:
   - `num_workers=1`
   - Configurable time limit (default: 20 seconds for local runs).
   - Instantiate decision variables **ONLY** for valid, eligible faculty-section pairs (prune invalid combinations before variable creation).
8. **Test Execution & Local Overhead**:
   - Heavy test suites (Playwright end-to-end tests, exhaustive optimization benchmarks) run exclusively in GitHub Actions CI, never during default local runs.
   - Local `make test` must run with the quick profile and finish in **under 2 minutes**.
9. **Backend Memory Footprint**:
   - The entire backend application process must comfortably run within a **512 MB RAM** budget.

---

## 4. Task Completion Protocol

Every development task must conclude with:
1. **Tests Verified**: Relevant unit and integration tests run and passing cleanly.
2. **Concise Change Summary**: A clear explanation of modifications made and rationale.
3. **Documentation Log**: An entry appended to [`/docs/progress.md`](file:///e:/AI%20project/docs/progress.md) recording:
   - Date and task objective.
   - Changes implemented.
   - Test results and verification status.
   - Next steps / backlog items.
