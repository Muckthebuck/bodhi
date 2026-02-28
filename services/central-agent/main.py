import asyncio
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
import httpx
import metrics
import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from neo4j import AsyncGraphDatabase
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field
from redis.asyncio import Redis

load_dotenv()

log = structlog.get_logger()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
POSTGRES_DSN = (
    os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_DSN")
    or f"postgresql://bodhi:{os.getenv('POSTGRES_PASSWORD', '')}@postgres:5432/bodhi"
)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
MEMORY_MANAGER_URL = os.getenv("MEMORY_MANAGER_URL", "http://memory-manager:8001")

RESPONSE_TIMEOUT = 5.0
MEMORY_RETRIEVE_TIMEOUT = 1.0  # fail fast — never block user response

_state: dict[str, Any] = {
    "redis": None,
    "pg_pool": None,
    "neo4j_driver": None,
    "active_agents": set(),
    "agent_last_seen": {},  # {agent_name: float timestamp}
    "pending_responses": {},
    "http_client": None,
    "ws_clients": {},  # {session_id: set[WebSocket]}
}


class InputRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)
    session_id: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")


class InputResponse(BaseModel):
    request_id: str
    response: str | None = None
    error: str | None = None


async def _fetch_memory_context(text: str, session_id: str) -> list[str]:
    """Retrieve top-3 relevant memories for *text*. Returns [] on any failure."""
    client: httpx.AsyncClient | None = _state.get("http_client")
    if client is None:
        return []
    try:
        resp = await asyncio.wait_for(
            client.post(
                f"{MEMORY_MANAGER_URL}/retrieve",
                json={"query": text, "limit": 3, "min_score": 0.4, "session_id": session_id},
            ),
            timeout=MEMORY_RETRIEVE_TIMEOUT,
        )
        if resp.status_code == 200:
            hits = resp.json()
            return [h["content"] for h in hits if h.get("content")]
    except Exception as exc:
        log.warning("memory_retrieve_failed", error=str(exc))
    return []


async def _broadcast_to_ws(msg: dict, session_id: str | None = None) -> None:
    """Send a JSON message to connected WebSocket clients.
    If session_id is given, only send to clients on that session.
    Otherwise broadcast to all."""
    targets: list[WebSocket] = []
    if session_id and session_id in _state["ws_clients"]:
        targets = list(_state["ws_clients"][session_id])
    elif session_id is None:
        for sockets in _state["ws_clients"].values():
            targets.extend(sockets)
    dead: list[tuple[str, WebSocket]] = []
    for ws in targets:
        try:
            await ws.send_json(msg)
        except Exception:
            # find session for this ws to clean up
            for sid, sockets in _state["ws_clients"].items():
                if ws in sockets:
                    dead.append((sid, ws))
    for sid, ws in dead:
        _state["ws_clients"].get(sid, set()).discard(ws)


async def _redis_subscriber() -> None:
    redis: Redis = _state["redis"]
    pubsub = redis.pubsub()
    # psubscribe for dynamic per-request response channels; plain subscribe for events
    await pubsub.psubscribe("language.response.*")
    await pubsub.subscribe("emotion.state_changed", "memory.stored")
    log.info("redis_subscriber_started")

    async for message in pubsub.listen():
        msg_type: str = message["type"]
        if msg_type not in ("message", "pmessage"):
            continue
        try:
            channel: str = message["channel"]
            data: str = message["data"]

            if channel.startswith("language.response."):
                # channel = language.response.<request_id>
                request_id = channel[len("language.response.") :]
                try:
                    payload = json.loads(data)
                    response_text = payload.get("response", json.dumps(payload))
                except Exception:
                    response_text = data
                future: asyncio.Future | None = _state["pending_responses"].get(request_id)
                if future and not future.done():
                    future.set_result(response_text)

            elif channel == "emotion.state_changed":
                log.info("emotion_state_changed", data=data)
                try:
                    emotion_data = json.loads(data)
                    await _broadcast_to_ws(
                        {
                            "type": "emotion.update",
                            "valence": emotion_data.get("valence", 0.0),
                            "arousal": emotion_data.get("arousal", 0.0),
                            "label": emotion_data.get("label", "neutral"),
                        }
                    )
                except Exception as ws_exc:
                    log.warning("ws_emotion_broadcast_failed", error=str(ws_exc))

            elif channel == "memory.stored":
                log.info("memory_stored", data=data)

        except Exception as exc:
            log.error("redis_subscriber_message_error", error=str(exc))


