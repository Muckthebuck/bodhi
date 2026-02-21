# Central Agent Architecture - Detailed Design

**Date:** 2026-02-14  
**Status:** Detailed Design Complete  
**Role:** Executive Control & Orchestration (Prefrontal Cortex Analog)

---

## 1. Architecture Overview

### 1.1 Central Agent as Executive Controller

The Central Agent is the "brain's executive center" - it:
- **Perceives:** Aggregates inputs from all sensory agents
- **Reasons:** Decides what to do based on context, goals, and personality
- **Acts:** Dispatches commands to motor agents and skill executors
- **Reflects:** Background reasoning for proactive suggestions
- **Adapts:** Learns which strategies work, adjusts attention allocation

```
┌────────────────────────────────────────────────────────────────┐
│                     CENTRAL AGENT                              │
│            (Prefrontal Cortex Analog)                          │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Event      │  │  Background  │  │   Attention  │        │
│  │   Handler    │  │  Reasoner    │  │  Mechanism   │        │
│  │  (Reactive)  │  │ (Proactive)  │  │  (Focus)     │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                │
│         └──────────────────┼──────────────────┘                │
│                            │                                   │
│                    ┌───────▼────────┐                          │
│                    │ Working Memory │                          │
│                    │    (Redis)     │                          │
│                    └───────┬────────┘                          │
│                            │                                   │
│         ┌──────────────────┼──────────────────┐               │
│         │                  │                  │               │
│    ┌────▼─────┐    ┌──────▼──────┐    ┌─────▼──────┐        │
│    │ Intent   │    │  Planning   │    │  Skill     │        │
│    │Classifier│    │   Engine    │    │ Selector   │        │
│    └────┬─────┘    └──────┬──────┘    └─────┬──────┘        │
│         └──────────────────┼──────────────────┘               │
│                            │                                   │
│                    ┌───────▼────────┐                          │
│                    │   Response     │                          │
│                    │  Generator     │                          │
│                    └───────┬────────┘                          │
└────────────────────────────┼──────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
         ┌──────▼──────┐ ┌──▼──────┐ ┌──▼──────────┐
         │ Motor       │ │ Skill   │ │ Memory      │
         │ Agents      │ │Executor │ │Consolidation│
         └─────────────┘ └─────────┘ └─────────────┘
```

### 1.2 Core Components

| Component | Responsibility | Technology | Latency Budget |
|-----------|---------------|------------|----------------|
| **Event Handler** | Reactive processing of incoming events | Python asyncio | 10-50ms |
| **Background Reasoner** | Proactive pattern detection, suggestions | Python + model | 100-500ms |
| **Attention Mechanism** | Prioritize and focus compute resources | Hybrid (rules + learned + pointer) | 20ms |
| **Working Memory** | Current context, goals, active state | Redis (structured objects) | <5ms |
| **Intent Classifier** | What does user want? | DistilBERT-tiny (25MB) | 50ms |
| **Planning Engine** | Multi-step task planning | Cascading: Rules → GPT-2-small | 50-150ms |
| **Skill Selector** | Which skill to invoke? | Learned routing (5MB) | 20ms |
| **Response Generator** | Generate natural language output | Cascading: Templates → GPT-2 | 50-100ms |

---

## 2. Hybrid Decision Loop

### 2.1 Dual-Process Architecture

**Process 1: Event-Driven (Fast, Reactive)**
- Handles immediate user interactions
- Responds to sensory events (screen changes, audio input)
- Low latency (<200ms)

**Process 2: Background Reasoning (Slow, Proactive)**
- Monitors for patterns over time
- Suggests proactive actions
- Runs every 5-10 seconds

