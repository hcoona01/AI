"""Unit tests for GistStore with mocked httpx transport.

Validates:
1. Success flow (fetch, ETag 304, in-memory TTL cache, patch write).
2. Optimistic concurrency conflict (409 detection and retry failure).
3. Rate limit handling (403 with X-RateLimit-Remaining: 0).
4. Truncated file handling (>1MB fetching raw_url).
5. Auto-creation of private Gist when GIST_ID is empty.
"""

import json

import httpx
import pytest

from app.core.errors import ConflictError, RateLimitError
from app.repositories.gist_store import GistStore


@pytest.mark.anyio
async def test_gist_store_success_and_caching():
    """Test standard fetch, ETag 304 caching, in-memory TTL caching, and patch updates."""
    get_count = 0
    patch_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal get_count, patch_count

        if request.method == "GET":
            get_count += 1
            if request.headers.get("if-none-match") == '"W/etag-abc"':
                return httpx.Response(304, headers={"etag": '"W/etag-abc"'})

            payload = {
                "id": "gist-123",
                "updated_at": "2026-10-30T10:00:00Z",
                "files": {
                    "users.json": {
                        "filename": "users.json",
                        "truncated": False,
                        "content": '[{"id": "u-01", "email": "test@univ.edu"}]',
                    }
                },
            }
            return httpx.Response(
                200,
                json=payload,
                headers={"etag": '"W/etag-abc"', "x-ratelimit-remaining": "4999"},
            )

        if request.method == "PATCH":
            patch_count += 1
            body = json.loads(request.content)
            updated_users = body["files"]["users.json"]["content"]
            payload = {
                "id": "gist-123",
                "updated_at": "2026-10-30T10:05:00Z",
                "files": {
                    "users.json": {
                        "filename": "users.json",
                        "truncated": False,
                        "content": updated_users,
                    }
                },
            }
            return httpx.Response(
                200,
                json=payload,
                headers={"etag": '"W/etag-def"', "x-ratelimit-remaining": "4998"},
            )

        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    store = GistStore(
        token="test-token", gist_id="gist-123", client=client, ttl_seconds=0.1
    )

    # 1. Initial read
    content, version = await store.read_file("users.json")
    assert "u-01" in content
    assert version == "2026-10-30T10:00:00Z"
    assert get_count == 1

    # 2. In-memory TTL cache read (should not increment get_count)
    content2, _ = await store.read_file("users.json", force_refresh=False)
    assert content2 == content
    assert get_count == 1

    # 3. ETag 304 test: force refresh passes ETag and receives 304
    content3, _ = await store.read_file("users.json", force_refresh=True)
    assert content3 == content
    assert get_count == 2

    # 4. Patch write
    new_version = await store.write_file(
        "users.json",
        '[{"id": "u-01", "email": "test@univ.edu"}, {"id": "u-02"}]',
        expected_version="2026-10-30T10:00:00Z",
    )
    assert new_version == "2026-10-30T10:05:00Z"
    assert patch_count == 1


@pytest.mark.anyio
async def test_gist_truncated_file_fetches_raw_url():
    """Verify that truncated files (>1MB) trigger raw_url download."""
    raw_url_fetched = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal raw_url_fetched
        url_str = str(request.url)

        if "raw/users.json" in url_str:
            raw_url_fetched = True
            large_content = json.dumps([{"id": f"large-u-{i}"} for i in range(100)])
            return httpx.Response(200, text=large_content)

        if request.method == "GET":
            payload = {
                "id": "gist-123",
                "updated_at": "2026-10-30T10:00:00Z",
                "files": {
                    "users.json": {
                        "filename": "users.json",
                        "truncated": True,
                        "raw_url": "https://gist.githubusercontent.com/raw/users.json",
                        "content": None,
                    }
                },
            }
            return httpx.Response(
                200, json=payload, headers={"x-ratelimit-remaining": "5000"}
            )

        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    store = GistStore(token="test-token", gist_id="gist-123", client=client)

    content, version = await store.read_file("users.json")
    assert raw_url_fetched is True
    assert "large-u-99" in content
    assert version == "2026-10-30T10:00:00Z"


@pytest.mark.anyio
async def test_gist_rate_limit_handling():
    """Verify that HTTP 403 with x-ratelimit-remaining: 0 raises clear RateLimitError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            text='{"message": "API rate limit exceeded for user"}',
            headers={
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": "1793350000",
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    store = GistStore(token="test-token", gist_id="gist-123", client=client)

    with pytest.raises(RateLimitError) as exc_info:
        await store.fetch_gist(force_refresh=True)

    assert exc_info.value.status_code == 403
    assert exc_info.value.details["remaining"] == "0"
    assert exc_info.value.details["reset_at"] == 1793350000
    assert "rate limit exceeded" in exc_info.value.message.lower()


@pytest.mark.anyio
async def test_gist_optimistic_concurrency_conflict_409():
    """Verify optimistic concurrency: detected updated_at mismatch re-fetches and raises 409 on persistent conflict."""

    def handler(request: httpx.Request) -> httpx.Response:
        # Every GET returns updated_at='2026-10-30T11:00:00Z'
        payload = {
            "id": "gist-123",
            "updated_at": "2026-10-30T11:00:00Z",
            "files": {
                "users.json": {
                    "filename": "users.json",
                    "truncated": False,
                    "content": "[]",
                }
            },
        }
        return httpx.Response(
            200, json=payload, headers={"x-ratelimit-remaining": "4000"}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    store = GistStore(token="test-token", gist_id="gist-123", client=client)

    # Initial state
    store._cached_updated_at = "2026-10-30T11:00:00Z"

    # Expecting older version '2026-10-30T10:00:00Z' - both attempts should fail and raise ConflictError
    with pytest.raises(ConflictError) as exc_info:
        await store._write_with_retry(
            filename="users.json",
            content="[]",
            expected_version="2026-10-30T10:00:00Z",
            is_retry=True,  # Simulate second attempt failing
        )

    assert exc_info.value.status_code == 409
    assert "Optimistic concurrency violation" in exc_info.value.message


@pytest.mark.anyio
async def test_gist_auto_create_when_id_empty():
    """Verify private Gist is automatically created when GIST_ID is empty."""
    post_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal post_called
        if (
            request.method == "POST"
            and str(request.url) == "https://api.github.com/gists"
        ):
            post_called = True
            body = json.loads(request.content)
            assert body["public"] is False
            assert "users.json" in body["files"]
            return httpx.Response(
                201,
                json={
                    "id": "new-auto-gist-888",
                    "updated_at": "2026-10-30T12:00:00Z",
                    "files": {f: {"content": "[]"} for f in body["files"]},
                },
                headers={"etag": '"W/new-etag"'},
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    store = GistStore(token="test-token", gist_id="", client=client)

    created_id = await store.ensure_gist_initialized()
    assert post_called is True
    assert created_id == "new-auto-gist-888"
    assert store.gist_id == "new-auto-gist-888"
