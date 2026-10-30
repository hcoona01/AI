"""Seed the configured persistence store (local or GitHub Gist) from data/seed.

Idempotent by default. Supports complete reset via --reset.

Usage:
    python scripts/seed_store.py [--reset] [--backend local|gist]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Ensure backend package is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.repositories import (
    get_constraint_repository,
    get_course_repository,
    get_faculty_repository,
    get_resource_repository,
    get_section_repository,
    get_store,
    get_timeslot_repository,
    get_user_repository,
)
from app.schemas.constraint import ConstraintRule
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.schemas.user import User
from app.services.audit_service import AuditService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("seed_store")

SEED_DIR = REPO_ROOT / "data" / "seed"


async def seed_data(reset: bool = False, backend: str | None = None) -> dict[str, int]:
    """Load JSON files from data/seed/ into active store."""
    selected_backend = backend or settings.STORE_BACKEND
    print(f"[*] Connecting to storage backend: {selected_backend} (reset={reset})...")

    store = get_store(backend=selected_backend)
    audit_service = AuditService()

    user_repo = get_user_repository(store)
    faculty_repo = get_faculty_repository(store)
    course_repo = get_course_repository(store)
    section_repo = get_section_repository(store)
    resource_repo = get_resource_repository(store)
    timeslot_repo = get_timeslot_repository(store)
    constraint_repo = get_constraint_repository(store)

    collections: list[tuple[str, Any, Any, str]] = [
        ("users.json", User, user_repo, "id"),
        ("faculty.json", Faculty, faculty_repo, "id"),
        ("courses.json", Course, course_repo, "id"),
        ("sections.json", Section, section_repo, "id"),
        ("resources.json", Resource, resource_repo, "id"),
        ("timeslots.json", TimeSlot, timeslot_repo, "id"),
        ("constraints.json", ConstraintRule, constraint_repo, "rule_id"),
    ]

    counts: dict[str, int] = {}

    for filename, model_cls, repo, id_attr in collections:
        filepath = SEED_DIR / filename
        if not filepath.exists():
            print(f"[!] Warning: seed file not found: {filepath}")
            continue

        raw_data = json.loads(filepath.read_text(encoding="utf-8"))
        items = [model_cls.model_validate(record) for record in raw_data]

        if reset:
            await repo.bulk_replace(items)
            counts[filename] = len(items)
            print(f"[+] {filename}: replaced with {len(items)} items")
        else:
            # Idempotent: upsert missing or updated records
            existing_items = await repo.get_all(force_refresh=True)
            existing_ids = {getattr(ex, id_attr) for ex in existing_items}
            added_count = 0
            for item in items:
                item_id = getattr(item, id_attr)
                if item_id not in existing_ids:
                    await repo.upsert(item)
                    added_count += 1
            total_after = len(existing_ids) + added_count
            counts[filename] = total_after
            print(
                f"[+] {filename}: {added_count} new items added (total {total_after})"
            )

    # Record audit log
    await audit_service.log_event(
        actor_id="script:seed_store",
        action="STORE_SEEDED",
        entity="system",
        payload={"reset": reset, "backend": selected_backend, "counts": counts},
    )
    print("[*] Finished seeding. Recorded audit log event STORE_SEEDED.")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed academic data into active storage store."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Completely reset/overwrite store collections",
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["local", "gist"],
        default=None,
        help="Storage backend override",
    )
    args = parser.parse_args()

    asyncio.run(seed_data(reset=args.reset, backend=args.backend))


if __name__ == "__main__":
    main()
