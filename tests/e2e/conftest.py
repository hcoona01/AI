"""Playwright E2E test configuration and background server fixtures."""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator
import urllib.request
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def is_server_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            return resp.status in (200, 304, 404)
    except Exception:
        return False


@pytest.fixture(scope="session")
def backend_server() -> Generator[str, None, None]:
    """Ensure backend server is running on http://127.0.0.1:8000."""
    health_url = "http://127.0.0.1:8000/api/v1/health"
    proc = None

    if not is_server_ready(health_url):
        env = os.environ.copy()
        env["PYTHONPATH"] = f".;{REPO_ROOT / 'backend'};{REPO_ROOT / 'ml'}"
        env["OTP_DEV_MODE"] = "true"
        env["STORE_BACKEND"] = "local"
        env["ENVIRONMENT"] = "development"

        python_exe = sys.executable
        cmd = [
            python_exe,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Poll until up
        start = time.time()
        ready = False
        while time.time() - start < 20:
            if is_server_ready(health_url):
                ready = True
                break
            time.sleep(0.5)

        if not ready:
            if proc:
                proc.terminate()
            raise RuntimeError("Backend server failed to start within 20s")

    yield "http://127.0.0.1:8000"

    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


@pytest.fixture(scope="session")
def frontend_server(backend_server: str) -> Generator[str, None, None]:
    """Ensure frontend Vite dev server is running on http://127.0.0.1:5173."""
    front_url = "http://127.0.0.1:5173"
    proc = None

    if not is_server_ready(front_url):
        cmd = "npm run dev -- --host 127.0.0.1 --port 5173"
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT / "frontend"),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        start = time.time()
        ready = False
        while time.time() - start < 30:
            if is_server_ready(front_url):
                ready = True
                break
            time.sleep(0.5)

        if not ready:
            if proc:
                proc.terminate()
            raise RuntimeError("Frontend dev server failed to start within 30s")

    yield front_url

    if proc:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


@pytest.fixture
def app_url(frontend_server: str) -> str:
    return frontend_server

