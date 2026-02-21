import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from neo4j import AsyncGraphDatabase
from prometheus_client import make_asgi_app
from pydantic import BaseModel
from redis.asyncio import Redis

import metrics

load_dotenv()

log = structlog.get_logger()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    f"postgresql://bodhi:{os.getenv('POSTGRES_PASSWORD', '')}@postgres:5432/bodhi",
)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

RESPONSE_TIMEOUT = 5.0

_state: dict[str, Any] = {
    "redis": None,
    "pg_pool": None,
    "neo4j_driver": None,
    "active_agents": set(),
    "pending_responses": {},
}


class InputRequest(BaseModel):
    text: str
    session_id: str


class InputResponse(BaseModel):
    request_id: str
    response: str | None = None
    error: str | None = None


async def _redis_subscriber() -> None:
    redis: Redis = _state["redis"]
    channels = ["language.response", "emotion.state_changed", "memory.stored"]
    pubsub = redis.pubsub()
    await pubsub.subscribe(*channels)
    log.info("redis_subscriber_started", channels=channels)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        channel: str = message["channel"]
        data: str = message["data"]

        if channel == "language.response":
            # data format: "<request_id>:<response_text>"
            parts = data.split(":", 1)
            if len(parts) == 2:
                request_id, response_text = parts
                future: asyncio.Future | None = _state["pending_responses"].get(request_id)
                if future and not future.done():
                    future.set_result(response_text)

        elif channel == "emotion.state_changed":
            log.info("emotion_state_changed", data=data)

        elif channel == "memory.stored":
            log.info("memory_stored", data=data)


async def _heartbeat_watcher() -> None:
    redis: Redis = _state["redis"]
    pubsub = redis.pubsub()
    await pubsub.psubscribe("agent.heartbeat.*")

    async for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue
        channel: str = message["channel"]
        agent_name = channel.split(".")[-1]
        _state["active_agents"].add(agent_name)
        metrics.active_agents.set(len(_state["active_agents"]))


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("central_agent_starting")

    try:
        _state["redis"] = Redis.from_url(REDIS_URL, decode_responses=True)
        await _state["redis"].ping()
        log.info("redis_connected", url=REDIS_URL)
    except Exception as exc:
        log.error("redis_connect_failed", error=str(exc))

    try:
        _state["pg_pool"] = await asyncpg.create_pool(dsn=POSTGRES_DSN, min_size=2, max_size=10)
        log.info("postgres_connected")
    except Exception as exc:
        log.error("postgres_connect_failed", error=str(exc))

    try:
        _state["neo4j_driver"] = AsyncGraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        await _state["neo4j_driver"].verify_connectivity()
        log.info("neo4j_connected", uri=NEO4J_URI)
    except Exception as exc:
        log.error("neo4j_connect_failed", error=str(exc))

    background_tasks = []
    if _state["redis"]:
        background_tasks.append(asyncio.create_task(_redis_subscriber()))
        background_tasks.append(asyncio.create_task(_heartbeat_watcher()))

    log.info("central_agent_ready")
    yield

    log.info("central_agent_shutting_down")
    for task in background_tasks:
        task.cancel()

    if _state["redis"]:
        await _state["redis"].aclose()
    if _state["pg_pool"]:
        await _state["pg_pool"].close()
    if _state["neo4j_driver"]:
        await _state["neo4j_driver"].close()

    log.info("central_agent_stopped")


app = FastAPI(title="central-agent", version="0.1.0", lifespan=lifespan)
app.mount("/metrics", make_asgi_app())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "agent": "central-agent", "version": "0.1.0"}


@app.get("/status")
async def status() -> dict[str, Any]:
    import psutil

    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024

    redis_ok = False
    if _state["redis"]:
        try:
            await _state["redis"].ping()
            redis_ok = True
        except Exception:
            pass

    return {
        "memory_mb": round(mem_mb, 2),
        "active_agents": sorted(_state["active_agents"]),
        "connections": {
            "redis": redis_ok,
            "postgres": _state["pg_pool"] is not None,
            "neo4j": _state["neo4j_driver"] is not None,
        },
    }


@app.post("/input", response_model=InputResponse)
async def handle_input(body: InputRequest, request: Request) -> InputResponse:
    start = time.perf_counter()
    request_id = str(uuid.uuid4())

    if not _state["redis"]:
        metrics.requests_total.labels(status="error").inc()
        return JSONResponse(status_code=503, content={"error": "redis unavailable"})

    future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
    _state["pending_responses"][request_id] = future

    payload = f"{request_id}:{body.session_id}:{body.text}"
    try:
        await _state["redis"].publish("user.input", payload)
        log.info("input_published", request_id=request_id, session_id=body.session_id)

        response_text = await asyncio.wait_for(future, timeout=RESPONSE_TIMEOUT)
        metrics.requests_total.labels(status="success").inc()
        result = InputResponse(request_id=request_id, response=response_text)
    except asyncio.TimeoutError:
        log.warning("response_timeout", request_id=request_id)
        metrics.requests_total.labels(status="timeout").inc()
        result = InputResponse(request_id=request_id, error="timeout")
    except Exception as exc:
        log.error("input_handler_error", request_id=request_id, error=str(exc))
        metrics.requests_total.labels(status="error").inc()
        result = InputResponse(request_id=request_id, error="internal error")
    finally:
        _state["pending_responses"].pop(request_id, None)
        metrics.latency_seconds.observe(time.perf_counter() - start)

    return result
