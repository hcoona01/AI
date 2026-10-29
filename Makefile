# Makefile: Commands for dev, test, lint, train, benchmark, and e2e
# ML Package Import Strategy:
# Option 1 (Editable install): pip install -e ml
# Option 2 (PYTHONPATH): export PYTHONPATH=.:ml backend/app

PYTHON ?= python

.PHONY: help install-backend install-ml install-frontend dev-backend dev-frontend lint test train benchmark-quick e2e

help:
	@echo "Available commands:"
	@echo "  install-backend  Install backend dependencies"
	@echo "  install-ml       Install ML offline training dependencies"
	@echo "  install-frontend Install frontend dependencies"
	@echo "  dev-backend      Run FastAPI server locally"
	@echo "  dev-frontend     Run Vite dev server"
	@echo "  lint             Run ruff and black linting"
	@echo "  test             Run quick unit and integration tests (<2min)"
	@echo "  train            Run offline ML model training (ml/scripts/train.py)"
	@echo "  benchmark-quick  Run quick optimization benchmark"
	@echo "  e2e              Run frontend e2e tests (deferred to CI)"

install-backend:
	cd backend && pip install -r requirements.txt && pip install -e ../ml

install-ml:
	pip install -r ml/requirements-train.txt

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && PYTHONPATH=..:app uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

lint:
	ruff check backend ml
	black --check backend ml

test:
	PYTHONPATH=.:backend:ml pytest backend/tests ml/tests -q -m "not slow"

train:
	PYTHONPATH=. python ml/scripts/train.py

benchmark-quick:
	PYTHONPATH=. python ml/benchmark/run_benchmark.py --quick

e2e:
	cd frontend && npm run test:e2e
