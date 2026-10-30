"""Local filesystem persistence store for offline development and testing.

Provides identical interface to GistStore with:
- Atomic JSON file writes
- Per-file async concurrency locks
- Optimistic concurrency control (file mtime / content hash versioning)
- In-memory TTL cache
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.errors import ConflictError
from app.repositories.base import BaseStore

logger = logging.getLogger("app.repositories.local")

MANAGED_FILES = [
    "users.json",
    "faculty.json",
    "courses.json",
    "sections.json",
    "resources.json",
    "timeslots.json",
    "constraints.json",
    "forecasts.json",
    "assignments.json",
    "overrides.json",
    "audit_log.json",
]


class LocalStore(BaseStore):
    """File-system JSON persistence store matching the GitHub Gist store interface."""

    def __init__(
        self,
        base_dir: Path | str | None = None,
        seed_fallback_dir: Path | str | None = None,
        ttl_seconds: float = 2.0,
    ) -> None:
        if base_dir is None:
            self.base_dir = Path(settings.LOCAL_DATA_DIR).resolve()
        else:
            self.base_dir = Path(base_dir).resolve()

        self.seed_fallback_dir = (
            Path(seed_fallback_dir).resolve() if seed_fallback_dir is not None else None
        )
        self.ttl_seconds = ttl_seconds

        self._locks: dict[str, asyncio.Lock] = {}
        self._cache: dict[str, tuple[str, str, float]] = (
            {}
        )  # filename -> (content, version, timestamp)

        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_files()

    def _get_lock(self, filename: str) -> asyncio.Lock:
        """Retrieve or create an async lock for a specific file."""
        if filename not in self._locks:
            self._locks[filename] = asyncio.Lock()
        return self._locks[filename]

    def _ensure_files(self) -> None:
        """Seed any missing managed files from seed_fallback_dir or initialize with empty JSON."""
        for filename in MANAGED_FILES:
            target_path = self.base_dir / filename
            if not target_path.exists():
                if self.seed_fallback_dir:
                    fallback_path = self.seed_fallback_dir / filename
                    if fallback_path.exists():
                        try:
                            content = fallback_path.read_text(encoding="utf-8")
                            target_path.write_text(content, encoding="utf-8")
                            continue
                        except (OSError, UnicodeDecodeError) as exc:
                            logger.warning(
                                f"Could not copy seed file {filename}: {exc}"
                            )
                # Default initialize to empty array
                target_path.write_text("[]\n", encoding="utf-8")

    def _compute_version(self, content: str, mtime_ns: int) -> str:
        """Generate a deterministic version token from modification time and content digest."""
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        return f"{mtime_ns}_{digest}"

    async def read_file(
        self, filename: str, force_refresh: bool = False
    ) -> tuple[str, str | None]:
        """Read content and version token, leveraging TTL cache where applicable."""
        now = time.monotonic()
        if not force_refresh and filename in self._cache:
            content, version, cached_at = self._cache[filename]
            if (now - cached_at) < self.ttl_seconds:
                return content, version

        file_path = self.base_dir / filename
        if not file_path.exists():
            self._ensure_files()

        if not file_path.exists():
            # If still missing, return empty collection
            return "[]", None

        # Synchronous file read in threadpool if necessary, but fast enough for local JSON
        content = file_path.read_text(encoding="utf-8")
        stat = file_path.stat()
        version = self._compute_version(content, stat.st_mtime_ns)

        self._cache[filename] = (content, version, now)
        return content, version

    async def write_file(
        self, filename: str, content: str, expected_version: str | None = None
    ) -> str:
        """Atomically persist content to disk with optimistic concurrency verification."""
        lock = self._get_lock(filename)
        async with lock:
            file_path = self.base_dir / filename
            if file_path.exists():
                current_raw = file_path.read_text(encoding="utf-8")
                current_stat = file_path.stat()
                current_version = self._compute_version(
                    current_raw, current_stat.st_mtime_ns
                )

                if expected_version is not None and current_version != expected_version:
                    logger.warning(
                        f"Concurrency mismatch on {filename}: expected {expected_version}, found {current_version}"
                    )
                    raise ConflictError(
                        message=f"Optimistic concurrency violation on file '{filename}'. The file was modified by another operation.",
                        rule_id="CONCURRENCY_CONFLICT_409",
                    )

            # Atomic write via temp file
            temp_path = file_path.with_suffix(f".tmp_{time.time_ns()}")
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(file_path)

            new_stat = file_path.stat()
            new_version = self._compute_version(content, new_stat.st_mtime_ns)

            # Invalidate cache
            self._cache[filename] = (content, new_version, time.monotonic())
            return new_version

    async def get_file_metadata(self, filename: str) -> dict[str, Any]:
        """Retrieve diagnostic filesystem metadata."""
        file_path = self.base_dir / filename
        if not file_path.exists():
            return {"filename": filename, "exists": False}

        stat = file_path.stat()
        mtime_dt = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
        return {
            "filename": filename,
            "exists": True,
            "size": stat.st_size,
            "updated_at": mtime_dt.isoformat(),
            "mtime_ns": stat.st_mtime_ns,
        }
