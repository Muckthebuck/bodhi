from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
import redis.asyncio as aioredis
import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field, field_validator

import metrics as m

load_dotenv()

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATABASE_URL = (
    os.getenv("POSTGRES_URL")
    or os.getenv("DATABASE_URL")
    or f"postgresql://bodhi:{os.getenv('POSTGRES_PASSWORD', 'bodhi')}@postgres:5432/bodhi"
)
EMOTION_TRANSITION_SPEED = float(os.getenv("EMOTION_TRANSITION_SPEED", "0.1"))
DRIFT_RATE = 0.02
TRANSITION_INTERVAL = 1.0
PUBLISH_THRESHOLD = 0.05

BASELINE = {"valence": 0.1, "arousal": 0.3, "dominance": 0.5}

EVENT_EFFECTS: dict[str, dict[str, float]] = {
    "user.positive_feedback": {"valence": +0.3, "arousal": +0.1, "dominance": +0.1},
    "user.negative_feedback": {"valence": -0.2, "arousal": +0.2, "dominance": -0.1},
    "user.greeting":          {"valence": +0.2, "arousal": +0.2, "dominance": 0.0},
    "user.farewell":          {"valence": +0.1, "arousal": -0.2, "dominance": 0.0},
    "task.completed":         {"valence": +0.2, "arousal": +0.1, "dominance": +0.2},
    "task.failed":            {"valence": -0.1, "arousal": +0.1, "dominance": -0.1},
    "user.input":             {"valence": +0.05, "arousal": +0.1, "dominance": 0.0},
    "language.response":      {"valence": 0.0,  "arousal": -0.05, "dominance": 0.0},
}

# Validate at import time — before any I/O opens, so failures are clean with no leaks
_valid_vad = {"valence", "arousal", "dominance"}
for _event, _effects in EVENT_EFFECTS.items():
    if set(_effects.keys()) != _valid_vad:
        raise ValueError(f"EVENT_EFFECTS[{_event!r}] has invalid keys: {set(_effects.keys())}")

DEFAULT_PERSONALITY: dict[str, float] = {
    "openness": 0.8,
    "conscientiousness": 0.7,
    "extraversion": 0.5,
    "agreeableness": 0.8,
    "neuroticism": 0.2,
}

REDIS_SUBSCRIPTIONS = ["user.input", "task.completed", "task.failed", "language.response"]

# ---------------------------------------------------------------------------
# Shared mutable state
# ---------------------------------------------------------------------------

_state_lock = asyncio.Lock()

vad_current: dict[str, float] = {"valence": 0.1, "arousal": 0.3, "dominance": 0.5}
vad_target: dict[str, float] = {"valence": 0.1, "arousal": 0.3, "dominance": 0.5}
personality: dict[str, float] = dict(DEFAULT_PERSONALITY)

_redis_client: aioredis.Redis | None = None
_db_pool: asyncpg.Pool | None = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _vad_clamp(dim: str, value: float) -> float:
    if dim == "valence":
        return _clamp(value, -1.0, 1.0)
    return _clamp(value, 0.0, 1.0)


def _derive_label(v: float, a: float, d: float, openness: float) -> str:
    if v > 0.3 and a > 0.5:
        return "excited"
    if v > 0.3 and a <= 0.5:
        return "happy" if v > 0.6 else "content"
    if v < -0.2 and a > 0.5:
        return "anxious" if d < 0.4 else "frustrated"
    if v < -0.2 and a <= 0.5:
        return "sad"
    return "curious" if openness > 0.7 else "calm"


def _max_delta(a: dict[str, float], b: dict[str, float]) -> float:
    return max(abs(a[k] - b[k]) for k in a)


def _update_prometheus() -> None:
    for dim, val in vad_current.items():
        m.emotion_state.labels(dimension=dim).set(val)


# ---------------------------------------------------------------------------
# Postgres helpers
# ---------------------------------------------------------------------------


async def _load_personality_from_db() -> None:
    global personality
    if _db_pool is None:
        return
    try:
        async with _db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT value FROM settings WHERE key = $1", "emotion.personality"
            )
        if row:
            stored = json.loads(row["value"])
            personality = {**DEFAULT_PERSONALITY, **stored}
            log.info("personality_loaded_from_db")
    except Exception as exc:
        log.warning("personality_load_failed", error=str(exc))


async def _save_personality_to_db(data: dict[str, float]) -> None:
    if _db_pool is None:
        raise RuntimeError("database unavailable")
    async with _db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            "emotion.personality",
            json.dumps(data),
        )


# ---------------------------------------------------------------------------
# Emotion update logic
# ---------------------------------------------------------------------------


async def _apply_event(event_type: str, intensity: float) -> None:
    effects = EVENT_EFFECTS.get(event_type)
    if effects is None:
        return

    async with _state_lock:
        for dim, delta in effects.items():
            vad_target[dim] = _vad_clamp(dim, vad_target[dim] + delta * intensity)

    m.emotion_updates_total.labels(event_type=event_type).inc()
    await _publish_state()


