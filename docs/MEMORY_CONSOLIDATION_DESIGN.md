# Memory Consolidation System - Detailed Design

**Date:** 2026-02-14  
**Status:** Detailed Design Complete  
**Dependencies:** Redis, Qdrant, PostgreSQL (pgvector), Sentence-BERT mini

---

## 1. Architecture Overview

### 1.1 Three-Tier Memory System

```
┌────────────────────────────────────────────────────────────────┐
│                    SENSORY INPUT STREAM                        │
│         (User interaction, screen, audio, sensors)             │
└───────────────────────┬────────────────────────────────────────┘
                        │ Write <5ms
                        ▼
            ┌───────────────────────────┐
            │   WORKING MEMORY (Redis)  │
            │   Capacity: ~50-100MB     │
            │   TTL: 5-60 minutes       │
            │   (Context-adaptive)      │
            └────────┬──────────────────┘
                     │
                     │ [Real-time Filter]
                     │ Importance ≥ 0.5
                     ▼
            ┌───────────────────────────┐
            │  SHORT-TERM MEMORY        │
            │  (Qdrant Vector DB)       │
            │  Capacity: ~200MB         │
            │  Retention: 7-30 days     │
            │  Semantic search <50ms    │
            └────────┬──────────────────┘
                     │
                     │ [Consolidation Worker]
                     │ Importance ≥ 0.7 (sleep cycles)
                     │ With compression
                     ▼
            ┌───────────────────────────┐
            │  LONG-TERM MEMORY         │
            │  (PostgreSQL + pgvector)  │
            │  Capacity: GB scale       │
            │  Retention: Permanent     │
            │  Compressed storage       │
            └───────────────────────────┘
```

### 1.2 Memory Flow Rates

| Tier | Write Rate | Read Rate | Typical Latency | Storage |
|------|-----------|-----------|-----------------|---------|
| Working (Redis) | 100-1000 events/min | 10-50 queries/min | <5ms | 50-100MB |
| Short-term (Qdrant) | 10-50 memories/min | 5-20 queries/min | <50ms | 200MB |
| Long-term (PostgreSQL) | 1-10 memories/hour | 1-5 queries/hour | <200ms | GB scale |

---

## 2. Redis Working Memory Schema

### 2.1 Adaptive TTL Strategy

```python
def calculate_adaptive_ttl(event: dict, context: dict) -> int:
    """
    Dynamic TTL based on event importance and context.
    
    Range: 300-3600 seconds (5-60 minutes)
    
    Factors:
    - High importance → longer TTL
    - Active conversation → shorter TTL (will be refreshed)
    - Idle periods → longer TTL (preserve context)
    """
    base_ttl = 600  # 10 minutes default
    
    importance = event.get('importance', 0.5)
    is_active = context.get('user_active', False)
    
    # Importance multiplier (0.5-2.0x)
    importance_factor = 0.5 + (importance * 1.5)
    
    # Activity modifier
    if is_active:
        activity_factor = 0.8  # Shorter TTL, will refresh soon
    else:
        activity_factor = 1.5  # Longer TTL, preserve context
    
    ttl = int(base_ttl * importance_factor * activity_factor)
    
    # Clamp to range [300, 3600]
    return max(300, min(3600, ttl))
```

### 2.2 Redis Data Structures

