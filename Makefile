# Makefile: Development, Testing, Linting, Training, and Benchmarking
# Enforces CPU-only budget and lightweight memory footprint (<512MB RAM)

ifeq ($(OS),Windows_NT)
    VENV_BIN := .venv/Scripts
    PYTHON := $(if $(wildcard $(VENV_BIN)/python.exe),$(VENV_BIN)/python.exe,python)
    PYTEST := $(if $(wildcard $(VENV_BIN)/pytest.exe),$(VENV_BIN)/pytest.exe,pytest)
    RUFF := $(if $(wildcard $(VENV_BIN)/ruff.exe),$(VENV_BIN)/ruff.exe,ruff)
    BLACK := $(if $(wildcard $(VENV_BIN)/black.exe),$(VENV_BIN)/black.exe,black)
    UVICORN := $(if $(wildcard $(VENV_BIN)/uvicorn.exe),$(VENV_BIN)/uvicorn.exe,uvicorn)
    SET_ENV := set PYTHONPATH=.:backend:ml&&
else
    VENV_BIN := .venv/bin
    PYTHON := $(if $(wildcard $(VENV_BIN)/python),$(VENV_BIN)/python,python)
    PYTEST := $(if $(wildcard $(VENV_BIN)/pytest),$(VENV_BIN)/pytest,pytest)
    RUFF := $(if $(wildcard $(VENV_BIN)/ruff),$(VENV_BIN)/ruff,ruff)
    BLACK := $(if $(wildcard $(VENV_BIN)/black),$(VENV_BIN)/black,black)
    UVICORN := $(if $(wildcard $(VENV_BIN)/uvicorn),$(VENV_BIN)/uvicorn,uvicorn)
    SET_ENV := PYTHONPATH=.:backend:ml
endif

.PHONY: help install-backend install-ml install-frontend dev-backend dev-frontend lint test train benchmark-quick sync-gist e2e

help:
	@echo "Available commands:"
	@echo "  dev-backend      Run FastAPI server locally on port 8000"
	@echo "  dev-frontend     Run Vite dev server on port 5173"
	@echo "  test             Run quick unit tests (<2 min, CPU-only)"
	@echo "  lint             Run ruff and black code checks"
	@echo "  train            Run offline ML model training (ml/scripts/train.py)"
	@echo "  benchmark-quick  Run quick CP-SAT vs greedy benchmark"
	@echo "  sync-gist        Sync local database to GitHub Gist & verify live"
	@echo "  e2e              Run frontend e2e integration tests (optional)"
	@echo "  install-backend  Install runtime backend dependencies"
	@echo "  install-ml       Install offline ML training dependencies"
	@echo "  install-frontend Install frontend dependencies"

install-backend:
	$(PYTHON) -m pip install -r backend/requirements.txt
	$(PYTHON) -m pip install -e ml

install-ml:
	$(PYTHON) -m pip install -r ml/requirements-train.txt

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && $(SET_ENV) $(UVICORN) app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

lint:
	$(RUFF) check backend ml || true
	$(BLACK) --check backend ml || true

test:
	$(SET_ENV) $(PYTHON) -m coverage run -m pytest backend/tests ml/tests -q -m "not e2e and not slow"
	$(PYTHON) -m coverage report --include="backend/app/services/constraint_engine.py,backend/app/repositories/*,backend/app/api/v1/auth.py,backend/app/core/security.py" --fail-under=80

train:
	$(SET_ENV) $(PYTHON) ml/scripts/train.py

benchmark-quick:
	$(SET_ENV) $(PYTHON) ml/benchmark/run_benchmark.py --profile quick

benchmark-full:
	$(SET_ENV) $(PYTHON) ml/benchmark/run_benchmark.py --profile full

sync-gist:
	$(SET_ENV) $(PYTHON) scripts/sync_to_gist.py

e2e:
	$(SET_ENV) $(PYTEST) tests/e2e -m e2e -v