```python
import asyncio
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

class EventPriority(Enum):
    CRITICAL = 5     # User input, errors
    HIGH = 4         # Skill completions, important notifications
    NORMAL = 3       # Screen changes, audio events
    LOW = 2          # Background updates
    IDLE = 1         # System housekeeping

@dataclass
class Event:
    type: str
    priority: EventPriority
    payload: Dict[str, Any]
    timestamp: float
    source: str

class CentralAgent:
    """
    Brain-inspired executive controller with dual-process reasoning.
    
    Process 1: Event-driven (reactive, fast)
    Process 2: Background reasoning (proactive, slow)
    """
    
    def __init__(self, redis_client, skill_executor, memory_retriever, 
                 attention_mechanism, personality_params):
        self.redis = redis_client
        self.skill_executor = skill_executor
        self.memory = memory_retriever
        self.attention = attention_mechanism
        self.personality = personality_params
        
        # Event queue (priority queue)
        self.event_queue = asyncio.PriorityQueue()
        
        # Working memory (structured objects backed by Redis)
        self.working_memory = WorkingMemory(redis_client)
        
        # Model cache (cascading model selection)
        self.model_cache = ModelCache()
        
        # Failure handling
        self.circuit_breaker = CircuitBreaker()
        self.watchdog = WatchdogTimer()
        
        # State
        self.running = False
        self.background_reasoning_enabled = True
    
    async def start(self):
        """Start both processes."""
        self.running = True
        
        # Process 1: Event handler (reactive)
        asyncio.create_task(self._event_loop())
        
        # Process 2: Background reasoner (proactive)
        asyncio.create_task(self._background_reasoning_loop())
        
        # Monitor: Health check and failure recovery
        asyncio.create_task(self._health_monitor())
    
    async def _event_loop(self):
        """
        Main event loop (reactive).
        Processes events from priority queue.
        """
        while self.running:
            try:
                # Get highest priority event
                priority, event = await self.event_queue.get()
                
                # Watchdog: Start timer for this event
                self.watchdog.start(timeout=2.0)  # 2-second max per event
                
                # Process event
                await self._process_event(event)
                
                # Watchdog: Clear timer
                self.watchdog.clear()
                
            except asyncio.TimeoutError:
                print(f"[Central Agent] Event processing timeout: {event.type}")
                await self._handle_timeout(event)
            
            except Exception as e:
                print(f"[Central Agent] Error processing event: {e}")
                await self._handle_error(event, e)
    
    async def _process_event(self, event: Event):
        """
        Core event processing pipeline.
        
        Steps:
        1. Update working memory with event
        2. Retrieve relevant memories
        3. Apply attention mechanism (what to focus on?)
        4. Multi-modal fusion (combine sensory inputs)
        5. Intent classification (what does user want?)
        6. Planning (if complex task)
        7. Skill selection (which skill to invoke?)
        8. Response generation (what to say/do?)
        9. Action dispatch (execute)
        """
        start_time = time.time()
        
        # Step 1: Update working memory
        self.working_memory.add_event(event)
        
        # Step 2: Retrieve relevant memories (parallel with attention)
        memory_task = asyncio.create_task(
            self.memory.retrieve_context(
                query=event.payload.get('content', ''),
                k=5
            )
        )
        
        # Step 3: Attention mechanism (what to focus on?)
        attention_context = await self.attention.compute_attention(
            event=event,
            working_memory=self.working_memory,
            personality=self.personality
        )
        
        # Wait for memory retrieval
        relevant_memories = await memory_task
        
        # Step 4: Multi-modal fusion
        fused_context = await self._multi_modal_fusion(
            event=event,
            attention=attention_context,
            memories=relevant_memories
        )
        
        # Step 5: Intent classification (cascading)
        intent = await self._classify_intent_cascading(fused_context)
        
        # Step 6: Planning (if needed)
        if intent.requires_planning:
            plan = await self._plan_cascading(fused_context, intent)
        else:
            plan = None
        
        # Step 7: Skill selection
        selected_skill = await self._select_skill(intent, plan, fused_context)
        
        # Step 8: Response generation (cascading)
        response = await self._generate_response_cascading(
            intent=intent,
            skill=selected_skill,
            context=fused_context
        )
        
        # Step 9: Action dispatch
        await self._dispatch_action(selected_skill, response, event)
        
        # Log latency
        elapsed = (time.time() - start_time) * 1000
        self.working_memory.log_latency('event_processing', elapsed)
        
        if elapsed > 500:
            print(f"[Central Agent] WARNING: Latency {elapsed:.0f}ms (target <500ms)")
    
    async def _background_reasoning_loop(self):
        """
        Background reasoning (proactive).
        Runs periodically to detect patterns and suggest actions.
        """
        while self.running:
            await asyncio.sleep(5)  # Every 5 seconds
            
            if not self.background_reasoning_enabled:
                continue
            
            try:
                # Check if user is idle (no events for 10+ seconds)
                last_activity = self.working_memory.get('last_user_activity')
                if time.time() - last_activity < 10:
                    continue  # User active, don't interrupt
                
                # Pattern detection
                patterns = await self._detect_patterns()
                
                # Proactive suggestions
                if patterns:
                    suggestion = await self._generate_proactive_suggestion(patterns)
                    
                    if suggestion:
                        # Create synthetic event (low priority)
                        await self.event_queue.put((
                            EventPriority.LOW.value,
                            Event(
                                type='proactive_suggestion',
                                priority=EventPriority.LOW,
                                payload=suggestion,
                                timestamp=time.time(),
                                source='background_reasoner'
                            )
                        ))
            
            except Exception as e:
                print(f"[Background Reasoner] Error: {e}")
    
    async def _detect_patterns(self) -> list:
        """
        Analyze recent events for patterns.
        
        Examples:
        - User opens email at 9am daily → suggest automation
        - User struggles with task → suggest help
        - Repeated actions → suggest skill learning
        """
        recent_events = self.working_memory.get_recent_events(limit=50)
        
        patterns = []
        
        # Temporal pattern detection
        temporal_patterns = self._analyze_temporal_patterns(recent_events)
        patterns.extend(temporal_patterns)
        
        # Sequential pattern detection
        sequential_patterns = self._analyze_sequential_patterns(recent_events)
        patterns.extend(sequential_patterns)
        
        # Struggle detection (failed actions, repeated attempts)
        struggles = self._detect_struggles(recent_events)
        patterns.extend(struggles)
        
        return patterns
    
    async def _health_monitor(self):
        """
        Monitor system health and recover from failures.
        Runs every 10 seconds.
        """
        while self.running:
            await asyncio.sleep(10)
            
            # Check circuit breakers
            failed_components = self.circuit_breaker.get_failed()
            
            if failed_components:
                print(f"[Health Monitor] Failed components: {failed_components}")
                
                # Attempt recovery
                for component in failed_components:
                    if self.circuit_breaker.should_retry(component):
                        print(f"[Health Monitor] Retrying {component}...")
                        await self._recover_component(component)
            
            # Check memory usage
            memory_info = self.redis.info('memory')
            used_mb = memory_info['used_memory'] / (1024 * 1024)
            
            if used_mb > 90:  # 90MB threshold
                print(f"[Health Monitor] WARNING: Redis memory at {used_mb:.1f}MB")
                # Trigger emergency consolidation
                await self._trigger_emergency_consolidation()
```

