"""
Mock fixtures that simulate dependency failures.

These are imported by unit tests that need to exercise fault-handling paths
without real infrastructure. All fixtures return pre-configured AsyncMocks.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def hung_redis():
    """Redis mock whose publish hangs forever (simulates blocked network)."""
    mock = AsyncMock()

    async def _hang(*_args, **_kwargs):
        await asyncio.sleep(9_999)

    mock.publish = _hang
    mock.ping = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def failing_redis():
    """Redis mock that raises ConnectionError on every call."""
    mock = AsyncMock()
    mock.publish.side_effect = ConnectionError("Redis unreachable")
    mock.set.side_effect = ConnectionError("Redis unreachable")
    mock.get.side_effect = ConnectionError("Redis unreachable")
    return mock


@pytest.fixture
def failing_qdrant():
    """Qdrant mock that raises on upsert (embedding store failure)."""
    mock = AsyncMock()
    mock.upsert.side_effect = Exception("Qdrant connection refused")
    mock.search.side_effect = Exception("Qdrant connection refused")
    return mock


@pytest.fixture
def unreachable_neo4j():
    """Neo4j driver mock whose verify_connectivity hangs forever."""
    mock = MagicMock()

    async def _hang():
        await asyncio.sleep(9_999)

    mock.verify_connectivity = _hang
    mock.close = AsyncMock()
    return mock
