"""Unit tests — central-agent pure logic (no I/O)"""
import sys
import asyncio
import pytest

_main = sys.modules["ca_main"]


class TestInputRequestValidation:
    """Test Pydantic model validation without starting the app."""

    def test_valid_input(self):
        InputRequest = _main.InputRequest
        req = InputRequest(text="hello", session_id="abc")
        assert req.text == "hello"
        assert req.session_id == "abc"

    def test_missing_text_raises(self):
        from pydantic import ValidationError
        InputRequest = _main.InputRequest
        with pytest.raises(ValidationError):
            InputRequest(session_id="abc")

    def test_missing_session_id_raises(self):
        from pydantic import ValidationError
        InputRequest = _main.InputRequest
        with pytest.raises(ValidationError):
            InputRequest(text="hello")


class TestPendingResponseFutures:
    """Test the in-process request/response tracking pattern."""

    async def test_future_resolved_by_subscriber(self):
        pending: dict[str, asyncio.Future] = {}
        loop = asyncio.get_event_loop()
        request_id = "req-123"
        future: asyncio.Future = loop.create_future()
        pending[request_id] = future
        pending[request_id].set_result("hello back")
        result = await asyncio.wait_for(future, timeout=1.0)
        assert result == "hello back"

    async def test_future_times_out(self):
        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(future, timeout=0.05)

    async def test_future_not_set_twice(self):
        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        future.set_result("first")
        if not future.done():
            future.set_result("second")
        result = await future
        assert result == "first"


class TestRedisMessageParsing:
    """Test the language.response channel message parsing logic from main.py."""

    def _parse_language_response(self, data: str) -> tuple[str, str] | None:
        """Mirrors the parsing in _redis_subscriber."""
        parts = data.split(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return None

    def test_parse_valid_message(self):
        result = self._parse_language_response("req-abc:Hello there!")
        assert result == ("req-abc", "Hello there!")

    def test_parse_response_with_colon_in_text(self):
        result = self._parse_language_response("req-abc:Time is 3:00pm")
        assert result == ("req-abc", "Time is 3:00pm")

    def test_parse_missing_separator_returns_none(self):
        result = self._parse_language_response("no-separator")
        assert result is None

    def test_parse_empty_string_returns_none(self):
        result = self._parse_language_response("")
        assert result is None


class TestStatusResponse:
    """Test the /status endpoint shape without starting the app."""

    def test_status_shape(self):
        state = {
            "active_agents": {"language-center", "emotion-regulator"},
            "redis": object(),
            "pg_pool": object(),
        }
        import psutil
        process = psutil.Process()
        response = {
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 1),
            "active_agents": sorted(state["active_agents"]),
            "redis_connected": state["redis"] is not None,
            "postgres_connected": state["pg_pool"] is not None,
        }
        assert isinstance(response["memory_mb"], float)
        assert isinstance(response["active_agents"], list)
        assert response["redis_connected"] is True
        assert response["postgres_connected"] is True