```redis
# 1. Conversation context (hash with sliding TTL)
conversation:current {
  "session_id": "session_abc123",
  "user_id": "user_001",
  "last_message": "Can you help me organize my emails?",
  "turn_count": 5,
  "active_skills": ["email_categorization", "inbox_management"],
  "emotion_state": {"valence": 0.6, "arousal": 0.4},
  "last_update": 1707882800
}
TTL: Refreshed on each interaction, expires after 10-60 min of inactivity

# 2. Event stream (sorted set, scored by timestamp)
events:stream
  1707882800.123 -> {
    "type": "user_message",
    "content": "Organize my emails",
    "importance": 0.8,
    "embedding_id": "emb_001"  # Reference to cached embedding
  }
  1707882801.456 -> {
    "type": "skill_execution",
    "skill": "email_categorization",
    "success": true,
    "importance": 0.7
  }
TTL: Adaptive per event (5-60 minutes)

# 3. Active perceptions (hash, constantly updating)
perception:screen {
  "active_app": "Thunderbird",
  "window_title": "Inbox (127 unread)",
  "visible_objects": ["email_list", "compose_button"],
  "cursor_position": [450, 300],
  "last_frame_timestamp": 1707882802
}
TTL: 60 seconds (rapid refresh, short-lived)

perception:audio {
  "is_speaking": false,
  "ambient_noise_level": 0.3,
  "last_speech_timestamp": 1707882785
}
TTL: 60 seconds

# 4. Embedding cache (hash, avoid recomputing)
embeddings:cache {
  "emb_001": [0.1, 0.3, ..., 0.5],  # 384D vector
  "emb_002": [0.2, 0.1, ..., 0.7]
}
TTL: 600 seconds (10 minutes)

# 5. Consolidation queue (list, persistent)
consolidation:queue [
  "event_id_1", "event_id_2", "event_id_3"
]
No TTL (processed by worker, then removed)

# 6. Importance scores (sorted set for fast filtering)
importance:scores
  0.95 -> event_id_1
  0.87 -> event_id_2
  0.52 -> event_id_3
TTL: Synced with event TTL
```

### 2.3 Redis Memory Budget

```
Conversation context:     ~10 KB
Event stream (1000 events): ~2 MB
Perceptions:              ~50 KB
Embedding cache (500):    ~750 KB (500 × 384 × 4 bytes)
Consolidation queue:      ~50 KB
Importance scores:        ~100 KB
Overhead (Redis):         ~20 MB
─────────────────────────────────
Total:                    ~73 MB
Peak (with buffer):       ~100 MB
```

---

## 3. Importance Scoring (Refined)

### 3.1 Core Algorithm

```python
import math
import numpy as np
from typing import Dict, Any

def calculate_importance(event: Dict[str, Any], context: Dict[str, Any]) -> float:
    """
    Multi-factor importance scoring inspired by human memory formation.
    
    Neuroscience principles:
    - Emotional arousal enhances memory consolidation (amygdala → hippocampus)
    - Novelty triggers dopamine → stronger encoding
    - User agency (self-initiated) increases salience
    - Social interactions have innate priority
    - Repetition without new information → habituation (lower importance)
    
    Returns: 0.0-1.0 importance score
    """
    
    # Extract features
    user_initiated = 1.0 if event.get('triggered_by') == 'user' else 0.3
    
    emotion_data = event.get('emotion', {})
    emotional_intensity = abs(emotion_data.get('valence', 0.0)) + emotion_data.get('arousal', 0.0)
    emotional_intensity = min(emotional_intensity / 2.0, 1.0)  # Normalize to [0,1]
    
    novelty = _compute_novelty(event, context)
    utility = _predict_utility(event, context)
    social = 1.0 if event.get('participants', []) else 0.2
    
    time_diff = context['current_time'] - event['timestamp']
    recency = math.exp(-time_diff / 300)  # 5-minute half-life
    
    # Weighted combination
    weights = {
        'user_initiated': 0.25,
        'emotional': 0.20,
        'novelty': 0.20,
        'utility': 0.15,
        'social': 0.10,
        'recency': 0.10,
    }
    
    base_score = (
        weights['user_initiated'] * user_initiated +
        weights['emotional'] * emotional_intensity +
        weights['novelty'] * novelty +
        weights['utility'] * utility +
        weights['social'] * social +
        weights['recency'] * recency
    )
    
    # Modifiers
    
    # 1. User feedback override (explicit thumbs up/down)
    user_feedback = event.get('user_feedback')
    if user_feedback is not None:
        if user_feedback > 0:
            base_score = max(base_score, 0.8)  # Positive → min 0.8
        else:
            base_score = min(base_score, 0.3)  # Negative → max 0.3
    
    # 2. Skill execution success boost
    if event.get('type') == 'skill_execution' and event.get('success'):
        base_score *= 1.2
    
    # 3. Redundancy penalty (similar to recent memories)
    similarity = _check_redundancy(event, context['recent_memories'])
    if similarity > 0.85:
        base_score *= 0.5  # 50% penalty for near-duplicates
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, base_score))

def _compute_novelty(event: Dict[str, Any], context: Dict[str, Any]) -> float:
    """
    Novelty = dissimilarity to recent memories.
    Uses cached embeddings from Redis for speed.
    """
    recent_memories = context.get('recent_memories', [])
    
    if not recent_memories:
        return 1.0  # First memory is always novel
    
    # Get or compute embedding
    event_embedding = _get_cached_embedding(event['content'])
    
    # Compare to recent embeddings (last 50)
    similarities = []
    for mem in recent_memories[-50:]:
        mem_embedding = _get_cached_embedding(mem['content'])
        sim = np.dot(event_embedding, mem_embedding)  # Cosine similarity (normalized vectors)
        similarities.append(sim)
    
    max_similarity = max(similarities) if similarities else 0.0
    return 1.0 - max_similarity  # Novelty = 1 - max_similarity

def _predict_utility(event: Dict[str, Any], context: Dict[str, Any]) -> float:
    """
    Predict future utility based on event type and user patterns.
    
    TODO: Can be replaced with learned model (e.g., predict retrieval probability)
    """
    event_type = event['type']
    
    # Heuristic utility map
    utility_map = {
        'user_message': 0.8,
        'skill_execution': 0.75,
        'preference_update': 0.9,
        'user_feedback': 0.85,
        'screen_activity': 0.4,
        'audio_input': 0.3,
        'system_event': 0.2,
    }
    
    base_utility = utility_map.get(event_type, 0.5)
    
    # Boost if related to current task
    if context.get('active_task'):
        task_keywords = context['active_task'].lower().split()
        event_text = event.get('content', '').lower()
        if any(kw in event_text for kw in task_keywords):
            base_utility *= 1.3
    
    return min(base_utility, 1.0)

def _check_redundancy(event: Dict[str, Any], recent_memories: list) -> float:
    """Check if event is redundant (very similar to recent memory)."""
    if not recent_memories:
        return 0.0
    
    event_embedding = _get_cached_embedding(event['content'])
    
    # Only check last 20 memories (most recent)
    similarities = []
    for mem in recent_memories[-20:]:
        mem_embedding = _get_cached_embedding(mem['content'])
        sim = np.dot(event_embedding, mem_embedding)
        similarities.append(sim)
    
    return max(similarities) if similarities else 0.0
```

