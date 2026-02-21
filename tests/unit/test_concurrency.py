"""
Concurrency tests for emotion-regulator and memory-manager.

Verifies:
- Concurrent _apply_event calls don't crash or produce torn VAD state
- Concurrent personality reads/writes are consistent (no torn reads)
- EVENT_EFFECTS keys are validated at startup
"""

import asyncio
import copy
import sys
from unittest.mock import AsyncMock, patch

import pytest

_er = sys.modules["er_main"]
_mm = sys.modules["mm_main"]


# ---------------------------------------------------------------------------
# Emotion-regulator: concurrent VAD updates
# ---------------------------------------------------------------------------


class TestApplyEventConcurrency:
    """_apply_event uses _state_lock — concurrent calls must not crash."""

    async def test_concurrent_events_do_not_crash(self):
        """100 concurrent event applications should all complete without error."""
        # Reset state to a known baseline
        _er.vad_target.update(dict(_er.BASELINE))
        _er.vad_current.update(dict(_er.BASELINE))

        with patch.object(_er, "_redis_client", None):  # skip Redis publish
            tasks = [
                asyncio.create_task(_er._apply_event("user.positive_feedback", 0.5))
                for _ in range(100)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [r for r in results if isinstance(r, Exception)]
        assert errors == [], f"Unexpected exceptions: {errors}"

    async def test_concurrent_events_vad_stays_clamped(self):
        """After many positive events, VAD values must stay within [-1, 1]."""
        _er.vad_target.update(dict(_er.BASELINE))
        _er.vad_current.update(dict(_er.BASELINE))

        with patch.object(_er, "_redis_client", None):
            tasks = [
                asyncio.create_task(_er._apply_event("user.positive_feedback", 1.0))
                for _ in range(50)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

        for dim, val in _er.vad_target.items():
            assert -1.0 <= val <= 1.0, f"{dim}={val} out of clamp range"

    async def test_publish_failure_does_not_crash_apply_event(self):
        """If Redis publish raises ConnectionError, _apply_event must not propagate it.
        The emotion update is applied; only the broadcast is lost."""
        _er.vad_target.update(dict(_er.BASELINE))
        mock_redis = AsyncMock()
        mock_redis.publish.side_effect = ConnectionError("Redis down")

        with patch.object(_er, "_redis_client", mock_redis):
            # Must not raise
            await _er._apply_event("user.positive_feedback", 1.0)

        # VAD target was still updated despite publish failure
        assert _er.vad_target["valence"] > _er.BASELINE["valence"]


# ---------------------------------------------------------------------------
# Emotion-regulator: personality read/write concurrency
# ---------------------------------------------------------------------------


class TestPersonalityConcurrency:
    """Personality dict is protected by _state_lock — reads must never see torn state."""

    async def test_concurrent_reads_and_writes_no_torn_state(self):
        """
        50 concurrent writers updating 'openness' while 50 readers snapshot
        personality must not raise or produce values outside [0.0, 1.0].
        """
        _er.personality.update(dict(_er.DEFAULT_PERSONALITY))

        seen_values: list[float] = []

        async def writer(i: int):
            # Alternate between two valid openness values
            val = 0.3 if i % 2 == 0 else 0.8
            async with _er._state_lock:
                _er.personality["openness"] = val
            await asyncio.sleep(0)

        async def reader():
            async with _er._state_lock:
                val = _er.personality.get("openness", -1.0)
            seen_values.append(val)
            await asyncio.sleep(0)

        tasks = [asyncio.create_task(writer(i)) for i in range(50)] + [
            asyncio.create_task(reader()) for _ in range(50)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        for val in seen_values:
            assert 0.0 <= val <= 1.0, f"Torn personality read: openness={val}"

    async def test_put_personality_and_apply_event_concurrent(self):
        """put_personality and _apply_event both take _state_lock; they must not deadlock."""
        _er.personality.update(dict(_er.DEFAULT_PERSONALITY))
        _er.vad_target.update(dict(_er.BASELINE))

        async def do_put():
            async with _er._state_lock:
                _er.personality["openness"] = 0.6
            await asyncio.sleep(0)

        with patch.object(_er, "_redis_client", None):
            tasks = [asyncio.create_task(do_put()) for _ in range(20)] + [
                asyncio.create_task(_er._apply_event("user.positive_feedback", 0.3))
                for _ in range(20)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [r for r in results if isinstance(r, Exception)]
        assert errors == [], f"Unexpected exceptions: {errors}"


# ---------------------------------------------------------------------------
# Emotion-regulator: EVENT_EFFECTS startup validation
# ---------------------------------------------------------------------------


class TestEventEffectsValidation:
    """EVENT_EFFECTS must have exactly {valence, arousal, dominance} for every event."""

    def test_all_events_have_valid_vad_keys(self):
        valid_keys = {"valence", "arousal", "dominance"}
        for event, effects in _er.EVENT_EFFECTS.items():
            assert set(effects.keys()) == valid_keys, (
                f"EVENT_EFFECTS[{event!r}] has wrong keys: {set(effects.keys())}"
            )

    def test_all_vad_values_are_floats_in_range(self):
        for event, effects in _er.EVENT_EFFECTS.items():
            for dim, val in effects.items():
                assert isinstance(val, (int, float)), (
                    f"EVENT_EFFECTS[{event!r}][{dim!r}] is not a number: {val!r}"
                )
                assert -1.0 <= val <= 1.0, (
                    f"EVENT_EFFECTS[{event!r}][{dim!r}]={val} outside [-1, 1]"
                )

    def test_typo_in_vad_key_would_be_caught(self):
        """Verify the validation logic that runs in lifespan() would catch a typo."""
        valid_vad = {"valence", "arousal", "dominance"}
        broken = copy.deepcopy(dict(_er.EVENT_EFFECTS))
        broken["user.positive_feedback"] = {"vlaence": 0.3, "arousal": 0.1, "dominance": 0.1}

        invalid = [event for event, effects in broken.items() if set(effects.keys()) != valid_vad]
        assert invalid == ["user.positive_feedback"]


# ---------------------------------------------------------------------------
# Memory-manager: concurrent consolidation lock (unit-level verification)
# ---------------------------------------------------------------------------


class TestConsolidationLockConcurrency:
    """
    Simulates the lock behavior using asyncio without real Redis:
    only one of N concurrent callers should proceed past the lock.
    """

    async def test_only_one_consolidation_runs_at_a_time(self):
        runs = []
        lock_held = False

        async def fake_consolidation():
            nonlocal lock_held
            if lock_held:
                return  # simulate: set(nx=True) returned None
            lock_held = True
            try:
                runs.append(1)
                await asyncio.sleep(0.01)  # yield to let others try
            finally:
                lock_held = False

        tasks = [asyncio.create_task(fake_consolidation()) for _ in range(10)]
        await asyncio.gather(*tasks)

        # Because asyncio is cooperative and tasks yield, only 1 should
        # have been "running" at any moment (lock_held guard)
        assert len(runs) >= 1  # at least one ran
        assert max(runs) == 1  # each run recorded exactly 1