async def _publish_state() -> None:
    if _redis_client is None:
        return
    async with _state_lock:
        snapshot = dict(vad_current)
        label = _derive_label(
            snapshot["valence"], snapshot["arousal"], snapshot["dominance"],
            personality.get("openness", DEFAULT_PERSONALITY["openness"]),
        )

    payload = json.dumps({
        "valence": snapshot["valence"],
        "arousal": snapshot["arousal"],
        "dominance": snapshot["dominance"],
        "label": label,
    })
    try:
        await _redis_client.publish("emotion.state_changed", payload)
    except Exception as exc:
        log.warning("redis_publish_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Background transition tick
# ---------------------------------------------------------------------------


async def _transition_tick() -> None:
    while True:
        await asyncio.sleep(TRANSITION_INTERVAL)
        async with _state_lock:
            prev = dict(vad_current)
            for dim in ("valence", "arousal", "dominance"):
                step = EMOTION_TRANSITION_SPEED * TRANSITION_INTERVAL
                diff = vad_target[dim] - vad_current[dim]
                if abs(diff) <= step:
                    vad_current[dim] = vad_target[dim]
                else:
                    vad_current[dim] += step * (1 if diff > 0 else -1)

                drift_diff = BASELINE[dim] - vad_target[dim]
                drift_step = DRIFT_RATE * TRANSITION_INTERVAL
                if abs(drift_diff) <= drift_step:
                    vad_target[dim] = BASELINE[dim]
                else:
                    vad_target[dim] += drift_step * (1 if drift_diff > 0 else -1)

                vad_current[dim] = _vad_clamp(dim, vad_current[dim])
                vad_target[dim] = _vad_clamp(dim, vad_target[dim])

            changed = _max_delta(vad_current, prev) > PUBLISH_THRESHOLD

        _update_prometheus()

        if changed:
            m.emotion_transitions_total.inc()
            await _publish_state()


# ---------------------------------------------------------------------------
# Redis subscriber
# ---------------------------------------------------------------------------


async def _redis_subscriber() -> None:
    if _redis_client is None:
        return
    pubsub = _redis_client.pubsub()
    await pubsub.subscribe(*REDIS_SUBSCRIPTIONS)
    log.info("redis_subscribed", channels=REDIS_SUBSCRIPTIONS)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        channel: str = message["channel"]
        if isinstance(channel, bytes):
            channel = channel.decode()

        try:
            data = json.loads(message["data"])
        except (json.JSONDecodeError, TypeError):
            data = {}

        base_channel = channel.split(".")[0] + "." + channel.split(".")[1] if channel.count(".") >= 1 else channel
        event_type = channel if channel in EVENT_EFFECTS else base_channel
        intensity = float(data.get("intensity", 1.0))
        log.debug("redis_message", channel=channel, event_type=event_type)
        await _apply_event(event_type, intensity)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis_client, _db_pool

    _redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    log.info("redis_connected", url=REDIS_URL)

    try:
        _db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        log.info("postgres_connected")
        await _load_personality_from_db()
    except Exception as exc:
        log.warning("postgres_unavailable", error=str(exc))

    _update_prometheus()

    tick_task = asyncio.create_task(_transition_tick())
    sub_task = asyncio.create_task(_redis_subscriber())

    yield

    tick_task.cancel()
    sub_task.cancel()
    await asyncio.gather(tick_task, sub_task, return_exceptions=True)

    if _db_pool:
        await _db_pool.close()
    await _redis_client.aclose()
    log.info("shutdown_complete")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="emotion-regulator", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class UpdateRequest(BaseModel):
    event_type: str
    intensity: float = Field(default=1.0, ge=0.0, le=2.0)
    context: dict[str, Any] = Field(default_factory=dict)


class PersonalityUpdate(BaseModel):
    openness: float | None = Field(default=None, ge=0.0, le=1.0)
    conscientiousness: float | None = Field(default=None, ge=0.0, le=1.0)
    extraversion: float | None = Field(default=None, ge=0.0, le=1.0)
    agreeableness: float | None = Field(default=None, ge=0.0, le=1.0)
    neuroticism: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("*", mode="before")
    @classmethod
    def allow_none(cls, v: Any) -> Any:
        return v


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "agent": "emotion-regulator", "version": "0.1.0"}


@app.get("/state")
async def get_state() -> dict[str, Any]:
    async with _state_lock:
        current = dict(vad_current)
        target = dict(vad_target)

    label = _derive_label(
        current["valence"], current["arousal"], current["dominance"],
        personality.get("openness", DEFAULT_PERSONALITY["openness"]),
    )
    progress = {
        dim: round(
            1.0 - abs(target[dim] - current[dim]) / max(abs(target[dim] - BASELINE[dim]), 1e-6),
            4,
        )
        for dim in ("valence", "arousal", "dominance")
    }
    return {
        "current": current,
        "target": target,
        "label": label,
        "transition_progress": progress,
    }


@app.post("/update")
async def update_emotion(body: UpdateRequest) -> dict[str, Any]:
    await _apply_event(body.event_type, body.intensity)
    async with _state_lock:
        current = dict(vad_current)
    label = _derive_label(
        current["valence"], current["arousal"], current["dominance"],
        personality.get("openness", DEFAULT_PERSONALITY["openness"]),
    )
    return {"status": "ok", "label": label, "current": current}


@app.get("/personality")
async def get_personality() -> dict[str, Any]:
    return {"profile_name": "bodhi_default", "personality": dict(personality)}


@app.put("/personality")
async def put_personality(body: PersonalityUpdate) -> dict[str, Any]:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided")

    updated = {**personality, **updates}
    try:
        await _save_personality_to_db(updated)
    except Exception as exc:
        log.error("personality_save_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="Failed to persist personality") from exc

    async with _state_lock:
        personality.update(updates)
    log.info("personality_updated", fields=list(updates.keys()))
    return {"status": "ok", "personality": dict(personality)}


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=False)