### 3.2 Embedding Generation (Sentence-BERT Mini)

```python
from sentence_transformers import SentenceTransformer
import hashlib

class EmbeddingGenerator:
    """
    Lightweight embedding model for semantic similarity.
    Model: all-MiniLM-L6-v2 (22MB, 384D embeddings)
    """
    
    def __init__(self, model_name="all-MiniLM-L6-v2", redis_client=None):
        self.model = SentenceTransformer(model_name)
        self.redis = redis_client
        self.cache_ttl = 600  # 10 minutes
    
    def encode(self, text: str) -> np.ndarray:
        """Generate embedding with Redis caching."""
        
        # Check cache first
        cache_key = self._hash_text(text)
        
        if self.redis:
            cached = self.redis.hget('embeddings:cache', cache_key)
            if cached:
                return np.frombuffer(cached, dtype=np.float32)
        
        # Compute embedding
        embedding = self.model.encode(text, normalize_embeddings=True)
        
        # Cache for reuse
        if self.redis:
            self.redis.hset('embeddings:cache', cache_key, embedding.tobytes())
            self.redis.expire('embeddings:cache', self.cache_ttl)
        
        return embedding
    
    def _hash_text(self, text: str) -> str:
        """Generate deterministic hash for caching."""
        return hashlib.md5(text.encode()).hexdigest()[:16]
```

---

## 4. Consolidation Worker (Hippocampus)

### 4.1 Hybrid Consolidation Strategy