async def _heartbeat_watcher() -> None:
    redis: Redis = _state["redis"]
    pubsub = redis.pubsub()
    await pubsub.psubscribe("agent.heartbeat.*")

    async for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue
        try:
            channel: str = message["channel"]
            agent_name = channel.split(".")[-1]
            now = time.time()
            _state["active_agents"].add(agent_name)
            _state["agent_last_seen"][agent_name] = now

            # Prune agents not seen for more than 60 seconds
            stale = [n for n, ts in _state["agent_last_seen"].items() if now - ts > 60]
            for n in stale:
                _state["active_agents"].discard(n)
                del _state["agent_last_seen"][n]
                log.warning("agent_stale_removed", agent=n)

            metrics.active_agents.set(len(_state["active_agents"]))
        except Exception as exc:
            log.error("heartbeat_watcher_message_error", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("central_agent_starting")

    _state["http_client"] = httpx.AsyncClient(timeout=httpx.Timeout(2.0))

    try:
        _state["redis"] = Redis.from_url(REDIS_URL, decode_responses=True)
        await _state["redis"].ping()
        log.info("redis_connected", url=REDIS_URL)
    except Exception as exc:
        log.error("redis_connect_failed", error=str(exc))
        if _state.get("redis"):
            await _state["redis"].aclose()
        _state["redis"] = None

    try:
        _state["pg_pool"] = await asyncpg.create_pool(dsn=POSTGRES_DSN, min_size=2, max_size=10)
        log.info("postgres_connected")
    except Exception as exc:
        log.error("postgres_connect_failed", error=str(exc))

    try:
        _state["neo4j_driver"] = AsyncGraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        await asyncio.wait_for(
            _state["neo4j_driver"].verify_connectivity(),
            timeout=5.0,
        )
        log.info("neo4j_connected", uri=NEO4J_URI)
    except Exception as exc:
        log.error("neo4j_connect_failed", error=str(exc))
        if _state.get("neo4j_driver"):
            try:
                await _state["neo4j_driver"].close()
            except Exception as close_exc:
                log.warning("neo4j_driver_close_failed", error=str(close_exc))
        _state["neo4j_driver"] = None

    background_tasks = []
    if _state["redis"]:
        background_tasks.append(asyncio.create_task(_redis_subscriber()))
        background_tasks.append(asyncio.create_task(_heartbeat_watcher()))

    log.info("central_agent_ready")
    yield

    log.info("central_agent_shutting_down")
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

    if _state["http_client"]:
        await _state["http_client"].aclose()
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
        raise HTTPException(status_code=503, detail="Redis unavailable")

    future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
    _state["pending_responses"][request_id] = future

    # Retrieve relevant memories before dispatching (best-effort; never blocks user)
    memory_context = await _fetch_memory_context(body.text, body.session_id)

    payload = json.dumps(
        {
            "request_id": request_id,
            "session_id": body.session_id,
            "text": body.text,
            "memory_context": memory_context,
        }
    )
    try:
        try:
            await asyncio.wait_for(
                _state["redis"].publish("user.input", payload),
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            log.error("publish_timeout", request_id=request_id)
            metrics.requests_total.labels(status="error").inc()
            return InputResponse(request_id=request_id, error="publish timeout")

        log.info("input_published", request_id=request_id, session_id=body.session_id)

        try:
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


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket endpoint — real-time bidirectional chat
# ─────────────────────────────────────────────────────────────────────────────

_SESSION_ID_RE = r"^[a-zA-Z0-9_-]+$"


@app.websocket("/ws/chat")
async def ws_chat(
    ws: WebSocket,
    session_id: str = Query(..., min_length=1, max_length=100, pattern=_SESSION_ID_RE),
):
    await ws.accept()
    # Register this connection
    if session_id not in _state["ws_clients"]:
        _state["ws_clients"][session_id] = set()
    _state["ws_clients"][session_id].add(ws)
    log.info("ws_client_connected", session_id=session_id)

    try:
        while True:
            raw = await ws.receive_json()
            msg_type = raw.get("type")

            if msg_type != "user.message":
                await ws.send_json({"type": "error", "detail": f"unknown type: {msg_type}"})
                continue

            text = (raw.get("text") or "").strip()
            if not text or len(text) > 2_000:
                await ws.send_json({"type": "error", "detail": "text must be 1-2000 chars"})
                continue

            request_id = raw.get("request_id") or str(uuid.uuid4())

            if not _state["redis"]:
                await ws.send_json(
                    {"type": "error", "request_id": request_id, "detail": "Redis unavailable"}
                )
                continue

            start = time.perf_counter()
            future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
            _state["pending_responses"][request_id] = future

            # Send animation.command → talking
            await ws.send_json(
                {"type": "animation.command", "action": "thinking", "request_id": request_id}
            )

            memory_context = await _fetch_memory_context(text, session_id)
            payload = json.dumps(
                {
                    "request_id": request_id,
                    "session_id": session_id,
                    "text": text,
                    "memory_context": memory_context,
                }
            )

            try:
                await asyncio.wait_for(_state["redis"].publish("user.input", payload), timeout=2.0)
            except asyncio.TimeoutError:
                await ws.send_json(
                    {"type": "error", "request_id": request_id, "detail": "publish timeout"}
                )
                _state["pending_responses"].pop(request_id, None)
                metrics.requests_total.labels(status="error").inc()
                continue

            try:
                response_text = await asyncio.wait_for(future, timeout=RESPONSE_TIMEOUT)
                await ws.send_json(
                    {"type": "animation.command", "action": "talking", "request_id": request_id}
                )
                await ws.send_json(
                    {"type": "response.text", "request_id": request_id, "text": response_text}
                )
                await ws.send_json(
                    {"type": "animation.command", "action": "idle", "request_id": request_id}
                )
                metrics.requests_total.labels(status="success").inc()
            except asyncio.TimeoutError:
                await ws.send_json(
                    {"type": "error", "request_id": request_id, "detail": "response timeout"}
                )
                metrics.requests_total.labels(status="timeout").inc()
            finally:
                _state["pending_responses"].pop(request_id, None)
                metrics.latency_seconds.observe(time.perf_counter() - start)

    except WebSocketDisconnect:
        log.info("ws_client_disconnected", session_id=session_id)
    except Exception as exc:
        log.error("ws_error", session_id=session_id, error=str(exc))
    finally:
        _state["ws_clients"].get(session_id, set()).discard(ws)
        if not _state["ws_clients"].get(session_id):
            _state["ws_clients"].pop(session_id, None)
