"""Unit and integration tests for LocalStore and generic Repository[T]."""

import asyncio
from pathlib import Path

import pytest

from app.core.errors import ConflictError
from app.repositories.base import Repository
from app.repositories.local_store import LocalStore
from app.schemas.common import FacultyRank, UserRole
from app.schemas.constraint import ConstraintRule, RuleType
from app.schemas.faculty import Faculty, FacultyExpertise
from app.schemas.user import User


@pytest.fixture
def temp_store(tmp_path: Path) -> LocalStore:
    """Provide an isolated LocalStore backed by an empty temporary directory."""
    return LocalStore(base_dir=tmp_path, ttl_seconds=0.1)


@pytest.mark.anyio
async def test_repository_crud_operations(temp_store: LocalStore):
    """Test get_all, get, upsert, delete on generic Repository[User]."""
    repo = Repository(temp_store, "users.json", User, id_field="id")

    # Initial state should be empty
    all_users = await repo.get_all()
    assert len(all_users) == 0

    # Upsert new user
    user1 = User(
        id="u-001", email="turing@univ.edu", role=UserRole.FACULTY, faculty_id="f-01"
    )
    created = await repo.upsert(user1)
    assert created.id == "u-001"

    # Get by ID
    fetched = await repo.get("u-001")
    assert fetched is not None
    assert fetched.email == "turing@univ.edu"
    assert fetched.role == UserRole.FACULTY

    # Upsert second user
    user2 = User(id="u-002", email="admin@univ.edu", role=UserRole.ADMIN)
    await repo.upsert(user2)

    all_users = await repo.get_all(force_refresh=True)
    assert len(all_users) == 2

    # Update existing user
    user1_updated = User(
        id="u-001",
        email="alan.turing@univ.edu",
        role=UserRole.FACULTY,
        faculty_id="f-01",
    )
    await repo.upsert(user1_updated)

    fetched_updated = await repo.get("u-001", force_refresh=True)
    assert fetched_updated is not None
    assert fetched_updated.email == "alan.turing@univ.edu"

    # Delete user
    deleted = await repo.delete("u-001")
    assert deleted is True

    # Verify deleted
    assert await repo.get("u-001") is None
    all_users = await repo.get_all()
    assert len(all_users) == 1

    # Second delete returns False
    deleted_again = await repo.delete("u-001")
    assert deleted_again is False


@pytest.mark.anyio
async def test_repository_bulk_replace(temp_store: LocalStore):
    """Test atomic bulk replacement."""
    repo = Repository(temp_store, "users.json", User, id_field="id")

    items = [
        User(id="u-01", email="user1@univ.edu", role=UserRole.FACULTY),
        User(id="u-02", email="user2@univ.edu", role=UserRole.FACULTY),
        User(id="u-03", email="user3@univ.edu", role=UserRole.ADMIN),
    ]

    replaced = await repo.bulk_replace(items)
    assert len(replaced) == 3

    fetched_all = await repo.get_all(force_refresh=True)
    assert len(fetched_all) == 3
    assert {u.id for u in fetched_all} == {"u-01", "u-02", "u-03"}


@pytest.mark.anyio
async def test_repository_custom_id_field(temp_store: LocalStore):
    """Test Repository using ConstraintRule where id_field is 'rule_id'."""
    repo = Repository(
        temp_store, "constraints.json", ConstraintRule, id_field="rule_id"
    )

    rule = ConstraintRule(
        rule_id="HC-01",
        type=RuleType.HARD,
        description="Faculty expertise proficiency requirement",
        weight=1.0,
        enabled=True,
    )
    await repo.upsert(rule)

    fetched = await repo.get("HC-01")
    assert fetched is not None
    assert fetched.rule_id == "HC-01"
    assert fetched.type == RuleType.HARD

    deleted = await repo.delete("HC-01")
    assert deleted is True
    assert await repo.get("HC-01") is None


@pytest.mark.anyio
async def test_optimistic_concurrency_conflict(temp_store: LocalStore):
    """Test that modifying a file concurrently triggers ConflictError (409)."""
    filename = "users.json"
    _content, version = await temp_store.read_file(filename)

    # Simulate an external write on disk that changes mtime and content
    file_path = temp_store.base_dir / filename
    await asyncio.sleep(0.01)
    file_path.write_text('[{"id": "external"}]', encoding="utf-8")

    # Attempting to write with the original stale expected_version must fail
    with pytest.raises(ConflictError) as exc_info:
        await temp_store.write_file(
            filename, '[{"id": "mine"}]', expected_version=version
        )

    assert "Optimistic concurrency violation" in exc_info.value.message
    assert exc_info.value.status_code == 409


@pytest.mark.anyio
async def test_in_memory_ttl_cache(tmp_path: Path):
    """Verify that reads within TTL use cache, and force_refresh bypasses it."""
    store = LocalStore(base_dir=tmp_path, ttl_seconds=1.0)
    filename = "users.json"

    # Initial write
    await store.write_file(filename, '[{"id": "cached"}]')

    # Read into cache
    content1, _ = await store.read_file(filename)
    assert content1 == '[{"id": "cached"}]'

    # Manually overwrite file on disk
    file_path = tmp_path / filename
    file_path.write_text('[{"id": "disk_modified"}]', encoding="utf-8")

    # Read within TTL should still return cached content
    content2, _ = await store.read_file(filename, force_refresh=False)
    assert content2 == '[{"id": "cached"}]'

    # force_refresh=True must bypass cache and read the latest disk state
    content3, _ = await store.read_file(filename, force_refresh=True)
    assert content3 == '[{"id": "disk_modified"}]'


@pytest.mark.anyio
async def test_concurrent_async_writes(temp_store: LocalStore):
    """Verify per-file async lock prevents file corruption during simultaneous writes."""
    repo = Repository(temp_store, "faculty.json", Faculty, id_field="id")

    async def add_faculty(idx: int):
        f = Faculty(
            id=f"f-test-{idx:02d}",
            name=f"Prof {idx}",
            email=f"prof{idx}@univ.edu",
            rank=FacultyRank.ASSISTANT_PROFESSOR,
            expertise=[FacultyExpertise(tag="Algorithms", proficiency=4)],
            max_weekly_load_hours=12.0,
            max_courses=3,
            min_courses=1,
            max_preparations=2,
        )
        await repo.upsert(f)

    # Launch 10 simultaneous upsert coroutines
    await asyncio.gather(*(add_faculty(i) for i in range(10)))

    all_fac = await repo.get_all(force_refresh=True)
    assert len(all_fac) == 10
    fac_ids = {f.id for f in all_fac}
    assert fac_ids == {f"f-test-{i:02d}" for i in range(10)}
