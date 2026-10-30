"""Abstract base storage interfaces and generic repository for domain models.

Provides:
- BaseStore: Abstract contract for persistence engines (GitHub Gist, local disk).
- Repository[T]: Generic CRUD and bulk-replacement abstraction with typed deserialization.
"""

from __future__ import annotations

import abc
import asyncio
import json
import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

logger = logging.getLogger("app.repositories")

T = TypeVar("T")


class BaseStore(abc.ABC):
    """Abstract interface defining required storage operations."""

    @abc.abstractmethod
    async def read_file(
        self, filename: str, force_refresh: bool = False
    ) -> tuple[str, str | None]:
        """Read content and version identifier (e.g., ETag or updated_at) of a file.

        Returns:
            Tuple of (raw_text_content, version_token).
        """

    @abc.abstractmethod
    async def write_file(
        self, filename: str, content: str, expected_version: str | None = None
    ) -> str:
        """Persist content to a file with optimistic concurrency validation.

        Args:
            filename: Target file name (e.g., 'faculty.json').
            content: Raw serialized content.
            expected_version: Current version token. If changed externally, detects conflict.

        Returns:
            Updated version token after write.
        """

    @abc.abstractmethod
    async def get_file_metadata(self, filename: str) -> dict[str, Any]:
        """Return diagnostic metadata for a target file (size, updated_at, etag)."""


class Repository(Generic[T]):
    """Generic async repository providing CRUD and bulk operations over JSON-backed entities."""

    def __init__(
        self,
        store: BaseStore,
        filename: str,
        model_cls: type[T],
        id_field: str = "id",
    ) -> None:
        self.store = store
        self.filename = filename
        self.model_cls = model_cls
        self.id_field = id_field
        self._lock = asyncio.Lock()

    def _extract_id(self, item: T | dict[str, Any]) -> str | None:
        """Extract primary identifier from a model instance or raw dictionary."""
        if isinstance(item, dict):
            val = item.get(self.id_field)
            return str(val) if val is not None else None
        val = getattr(item, self.id_field, None)
        return str(val) if val is not None else None

    def _to_dict(self, item: T) -> dict[str, Any]:
        """Convert a model instance to a JSON-compatible dictionary."""
        if isinstance(item, BaseModel):
            return item.model_dump(mode="json")
        if isinstance(item, dict):
            return item
        if hasattr(item, "__dict__"):
            return item.__dict__
        raise ValueError(f"Cannot serialize item of type {type(item)}")

    def _to_model(self, raw: dict[str, Any]) -> T:
        """Deserialize raw dictionary into entity model type."""
        if issubclass(self.model_cls, BaseModel):
            return self.model_cls.model_validate(raw)
        return raw  # type: ignore[return-value]

    async def get_all(self, force_refresh: bool = False) -> list[T]:
        """Retrieve all records stored in this collection."""
        content, _ = await self.store.read_file(
            self.filename, force_refresh=force_refresh
        )
        if not content.strip():
            return []
        try:
            records = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error(f"Malformed JSON in {self.filename}: {exc}")
            raise ValueError(f"Corrupted storage file: {self.filename}") from exc

        if not isinstance(records, list):
            # Some stores might wrap collections or store dicts
            records = [records]

        return [self._to_model(item) for item in records]

    async def get(self, item_id: str, force_refresh: bool = False) -> T | None:
        """Fetch a single record by its primary identifier."""
        items = await self.get_all(force_refresh=force_refresh)
        target_str = str(item_id)
        for item in items:
            if self._extract_id(item) == target_str:
                return item
        return None

    async def upsert(self, item: T) -> T:
        """Insert a new record or update an existing record matching the item's identifier."""
        target_id = self._extract_id(item)
        if target_id is None:
            raise ValueError(f"Cannot upsert entity without '{self.id_field}'")

        async with self._lock:
            content, version = await self.store.read_file(
                self.filename, force_refresh=True
            )
            records: list[dict[str, Any]] = (
                json.loads(content) if content.strip() else []
            )

            item_dict = self._to_dict(item)
            found = False
            for idx, existing in enumerate(records):
                if self._extract_id(existing) == target_id:
                    records[idx] = item_dict
                    found = True
                    break

            if not found:
                records.append(item_dict)

            serialized = json.dumps(records, indent=2, ensure_ascii=False)
            await self.store.write_file(
                self.filename, serialized, expected_version=version
            )
            return item

    async def delete(self, item_id: str) -> bool:
        """Remove a record by its identifier. Returns True if deleted, False if not found."""
        target_str = str(item_id)
        async with self._lock:
            content, version = await self.store.read_file(
                self.filename, force_refresh=True
            )
            records: list[dict[str, Any]] = (
                json.loads(content) if content.strip() else []
            )

            original_len = len(records)
            records = [rec for rec in records if self._extract_id(rec) != target_str]

            if len(records) == original_len:
                return False

            serialized = json.dumps(records, indent=2, ensure_ascii=False)
            await self.store.write_file(
                self.filename, serialized, expected_version=version
            )
            return True

    async def bulk_replace(self, items: list[T]) -> list[T]:
        """Atomically replace the entire collection with the provided records."""
        async with self._lock:
            _, version = await self.store.read_file(self.filename, force_refresh=True)
            records = [self._to_dict(item) for item in items]
            serialized = json.dumps(records, indent=2, ensure_ascii=False)
            await self.store.write_file(
                self.filename, serialized, expected_version=version
            )
            return items
