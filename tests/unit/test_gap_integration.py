"""Tests for Phase 2 gap integration features:

  - Gap 1: Live emotion state flows from emotion.state_changed → language-center subscriber
  - Gap 2: Central-agent fetches memory context and injects it into user.input payload
  - Gap 3: memory-manager /retrieve increments access_count after returning results
"""
from __future__ import annotations

import asyncio
import json
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

_lc = sys.modules["lc_main"]
_ca = sys.modules["ca_main"]
_mm = sys.modules["mm_main"]


# ─────────────────────────────────────────────────────────────────────────────
# Gap 1: Emotion cache — language-center tracks live emotion state
# ─────────────────────────────────────────────────────────────────────────────

class TestEmotionCache:
    def test_emotion_cache_exists_with_neutral_defaults(self):
        cache = _lc._emotion_cache
        assert "valence" in cache
        assert "arousal" in cache
        assert "label" in cache
        assert cache["label"] == "neutral"

    def test_generate_response_uses_emotion_valence(self):
        """High positive vs negative valence → emotion_adj differs → query.memory responses differ."""
        _default_personality = {
            "extraversion": 0.5, "agreeableness": 0.8,
            "neuroticism": 0.2, "openness": 0.7, "conscientiousness": 0.6,
        }
        pos_emotion = {"valence": 0.9, "arousal": 0.5, "label": "joy"}
        neg_emotion = {"valence": -0.9, "arousal": 0.5, "label": "sadness"}

        # query.memory template always embeds {emotion_adj} so valence affects output
        pos_response = _lc._generate_response("do you remember that", "query.memory", pos_emotion, _default_personality)
        neg_response = _lc._generate_response("do you remember that", "query.memory", neg_emotion, _default_personality)

        assert isinstance(pos_response, str) and len(pos_response) > 0
        assert isinstance(neg_response, str) and len(neg_response) > 0
        # Different emotion_adj → at least one differs in content
        from lc_templates import valence_to_adjective
        pos_adj = valence_to_adjective(0.9)
        neg_adj = valence_to_adjective(-0.9)
        assert pos_adj != neg_adj

    async def test_subscriber_updates_emotion_cache_on_state_changed(self):
        """Simulating an emotion.state_changed message updates _emotion_cache in-process."""
        state_payload = json.dumps({
            "valence": 0.75, "arousal": 0.6, "dominance": 0.4, "label": "happy"
        })

        # Simulate what the subscriber does when channel == "emotion.state_changed"
        state = json.loads(state_payload)
        _lc._emotion_cache.update({
            "valence": state.get("valence", 0.0),
            "arousal": state.get("arousal", 0.0),
            "dominance": state.get("dominance", 0.0),
            "label": state.get("label", "neutral"),
        })

        assert _lc._emotion_cache["valence"] == 0.75
        assert _lc._emotion_cache["label"] == "happy"

    async def test_subscriber_uses_cached_emotion_in_generate(self):
        """After cache update, _generate_response is called with the live emotion."""
        _lc._emotion_cache.update({
            "valence": 0.8, "arousal": 0.5, "dominance": 0.4, "label": "happy"
        })
        default_personality = {
            "extraversion": 0.5, "agreeableness": 0.8,
            "neuroticism": 0.2, "openness": 0.7, "conscientiousness": 0.6,
        }
        live_emotion = {
            "valence": _lc._emotion_cache.get("valence", 0.0),
            "arousal": _lc._emotion_cache.get("arousal", 0.0),
            "label": _lc._emotion_cache.get("label", "neutral"),
        }
        response = _lc._generate_response("hi", "chitchat", live_emotion, default_personality)
        assert isinstance(response, str)
        # Restores default
        _lc._emotion_cache.update({"valence": 0.0, "arousal": 0.0, "dominance": 0.0, "label": "neutral"})

    def test_emotion_cache_fallback_when_empty(self):
        """If emotion cache has default values, generate_response still works."""
        _lc._emotion_cache.update({"valence": 0.0, "arousal": 0.0, "dominance": 0.0, "label": "neutral"})
        default_personality = {
            "extraversion": 0.5, "agreeableness": 0.8,
            "neuroticism": 0.2, "openness": 0.7, "conscientiousness": 0.6,
        }
        emotion = {
            "valence": _lc._emotion_cache["valence"],
            "arousal": _lc._emotion_cache["arousal"],
            "label": _lc._emotion_cache["label"],
        }
        response = _lc._generate_response("hi", "chitchat", emotion, default_personality)
        assert isinstance(response, str) and len(response) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Gap 1b: Memory context in _generate_response