```python
import asyncio
import time
import json
from enum import Enum

class ConsolidationMode(Enum):
    LIGHT = "light"      # Opportunistic (idle time)
    DEEP = "deep"        # Scheduled (sleep cycles)
    EMERGENCY = "emergency"  # Memory pressure

class MemoryConsolidationWorker:
    """
    Brain-inspired memory consolidation system.
    Runs in background, triggered by:
    1. Light: User idle for 15+ minutes
    2. Deep: Scheduled sleep cycle (e.g., 3am daily)
    3. Emergency: Redis memory usage > 90%
    """
    
    def __init__(self, redis_client, qdrant_client, pg_conn, embedding_gen):
        self.redis = redis_client
        self.qdrant = qdrant_client
        self.pg = pg_conn
        self.embedding_gen = embedding_gen
        
        # Thresholds
        self.working_to_shortterm_threshold = 0.5
        self.shortterm_to_longterm_threshold = 0.7
        
        # State
        self.running = False
        self.last_consolidation = 0
    
    async def start(self):
        """Start background consolidation loops."""
        self.running = True
        
        # Light consolidation loop (opportunistic)
        asyncio.create_task(self._light_consolidation_loop())
        
        # Deep consolidation loop (scheduled)
        asyncio.create_task(self._deep_consolidation_loop())
        
        # Emergency consolidation (memory pressure)
        asyncio.create_task(self._monitor_memory_pressure())
    
    async def _light_consolidation_loop(self):
        """Run light consolidation when user idle."""
        while self.running:
            await asyncio.sleep(60)  # Check every minute
            
            # Check if user idle
            last_activity = self.redis.get('user:last_activity')
            if last_activity:
                idle_time = time.time() - float(last_activity)
                
                if idle_time > 900:  # 15 minutes idle
                    print("[Consolidation] Light cycle triggered (idle)")
                    await self._consolidate(mode=ConsolidationMode.LIGHT)
    
    async def _deep_consolidation_loop(self):
        """Run deep consolidation during sleep hours."""
        while self.running:
            # Check if sleep time (configured per user)
            sleep_start = self._get_user_sleep_time()
            current_hour = time.localtime().tm_hour
            
            if current_hour == sleep_start:
                print("[Consolidation] Deep cycle triggered (sleep)")
                await self._consolidate(mode=ConsolidationMode.DEEP)
                await asyncio.sleep(3600)  # Run once per hour max
            else:
                await asyncio.sleep(600)  # Check every 10 minutes
    
    async def _monitor_memory_pressure(self):
        """Emergency consolidation if Redis memory high."""
        while self.running:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            info = self.redis.info('memory')
            used_memory_mb = info['used_memory'] / (1024 * 1024)
            
            if used_memory_mb > 90:  # 90MB threshold (out of 100MB budget)
                print(f"[Consolidation] EMERGENCY: Redis memory at {used_memory_mb:.1f}MB")
                await self._consolidate(mode=ConsolidationMode.EMERGENCY)
    
    async def _consolidate(self, mode: ConsolidationMode):
        """
        Main consolidation logic.
        
        Light mode: Redis → Qdrant only
        Deep mode: Full pipeline (Redis → Qdrant → PostgreSQL + forgetting + optimization)
        Emergency mode: Aggressive Redis → Qdrant, prune low-importance
        """
        start_time = time.time()
        
        print(f"[Consolidation] Starting {mode.value} consolidation...")
        
        # Phase 1: Working → Short-term (always)
        stats_phase1 = await self._consolidate_working_to_shortterm(mode)
        
        # Phase 2: Short-term → Long-term (deep mode only)
        stats_phase2 = {}
        if mode == ConsolidationMode.DEEP:
            stats_phase2 = await self._consolidate_shortterm_to_longterm()
        
        # Phase 3: Apply forgetting curve (deep mode only)
        stats_phase3 = {}
        if mode == ConsolidationMode.DEEP:
            stats_phase3 = await self._apply_forgetting_curve()
        
        # Phase 4: Optimize storage (deep mode only)
        if mode == ConsolidationMode.DEEP:
            await self._optimize_storage()
        
        elapsed = time.time() - start_time
        self.last_consolidation = time.time()
        
        print(f"[Consolidation] {mode.value} cycle complete in {elapsed:.2f}s")
        print(f"  Phase 1 (Redis→Qdrant): {stats_phase1.get('moved', 0)} memories")
        if stats_phase2:
            print(f"  Phase 2 (Qdrant→PG): {stats_phase2.get('moved', 0)} memories")
        if stats_phase3:
            print(f"  Phase 3 (Forgetting): {stats_phase3.get('deleted', 0)} deleted, {stats_phase3.get('decayed', 0)} decayed")
    
    async def _consolidate_working_to_shortterm(self, mode: ConsolidationMode) -> dict:
        """Move important memories from Redis to Qdrant."""
        
        # Fetch events from Redis stream
        events = self.redis.zrange('events:stream', 0, -1, withscores=True)
        
        if not events:
            return {'moved': 0}
        
        moved_count = 0
        compressed_size = 0
        original_size = 0
        
        for event_json, timestamp in events:
            event = json.loads(event_json)
            original_size += len(event_json)
            
            # Importance check
            importance = event.get('importance', 0.0)
            
            # Emergency mode: lower threshold
            threshold = 0.3 if mode == ConsolidationMode.EMERGENCY else self.working_to_shortterm_threshold
            
            if importance >= threshold:
                # Generate embedding (cached if possible)
                embedding = self.embedding_gen.encode(event['content'])
                
                # Compress content for storage
                compressed_content = self._compress_event(event)
                compressed_size += len(json.dumps(compressed_content))
                
                # Store in Qdrant
                point_id = str(uuid.uuid4())
                self.qdrant.upsert(
                    collection_name="episodic_memory",
                    points=[{
                        "id": point_id,
                        "vector": embedding.tolist(),
                        "payload": {
                            "timestamp": timestamp,
                            "content": compressed_content['content'],
                            "type": event['type'],
                            "importance": importance,
                            "emotion": event.get('emotion', {}),
                            "participants": event.get('participants', []),
                            "context_summary": compressed_content.get('context_summary', ''),
                            "consolidated_at": time.time(),
                            "access_count": 0,
                        }
                    }]
                )
                
                moved_count += 1
        
        # Clear processed events from Redis
        self.redis.delete('events:stream')
        
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        return {
            'moved': moved_count,
            'compression_ratio': compression_ratio
        }
    
    def _compress_event(self, event: dict) -> dict:
        """
        Compress event for storage (lossy compression).
        
        Strategies:
        - Summarize long text (keep first/last sentences + keywords)
        - Discard low-value metadata
        - Quantize numerical values
        """
        content = event.get('content', '')
        
        # Summarize if long (>200 chars)
        if len(content) > 200:
            # Extract sentences
            sentences = content.split('. ')
            if len(sentences) > 3:
                # Keep first + last + middle
                compressed_text = '. '.join([
                    sentences[0],
                    sentences[len(sentences)//2],
                    sentences[-1]
                ])
            else:
                compressed_text = content[:200] + '...'
        else:
            compressed_text = content
        
        # Context summarization
        context = event.get('context', {})
        context_summary = {
            'app': context.get('app'),
            'screen_region': context.get('screen_region', [0, 0, 100, 100]),
        }
        
        return {
            'content': compressed_text,
            'context_summary': context_summary
        }
    
    async def _consolidate_shortterm_to_longterm(self) -> dict:
        """Move high-importance memories from Qdrant to PostgreSQL."""
        
        # Query high-importance memories
        results = self.qdrant.scroll(
            collection_name="episodic_memory",
            scroll_filter={
                "must": [
                    {"key": "importance", "range": {"gte": self.shortterm_to_longterm_threshold}}
                ]
            },
            limit=500  # Batch size
        )
        
        if not results[0]:
            return {'moved': 0}
        
        cursor = self.pg.cursor()
        moved_count = 0
        
        for point in results[0]:
            payload = point.payload
            
            # Further compression for long-term storage
            # Store only essential fields + embedding
            cursor.execute("""
                INSERT INTO long_term_memories 
                (id, timestamp, content, memory_type, importance, 
                 emotion, participants, context_summary, embedding, 
                 access_count, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    access_count = long_term_memories.access_count + 1,
                    importance = EXCLUDED.importance
            """, (
                point.id,
                payload['timestamp'],
                payload['content'],
                payload['type'],
                payload['importance'],
                json.dumps(payload.get('emotion', {})),
                payload.get('participants', []),
                json.dumps(payload.get('context_summary', {})),
                point.vector,  # pgvector
                payload.get('access_count', 0)
            ))
            
            moved_count += 1
        
        self.pg.commit()
        
        return {'moved': moved_count}
    
    async def _apply_forgetting_curve(self) -> dict:
        """
        Ebbinghaus forgetting curve with probabilistic deletion.
        
        Decay formula: R(t) = e^(-t/S)
        where R = retention, t = time since consolidation, S = memory strength
        
        Probabilistic deletion:
        - Importance < 0.1: 90% chance of deletion
        - Importance 0.1-0.2: 50% chance of deletion
        - Importance 0.2-0.3: 20% chance of deletion
        - Importance > 0.3: No deletion, just decay
        """
        
        current_time = time.time()
        deleted_count = 0
        decayed_count = 0
        
        # Scroll through all memories in Qdrant
        offset = None
        while True:
            results = self.qdrant.scroll(
                collection_name="episodic_memory",
                limit=100,
                offset=offset
            )
            
            if not results[0]:
                break
            
            for point in results[0]:
                consolidated_at = point.payload['consolidated_at']
                original_importance = point.payload['importance']
                access_count = point.payload.get('access_count', 0)
                
                # Time since consolidation (days)
                days_elapsed = (current_time - consolidated_at) / 86400
                
                # Memory strength (higher importance + access = slower decay)
                base_strength = original_importance * 30  # Days to 50% retention
                access_bonus = access_count * 5  # Each access adds 5 days
                strength = base_strength + access_bonus
                
                # Apply forgetting curve
                retention = math.exp(-days_elapsed / strength)
                decayed_importance = original_importance * retention
                
                # Probabilistic deletion for low-importance
                should_delete = False
                if decayed_importance < 0.1:
                    should_delete = (random.random() < 0.9)  # 90% chance
                elif decayed_importance < 0.2:
                    should_delete = (random.random() < 0.5)  # 50% chance
                elif decayed_importance < 0.3:
                    should_delete = (random.random() < 0.2)  # 20% chance
                
                if should_delete:
                    self.qdrant.delete(
                        collection_name="episodic_memory",
                        points_selector=[point.id]
                    )
                    deleted_count += 1
                else:
                    # Update importance (decay)
                    self.qdrant.set_payload(
                        collection_name="episodic_memory",
                        payload={"importance": decayed_importance},
                        points=[point.id]
                    )
                    decayed_count += 1
            
            offset = results[1]  # Next offset
            if offset is None:
                break
        
        return {
            'deleted': deleted_count,
            'decayed': decayed_count
        }
    
    async def _optimize_storage(self):
        """Optimize databases for performance."""
        
        # Qdrant: Optimize collection
        self.qdrant.update_collection(
            collection_name="episodic_memory",
            optimizer_config={"indexing_threshold": 10000}
        )
        
        # PostgreSQL: VACUUM and reindex
        cursor = self.pg.cursor()
        cursor.execute("VACUUM ANALYZE long_term_memories")
        cursor.execute("REINDEX TABLE long_term_memories")
        self.pg.commit()
    
    def _get_user_sleep_time(self) -> int:
        """Get user's configured sleep start hour (default 3am)."""
        # TODO: Load from user preferences
        return 3
```