---

## 3. Attention Mechanism (AlphaStar-Inspired)

### 3.1 Hybrid Attention Architecture

**Three-stage attention:**
1. **Priority Queue:** Rule-based critical events (user input always processed)
2. **Learned Attention:** Neural network learns importance from outcomes
3. **Pointer Networks:** Point to specific elements in context (like AlphaStar's entity selection)

```python
import torch
import torch.nn as nn
import numpy as np

class HybridAttentionMechanism:
    """
    AlphaStar-inspired attention with priority queue + learned attention + pointer networks.
    
    Inspired by:
    - AlphaStar: Pointer networks for entity selection
    - Transformer: Self-attention for context
    - Priority scheduling: Rule-based urgency
    """
    
    def __init__(self, embedding_dim=128):
        self.embedding_dim = embedding_dim
        
        # Learned attention model (lightweight)
        self.attention_model = AttentionNetwork(embedding_dim)
        
        # Pointer network (select specific entities/skills)
        self.pointer_network = PointerNetwork(embedding_dim)
        
        # Rule-based priorities
        self.priority_rules = {
            'user_message': 10,
            'error': 9,
            'skill_completion': 7,
            'screen_change': 5,
            'audio_event': 5,
            'background_update': 2,
        }
    
    async def compute_attention(self, event: Event, working_memory, personality) -> dict:
        """
        Compute attention distribution over all active elements.
        
        Returns:
        {
            'focus_elements': [event, memory1, skill2, ...],  # Top-k attended elements
            'attention_weights': [0.4, 0.3, 0.2, 0.1],
            'pointer_targets': ['skill_id_1', 'memory_id_3'],  # Specific pointed-to items
            'compute_budget': {'visual': 0.3, 'audio': 0.1, 'language': 0.6}
        }
        """
        
        # Stage 1: Rule-based priority (critical events)
        base_priority = self.priority_rules.get(event.type, 5)
        
        # Stage 2: Learned attention over context elements
        context_elements = self._gather_context_elements(event, working_memory)
        attention_weights = await self._compute_learned_attention(context_elements, personality)
        
        # Stage 3: Pointer network (select specific targets)
        pointer_targets = await self._compute_pointers(context_elements, attention_weights)
        
        # Combine: Boost rule-based priorities, modulate by learned attention
        combined_weights = self._combine_attention(base_priority, attention_weights)
        
        # Select top-k elements to focus on
        top_k = 5
        focus_elements = sorted(
            zip(context_elements, combined_weights),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # Allocate compute budget across modalities
        compute_budget = self._allocate_compute_budget(focus_elements, personality)
        
        return {
            'focus_elements': [elem for elem, _ in focus_elements],
            'attention_weights': [weight for _, weight in focus_elements],
            'pointer_targets': pointer_targets,
            'compute_budget': compute_budget
        }
    
    def _gather_context_elements(self, event: Event, working_memory) -> list:
        """Gather all elements that could be attended to."""
        elements = []
        
        # Current event
        elements.append({
            'type': 'event',
            'id': event.type,
            'embedding': self._embed_event(event),
            'priority': self.priority_rules.get(event.type, 5)
        })
        
        # Recent events from working memory
        recent_events = working_memory.get_recent_events(limit=10)
        for evt in recent_events:
            elements.append({
                'type': 'recent_event',
                'id': evt['id'],
                'embedding': self._embed_event(evt),
                'priority': 3
            })
        
        # Active skills
        active_skills = working_memory.get('active_skills', [])
        for skill_id in active_skills:
            elements.append({
                'type': 'skill',
                'id': skill_id,
                'embedding': self._embed_skill(skill_id),
                'priority': 4
            })
        
        # Goals
        goals = working_memory.get('goal_stack', [])
        for goal in goals:
            elements.append({
                'type': 'goal',
                'id': goal['goal'],
                'embedding': self._embed_goal(goal),
                'priority': int(goal['priority'] * 10)
            })
        
        return elements
    
    async def _compute_learned_attention(self, elements: list, personality: dict) -> np.ndarray:
        """
        Learned attention weights via neural network.
        
        Model learns: Which elements led to successful outcomes?
        """
        # Stack embeddings
        embeddings = torch.stack([torch.tensor(e['embedding']) for e in elements])
        
        # Add personality conditioning
        personality_vector = self._personality_to_vector(personality)
        personality_broadcast = personality_vector.repeat(len(elements), 1)
        
        # Compute attention
        attention_logits = self.attention_model(embeddings, personality_broadcast)
        attention_weights = torch.softmax(attention_logits, dim=0)
        
        return attention_weights.detach().numpy()
    
    async def _compute_pointers(self, elements: list, attention_weights: np.ndarray) -> list:
        """
        Pointer network: Select specific entities to interact with.
        
        Like AlphaStar selecting units, we select:
        - Which skill to invoke
        - Which memory to retrieve
        - Which goal to prioritize
        """
        # Filter to actionable elements (skills, goals)
        actionable = [e for e in elements if e['type'] in ['skill', 'goal']]
        
        if not actionable:
            return []
        
        # Pointer network: Query = current context, Keys = actionable elements
        query = torch.mean(torch.stack([torch.tensor(e['embedding']) for e in elements]), dim=0)
        keys = torch.stack([torch.tensor(e['embedding']) for e in actionable])
        
        pointer_logits = self.pointer_network(query, keys)
        pointer_probs = torch.softmax(pointer_logits, dim=0)
        
        # Select top-2 pointers
        top_indices = torch.topk(pointer_probs, k=min(2, len(actionable))).indices
        
        return [actionable[i]['id'] for i in top_indices]
    
    def _allocate_compute_budget(self, focus_elements: list, personality: dict) -> dict:
        """
        Allocate compute resources across modalities based on attention.
        
        Higher attention → more compute allocated.
        """
        # Count modalities in focus
        modality_counts = {'visual': 0, 'audio': 0, 'language': 0, 'memory': 0}
        
        for elem, weight in focus_elements:
            if elem['type'] in ['event', 'recent_event']:
                if 'screen' in elem['id']:
                    modality_counts['visual'] += weight
                elif 'audio' in elem['id']:
                    modality_counts['audio'] += weight
                else:
                    modality_counts['language'] += weight
            elif elem['type'] == 'goal':
                modality_counts['memory'] += weight
        
        # Normalize to sum to 1.0
        total = sum(modality_counts.values())
        if total > 0:
            compute_budget = {k: v / total for k, v in modality_counts.items()}
        else:
            compute_budget = {'visual': 0.3, 'audio': 0.1, 'language': 0.4, 'memory': 0.2}
        
        return compute_budget

class AttentionNetwork(nn.Module):
    """Lightweight attention network (5MB)."""
    def __init__(self, embedding_dim=128, hidden_dim=64):
        super().__init__()
        self.fc1 = nn.Linear(embedding_dim * 2, hidden_dim)  # embedding + personality
        self.fc2 = nn.Linear(hidden_dim, 1)
    
    def forward(self, embeddings, personality):
        x = torch.cat([embeddings, personality], dim=1)
        x = torch.relu(self.fc1(x))
        logits = self.fc2(x)
        return logits

class PointerNetwork(nn.Module):
    """Pointer network for selecting specific entities."""
    def __init__(self, embedding_dim=128):
        super().__init__()
        self.W_query = nn.Linear(embedding_dim, embedding_dim)
        self.W_key = nn.Linear(embedding_dim, embedding_dim)
    
    def forward(self, query, keys):
        # Query: (embedding_dim,)
        # Keys: (num_keys, embedding_dim)
        
        query_proj = self.W_query(query)  # (embedding_dim,)
        keys_proj = self.W_key(keys)      # (num_keys, embedding_dim)
        
        # Dot product attention
        logits = torch.matmul(keys_proj, query_proj)  # (num_keys,)
        
        return logits
```

---

## 4. Working Memory (Redis-Backed Structured Objects)

### 4.1 Schema Design

```python
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json
import redis

@dataclass
class GoalItem:
    goal: str
    priority: float
    created_at: float
    status: str  # 'active', 'pending', 'completed'

@dataclass
class EmotionalState:
    valence: float  # -1 to +1
    arousal: float  # 0 to 1
    dominance: float  # 0 to 1

@dataclass
class WorkingMemoryState:
    """
    Structured working memory state.
    Backed by Redis hashes for persistence.
    """
    # Current context
    session_id: str
    user_id: str
    user_state: str  # 'active', 'idle', 'away'
    active_app: Optional[str]
    last_user_activity: float
    
    # Goals and tasks
    goal_stack: List[GoalItem]
    current_task: Optional[str]
    
    # Emotional state
    emotion: EmotionalState
    
    # Active processes
    active_skills: List[str]
    active_modules: List[str]
    
    # Attention budget
    compute_budget: Dict[str, float]
    
    # Recent events (last 10)
    recent_events: List[Dict[str, Any]]
    
    # Retrieved memories
    relevant_memories: List[Dict[str, Any]]
    
    # Latency tracking
    latency_log: Dict[str, List[float]]

class WorkingMemory:
    """
    Working memory manager with Redis backing.
    
    Provides structured object interface over Redis hashes.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.key_prefix = 'working_memory:'
    
    def get_state(self) -> WorkingMemoryState:
        """Load current working memory state from Redis."""
        data = self.redis.hgetall(f'{self.key_prefix}state')
        
        if not data:
            # Initialize default state
            return self._initialize_default_state()
        
        # Deserialize from Redis
        return self._deserialize_state(data)
    
    def update_state(self, state: WorkingMemoryState):
        """Save working memory state to Redis."""
        serialized = self._serialize_state(state)
        self.redis.hset(f'{self.key_prefix}state', mapping=serialized)
        self.redis.expire(f'{self.key_prefix}state', 3600)  # 1-hour TTL
    
    def add_event(self, event: Event):
        """Add event to recent events list."""
        state = self.get_state()
        
        # Add to recent events (keep last 10)
        event_dict = {
            'type': event.type,
            'priority': event.priority.value,
            'payload': event.payload,
            'timestamp': event.timestamp,
            'source': event.source
        }
        
        state.recent_events.append(event_dict)
        state.recent_events = state.recent_events[-10:]  # Keep last 10
        
        # Update last activity if user event
        if 'user' in event.source:
            state.last_user_activity = event.timestamp
        
        self.update_state(state)
    
    def get(self, key: str, default=None) -> Any:
        """Get specific field from working memory."""
        state = self.get_state()
        return getattr(state, key, default)
    
    def set(self, key: str, value: Any):
        """Set specific field in working memory."""
        state = self.get_state()
        setattr(state, key, value)
        self.update_state(state)
    
    def log_latency(self, operation: str, latency_ms: float):
        """Log operation latency for monitoring."""
        state = self.get_state()
        
        if operation not in state.latency_log:
            state.latency_log[operation] = []
        
        state.latency_log[operation].append(latency_ms)
        
        # Keep last 100 measurements
        state.latency_log[operation] = state.latency_log[operation][-100:]
        
        self.update_state(state)
    
    def _serialize_state(self, state: WorkingMemoryState) -> dict:
        """Serialize state to Redis-compatible format."""
        return {
            'data': json.dumps(asdict(state))
        }
    
    def _deserialize_state(self, data: dict) -> WorkingMemoryState:
        """Deserialize state from Redis."""
        state_dict = json.loads(data[b'data'])
        
        # Reconstruct nested objects
        state_dict['goal_stack'] = [GoalItem(**g) for g in state_dict['goal_stack']]
        state_dict['emotion'] = EmotionalState(**state_dict['emotion'])
        
        return WorkingMemoryState(**state_dict)
    
    def _initialize_default_state(self) -> WorkingMemoryState:
        """Create default working memory state."""
        return WorkingMemoryState(
            session_id=str(uuid.uuid4()),
            user_id='user_001',
            user_state='active',
            active_app=None,
            last_user_activity=time.time(),
            goal_stack=[],
            current_task=None,
            emotion=EmotionalState(valence=0.0, arousal=0.5, dominance=0.5),
            active_skills=[],
            active_modules=['central_agent'],
            compute_budget={'visual': 0.3, 'audio': 0.1, 'language': 0.4, 'memory': 0.2},
            recent_events=[],
            relevant_memories=[],
            latency_log={}
        )
```

---

## 5. Cascading Model Selection with Learning

### 5.1 Model Hierarchy

**For each task (e.g., intent classification):**
- **Tier 1 (Fast):** Rule-based or tiny model (<10ms, 90% accuracy)
- **Tier 2 (Balanced):** DistilBERT-tiny (50ms, 95% accuracy)
- **Tier 3 (Powerful):** GPT-2-small (150ms, 98% accuracy)

**Strategy:** Try Tier 1 → If confidence < threshold, escalate to Tier 2 → If still low, Tier 3

### 5.2 Learned Routing

**Learn which model tier is best for which input patterns:**
- Track: Input features → Tier used → Success/Latency
- Train routing model: Input → Predicted optimal tier
- Minimize: Total latency while maintaining accuracy

```python
class CascadingModelSelector:
    """
    Cascading model selection with learned routing.
    
    Learns optimal model tier for each input type to minimize latency.
    """
    
    def __init__(self):
        # Model tiers (fast → powerful)
        self.intent_classifiers = {
            'tier1': RuleBasedIntentClassifier(),  # 5ms, 85% accuracy
            'tier2': DistilBERTIntentClassifier(),  # 50ms, 95% accuracy
            'tier3': GPT2IntentClassifier(),        # 150ms, 98% accuracy
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'tier1': 0.90,  # If confidence < 0.90, escalate to tier2
            'tier2': 0.95,  # If confidence < 0.95, escalate to tier3
        }
        
        # Learned routing model (predicts optimal tier)
        self.routing_model = RoutingNetwork()
        
        # Statistics for learning
        self.routing_stats = []
    
    async def classify_intent_cascading(self, context: dict) -> dict:
        """
        Cascade through model tiers until confident.
        
        Returns:
        {
            'intent': 'organize_email',
            'confidence': 0.96,
            'tier_used': 'tier2',
            'latency_ms': 52
        }
        """
        start_time = time.time()
        
        # Check learned routing (predict optimal tier)
        predicted_tier = await self._predict_optimal_tier(context)
        
        # Try predicted tier first
        result = await self._try_tier(predicted_tier, context)
        
        if result['confidence'] >= self.confidence_thresholds.get(predicted_tier, 1.0):
            # Success on predicted tier
            latency_ms = (time.time() - start_time) * 1000
            result['latency_ms'] = latency_ms
            
            # Log for learning
            self._log_routing_decision(context, predicted_tier, result, success=True)
            
            return result
        
        # Predicted tier failed, cascade through remaining tiers
        tiers = ['tier1', 'tier2', 'tier3']
        start_index = tiers.index(predicted_tier) + 1
        
        for tier in tiers[start_index:]:
            result = await self._try_tier(tier, context)
            
            if result['confidence'] >= self.confidence_thresholds.get(tier, 1.0):
                latency_ms = (time.time() - start_time) * 1000
                result['latency_ms'] = latency_ms
                
                # Log (predicted tier was suboptimal)
                self._log_routing_decision(context, tier, result, success=False)
                
                return result
        
        # All tiers tried, return best result
        latency_ms = (time.time() - start_time) * 1000
        result['latency_ms'] = latency_ms
        return result
    
    async def _try_tier(self, tier: str, context: dict) -> dict:
        """Try a specific model tier."""
        classifier = self.intent_classifiers[tier]
        result = await classifier.classify(context)
        result['tier_used'] = tier
        return result
    
    async def _predict_optimal_tier(self, context: dict) -> str:
        """
        Use learned routing model to predict optimal tier.
        
        Features:
        - Text length
        - Keyword presence (common intents can use tier1)
        - User history (repeated patterns → tier1)
        - Ambiguity score (high ambiguity → higher tier)
        """
        features = self._extract_routing_features(context)
        tier_logits = self.routing_model(features)
        predicted_tier = ['tier1', 'tier2', 'tier3'][torch.argmax(tier_logits)]
        return predicted_tier
    
    def _log_routing_decision(self, context, tier_used, result, success):
        """Log decision for learning."""
        self.routing_stats.append({
            'features': self._extract_routing_features(context),
            'predicted_tier': tier_used,
            'actual_confidence': result['confidence'],
            'latency_ms': result.get('latency_ms', 0),
            'success': success,
            'timestamp': time.time()
        })
        
        # Train routing model periodically (every 100 decisions)
        if len(self.routing_stats) >= 100:
            asyncio.create_task(self._train_routing_model())
    
    async def _train_routing_model(self):
        """Train routing model on collected stats."""
        # TODO: Implement online learning
        # Optimize: Minimize latency while maintaining accuracy
        pass
```

---

## 6. Personality Integration (Input Conditioning)

### 6.1 Personality as Context

**Big Five personality parameters condition all reasoning:**

```python
def add_personality_conditioning(context: dict, personality: dict) -> dict:
    """
    Add personality as explicit context for model input.
    
    Personality influences:
    - Extraversion → Proactivity, verbosity
    - Openness → Creative vs conservative suggestions
    - Conscientiousness → Structured vs flexible responses
    - Agreeableness → Supportive vs challenging tone
    - Neuroticism → Emotional expressiveness
    """
    
    # Convert Big Five to natural language prompt
    personality_prompt = _personality_to_prompt(personality)
    
    # Add to context
    context['personality_conditioning'] = personality_prompt
    context['personality_vector'] = _personality_to_vector(personality)
    
    return context

def _personality_to_prompt(personality: dict) -> str:
    """Convert personality params to natural language."""
    traits = []
    
    if personality['extraversion'] > 0.7:
        traits.append("You are outgoing and proactive.")
    elif personality['extraversion'] < 0.3:
        traits.append("You are reserved and only speak when needed.")
    
    if personality['openness'] > 0.7:
        traits.append("You suggest creative and unconventional solutions.")
    elif personality['openness'] < 0.3:
        traits.append("You prefer tried-and-true methods.")
    
    if personality['conscientiousness'] > 0.7:
        traits.append("You are organized and detail-oriented.")
    elif personality['conscientiousness'] < 0.3:
        traits.append("You are flexible and spontaneous.")
    
    if personality['agreeableness'] > 0.7:
        traits.append("You are supportive and empathetic.")
    elif personality['agreeableness'] < 0.3:
        traits.append("You provide direct, critical feedback.")
    
    if personality['neuroticism'] > 0.7:
        traits.append("You are emotionally expressive.")
    elif personality['neuroticism'] < 0.3:
        traits.append("You are calm and even-toned.")
    
    return " ".join(traits)
```

---

## 7. Multi-Modal Fusion (Parallel Extraction + Hierarchical Integration)

### 7.1 Parallel Feature Extraction

```python
async def _multi_modal_fusion(self, event: Event, attention: dict, memories: list) -> dict:
    """
    Multi-modal fusion with parallel feature extraction.
    
    Stage 1: Parallel extraction (minimize latency)
    Stage 2: Hierarchical integration
    Stage 3: Decision-level fusion
    """
    
    # Stage 1: Parallel feature extraction
    tasks = []
    
    # Visual features (if screen event)
    if event.type in ['screen_change', 'screen_activity']:
        tasks.append(asyncio.create_task(
            self._extract_visual_features(event.payload.get('screen_data'))
        ))
    else:
        tasks.append(asyncio.create_task(asyncio.sleep(0)))  # No-op
    
    # Audio features (if audio event)
    if event.type in ['audio_input', 'speech']:
        tasks.append(asyncio.create_task(
            self._extract_audio_features(event.payload.get('audio_data'))
        ))
    else:
        tasks.append(asyncio.create_task(asyncio.sleep(0)))
    
    # Text features (always)
    tasks.append(asyncio.create_task(
        self._extract_text_features(event.payload.get('content', ''))
    ))
    
    # Wait for all feature extraction to complete
    visual_features, audio_features, text_features = await asyncio.gather(*tasks)
    
    # Stage 2: Hierarchical integration
    # Integrate sensory features
    sensory_integrated = self._integrate_sensory(visual_features, audio_features)
    
    # Combine with text and memories
    context_integrated = self._integrate_context(sensory_integrated, text_features, memories)
    
    # Stage 3: Decision-level fusion
    # Apply attention weights
    focused_context = self._apply_attention_weights(context_integrated, attention)
    
    return focused_context
```

---

## 8. Failure Handling & User Transparency

### 8.1 Watchdog Timer

```python
class WatchdogTimer:
    """Timeout protection for long-running operations."""
    
    def __init__(self):
        self.current_timeout = None
        self.current_task = None
    
    def start(self, timeout: float):
        """Start watchdog timer."""
        self.current_timeout = timeout
        self.current_task = asyncio.create_task(self._monitor(timeout))
    
    def clear(self):
        """Clear watchdog (operation completed successfully)."""
        if self.current_task:
            self.current_task.cancel()
            self.current_task = None
    
    async def _monitor(self, timeout: float):
        """Monitor task execution."""
        await asyncio.sleep(timeout)
        
        # Timeout reached
        raise asyncio.TimeoutError(f"Operation exceeded {timeout}s timeout")
```

### 8.2 Circuit Breaker

```python
class CircuitBreaker:
    """Disable failing components temporarily."""
    
    def __init__(self, failure_threshold=3, reset_timeout=60):
        self.failure_counts = {}
        self.disabled_components = {}
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
    
    def record_failure(self, component: str):
        """Record component failure."""
        self.failure_counts[component] = self.failure_counts.get(component, 0) + 1
        
        if self.failure_counts[component] >= self.failure_threshold:
            print(f"[Circuit Breaker] Disabling {component} (threshold reached)")
            self.disabled_components[component] = time.time()
    
    def is_disabled(self, component: str) -> bool:
        """Check if component is disabled."""
        if component not in self.disabled_components:
            return False
        
        # Check if reset timeout elapsed
        disabled_at = self.disabled_components[component]
        if time.time() - disabled_at > self.reset_timeout:
            print(f"[Circuit Breaker] Re-enabling {component} (timeout elapsed)")
            del self.disabled_components[component]
            self.failure_counts[component] = 0
            return False
        
        return True
    
    def should_retry(self, component: str) -> bool:
        """Check if component should be retried."""
        return self.is_disabled(component) and time.time() - self.disabled_components[component] > self.reset_timeout
```

### 8.3 Adaptive Degradation with User Transparency

```python
async def _handle_timeout(self, event: Event):
    """
    Handle event processing timeout.
    
    Options:
    1. Use cached/template response
    2. Ask user if they want to wait
    3. Degrade to simpler processing
    """
    
    # Ask user preference
    user_choice = await self._ask_user_preference(
        message=f"Processing '{event.type}' is taking longer than usual.",
        options=[
            "Wait for full processing",
            "Use faster (less accurate) processing",
            "Skip this event"
        ],
        timeout=5  # Auto-select "Use faster" after 5s if no response
    )
    
    if user_choice == "Wait for full processing":
        # Extend timeout, try again
        self.watchdog.start(timeout=5.0)  # Extended timeout
        await self._process_event(event)
    
    elif user_choice == "Use faster (less accurate) processing":
        # Degrade: Use tier1 models only, skip memory retrieval
        await self._process_event_degraded(event)
    
    else:  # Skip
        print(f"[Central Agent] Skipping event: {event.type}")

async def _handle_error(self, event: Event, error: Exception):
    """
    Handle processing error.
    
    Options:
    1. Retry with degraded processing
    2. Ask user if they want to report error
    3. Restart component
    """
    
    # Log error
    print(f"[Central Agent] Error processing {event.type}: {error}")
    
    # Circuit breaker: Record failure
    self.circuit_breaker.record_failure('central_agent')
    
    # Ask user
    user_choice = await self._ask_user_preference(
        message=f"An error occurred while processing your request: {error}",
        options=[
            "Retry with simpler processing",
            "Restart system",
            "Ignore and continue"
        ],
        timeout=10
    )
    
    if user_choice == "Retry with simpler processing":
        await self._process_event_degraded(event)
    
    elif user_choice == "Restart system":
        await self._restart_central_agent()
    
    else:  # Ignore
        pass
```

---

## 9. Performance Targets & Latency Budget

### 9.1 End-to-End Latency (Target <500ms)

| Stage | Target (ms) | Budget | Notes |
|-------|------------|--------|-------|
| Event collection | 5 | 1% | Read from Redis |
| Memory retrieval | 50 | 10% | Qdrant semantic search |
| Attention computation | 20 | 4% | Hybrid attention |
| Parallel feature extraction | 30 | 6% | Visual + Audio + Text |
| Intent classification | 50 | 10% | Cascading (tier1/tier2) |
| Planning (if needed) | 150 | 30% | Cascading (rules/GPT-2) |
| Skill selection | 20 | 4% | Learned routing |
| Response generation | 100 | 20% | Cascading (template/GPT-2) |
| Action dispatch | 20 | 4% | gRPC call to executors |
| **Buffer** | 55 | 11% | Safety margin |
| **Total** | **500** | **100%** | |

### 9.2 Memory Budget (8GB RPi5)

```
Central Agent Components:
  - Python runtime: 50 MB
  - Working memory (Redis): 100 MB
  - Model cache: 300 MB
    - DistilBERT-tiny: 25 MB
    - GPT-2-small: 100 MB
    - Attention models: 10 MB
    - Pointer network: 5 MB
    - Routing network: 5 MB
    - Other: 155 MB (buffer)
  - Attention mechanism: 20 MB
  - Event queue: 10 MB
  - Background reasoning: 50 MB
  ────────────────────────
  Total: 530 MB

Remaining for other agents: 7.5 GB
```

---

## 10. Implementation Roadmap

### Phase 1 (MVP - Weeks 1-2):
- [ ] Event-driven loop (reactive only)
- [ ] Basic working memory (Redis-backed)
- [ ] Simple attention (priority queue)
- [ ] Cascading intent classification (tier1 + tier2)
- [ ] Template-based response generation
- [ ] Basic failure handling (timeouts)

### Phase 2 (Core Features - Weeks 3-4):
- [ ] Background reasoning loop (proactive)
- [ ] Learned attention mechanism
- [ ] Multi-modal fusion (parallel extraction)
- [ ] Personality integration (input conditioning)
- [ ] Cascading planning (rules + GPT-2)
- [ ] Circuit breakers

### Phase 3 (Advanced - Weeks 5-6):
- [ ] Pointer networks (AlphaStar-style)
- [ ] Learned routing for cascading models
- [ ] Adaptive degradation
- [ ] User transparency (ask preferences on failures)
- [ ] Pattern detection (background reasoner)
- [ ] Proactive suggestions

### Phase 4 (Optimization - Weeks 7-8):
- [ ] Latency profiling and optimization
- [ ] Model quantization (INT8)
- [ ] Compute budget allocation tuning
- [ ] A/B testing attention strategies
- [ ] Performance monitoring dashboard

---

## 11. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Latency exceeds 500ms | High | High | Cascading models, adaptive degradation, profiling |
| Model loading slow | Medium | Medium | Preload frequently-used models, async loading |
| Memory overflow | Medium | High | Circuit breakers, emergency consolidation |
| Background reasoning interferes | Low | Medium | Priority scheduling, CPU throttling |
| User frustrated by errors | Medium | High | Transparent communication, graceful degradation |
| Attention mechanism ineffective | Medium | Medium | Learn from outcomes, A/B test strategies |
| Personality integration weak | Low | Low | Tune prompts, collect user feedback |

---

**Document Status:** Central Agent Architecture design complete. Ready for implementation.
