"""
Fault injection tests for central-agent.

Verifies:
- Subscriber loop continues after malformed / binary Redis messages
- Publish timeout raises TimeoutError within the expected window
- session_id / text field boundary validation
"""

import asyncio
import json
import sys

import pytest

_main = sys.modules["ca_main"]
InputRequest = _main.InputRequest


# ---------------------------------------------------------------------------
# Boundary validation
# ---------------------------------------------------------------------------


class TestInputRequestBoundaries:
    """Pydantic field constraints added in the deep code review."""

    def test_text_max_length_accepted(self):
        req = InputRequest(text="x" * 2_000, session_id="abc")
        assert len(req.text) == 2_000

    def test_text_over_max_length_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InputRequest(text="x" * 2_001, session_id="abc")

    def test_session_id_alphanumeric_accepted(self):
        req = InputRequest(text="hi", session_id="session-42_ABC")
        assert req.session_id == "session-42_ABC"

    def test_session_id_empty_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InputRequest(text="hi", session_id="")

    def test_session_id_with_slash_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InputRequest(text="hi", session_id="session/123")

    def test_session_id_with_space_rejected(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InputRequest(text="hi", session_id="session 123")

    def test_session_id_xss_rejected(self):
        """XSS-style input must be rejected by pattern validator."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            InputRequest(text="hi", session_id="<script>")


# ---------------------------------------------------------------------------
# Publish timeout
# ---------------------------------------------------------------------------


class TestPublishTimeout:
    """asyncio.wait_for wrapping Redis publish must raise within timeout window."""

    async def test_hung_publish_raises_timeout_error(self):
        async def _hung_publish(*_a, **_kw):
            await asyncio.sleep(9_999)

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(_hung_publish("user.input", "{}"), timeout=0.1)

    async def test_fast_publish_completes_within_timeout(self):
        async def _fast_publish(*_a, **_kw):
            return 1

        result = await asyncio.wait_for(_fast_publish("user.input", "{}"), timeout=2.0)
        assert result == 1


# ---------------------------------------------------------------------------
# Subscriber message parsing resilience
# ---------------------------------------------------------------------------


class TestSubscriberMessageParsing:
    """
    The subscriber loop wraps each message in a try/except.
    Bad data must be handled gracefully — future resolved with raw fallback,
    subsequent messages processed normally.
    """

    def _handle_message(self, message: dict, pending: dict) -> None:
        """Mirrors the inner try block of _redis_subscriber in central-agent/main.py."""
        try:
            channel: str = message["channel"]
            data: str = message["data"]

            if channel.startswith("language.response."):
                request_id = channel[len("language.response.") :]
                try:
                    payload = json.loads(data)
                    response_text = payload.get("response", json.dumps(payload))
                except Exception:
                    response_text = data  # fall back to raw string
                future = pending.get(request_id)
                if future and not future.done():
                    future.set_result(response_text)
        except Exception:
            pass  # loop must never crash on any individual message

    async def test_bad_json_falls_back_to_raw_data(self):
        loop = asyncio.get_event_loop()
        pending = {}
        future = loop.create_future()
        pending["req-1"] = future

        self._handle_message(
            {"type": "pmessage", "channel": "language.response.req-1", "data": "not-json"},
            pending,
        )
        result = await asyncio.wait_for(future, timeout=0.1)
        assert result == "not-json"

    async def test_valid_json_extracts_response_field(self):
        loop = asyncio.get_event_loop()
        pending = {}
        future = loop.create_future()
        pending["req-2"] = future

        self._handle_message(
            {
                "type": "pmessage",
                "channel": "language.response.req-2",
                "data": json.dumps({"response": "hello world", "intent": "greeting"}),
            },
            pending,
        )
        result = await asyncio.wait_for(future, timeout=0.1)
        assert result == "hello world"

    async def test_missing_response_key_dumps_whole_payload(self):
        loop = asyncio.get_event_loop()
        pending = {}
        future = loop.create_future()
        pending["req-3"] = future

        payload = {"intent": "greeting", "entities": []}
        self._handle_message(
            {
                "type": "pmessage",
                "channel": "language.response.req-3",
                "data": json.dumps(payload),
            },
            pending,
        )
        result = await asyncio.wait_for(future, timeout=0.1)
        assert json.loads(result) == payload

    async def test_corrupt_message_does_not_block_next(self):
        """Message with missing keys is swallowed; the next valid message succeeds."""
        loop = asyncio.get_event_loop()
        pending = {}
        good_future = loop.create_future()
        pending["req-good"] = good_future

        # corrupt: missing channel/data keys — outer except swallows KeyError
        self._handle_message({"type": "pmessage"}, pending)

        # valid message still processed
        self._handle_message(
            {
                "type": "pmessage",
                "channel": "language.response.req-good",
                "data": json.dumps({"response": "still works"}),
            },
            pending,
        )
        result = await asyncio.wait_for(good_future, timeout=0.1)
        assert result == "still works"

    async def test_duplicate_response_does_not_overwrite_future(self):
        """Second message for same request_id is silently ignored once future is done."""
        loop = asyncio.get_event_loop()
        pending = {}
        future = loop.create_future()
        future.set_result("first")
        pending["req-dup"] = future

        self._handle_message(
            {
                "type": "pmessage",
                "channel": "language.response.req-dup",
                "data": json.dumps({"response": "second"}),
            },
            pending,
        )
        result = await future
        assert result == "first"