---

## 5. Memory Retrieval System

### 5.1 Unified Retrieval Interface

```python
class MemoryRetriever:
    """
    Multi-tier memory retrieval with intelligent ranking.
    
    Retrieval strategies:
    1. Semantic search (embedding similarity)
    2. Temporal queries (time range)
    3. Hybrid (semantic + temporal + importance)
    """
    
    def __init__(self, redis_client, qdrant_client, pg_conn, embedding_gen):
        self.redis = redis_client
        self.qdrant = qdrant_client
        self.pg = pg_conn
        self.embedding_gen = embedding_gen
    
    async def retrieve_context(self, query: str, k: int = 5, 
                               include_longterm: bool = True) -> list:
        """
        Retrieve top-k most relevant memories for query.
        
        Multi-stage retrieval:
        1. Working memory (recent context, always included)
        2. Short-term memory (semantic search in Qdrant)
        3. Long-term memory (if needed, pgvector search)
        
        Returns: List of memories with combined relevance score
        """
        
        results = []
        
        # Stage 1: Working memory (last 10 events)
        recent_events = self.redis.zrange('events:stream', -10, -1, withscores=True)
        for event_json, timestamp in recent_events:
            event = json.loads(event_json)
            results.append({
                'source': 'working_memory',
                'content': event['content'],
                'timestamp': timestamp,
                'importance': event.get('importance', 0.5),
                'relevance': 1.0,  # Most recent = most relevant
                'age_days': 0
            })
        
        # Stage 2: Short-term memory (semantic search)
        query_embedding = self.embedding_gen.encode(query)
        
        qdrant_results = self.qdrant.search(
            collection_name="episodic_memory",
            query_vector=query_embedding.tolist(),
            limit=k * 2,  # Over-retrieve, will re-rank
            score_threshold=0.6  # Minimum similarity
        )
        
        for result in qdrant_results:
            age_days = (time.time() - result.payload['timestamp']) / 86400
            results.append({
                'source': 'shortterm_memory',
                'content': result.payload['content'],
                'timestamp': result.payload['timestamp'],
                'importance': result.payload['importance'],
                'relevance': result.score,
                'age_days': age_days,
                'emotion': result.payload.get('emotion', {})
            })
        
        # Stage 3: Long-term memory (if not enough results)
        if include_longterm and len(results) < k:
            cursor = self.pg.cursor()
            cursor.execute("""
                SELECT id, content, timestamp, importance, 
                       embedding <-> %s::vector AS distance
                FROM long_term_memories
                WHERE embedding <-> %s::vector < 0.5
                ORDER BY distance ASC
                LIMIT %s
            """, (query_embedding.tolist(), query_embedding.tolist(), k))
            
            for row in cursor.fetchall():
                age_days = (time.time() - row[2]) / 86400
                results.append({
                    'source': 'longterm_memory',
                    'content': row[1],
                    'timestamp': row[2],
                    'importance': row[3],
                    'relevance': 1.0 - row[4],  # Convert distance to similarity
                    'age_days': age_days
                })
        
        # Re-rank by combined score
        current_time = time.time()
        for mem in results:
            # Recency factor (exponential decay, 7-day half-life)
            recency_factor = math.exp(-mem['age_days'] / 7)
            
            # Combined score: 50% relevance, 30% importance, 20% recency
            mem['combined_score'] = (
                0.5 * mem['relevance'] +
                0.3 * mem['importance'] +
                0.2 * recency_factor
            )
        
        # Sort and return top-k
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        return results[:k]
    
    async def retrieve_temporal(self, start_time: float, end_time: float) -> list:
        """Retrieve all memories within time range."""
        
        results = []
        
        # Qdrant temporal filter
        qdrant_results = self.qdrant.scroll(
            collection_name="episodic_memory",
            scroll_filter={
                "must": [
                    {"key": "timestamp", "range": {"gte": start_time, "lte": end_time}}
                ]
            },
            limit=1000
        )
        
        for point in qdrant_results[0]:
            results.append({
                'source': 'shortterm_memory',
                'content': point.payload['content'],
                'timestamp': point.payload['timestamp'],
                'importance': point.payload['importance']
            })
        
        # PostgreSQL for older memories
        cursor = self.pg.cursor()
        cursor.execute("""
            SELECT content, timestamp, importance
            FROM long_term_memories
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """, (start_time, end_time))
        
        for row in cursor.fetchall():
            results.append({
                'source': 'longterm_memory',
                'content': row[0],
                'timestamp': row[1],
                'importance': row[2]
            })
        
        return results
    
    async def retrieve_by_importance(self, min_importance: float, limit: int = 100) -> list:
        """Retrieve high-importance memories (e.g., for review, summarization)."""
        
        results = []
        
        # Qdrant filter
        qdrant_results = self.qdrant.scroll(
            collection_name="episodic_memory",
            scroll_filter={
                "must": [
                    {"key": "importance", "range": {"gte": min_importance}}
                ]
            },
            limit=limit
        )
        
        for point in qdrant_results[0]:
            results.append({
                'content': point.payload['content'],
                'timestamp': point.payload['timestamp'],
                'importance': point.payload['importance']
            })
        
        return results
```

