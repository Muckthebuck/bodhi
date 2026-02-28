"""WebSocket /ws/chat endpoint tests for central-agent."""

import asyncio
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Load central-agent module via conftest aliasing
_ca = sys.modules.get("central_agent_main")
if _ca is None:
    from importlib import import_module

    _ca = import_module("services.central-agent.main")


class TestWsChat:
    """Tests for the WebSocket /ws/chat endpoint."""

    async def test_ws_connect_and_receive_response(self):
        """Client sends user.message and receives response.text."""
        mock_ws = AsyncMock()
        mock_ws.receive_json = AsyncMock(
            side_effect=[
                {"type": "user.message", "text": "hello", "request_id": "req-1"},
                Exception("disconnect"),  # simulate disconnect after one message
            ]
        )
        mock_ws.send_json = AsyncMock()
        mock_ws.accept = AsyncMock()

        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        original_redis = _ca._state.get("redis")
        original_clients = _ca._state.get("ws_clients", {})
        _ca._state["redis"] = mock_redis
        _ca._state["ws_clients"] = {}

        # Simulate the response arriving via pending_responses
        async def mock_fetch(*a, **kw):
            return []

        sent_messages = []

        async def capture_send(msg):
            sent_messages.append(msg)
            # When we see animation.command thinking, resolve the future
            if msg.get("action") == "thinking":
                # Find and resolve the pending future
                for rid, fut in list(_ca._state["pending_responses"].items()):
                    if not fut.done():
                        fut.set_result("Hello back!")

        mock_ws.send_json = capture_send

        try:
            with patch.object(_ca, "_fetch_memory_context", side_effect=mock_fetch):
                try:
                    await _ca.ws_chat(mock_ws, session_id="test-session")
                except Exception:
                    pass  # disconnect exception is expected

            # Verify messages sent
            types_sent = [m.get("type") for m in sent_messages]
            assert "animation.command" in types_sent
            assert "response.text" in types_sent

            # Check response content
            response_msgs = [m for m in sent_messages if m.get("type") == "response.text"]
            assert len(response_msgs) >= 1
            assert response_msgs[0]["text"] == "Hello back!"
            assert response_msgs[0]["request_id"] == "req-1"
        finally:
            _ca._state["redis"] = original_redis
            _ca._state["ws_clients"] = original_clients

    async def test_ws_unknown_message_type(self):
        """Unknown message type returns error."""
        mock_ws = AsyncMock()
        mock_ws.receive_json = AsyncMock(
            side_effect=[
                {"type": "unknown.type", "text": "hello"},
                Exception("disconnect"),
            ]
        )
        sent = []
        mock_ws.send_json = AsyncMock(side_effect=lambda m: sent.append(m))
        mock_ws.accept = AsyncMock()

        original_clients = _ca._state.get("ws_clients", {})
        _ca._state["ws_clients"] = {}

        try:
            try:
                await _ca.ws_chat(mock_ws, session_id="s1")
            except Exception:
                pass
            error_msgs = [m for m in sent if m.get("type") == "error"]
            assert len(error_msgs) >= 1
            assert "unknown type" in error_msgs[0]["detail"]
        finally:
            _ca._state["ws_clients"] = original_clients

    async def test_ws_empty_text_rejected(self):
        """Empty text returns error."""
        mock_ws = AsyncMock()
        mock_ws.receive_json = AsyncMock(
            side_effect=[
                {"type": "user.message", "text": ""},
                Exception("disconnect"),
            ]
        )
        sent = []
        mock_ws.send_json = AsyncMock(side_effect=lambda m: sent.append(m))
        mock_ws.accept = AsyncMock()

        original_clients = _ca._state.get("ws_clients", {})
        _ca._state["ws_clients"] = {}
        try:
            try:
                await _ca.ws_chat(mock_ws, session_id="s1")
            except Exception:
                pass
            error_msgs = [m for m in sent if m.get("type") == "error"]
            assert len(error_msgs) >= 1
            assert "1-2000" in error_msgs[0]["detail"]
        finally:
            _ca._state["ws_clients"] = original_clients

    async def test_ws_redis_unavailable(self):
        """When Redis is None, returns error for user.message."""
        mock_ws = AsyncMock()
        mock_ws.receive_json = AsyncMock(
            side_effect=[
                {"type": "user.message", "text": "hi", "request_id": "r1"},
                Exception("disconnect"),
            ]
        )
        sent = []
        mock_ws.send_json = AsyncMock(side_effect=lambda m: sent.append(m))
        mock_ws.accept = AsyncMock()

        original_redis = _ca._state.get("redis")
        original_clients = _ca._state.get("ws_clients", {})
        _ca._state["redis"] = None
        _ca._state["ws_clients"] = {}
        try:
            try:
                await _ca.ws_chat(mock_ws, session_id="s1")
            except Exception:
                pass
            error_msgs = [m for m in sent if m.get("type") == "error"]
            assert len(error_msgs) >= 1
            assert "Redis" in error_msgs[0]["detail"]
        finally:
            _ca._state["redis"] = original_redis
            _ca._state["ws_clients"] = original_clients

    async def test_ws_client_cleanup_on_disconnect(self):
        """Client is removed from ws_clients on disconnect."""
        mock_ws = AsyncMock()
        mock_ws.receive_json = AsyncMock(side_effect=_ca.WebSocketDisconnect())
        mock_ws.accept = AsyncMock()

        _ca._state["ws_clients"] = {}
        try:
            await _ca.ws_chat(mock_ws, session_id="cleanup-test")
        except Exception:
            pass

        assert "cleanup-test" not in _ca._state["ws_clients"]


class TestBroadcastToWs:
    """Tests for _broadcast_to_ws helper."""

    async def test_broadcast_to_all(self):
        """Broadcast without session_id sends to all clients."""
        ws1, ws2 = AsyncMock(), AsyncMock()
        _ca._state["ws_clients"] = {"s1": {ws1}, "s2": {ws2}}
        try:
            await _ca._broadcast_to_ws({"type": "emotion.update", "label": "happy"})
            ws1.send_json.assert_called_once()
            ws2.send_json.assert_called_once()
        finally:
            _ca._state["ws_clients"] = {}

    async def test_broadcast_to_session(self):
        """Broadcast with session_id only sends to that session."""
        ws1, ws2 = AsyncMock(), AsyncMock()
        _ca._state["ws_clients"] = {"s1": {ws1}, "s2": {ws2}}
        try:
            await _ca._broadcast_to_ws({"type": "test"}, session_id="s1")
            ws1.send_json.assert_called_once()
            ws2.send_json.assert_not_called()
        finally:
            _ca._state["ws_clients"] = {}

    async def test_dead_client_removed(self):
        """Client that raises on send_json is cleaned up."""
        ws_good = AsyncMock()
        ws_dead = AsyncMock()
        ws_dead.send_json.side_effect = Exception("connection closed")
        _ca._state["ws_clients"] = {"s1": {ws_good, ws_dead}}
        try:
            await _ca._broadcast_to_ws({"type": "test"})
            ws_good.send_json.assert_called_once()
            assert ws_dead not in _ca._state["ws_clients"].get("s1", set())
        finally:
            _ca._state["ws_clients"] = {}
