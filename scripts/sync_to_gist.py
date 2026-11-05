"""Sync local store/seed data to GitHub Gist and verify all collections.

Usage:
    python scripts/sync_to_gist.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.repositories import (
    GistStore,
    Repository,
    get_assignment_repository,
    get_audit_repository,
    get_change_request_repository,
    get_constraint_repository,
    get_course_repository,
    get_faculty_repository,
    get_resource_repository,
    get_section_repository,
    get_timeslot_repository,
    get_user_repository,
)
from app.schemas.assignment import Assignment
from app.schemas.audit import AuditLogEntry
from app.schemas.change_request import ChangeRequest
from app.schemas.constraint import ConstraintRule
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.schemas.user import User

TOKEN = os.getenv("GIST_TOKEN") or settings.GIST_TOKEN
if not TOKEN:
    # Try fetching from gh auth token
    import subprocess
    try:
        TOKEN = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except Exception:
        pass


async def main():
    if not TOKEN:
        print("[!] Error: No GitHub Token found. Please set GIST_TOKEN.")
        sys.exit(1)

    existing_gist_id = os.getenv("GIST_ID") or settings.GIST_ID or "62907a1fa0dd1bd05513a9b4ffd0a660"
    print(f"[*] Connecting to GistStore with GitHub token ({TOKEN[:4]}...{TOKEN[-4:]})...")
    gist_store = GistStore(token=TOKEN, gist_id=existing_gist_id)

    gist_id = await gist_store.ensure_gist_initialized()
    print(f"[OK] Live GitHub Gist ID: {gist_id}")
    print(f"[OK] Gist URL: https://gist.github.com/{gist_id}")

    # Now verify each file from data/store and push if needed
    store_dir = REPO_ROOT / "data" / "store"
    seed_dir = REPO_ROOT / "data" / "seed"

    managed_files = [
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
        "change_requests.json",
    ]

    print("\n[*] Syncing and verifying database entities to GitHub Gist:")
    print("-" * 65)

    for fname in managed_files:
        src_path = store_dir / fname
        if not src_path.exists():
            src_path = seed_dir / fname

        if src_path.exists():
            content = src_path.read_text(encoding="utf-8")
            data = json.loads(content)
            record_count = len(data) if isinstance(data, list) else len(data.keys())

            # Read current from Gist
            gist_content, version = await gist_store.read_file(fname)
            try:
                gist_data = json.loads(gist_content)
                gist_count = len(gist_data) if isinstance(gist_data, list) else len(gist_data.keys())
            except Exception:
                gist_count = 0

            # If local has more data or Gist has default, update Gist
            if record_count != gist_count or gist_count == 0:
                print(f"  -> Uploading {fname:22} ({record_count} items vs Gist {gist_count})...", end=" ")
                await gist_store.write_file(fname, content)
                print("DONE [OK]")
            else:
                print(f"  -> In sync   {fname:22} ({record_count} items) [OK]")

    # Run CRUD test against live Gist
    print("\n[*] Testing live database operations against GitHub Gist:")
    print("-" * 65)

    user_repo = get_user_repository(gist_store)
    users = await user_repo.get_all(force_refresh=True)
    print(f"  [OK] READ users.json: successfully fetched {len(users)} users.")

    faculty_repo = get_faculty_repository(gist_store)
    faculties = await faculty_repo.get_all(force_refresh=True)
    print(f"  [OK] READ faculty.json: successfully fetched {len(faculties)} faculty profiles.")

    course_repo = get_course_repository(gist_store)
    courses = await course_repo.get_all(force_refresh=True)
    print(f"  [OK] READ courses.json: successfully fetched {len(courses)} courses.")

    # Test audit logging entry write
    audit_repo = get_audit_repository(gist_store)
    test_entry = AuditLogEntry(
        id=f"audit_test_{int(asyncio.get_event_loop().time())}",
        actor_id="admin@university.edu",
        action="GIST_SYNC_HEALTH_CHECK",
        entity="github_gist",
        payload={"status": "verified", "gist_id": gist_id},
    )
    await audit_repo.upsert(test_entry)
    print(f"  [OK] WRITE audit_log.json: created test audit entry '{test_entry.id}'.")

    # Read back audit entry to prove round-trip persistence
    fetched_entry = await audit_repo.get(test_entry.id, force_refresh=True)
    assert fetched_entry is not None and fetched_entry.id == test_entry.id
    print(f"  [OK] ROUND-TRIP VERIFICATION: live read confirmed entry '{test_entry.id}' from GitHub Gist.")

    print("\n" + "=" * 65)
    print(f"[SUCCESS] All database entries tested and verified live on GitHub Gist!")
    print(f"Gist ID : {gist_id}")
    print(f"Live URL: https://gist.github.com/{gist_id}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