---

## 6. PostgreSQL Schema (Long-Term Memory)

### 6.1 Table Schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector extension

CREATE TABLE long_term_memories (
    id UUID PRIMARY KEY,
    timestamp FLOAT NOT NULL,
    content TEXT NOT NULL,
    memory_type VARCHAR(50),
    
    -- Importance metrics
    importance FLOAT NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    
    -- Contextual data
    emotion JSONB,
    participants TEXT[],
    context_summary JSONB,
    
    -- Semantic search
    embedding vector(384),  -- Sentence-BERT mini embedding
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT importance_check CHECK (importance >= 0.0 AND importance <= 1.0)
);

-- Indexes
CREATE INDEX idx_longterm_timestamp ON long_term_memories(timestamp);
CREATE INDEX idx_longterm_importance ON long_term_memories(importance);
CREATE INDEX idx_longterm_type ON long_term_memories(memory_type);
CREATE INDEX idx_longterm_embedding ON long_term_memories USING ivfflat (embedding vector_cosine_ops);

-- Partitioning by year (optional, for large datasets)
-- CREATE TABLE long_term_memories_2026 PARTITION OF long_term_memories
-- FOR VALUES FROM (1704067200) TO (1735689600);  -- Unix timestamps
```

---

## 7. Performance Targets

| Operation | Target | Acceptable | Critical | Notes |
|-----------|--------|-----------|----------|-------|
| Redis write | <2ms | <5ms | <10ms | Event ingestion |
| Redis read | <1ms | <3ms | <5ms | Recent context lookup |
| Importance calculation | <5ms | <10ms | <20ms | Per event |
| Embedding generation | <20ms | <50ms | <100ms | Sentence-BERT mini |
| Qdrant upsert | <10ms | <30ms | <50ms | Single point |
| Qdrant search | <30ms | <50ms | <100ms | Top-10 results |
| PostgreSQL insert | <20ms | <50ms | <100ms | With pgvector |
| PostgreSQL search | <100ms | <200ms | <500ms | Semantic search |
| Light consolidation | <10s | <30s | <60s | 100-500 memories |
| Deep consolidation | <2min | <5min | <10min | Full cycle |

---

## 8. Storage Estimates

### 8.1 Per-Memory Overhead

| Tier | Size per Memory | Notes |
|------|----------------|-------|
| Redis (working) | ~2 KB | JSON + metadata |
| Qdrant (short-term) | ~2 KB | Compressed content + vector |
| PostgreSQL (long-term) | ~1.5 KB | Further compression |

### 8.2 Total Storage (10,000 memories)

```
Working memory (Redis):
  - Active events (~500): ~1 MB
  - Embeddings cache: ~750 KB
  - Overhead: ~20 MB
  Total: ~22 MB

