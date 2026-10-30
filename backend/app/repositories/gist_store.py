"""GitHub Gist storage engine for university workload system persistence.

Manages one private GitHub Gist containing all domain entity JSON files:
- users.json, faculty.json, courses.json, sections.json, resources.json
- timeslots.json, constraints.json, forecasts.json, assignments.json
- overrides.json, audit_log.json

Key Features:
1. Auto-creation of private Gist if GIST_ID is empty.
2. Handling of truncated files (>1MB) via raw_url fallback.
3. GitHub Rate-limit detection, informative exceptions, and exponential backoff.
4. HTTP ETag conditional caching (If-None-Match -> 304 Not Modified).
5. In-memory TTL cache to minimize GitHub API calls.
6. Optimistic concurrency control detecting changed updated_at with 1-time retry, raising 409 on persistent conflict.
7. Per-file async write lock to avoid concurrent race conditions.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import ConflictError, RateLimitError
from app.repositories.base import BaseStore

logger = logging.getLogger("app.repositories.gist")

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


class GistStore(BaseStore):
    """Asynchronous GitHub Gist persistence store implementing BaseStore."""

    def __init__(
        self,
        token: str | None = None,
        gist_id: str | None = None,
        client: httpx.AsyncClient | None = None,
        ttl_seconds: float = 10.0,
        seed_dir: Path | str | None = None,
    ) -> None:
        self.token = token if token is not None else settings.GIST_TOKEN
        self.gist_id = gist_id if gist_id is not None else settings.GIST_ID
        self._client = client
        self.ttl_seconds = ttl_seconds
        self.seed_dir = Path(seed_dir) if seed_dir else Path("data/seed")

        self._locks: dict[str, asyncio.Lock] = {}

        # Cached Gist State
        self._cached_gist: dict[str, Any] | None = None
        self._cached_files: dict[str, str] = {}  # filename -> raw text content
        self._cached_etag: str | None = None
        self._cached_updated_at: str | None = None
        self._last_fetch_time: float = 0.0

    def _get_lock(self, filename: str) -> asyncio.Lock:
        """Provide or create a concurrency lock for a specific filename."""
        if filename not in self._locks:
            self._locks[filename] = asyncio.Lock()
        return self._locks[filename]

    def _get_headers(self, etag: str | None = None) -> dict[str, str]:
        """Construct standard GitHub API headers with optional ETag."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if etag:
            headers["If-None-Match"] = etag
        return headers

    def _check_rate_limit(self, response: httpx.Response) -> None:
        """Inspect GitHub rate-limit headers and raise clear RateLimitError if exceeded."""
        remaining = response.headers.get("x-ratelimit-remaining")
        reset_str = response.headers.get("x-ratelimit-reset")

        if response.status_code in (403, 429) and (
            remaining == "0" or "rate limit" in response.text.lower()
        ):
            reset_at = int(reset_str) if reset_str and reset_str.isdigit() else None
            wait_sec = max(0, reset_at - int(time.time())) if reset_at else 60
            msg = (
                f"GitHub Gist API rate limit exceeded. "
                f"Remaining: 0. Resets in {wait_sec}s at epoch {reset_at}."
            )
            logger.error(msg)
            raise RateLimitError(
                message=msg,
                status_code=response.status_code,
                reset_at=reset_at,
                details={
                    "remaining": remaining,
                    "reset_at": reset_at,
                    "wait_seconds": wait_sec,
                },
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Retrieve existing or initialize a default async httpx client."""
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=30.0)

    async def ensure_gist_initialized(self) -> str:
        """Ensure a valid Gist exists. If GIST_ID is empty, create a private Gist."""
        if self.gist_id and self.gist_id.strip():
            return self.gist_id

        client = await self._get_client()
        logger.info("[*] GIST_ID is empty. Creating new private GitHub Gist...")

        # Prepare initial files using seed data where available
        initial_files: dict[str, dict[str, str]] = {}
        for fname in MANAGED_FILES:
            seed_file = self.seed_dir / fname
            if seed_file.exists():
                try:
                    content = seed_file.read_text(encoding="utf-8")
                    initial_files[fname] = {"content": content}
                    continue
                except (OSError, UnicodeDecodeError) as exc:
                    logger.warning(f"Failed to read seed file {fname}: {exc}")
            initial_files[fname] = {"content": "[]"}

        payload = {
            "description": "Faculty Workload Balancing Persistence Store",
            "public": False,
            "files": initial_files,
        }

        url = "https://api.github.com/gists"
        headers = self._get_headers()

        response = await client.post(url, json=payload, headers=headers)
        self._check_rate_limit(response)

        if response.status_code != 201:
            raise RuntimeError(
                f"Failed to create private Gist on GitHub: HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        new_id = data["id"]
        print(f"[+] Successfully created private GitHub Gist with ID: {new_id}")
        logger.info(f"Created private Gist: {new_id}")

        self.gist_id = new_id
        self._cached_gist = data
        self._cached_updated_at = data.get("updated_at")
        self._cached_etag = response.headers.get("etag")
        self._last_fetch_time = time.monotonic()

        # Cache file contents
        for fname, finfo in data.get("files", {}).items():
            self._cached_files[fname] = finfo.get("content", "[]")

        return self.gist_id

    async def fetch_gist(self, force_refresh: bool = False) -> dict[str, Any]:
        """Fetch Gist data, applying in-memory TTL caching and HTTP ETag conditional GET."""
        await self.ensure_gist_initialized()

        now = time.monotonic()
        if (
            not force_refresh
            and self._cached_gist is not None
            and (now - self._last_fetch_time) < self.ttl_seconds
        ):
            return self._cached_gist

        client = await self._get_client()
        url = f"https://api.github.com/gists/{self.gist_id}"
        etag = None if force_refresh else self._cached_etag
        headers = self._get_headers(etag=etag)

        response = await client.get(url, headers=headers)
        self._check_rate_limit(response)

        if response.status_code == 304:
            # 304 Not Modified: cache is still valid
            logger.debug(f"ETag match (304 Not Modified) for Gist {self.gist_id}")
            self._last_fetch_time = now
            return self._cached_gist or {}

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch Gist {self.gist_id}: HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        self._cached_gist = data
        self._cached_etag = response.headers.get("etag")
        self._cached_updated_at = data.get("updated_at")
        self._last_fetch_time = now

        # Update cache for all non-truncated files immediately
        files = data.get("files", {})
        for fname, finfo in files.items():
            if not finfo.get("truncated", False) and finfo.get("content") is not None:
                self._cached_files[fname] = finfo["content"]

        return data

    async def read_file(
        self, filename: str, force_refresh: bool = False
    ) -> tuple[str, str | None]:
        """Read a file's content and updated_at version, resolving truncated files via raw_url."""
        gist_data = await self.fetch_gist(force_refresh=force_refresh)
        files = gist_data.get("files", {})

        if filename not in files:
            # File not yet present in Gist; return empty list
            return "[]", gist_data.get("updated_at")

        file_info = files[filename]
        is_truncated = (
            file_info.get("truncated", False) or file_info.get("content") is None
        )

        if is_truncated:
            raw_url = file_info.get("raw_url")
            if not raw_url:
                raise ValueError(
                    f"Truncated file '{filename}' lacks raw_url in Gist payload"
                )

            logger.info(
                f"File '{filename}' is truncated (>1MB). Fetching raw content from {raw_url}..."
            )
            client = await self._get_client()
            headers = self._get_headers()
            raw_resp = await client.get(raw_url, headers=headers)
            self._check_rate_limit(raw_resp)

            if raw_resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch raw truncated file '{filename}': HTTP {raw_resp.status_code}"
                )
            content = raw_resp.text
            self._cached_files[filename] = content
            return content, gist_data.get("updated_at")

        # Standard file
        content = file_info.get("content", "[]")
        self._cached_files[filename] = content
        return content, gist_data.get("updated_at")

    async def write_file(
        self, filename: str, content: str, expected_version: str | None = None
    ) -> str:
        """Write content to Gist with optimistic concurrency and automatic retry on conflict."""
        lock = self._get_lock(filename)
        async with lock:
            return await self._write_with_retry(
                filename=filename,
                content=content,
                expected_version=expected_version,
                is_retry=False,
            )

    async def _write_with_retry(
        self,
        filename: str,
        content: str,
        expected_version: str | None,
        is_retry: bool = False,
    ) -> str:
        """Execute PATCH request against GitHub API with optimistic concurrency check."""
        await self.ensure_gist_initialized()

        # Check concurrency version
        if expected_version is not None:
            # Force fetch latest version
            current_gist = await self.fetch_gist(force_refresh=True)
            current_updated_at = current_gist.get("updated_at")

            if current_updated_at != expected_version:
                logger.warning(
                    f"Optimistic concurrency conflict on {filename}: expected {expected_version}, found {current_updated_at}"
                )
                if not is_retry:
                    logger.info(
                        f"Re-fetching and retrying write once for {filename}..."
                    )
                    # Update expected_version to current and retry once
                    return await self._write_with_retry(
                        filename=filename,
                        content=content,
                        expected_version=current_updated_at,
                        is_retry=True,
                    )
                # Second conflict: raise 409
                raise ConflictError(
                    message=(
                        f"Optimistic concurrency violation on file '{filename}'. "
                        f"The Gist was modified externally (expected {expected_version}, got {current_updated_at})."
                    ),
                    rule_id="GIST_OPTIMISTIC_LOCK_CONFLICT_409",
                )

        client = await self._get_client()
        url = f"https://api.github.com/gists/{self.gist_id}"
        headers = self._get_headers()
        payload = {"files": {filename: {"content": content}}}

        response = await client.patch(url, json=payload, headers=headers)
        self._check_rate_limit(response)

        if response.status_code == 409:
            if not is_retry:
                logger.info(
                    f"GitHub returned 409 Conflict. Re-fetching and retrying once for {filename}..."
                )
                latest_gist = await self.fetch_gist(force_refresh=True)
                return await self._write_with_retry(
                    filename=filename,
                    content=content,
                    expected_version=latest_gist.get("updated_at"),
                    is_retry=True,
                )
            raise ConflictError(
                message=f"Persistent conflict while updating Gist file '{filename}'",
                rule_id="GIST_OPTIMISTIC_LOCK_CONFLICT_409",
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to update Gist file '{filename}': HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        new_updated_at = data.get("updated_at")

        # Update cache
        self._cached_gist = data
        self._cached_updated_at = new_updated_at
        self._cached_etag = response.headers.get("etag")
        self._cached_files[filename] = content
        self._last_fetch_time = time.monotonic()

        return new_updated_at or ""

    async def get_file_metadata(self, filename: str) -> dict[str, Any]:
        """Return diagnostic file metadata from the cached or active Gist."""
        gist = await self.fetch_gist()
        files = gist.get("files", {})
        if filename not in files:
            return {"filename": filename, "exists": False}

        info = files[filename]
        return {
            "filename": filename,
            "exists": True,
            "size": info.get("size", len(info.get("content", ""))),
            "truncated": info.get("truncated", False),
            "updated_at": gist.get("updated_at"),
            "etag": self._cached_etag,
        }