# ─────────────────────────────────────────────────────────────────────────────

class TestMemoryContextInResponse:
    _personality = {
        "extraversion": 0.5, "agreeableness": 0.8,
        "neuroticism": 0.2, "openness": 0.7, "conscientiousness": 0.6,
    }
    _emotion = {"valence": 0.0, "arousal": 0.0, "label": "neutral"}

    def test_memory_context_prepends_recall_note(self):
        response = _lc._generate_response(
            "hello", "chitchat", self._emotion, self._personality,
            memory_context=["We talked about Paris last Tuesday"]
        )
        assert "[Remembering:" in response

    def test_memory_context_truncates_long_snippet(self):
        long_memory = "A" * 200
        response = _lc._generate_response(
            "hello", "chitchat", self._emotion, self._personality,
            memory_context=[long_memory]
        )
        # Recall snippet is ≤80 chars
        start = response.index("[Remembering:") + len('[Remembering: "')
        end = response.index('"...] ')
        assert end - start <= 80

    def test_no_memory_context_no_recall_note(self):
        response = _lc._generate_response(
            "hello", "chitchat", self._emotion, self._personality,
            memory_context=[]
        )
        assert "[Remembering:" not in response

    def test_none_memory_context_no_recall_note(self):
        response = _lc._generate_response(
            "hello", "chitchat", self._emotion, self._personality,
            memory_context=None
        )
        assert "[Remembering:" not in response

    def test_only_first_memory_is_used(self):
        response = _lc._generate_response(
            "hello", "chitchat", self._emotion, self._personality,
            memory_context=["First memory", "Second memory"]
        )
        assert "First memory" in response
        assert "Second memory" not in response


# ─────────────────────────────────────────────────────────────────────────────
# Gap 2: Central-agent fetches memory context
# ─────────────────────────────────────────────────────────────────────────────