Short-term memory (Qdrant):
  - Memories (~5,000): ~10 MB
  - HNSW index: ~50 MB
  - Metadata: ~10 MB
  Total: ~70 MB

Long-term memory (PostgreSQL):
  - Memories (~10,000): ~15 MB
  - Pgvector index: ~40 MB
  - Overhead: ~10 MB
  Total: ~65 MB

GRAND TOTAL: ~157 MB (well under 500MB budget)
```

---

## 9. TODOs & Future Enhancements

### Phase 1 (MVP):
- [ ] Implement Redis schema with adaptive TTL
- [ ] Importance scoring algorithm
- [ ] Sentence-BERT mini embedding integration
- [ ] Consolidation worker (light + deep modes)
- [ ] Basic retrieval (semantic search)

### Phase 2 (Refinements):
- [ ] Probabilistic forgetting with tunable parameters
- [ ] Compression optimization (benchmark ratios)
- [ ] Learned utility prediction model (replace heuristic)
- [ ] A/B test importance formula variations
- [ ] Memory access tracking for reinforcement

### Phase 3 (Advanced):
- [ ] Hierarchical memory (cluster related memories)
- [ ] Cross-memory inference (connect dots)
- [ ] Memory replay for skill training
- [ ] Federated memory sharing (privacy-preserving)
- [ ] Adaptive consolidation triggers (learn optimal times)

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Redis memory overflow | Medium | High | Emergency consolidation, adaptive TTL, monitoring |
| Qdrant indexing latency | Low | Medium | Batch upserts, async indexing |
| PostgreSQL disk space | Low | High | Partitioning, compression, pruning old data |
| Forgetting important memories | Medium | High | Conservative thresholds, retrieval reinforcement |
| Embedding model drift | Low | Medium | Periodic retraining, version tracking |
| Consolidation blocks system | Low | Medium | Async workers, priority scheduling |

---

**Document Status:** Memory Consolidation System design complete. Ready for implementation.
