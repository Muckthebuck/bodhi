from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
import metrics
import redis.asyncio as aioredis
import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

log = structlog.get_logger()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
POSTGRES_DSN = (
    os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_DSN")
    or f"postgresql://bodhi:{os.getenv('POSTGRES_PASSWORD', '')}@postgres:5432/bodhi"
)
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = "memories"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_DIM = 384
WORKING_MEMORY_TTL = 3600
CONSOLIDATION_INTERVAL = 1800
_CONSOLIDATION_LOCK_KEY = "lock:consolidation"
_CONSOLIDATION_LOCK_TTL = CONSOLIDATION_INTERVAL + 300  # expire if service dies mid-run

_redis: aioredis.Redis | None = None
_pg_pool: asyncpg.Pool | None = None
_qdrant: AsyncQdrantClient | None = None
_embedder = None
_embedder_lock = asyncio.Lock()


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


async def _embed(text: str) -> list[float]:
    loop = asyncio.get_event_loop()
    async with _embedder_lock:
        embedder = await loop.run_in_executor(None, _get_embedder)
    vector = await loop.run_in_executor(None, lambda: embedder.encode(text).tolist())
    return vector


async def _ensure_qdrant_collection() -> None:
    try:
        await _qdrant.get_collection(QDRANT_COLLECTION)
    except (UnexpectedResponse, Exception):
        await _qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        log.info("qdrant_collection_created", collection=QDRANT_COLLECTION)


async def _subscribe_user_input() -> None:
    pubsub = _redis.pubsub()
    await pubsub.subscribe("user.input")
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            content = data.get("content") or data.get("text") or str(data)
            session_id = data.get("session_id", "")
            key = f"working_memory:{uuid.uuid4()}"
            payload = json.dumps(
                {
                    "content": content,
                    "memory_type": "working",
                    "importance": 0.5,
                    "session_id": session_id,
                    "metadata": {},
                }
            )
            await _redis.setex(key, WORKING_MEMORY_TTL, payload)
            await _redis.publish(
                "memory.stored", json.dumps({"key": key, "memory_type": "working"})
            )
            metrics.memory_stored_total.labels(memory_type="working").inc()
        except Exception as exc:
            log.warning("user_input_store_failed", error=str(exc))


async def _consolidation_loop() -> None:
    while True:
        await asyncio.sleep(CONSOLIDATION_INTERVAL)
        await _run_consolidation()


async def _run_consolidation() -> None:
    # Redis distributed lock — safe across service restarts (asyncio.Lock is not)
    acquired = await _redis.set(_CONSOLIDATION_LOCK_KEY, "1", nx=True, ex=_CONSOLIDATION_LOCK_TTL)
    if not acquired:
        log.info("consolidation_already_running_skipped")
        return
    try:
        t0 = time.perf_counter()
        consolidated = 0
        try:
            # SCAN is non-blocking; KEYS would freeze Redis for all services.
            # Overall timeout prevents the lock being held if Redis stalls.
            keys: list[str] = []
            try:
                async with asyncio.timeout(60):
                    cursor = 0
                    max_iterations = 500
                    iteration = 0
                    while True:
                        cursor, partial = await _redis.scan(
                            cursor, match="working_memory:*", count=1000
                        )
                        keys.extend(partial)
                        iteration += 1
                        if cursor == 0 or iteration >= max_iterations:
                            break
                    if iteration >= max_iterations:
                        log.error(
                            "consolidation_scan_truncated_data_loss_possible", keys_found=len(keys)
                        )
            except asyncio.TimeoutError:
                log.warning("consolidation_scan_timeout", keys_found=len(keys))

            # Deduplicate — Redis SCAN can return the same key twice if keyspace changes mid-scan
            keys = list(set(keys))

            for key in keys:
                raw = await _redis.get(key)
                if raw is None:
                    continue
                try:
                    entry = json.loads(raw)
                except Exception:
                    continue
                if entry.get("importance", 0) <= 0.7:
                    continue

                # Store episodic first; on failure keep working memory for next run.
                try:
                    await _store_episodic(
                        content=entry["content"],
                        session_id=entry.get("session_id", ""),
                        importance=entry.get("importance", 0.5),
                        metadata=entry.get("metadata", {}),
                    )
                except Exception as exc:
                    log.warning("consolidation_episodic_failed", key=key, error=str(exc))
                    continue  # keep working memory; retry on next consolidation run

                # Episodic succeeded; attempt semantic. Failure is non-fatal — still delete
                # the working memory key to prevent duplicate episodic inserts.
                try:
                    await _store_semantic(
                        content=entry["content"],
                        session_id=entry.get("session_id", ""),
                        importance=entry.get("importance", 0.5),
                        metadata=entry.get("metadata", {}),
                    )
                except Exception as exc:
                    log.warning("consolidation_semantic_failed", key=key, error=str(exc))
                    # Fall through to delete — episodic is the source of truth

                # Remove from working set. On delete failure set a short TTL so the key
                # expires before the next 30-min consolidation run.
                try:
                    await _redis.delete(key)
                except Exception as del_exc:
                    log.warning(
                        "consolidation_delete_failed_setting_expiry", key=key, error=str(del_exc)
                    )
                    try:
                        await _redis.expire(key, 300)  # 5 min << 30 min interval
                    except Exception:
                        pass
                consolidated += 1
            metrics.consolidation_runs_total.inc()
            metrics.memory_latency_seconds.labels(operation="consolidation").observe(
                time.perf_counter() - t0
            )
            log.info("consolidation_complete", consolidated=consolidated)
        except Exception as exc:
            log.error("consolidation_failed", error=str(exc))
    finally:
        await _redis.delete(_CONSOLIDATION_LOCK_KEY)