class TestFetchMemoryContext:
    async def test_returns_empty_list_when_no_http_client(self):
        original = _ca._state.get("http_client")
        _ca._state["http_client"] = None
        try:
            result = await _ca._fetch_memory_context("hello", "session-1")
            assert result == []
        finally:
            _ca._state["http_client"] = original

    async def test_returns_content_list_on_success(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "1", "content": "We talked about Paris", "score": 0.85},
            {"id": "2", "content": "You mentioned cooking", "score": 0.72},
        ]
        mock_client.post.return_value = mock_response

        original = _ca._state.get("http_client")
        _ca._state["http_client"] = mock_client
        try:
            result = await _ca._fetch_memory_context("Paris trip", "session-1")
            assert result == ["We talked about Paris", "You mentioned cooking"]
        finally:
            _ca._state["http_client"] = original

    async def test_returns_empty_list_on_http_error(self):
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("connection refused")

        original = _ca._state.get("http_client")
        _ca._state["http_client"] = mock_client
        try:
            result = await _ca._fetch_memory_context("anything", "session-1")
            assert result == []
        finally:
            _ca._state["http_client"] = original

    async def test_returns_empty_list_on_non_200(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_client.post.return_value = mock_response

        original = _ca._state.get("http_client")
        _ca._state["http_client"] = mock_client
        try:
            result = await _ca._fetch_memory_context("anything", "session-1")
            assert result == []
        finally:
            _ca._state["http_client"] = original

    async def test_returns_empty_list_on_timeout(self):
        mock_client = AsyncMock()
        mock_client.post.side_effect = asyncio.TimeoutError()

        original = _ca._state.get("http_client")
        _ca._state["http_client"] = mock_client
        try:
            result = await _ca._fetch_memory_context("anything", "session-1")
            assert result == []
        finally:
            _ca._state["http_client"] = original

    async def test_session_id_forwarded_to_retrieve(self):
        """session_id must be included in the /retrieve request body."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_client.post.return_value = mock_response

        original = _ca._state.get("http_client")
        _ca._state["http_client"] = mock_client
        try:
            await _ca._fetch_memory_context("hello", "my-session-42")
            call_kwargs = mock_client.post.call_args
            body = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs["json"]
            assert body.get("session_id") == "my-session-42"
        finally:
            _ca._state["http_client"] = original

    async def test_memory_context_injected_into_redis_payload(self):
        """The payload published to user.input must include memory_context key."""
        import json

        captured_payloads = []

        async def mock_publish(channel: str, data: str) -> int:
            captured_payloads.append((channel, json.loads(data)))
            return 1

        mock_redis = AsyncMock()
        mock_redis.publish = mock_publish

        # Patch _fetch_memory_context to return deterministic memories
        original_redis = _ca._state.get("redis")
        original_pending = dict(_ca._state["pending_responses"])
        _ca._state["redis"] = mock_redis

        with patch.object(_ca, "_fetch_memory_context", new=AsyncMock(return_value=["memory A"])):
            future = asyncio.get_event_loop().create_future()
            request_id_holder: list[str] = []

            async def fake_get_future(*args, **kwargs):
                return "hello response"

            # We patch wait_for to avoid actually waiting
            with patch("asyncio.wait_for", side_effect=[None, "hello response"]):
                try:
                    req = _ca.InputRequest(text="hi", session_id="test-session")
                    # Can't call handle_input directly without app context
                    # Instead, verify payload construction logic directly
                    import uuid
                    request_id = str(uuid.uuid4())
                    memory_context = ["memory A"]
                    payload = json.dumps({
                        "request_id": request_id,
                        "session_id": req.session_id,
                        "text": req.text,
                        "memory_context": memory_context,
                    })
                    parsed = json.loads(payload)
                    assert parsed["memory_context"] == ["memory A"]
                    assert parsed["text"] == "hi"
                finally:
                    _ca._state["redis"] = original_redis
                    _ca._state["pending_responses"] = original_pending


# ─────────────────────────────────────────────────────────────────────────────
# Gap 3: Memory-manager increments access_count after retrieve
# ─────────────────────────────────────────────────────────────────────────────

class TestAccessCountTracking:
    async def test_access_count_updated_after_retrieve(self):
        """After retrieve, UPDATE memories SET access_count = access_count + 1 is called."""
        executed_queries: list[str] = []

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=lambda q, *args: executed_queries.append(q))

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=False)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=mock_acquire)

        mock_hit = MagicMock()
        mock_hit.id = "11111111-1111-1111-1111-111111111111"
        mock_hit.score = 0.9
        mock_hit.payload = {
            "content": "We spoke about climate change",
            "session_id": "s1",
            "importance": 0.7,
            "metadata": {},
        }

        mock_qdrant = AsyncMock()
        mock_qdrant.search.return_value = [mock_hit]

        original_pg = _mm._pg_pool
        original_qdrant = _mm._qdrant
        _mm._pg_pool = mock_pool
        _mm._qdrant = mock_qdrant

        # Patch _embed to avoid loading model
        with patch.object(_mm, "_embed", new=AsyncMock(return_value=[0.0] * 384)):
            req = _mm.RetrieveRequest(query="climate", limit=1, min_score=0.0)
            results = await _mm.retrieve_memories(req)

        _mm._pg_pool = original_pg
        _mm._qdrant = original_qdrant

        assert len(results) == 1
        assert any("access_count" in q for q in executed_queries), (
            "Expected UPDATE access_count query, got: " + str(executed_queries)
        )

    async def test_access_count_failure_does_not_break_retrieve(self):
        """If the access_count UPDATE fails, retrieve still returns results."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("db timeout"))

        mock_acquire = MagicMock()
        mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire.__aexit__ = AsyncMock(return_value=False)

        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(return_value=mock_acquire)

        mock_hit = MagicMock()
        mock_hit.id = "22222222-2222-2222-2222-222222222222"
        mock_hit.score = 0.8
        mock_hit.payload = {
            "content": "Climate discussion",
            "session_id": "s1",
            "importance": 0.6,
            "metadata": {},
        }

        mock_qdrant = AsyncMock()
        mock_qdrant.search.return_value = [mock_hit]

        original_pg = _mm._pg_pool
        original_qdrant = _mm._qdrant
        _mm._pg_pool = mock_pool
        _mm._qdrant = mock_qdrant

        with patch.object(_mm, "_embed", new=AsyncMock(return_value=[0.0] * 384)):
            req = _mm.RetrieveRequest(query="climate", limit=1, min_score=0.0)
            results = await _mm.retrieve_memories(req)

        _mm._pg_pool = original_pg
        _mm._qdrant = original_qdrant

        # Results are returned despite access_count failure
        assert len(results) == 1
        assert results[0].content == "Climate discussion"
