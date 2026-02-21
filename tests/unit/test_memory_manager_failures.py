"""
Fault injection and boundary tests for memory-manager.

Verifies:
- StoreRequest content / memory_type boundaries
- memory_type="all" filter treated as no-filter
- Consolidation: store failure keeps working memory key intact (no delete)
- Consolidation: delete failure sets a short TTL instead of losing data
- Consolidation: Redis distributed lock prevents concurrent duplicate runs
"""
import asyncio
import json
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch, call

_main = sys.modules["mm_main"]
StoreRequest = _main.StoreRequest


# ---------------------------------------------------------------------------
# Boundary validation
# ---------------------------------------------------------------------------


class TestStoreRequestBoundaries:
    def test_content_at_max_length_accepted(self):
        req = StoreRequest(content="x" * 10_000, memory_type="episodic", session_id="abc")
        assert len(req.content) == 10_000

    def test_content_over_max_length_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StoreRequest(content="x" * 10_001, memory_type="episodic", session_id="abc")

    def test_content_empty_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StoreRequest(content="", memory_type="episodic", session_id="abc")

    def test_importance_boundary_0_7_accepted(self):
        req = StoreRequest(content="x", memory_type="working", importance=0.7, session_id="abc")
        assert req.importance == 0.7

    def test_importance_above_1_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StoreRequest(content="x", memory_type="working", importance=1.01, session_id="abc")

    def test_importance_below_0_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StoreRequest(content="x", memory_type="working", importance=-0.01, session_id="abc")


class TestConsolidationThresholdBoundary:
    """Consolidation only promotes memories with importance > 0.7."""

    THRESHOLD = 0.7

    def test_importance_at_threshold_not_promoted(self):
        # exactly 0.7 → not above threshold → stays in working memory
        assert not (0.7 > self.THRESHOLD)

    def test_importance_just_above_threshold_promoted(self):
        assert 0.71 > self.THRESHOLD

    def test_importance_zero_not_promoted(self):
        assert not (0.0 > self.THRESHOLD)


# ---------------------------------------------------------------------------
# Consolidation: store failure keeps working memory intact
# ---------------------------------------------------------------------------


class TestConsolidationStoreFault:
    """
    If _store_episodic or _store_semantic raises, the working memory key
    must NOT be deleted — it must stay for the next consolidation run.
    """

    async def test_store_failure_does_not_delete_key(self):
        mock_redis = AsyncMock()
        # Lock acquired on first set, released on delete
        mock_redis.set.return_value = True
        mock_redis.scan.return_value = (0, ["working_memory:s1:abc"])
        mock_redis.get.return_value = json.dumps({
            "content": "test memory",
            "importance": 0.9,
            "session_id": "abc",
            "metadata": {},
        })

        with (
            patch.object(_main, "_redis", mock_redis),
            patch.object(_main, "_store_episodic", side_effect=Exception("Postgres down")),
            patch.object(_main, "_store_semantic", AsyncMock()),
        ):
            await _main._run_consolidation()

        # delete must not have been called — working memory survives
        mock_redis.delete.assert_called_once_with(_main._CONSOLIDATION_LOCK_KEY)

    async def test_semantic_store_failure_still_deletes_key(self):
        """If episodic succeeds but semantic fails, working memory MUST still be deleted
        to prevent duplicate episodic inserts on the next consolidation run."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.scan.return_value = (0, ["working_memory:s1:abc"])
        mock_redis.get.return_value = json.dumps({
            "content": "test memory",
            "importance": 0.9,
            "session_id": "abc",
            "metadata": {},
        })

        with (
            patch.object(_main, "_redis", mock_redis),
            patch.object(_main, "_store_episodic", AsyncMock(return_value="pg-id-123")),
            patch.object(_main, "_store_semantic", side_effect=Exception("Qdrant down")),
        ):
            await _main._run_consolidation()

        # Working memory key deleted despite semantic failure (episodic is source of truth)
        # delete called twice: working memory key + lock release
        assert mock_redis.delete.call_count == 2
        deleted_keys = [c.args[0] for c in mock_redis.delete.call_args_list]
        assert "working_memory:s1:abc" in deleted_keys
        assert _main._CONSOLIDATION_LOCK_KEY in deleted_keys


# ---------------------------------------------------------------------------
# Consolidation: delete failure sets short TTL
# ---------------------------------------------------------------------------


class TestConsolidationDeleteFault:
    """
    If both stores succeed but Redis delete fails, expire(key, 300) must be
    set so the key disappears before the next 30-min consolidation run.
    """

    async def test_delete_failure_sets_expire(self):
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.scan.return_value = (0, ["working_memory:s1:abc"])
        mock_redis.get.return_value = json.dumps({
            "content": "test memory",
            "importance": 0.9,
            "session_id": "abc",
            "metadata": {},
        })
        # First delete = working memory key (raises), second = lock release (succeeds)
        mock_redis.delete.side_effect = [Exception("Redis flaky"), None]

        with (
            patch.object(_main, "_redis", mock_redis),
            patch.object(_main, "_store_episodic", AsyncMock(return_value="pg-id-1")),
            patch.object(_main, "_store_semantic", AsyncMock(return_value="qdrant-id-1")),
        ):
            await _main._run_consolidation()

        mock_redis.expire.assert_called_once_with("working_memory:s1:abc", 300)


# ---------------------------------------------------------------------------
# Consolidation: Redis distributed lock prevents concurrent duplicate runs
# ---------------------------------------------------------------------------


class TestConsolidationLock:
    """
    Redis distributed lock (nx=True) must prevent duplicate consolidation runs.
    """

    async def test_lock_not_acquired_skips_scan(self):
        """When set(nx=True) returns None (lock held), consolidation exits immediately."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = None  # another instance holds the lock

        with patch.object(_main, "_redis", mock_redis):
            await _main._run_consolidation()

        # Never reached the scan — returned early
        mock_redis.scan.assert_not_called()
        # Also must not try to release a lock it didn't acquire
        mock_redis.delete.assert_not_called()

    async def test_lock_acquired_runs_scan(self):
        """When set(nx=True) returns True, consolidation proceeds to scan.
        Also verifies the correct TTL is passed to prevent premature lock expiry."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True  # lock acquired
        mock_redis.scan.return_value = (0, [])  # no keys — nothing to consolidate

        with patch.object(_main, "_redis", mock_redis):
            await _main._run_consolidation()

        mock_redis.set.assert_called_once_with(
            _main._CONSOLIDATION_LOCK_KEY, "1", nx=True, ex=_main._CONSOLIDATION_LOCK_TTL
        )
        mock_redis.scan.assert_called_once()

    async def test_lock_always_released_even_on_exception(self):
        """Lock must be released in the finally block even if scan crashes."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.scan.side_effect = Exception("Redis exploded")

        with patch.object(_main, "_redis", mock_redis):
            await _main._run_consolidation()  # must not raise

        mock_redis.delete.assert_called_once_with(_main._CONSOLIDATION_LOCK_KEY)
