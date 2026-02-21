"""language-center — NLU/NLG microservice for the Bodhi AI companion.

Responsibilities:
  • Intent recognition & entity extraction  (keyword/pattern-based, Phase 2)
  • Sentiment analysis                       (pattern-based, Phase 2)
  • Response generation                      (template + personality/emotion)
  • Redis pub/sub bridge: user.input → language.response.{request_id}
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as aioredis
import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

from metrics import (
    intent_classified_total,
    language_latency_seconds,
    language_requests_total,
)
from templates import TEMPLATES, valence_to_adjective

load_dotenv()

log = structlog.get_logger()

REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
SERVICE_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Module-level model cache (lazy-loaded on first NLU request)
# ---------------------------------------------------------------------------
_model: Any = None
_tokenizer: Any = None
_model_loaded: bool = False
_model_lock = asyncio.Lock()
_executor = ThreadPoolExecutor(max_workers=2)

# ---------------------------------------------------------------------------
# Intent patterns  (Phase 2: keyword/regex classification)
# ---------------------------------------------------------------------------
_INTENT_PATTERNS: list[tuple[str, list[re.Pattern[str]]]] = [
    (
        "system.shutdown",
        [
            re.compile(r"\b(goodnight|good night|bye|goodbye|shutdown|shut down|sleep|see you)\b", re.I),
        ],
    ),
    (
        "system.status",
        [
            re.compile(r"\b(how are you|how('re| are) you|status|are you ok|feeling|doing)\b", re.I),
        ],
    ),
    (
        "task.create",
        [
            re.compile(r"\b(remind me|set a reminder|create (a )?(task|reminder)|add (a )?(task|reminder)|remember to)\b", re.I),
        ],
    ),
    (
        "task.list",
        [
            re.compile(r"\b(list (my )?(tasks?|reminders?)|what('s| is) on my (list|agenda)|show (me )?(my )?(tasks?|reminders?))\b", re.I),
        ],
    ),
    (
        "skill.execute",
        [
            re.compile(r"\b(run|execute|start|launch|activate|trigger)\b", re.I),
        ],
    ),
    (
        "query.memory",
        [
            re.compile(r"\b(do you remember|remember when|recall|don'?t you remember)\b", re.I),
        ],
    ),
    (
        "query.factual",
        [
            re.compile(r"\b(what is|what are|who is|who are|when did|where is|how does|tell me about|explain|define)\b", re.I),
        ],
    ),
    (
        "chitchat",
        [
            re.compile(r"\b(hi|hello|hey|sup|what'?s up|how'?s it going|hola|howdy|greetings)\b", re.I),
        ],
    ),
]

_SENTIMENT_POSITIVE = re.compile(
    r"\b(great|good|happy|love|excellent|wonderful|fantastic|awesome|nice|glad|joy|pleased|amazing)\b",
    re.I,
)
_SENTIMENT_NEGATIVE = re.compile(
    r"\b(bad|sad|hate|terrible|awful|horrible|angry|upset|frustrated|depressed|annoyed|worried|scared)\b",
    re.I,
)

_DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)\b",
    re.I,
)
_TIME_PATTERN = re.compile(r"\b(\d{1,2}:\d{2}(?:\s*[ap]m)?|\d{1,2}\s*[ap]m)\b", re.I)
_NAME_PATTERN = re.compile(r"\b(?:my name is|i'?m|call me)\s+([A-Z][a-z]+)\b")


# ---------------------------------------------------------------------------
# Model helpers (lazy load)
# ---------------------------------------------------------------------------

def _load_model_sync() -> bool:
    """Load distilbert tokenizer/model synchronously (called in executor)."""
    global _tokenizer, _model, _model_loaded
    try:
        from transformers import pipeline  # noqa: PLC0415

        _model = pipeline(
            "text-classification",
            model="distilbert-base-uncased",
            device=-1,  # CPU — ARM64 / RPi5
            truncation=True,
            max_length=128,
        )
        _model_loaded = True
        log.info("distilbert loaded", status="ok")
        return True
    except Exception as exc:
        log.warning("model_load_failed", error=str(exc))
        _model_loaded = False
        return False


async def _ensure_model() -> None:
    """Lazy-load the model exactly once, thread-safely."""
    global _model_loaded
    async with _model_lock:
        if _model is None:
            await asyncio.get_event_loop().run_in_executor(_executor, _load_model_sync)


# ---------------------------------------------------------------------------
# NLU helpers
# ---------------------------------------------------------------------------

def _classify_intent(text: str) -> tuple[str, float]:
    """Pattern-based intent classification.  Returns (intent, confidence)."""
    for intent, patterns in _INTENT_PATTERNS:
        for pat in patterns:
            if pat.search(text):
                return intent, 0.85
    return "unknown", 0.40


def _extract_entities(text: str) -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []
    for m in _DATE_PATTERN.finditer(text):
        entities.append({"type": "DATE", "value": m.group(0)})
    for m in _TIME_PATTERN.finditer(text):
        entities.append({"type": "TIME", "value": m.group(0)})
    for m in _NAME_PATTERN.finditer(text):
        entities.append({"type": "PERSON", "value": m.group(1)})
    return entities


def _analyse_sentiment(text: str) -> tuple[str, float]:
    pos = len(_SENTIMENT_POSITIVE.findall(text))
    neg = len(_SENTIMENT_NEGATIVE.findall(text))
    total = pos + neg or 1
    if pos > neg:
        return "positive", round(pos / total, 2)
    if neg > pos:
        return "negative", round(neg / total, 2)
    return "neutral", 0.5


# ---------------------------------------------------------------------------
# NLG helpers
# ---------------------------------------------------------------------------

def _personality_tone(personality: dict[str, float]) -> dict[str, Any]:
    """Derive tone modifiers from Big Five scores."""
    extraversion = personality.get("extraversion", 0.5)
    neuroticism = personality.get("neuroticism", 0.5)
    agreeableness = personality.get("agreeableness", 0.5)

    # Warm/longer responses for high extraversion; cautious for high neuroticism
    warmth = min(1.0, extraversion + agreeableness * 0.3)
    caution = neuroticism > 0.6

    return {"warmth": warmth, "caution": caution, "verbose": extraversion > 0.6}


def _select_template(intent: str, personality: dict[str, float]) -> str:
    """Pick a template; prefer later (warmer) templates for high extraversion."""
    pool = TEMPLATES.get(intent, TEMPLATES["unknown"])
    extraversion = personality.get("extraversion", 0.5)
    # High extraversion → bias towards later (richer) templates
    idx = int(extraversion * (len(pool) - 1))
    return pool[idx]


def _render_template(
    template: str,
    *,
    name: str = "friend",
    topic: str = "that",
    task: str = "",
    count: int = 0,
    emotion_adj: str = "good",
) -> str:
    return (
        template.replace("{name}", name)
        .replace("{topic}", topic)
        .replace("{task}", task)
        .replace("{count}", str(count))
        .replace("{emotion_adj}", emotion_adj)
    )


def _generate_response(
    prompt: str,
    intent: str,
    emotion: dict[str, Any],
    personality: dict[str, float],
) -> str:
    valence: float = emotion.get("valence", 0.0)
    emotion_adj = valence_to_adjective(valence)

    # Derive topic from prompt (first noun-ish chunk after a wh-word, or fallback)
    topic_match = re.search(
        r"\b(?:about|of|regarding|is|are|was|were)\s+([a-zA-Z0-9 ]{2,30})", prompt, re.I
    )
    topic = topic_match.group(1).strip() if topic_match else "that"

    tone = _personality_tone(personality)
    template = _select_template(intent, personality)
    text = _render_template(template, topic=topic, emotion_adj=emotion_adj)

    # Cautious suffix for high neuroticism
    if tone["caution"]:
        text += " (Let me know if I got anything wrong.)"

    return text


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class UnderstandRequest(BaseModel):
    text: str
    session_id: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


class UnderstandResponse(BaseModel):
    intent: str
    intent_confidence: float
    entities: list[dict[str, str]]
    sentiment: str
    sentiment_score: float


class EmotionInput(BaseModel):
    valence: float = 0.0
    arousal: float = 0.0
    label: str = "neutral"


class GenerateRequest(BaseModel):
    prompt: str
    intent: str = "chitchat"
    emotion: EmotionInput = Field(default_factory=EmotionInput)
    personality: dict[str, float] = Field(default_factory=dict)
    max_tokens: int = 256


class GenerateResponse(BaseModel):
    text: str
    tokens_used: int
    latency_ms: int


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    label: str
    score: float


# ---------------------------------------------------------------------------
# Redis subscriber
# ---------------------------------------------------------------------------

async def _redis_subscriber(redis_client: aioredis.Redis) -> None:
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("user.input")
    log.info("redis_subscribed", channel="user.input")
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            payload: dict[str, Any] = json.loads(message["data"])
            text: str = payload.get("text", "")
            request_id: str = payload.get("request_id", "unknown")
            session_id: str = payload.get("session_id", "")

            intent, confidence = _classify_intent(text)
            entities = _extract_entities(text)
            sentiment_label, sentiment_score = _analyse_sentiment(text)

            result = {
                "request_id": request_id,
                "session_id": session_id,
                "intent": intent,
                "intent_confidence": confidence,
                "entities": entities,
                "sentiment": sentiment_label,
                "sentiment_score": sentiment_score,
            }
            channel = f"language.response.{request_id}"
            await redis_client.publish(channel, json.dumps(result))
            log.info("published_response", channel=channel, intent=intent)
        except Exception as exc:
            log.error("redis_message_error", error=str(exc))


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client: aioredis.Redis | None = None
    subscriber_task: asyncio.Task[None] | None = None
    try:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        app.state.redis = redis_client
        subscriber_task = asyncio.create_task(_redis_subscriber(redis_client))
        log.info("language_center_started", redis=REDIS_URL)
        yield
    finally:
        if subscriber_task:
            subscriber_task.cancel()
            try:
                await subscriber_task
            except asyncio.CancelledError:
                pass
        if redis_client:
            await redis_client.aclose()
        _executor.shutdown(wait=False)
        log.info("language_center_stopped")


app = FastAPI(title="language-center", version=SERVICE_VERSION, lifespan=lifespan)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, Any]:
    language_requests_total.labels(endpoint="health").inc()
    return {
        "status": "healthy",
        "agent": "language-center",
        "version": SERVICE_VERSION,
        "model_loaded": _model_loaded,
    }


@app.post("/understand", response_model=UnderstandResponse)
async def understand(req: UnderstandRequest) -> UnderstandResponse:
    start = time.perf_counter()
    language_requests_total.labels(endpoint="understand").inc()

    # Lazy-load model (non-blocking)
    await _ensure_model()

    intent, confidence = _classify_intent(req.text)
    entities = _extract_entities(req.text)
    sentiment_label, sentiment_score = _analyse_sentiment(req.text)

    intent_classified_total.labels(intent=intent).inc()
    language_latency_seconds.labels(endpoint="understand").observe(time.perf_counter() - start)

    return UnderstandResponse(
        intent=intent,
        intent_confidence=confidence,
        entities=entities,
        sentiment=sentiment_label,
        sentiment_score=sentiment_score,
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    start = time.perf_counter()
    language_requests_total.labels(endpoint="generate").inc()

    emotion_dict = req.emotion.model_dump()
    personality = req.personality

    # Run template rendering in executor to avoid blocking if extended later
    loop = asyncio.get_event_loop()
    text: str = await loop.run_in_executor(
        _executor,
        _generate_response,
        req.prompt,
        req.intent,
        emotion_dict,
        personality,
    )

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    tokens_used = len(text.split())
    language_latency_seconds.labels(endpoint="generate").observe(time.perf_counter() - start)

    return GenerateResponse(text=text, tokens_used=tokens_used, latency_ms=elapsed_ms)


@app.post("/sentiment", response_model=SentimentResponse)
async def sentiment(req: SentimentRequest) -> SentimentResponse:
    start = time.perf_counter()
    language_requests_total.labels(endpoint="sentiment").inc()

    label, score = _analyse_sentiment(req.text)

    language_latency_seconds.labels(endpoint="sentiment").observe(time.perf_counter() - start)
    return SentimentResponse(label=label, score=score)


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=False)
