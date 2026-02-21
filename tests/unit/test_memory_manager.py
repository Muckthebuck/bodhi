"""Unit tests — memory-manager pure logic (no I/O)"""
import sys
import pytest

_main = sys.modules["mm_main"]
StoreRequest = _main.StoreRequest
RetrieveRequest = _main.RetrieveRequest
MemoryResult = _main.MemoryResult


class TestStoreRequestValidation:
    def test_valid_episodic(self):
        req = StoreRequest(
            content="had lunch",
            memory_type="episodic",
            importance=0.5,
            session_id="abc",
        )
        assert req.memory_type == "episodic"

    def test_valid_semantic(self):
        req = StoreRequest(
            content="user prefers dark mode",
            memory_type="semantic",
            importance=0.8,
            session_id="abc",
        )
        assert req.importance == 0.8

    def test_valid_working(self):
        req = StoreRequest(
            content="current task is drafting email",
            memory_type="working",
            importance=0.3,
            session_id="abc",
        )
        assert req.memory_type == "working"

    def test_invalid_memory_type_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StoreRequest(
                content="bad",
                memory_type="unknown_type",
                importance=0.5,
                session_id="abc",
            )

    def test_missing_content_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StoreRequest(memory_type="episodic", importance=0.5, session_id="abc")

    def test_importance_defaults_to_half(self):
        req = StoreRequest(content="test", memory_type="episodic", session_id="abc")
        assert req.importance == 0.5


class TestRetrieveRequestValidation:
    def test_valid_request(self):
        req = RetrieveRequest(query="dark mode preference", limit=5, min_score=0.5)
        assert req.limit == 5

    def test_defaults(self):
        req = RetrieveRequest(query="test")
        assert req.limit >= 1
        assert req.min_score >= 0.0

    def test_missing_query_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RetrieveRequest(limit=5)


class TestConsolidationThreshold:
    """Consolidation moves working memories with importance > 0.7 to long-term."""

    THRESHOLD = 0.7

    def _should_consolidate(self, importance: float) -> bool:
        return importance > self.THRESHOLD

    def test_high_importance_consolidates(self):
        assert self._should_consolidate(0.8) is True

    def test_low_importance_stays_working(self):
        assert self._should_consolidate(0.5) is False

    def test_at_threshold_does_not_consolidate(self):
        assert self._should_consolidate(0.7) is False

    def test_just_above_threshold_consolidates(self):
        assert self._should_consolidate(0.71) is True

    def test_maximum_importance_consolidates(self):
        assert self._should_consolidate(1.0) is True

    def test_minimum_importance_stays(self):
        assert self._should_consolidate(0.0) is False


class TestMemoryResultModel:
    def test_memory_result_fields(self):
        result = MemoryResult(
            id="uuid-123",
            content="test content",
            score=0.85,
            session_id="abc",
            importance=0.6,
            metadata={"memory_type": "episodic"},
        )
        assert result.id == "uuid-123"
        assert result.score == 0.85

    def test_score_is_float(self):
        result = MemoryResult(
            id="uuid-456",
            content="test",
            score=0.5,
            session_id="abc",
            importance=0.5,
            metadata={},
        )
        assert isinstance(result.score, float)