async def _store_episodic(
    content: str,
    session_id: str,
    importance: float,
    metadata: dict,
) -> str:
    async with asyncio.timeout(5.0):
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
            INSERT INTO memories (session_id, content, memory_type, importance, metadata)
            VALUES ($1, $2, 'episodic', $3, $4)
            RETURNING memory_id
            """,
                session_id,
                content,
                importance,
                json.dumps(metadata),
            )
    memory_id = str(row["memory_id"])
    await _redis.publish(
        "memory.stored",
        json.dumps({"memory_id": memory_id, "memory_type": "episodic"}),
    )
    return memory_id


async def _store_semantic(
    content: str,
    session_id: str,
    importance: float,
    metadata: dict,
) -> str:
    point_id = str(uuid.uuid4())
    try:
        vector = await _embed(content)
        await _qdrant.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "content": content,
                        "session_id": session_id,
                        "importance": importance,
                        "memory_type": "semantic",
                        "metadata": metadata,
                    },
                )
            ],
        )
        await _redis.publish(
            "memory.stored",
            json.dumps({"point_id": point_id, "memory_type": "semantic"}),
        )
    except Exception as exc:
        log.warning("qdrant_store_failed_fallback_postgres", error=str(exc))
        # Fall back to Postgres with memory_type='semantic' so the API response
        # and DB stay consistent (Qdrant is the source of truth for vectors, but
        # Postgres holds the record until Qdrant is available again).
        async with asyncio.timeout(5.0):
            async with _pg_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO memories (session_id, content, memory_type, importance, metadata)
                    VALUES ($1, $2, 'semantic', $3, $4)
                    RETURNING memory_id
                    """,
                    session_id,
                    content,
                    importance,
                    json.dumps(metadata),
                )
        memory_id = str(row["memory_id"])
        await _redis.publish(
            "memory.stored",
            json.dumps({"memory_id": memory_id, "memory_type": "semantic"}),
        )
        return memory_id
    return point_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis, _pg_pool, _qdrant

    _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    _pg_pool = await asyncpg.create_pool(POSTGRES_DSN, min_size=2, max_size=10)
    _qdrant = AsyncQdrantClient(url=QDRANT_URL)

    await _ensure_qdrant_collection()

    consolidation_task = asyncio.create_task(_consolidation_loop())
    subscriber_task = asyncio.create_task(_subscribe_user_input())

    log.info("memory_manager_started", port=8001)
    yield

    consolidation_task.cancel()
    subscriber_task.cancel()
    await asyncio.gather(consolidation_task, subscriber_task, return_exceptions=True)
    await _redis.aclose()
    await _pg_pool.close()
    await _qdrant.close()


app = FastAPI(title="memory-manager", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class StoreRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)
    memory_type: str = Field(pattern="^(episodic|semantic|working)$")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    session_id: str = Field(default="", pattern=r"^[a-zA-Z0-9_-]*$")
    metadata: dict[str, Any] = Field(default_factory=dict)


class StoreResponse(BaseModel):
    id: str
    memory_type: str


class RetrieveRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=100)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    memory_type: str | None = None
    session_id: str = Field(default="", pattern=r"^[a-zA-Z0-9_-]*$")


class MemoryResult(BaseModel):
    id: str
    content: str
    similarity: float
    session_id: str
    importance: float
    metadata: dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "agent": "memory-manager", "version": "0.1.0"}


@app.post("/store", response_model=StoreResponse)
async def store_memory(req: StoreRequest) -> StoreResponse:
    t0 = time.perf_counter()
    try:
        if req.memory_type == "working":
            key = f"working_memory:{uuid.uuid4()}"
            payload = req.model_dump_json()
            await _redis.setex(key, WORKING_MEMORY_TTL, payload)
            await _redis.publish(
                "memory.stored",
                json.dumps({"key": key, "memory_type": "working"}),
            )
            result_id = key

        elif req.memory_type == "episodic":
            result_id = await _store_episodic(
                content=req.content,
                session_id=req.session_id,
                importance=req.importance,
                metadata=req.metadata,
            )

        else:  # semantic
            result_id = await _store_semantic(
                content=req.content,
                session_id=req.session_id,
                importance=req.importance,
                metadata=req.metadata,
            )

        metrics.memory_stored_total.labels(memory_type=req.memory_type).inc()
        metrics.memory_latency_seconds.labels(operation="store").observe(time.perf_counter() - t0)
        return StoreResponse(id=result_id, memory_type=req.memory_type)

    except Exception as exc:
        log.error("store_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/retrieve", response_model=list[MemoryResult])
async def retrieve_memories(req: RetrieveRequest) -> list[MemoryResult]:
    t0 = time.perf_counter()
    try:
        vector = await _embed(req.query)
        search_filter = None
        must_conditions: list[Any] = []
        if req.memory_type and req.memory_type != "all":
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            must_conditions.append(
                FieldCondition(key="memory_type", match=MatchValue(value=req.memory_type))
            )
        if req.session_id:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            must_conditions.append(
                FieldCondition(key="session_id", match=MatchValue(value=req.session_id))
            )
        if must_conditions:
            from qdrant_client.models import Filter

            search_filter = Filter(must=must_conditions)

        hits = await _qdrant.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=vector,
            limit=req.limit,
            score_threshold=req.min_score,
            query_filter=search_filter,
        )

        metrics.memory_retrieved_total.inc()
        metrics.memory_latency_seconds.labels(operation="retrieve").observe(
            time.perf_counter() - t0
        )

        results = [
            MemoryResult(
                id=str(hit.id),
                content=hit.payload.get("content", ""),
                similarity=hit.score,
                session_id=hit.payload.get("session_id", ""),
                importance=hit.payload.get("importance", 0.5),
                metadata=hit.payload.get("metadata", {}),
            )
            for hit in hits
        ]

        # Increment access_count for returned memories (best-effort)
        if results and _pg_pool:
            hit_ids = [r.id for r in results]
            try:
                async with asyncio.timeout(2.0):
                    async with _pg_pool.acquire() as conn:
                        await conn.execute(
                            """
                            UPDATE memories
                               SET access_count = access_count + 1,
                                   last_accessed = NOW()
                             WHERE memory_id = ANY($1::uuid[])
                            """,
                            hit_ids,
                        )
            except Exception as exc:
                log.warning("access_count_update_failed", error=str(exc))

        return results
    except Exception as exc:
        log.error("retrieve_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/recent", response_model=list[dict])
async def recent_memories(limit: int = 10, session_id: str | None = None) -> list[dict]:
    try:
        async with asyncio.timeout(5.0):
            async with _pg_pool.acquire() as conn:
                if session_id:
                    rows = await conn.fetch(
                        """
                        SELECT memory_id, session_id, content, memory_type, importance,
                               access_count, last_accessed, created_at, metadata
                        FROM memories
                        WHERE session_id = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        session_id,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT memory_id, session_id, content, memory_type, importance,
                               access_count, last_accessed, created_at, metadata
                        FROM memories
                        ORDER BY created_at DESC
                        LIMIT $1
                        """,
                        limit,
                    )
        return [dict(row) for row in rows]
    except Exception as exc:
        log.error("recent_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/consolidate")
async def consolidate() -> dict:
    await _run_consolidation()
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
