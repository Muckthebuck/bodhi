# Module Activation Strategy Design

**Last Updated:** 2026-02-21  
**Status:** Design Complete  
**Target Platform:** Raspberry Pi 5 (8GB RAM, ARM64)

---

## 1. Overview & Philosophy

The Module Activation Strategy is the **resource management layer** that determines which cognitive agents are loaded in memory at any given time. Inspired by the human brain's selective attention and energy conservation mechanisms, this system ensures:

1. **Responsiveness:** Critical modules are always ready
2. **Efficiency:** Unused modules are unloaded to save memory and power
3. **Intelligence:** Predictive loading based on learned user patterns
4. **Adaptability:** Dynamic adjustment to power states and memory pressure

### Design Principles

- **Lazy Loading:** Load modules only when needed
- **Predictive Anticipation:** Pre-load modules before they're needed (learned patterns)
- **Graceful Degradation:** If memory constrained, prioritize essential functions
- **Power Awareness:** Aggressive unloading on battery, relaxed when plugged in
- **User Transparency:** Show loading states, allow manual overrides

---

## 2. Module States (5-State Finite State Machine)

Each module can be in one of five states, arranged from most resource-intensive to least:

### State Definitions

```
┌────────────────────────────────────────────────────────────┐
│                     MODULE STATE FSM                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌────────┐  activate   ┌────────┐  standby   ┌─────────┐│
│   │UNLOADED├────────────>│STANDBY ├───────────>│ ACTIVE  ││
│   └───┬────┘             └───┬────┘            └────┬────┘│
│       ^                      ^                      │     │
│       │                      │   hibernate         │     │
│       │  unload              └─────────────────────┘     │
│       │                      ┌──────────┐               │
│       └──────────────────────┤HIBERNATED│<──────────────┘
│                              └─────┬────┘               │
│                                    │                     │
│                              ┌─────▼────┐               │
│                              │SUSPENDED │               │
│                              └──────────┘               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

#### 1. **ACTIVE** (Highest Resource Usage)
- **Memory:** Full model + runtime buffers loaded
- **CPU:** Processing inputs at target rate (e.g., Visual Agent at 5 FPS)
- **Power:** Full power draw (e.g., 2-4W per module)
- **Latency:** Immediate response (<10ms to process input)
- **Transitions:**
  - → **STANDBY:** After inactivity timeout (configurable per module)
  - → **HIBERNATED:** On memory pressure or explicit command

#### 2. **STANDBY** (Medium-Low Resource Usage)
- **Memory:** Full model loaded, minimal runtime buffers
- **CPU:** Idle, ready to process on demand
- **Power:** Low (model in RAM but not inferring, ~0.5W)
- **Latency:** Fast activation (<50ms to resume processing)
- **Transitions:**
  - → **ACTIVE:** On input received or goal-driven activation
  - → **HIBERNATED:** After extended inactivity (2x timeout)
  - → **UNLOADED:** On memory pressure (if not in minimum active set)

#### 3. **HIBERNATED** (Low Resource Usage)
- **Memory:** Core state preserved, models unloaded
- **CPU:** None (state persisted to Redis)
- **Power:** Minimal (~0.1W for Redis persistence)
- **Latency:** Medium activation (200-500ms to reload models)
- **Transitions:**
  - → **STANDBY:** On predicted need (70%+ confidence)
  - → **SUSPENDED:** On severe memory pressure (rarely used)
  - → **UNLOADED:** On explicit command or long-term disuse

#### 4. **SUSPENDED** (Very Low Resource Usage)
- **Memory:** State swapped to disk (if swap enabled)
- **CPU:** None
- **Power:** Zero (only disk storage)
- **Latency:** Slow activation (1-3s to restore from disk)
- **Note:** Only used on extreme memory pressure, rare on 8GB RPi5
- **Transitions:**
  - → **HIBERNATED:** On memory availability
  - → **UNLOADED:** On manual cleanup or restart

#### 5. **UNLOADED** (Zero Resource Usage)
- **Memory:** Zero (not in memory, not on disk)
- **CPU:** None
- **Power:** Zero
- **Latency:** Full load time (500ms-2s depending on module)
- **Transitions:**
  - → **STANDBY:** On explicit activation request
  - → **ACTIVE:** On urgent activation (staged load: core first, rest async)

### State Transition Rules

**Upward transitions (loading):**
- Must respect memory budget (see Section 12)
- If budget exceeded, trigger eviction (see Section 4)
- Use staged loading for UNLOADED → ACTIVE (see Section 9)

**Downward transitions (unloading):**
- Must not violate minimum active set (see Section 5)
- Apply cooldown period to prevent thrashing (see Section 6)
- Persist state to Redis before unloading

---

## 3. Activation Triggers (Three-Tier Intelligence)

Modules are activated through three complementary mechanisms:

### 3.1 Input-Driven Activation (Bottom-Up, Reactive)

**Trigger:** Incoming data from sensors or user interaction

**Examples:**
- Screen pixels changed → Activate **Visual Agent**
- Audio samples detected → Activate **Auditory Agent**
- User typed text → Activate **Language Center**
- Emotion detected in voice → Activate **Emotion Regulator**

**Implementation:**
```python
class InputRouter:
    """Routes inputs to appropriate modules, activating as needed."""
    
    MODALITY_TO_MODULE = {
        'screen_frame': 'visual_agent',
        'audio_chunk': 'auditory_agent',
        'text_input': 'language_center',
        'tool_response': 'skill_executor',
        'emotion_signal': 'emotion_regulator'
    }
    
    async def route_input(self, input_data: Dict[str, Any]):
        """Route input and activate target module if needed."""
        modality = input_data['type']
        module_id = self.MODALITY_TO_MODULE.get(modality)
        
        if not module_id:
            logger.warning(f"Unknown modality: {modality}")
            return
        
        # Check if module is active
        module_state = await self.activation_mgr.get_state(module_id)
        
        if module_state == ModuleState.UNLOADED:
            # Urgent activation: staged load
            await self.activation_mgr.activate(
                module_id, 
                priority=Priority.HIGH,
                reason=f"input_driven:{modality}"
            )
        elif module_state == ModuleState.STANDBY:
            # Quick activation
            await self.activation_mgr.wake(module_id)
        
        # Dispatch input
        await self.message_bus.publish(
            f"module.{module_id}.input",
            input_data
        )
```

**Latency Requirements:**
- If module in STANDBY: <50ms to activate and process
- If module in HIBERNATED: <500ms to activate and process
- If module in UNLOADED: <2s to activate and process (staged loading)

### 3.2 Goal-Driven Activation (Top-Down, Task-Based)

**Trigger:** Central Agent needs module to accomplish a task

**Examples:**
- User asks "Summarize my emails" → Activate **Language Center** + **Tool Plugin (Email)**
- User asks "What's on my screen?" → Activate **Visual Agent**
- Skill execution requires tool access → Activate **Skill Executor**

**Implementation:**
```python
class CentralAgent:
    """Executive controller with goal-driven activation."""
    
    async def execute_intent(self, intent: Intent):
        """Execute intent, activating necessary modules."""
        # Determine required modules via capability matching
        required_modules = self.capability_planner.get_modules_for_intent(intent)
        
        # Parallel activation of all required modules
        activation_tasks = []
        for module_id, urgency in required_modules:
            if urgency == Urgency.CRITICAL:
                # Must be active before proceeding
                activation_tasks.append(
                    self.activation_mgr.activate(
                        module_id,
                        priority=Priority.HIGH,
                        reason=f"goal_driven:{intent.type}",
                        blocking=True  # Wait for activation
                    )
                )
            else:
                # Can load asynchronously
                activation_tasks.append(
                    self.activation_mgr.activate(
                        module_id,
                        priority=Priority.MEDIUM,
                        reason=f"goal_driven:{intent.type}",
                        blocking=False
                    )
                )
        
        await asyncio.gather(*activation_tasks)
        
        # Execute intent
        result = await self.intent_executor.execute(intent)
        return result
```

**Capability Planner:**
Maps intents to required modules using a rule-based + learned approach.

```python
class CapabilityPlanner:
    """Maps intents to required modules."""
    
    INTENT_MODULE_MAP = {
        'summarize_screen': [('visual_agent', Urgency.CRITICAL)],
        'respond_to_voice': [
            ('auditory_agent', Urgency.CRITICAL),
            ('language_center', Urgency.CRITICAL),
            ('voice_synthesis', Urgency.MEDIUM)
        ],
        'execute_skill': [('skill_executor', Urgency.CRITICAL)],
        'access_tool': [('tool_plugin_system', Urgency.CRITICAL)],
    }
    
    def get_modules_for_intent(self, intent: Intent) -> List[Tuple[str, Urgency]]:
        """Return (module_id, urgency) pairs for intent."""
        # Rule-based lookup
        modules = self.INTENT_MODULE_MAP.get(intent.type, [])
        
        # TODO: Enhance with learned predictions
        # Could use ML model: intent → probability distribution over modules
        
        return modules
```

### 3.3 Predictive Activation (Pattern-Based, Proactive)

**Trigger:** Learned user patterns predict module will be needed soon

**Examples:**
- User opens email client at 9am daily → Pre-activate **Language Center** at 8:58am
- User typically voice-commands after lunch → Pre-activate **Auditory Agent** at 12:55pm
- User frequently checks calendar after coffee → Pre-activate **Skill Executor** when coffee detected

**Pattern Learning:**
```python
class PatternLearner:
    """Learns user patterns to predict module activation."""
    
    def __init__(self, db: PostgreSQL):
        self.db = db
        self.model = None  # Trained ML model (e.g., LightGBM)
    
    async def record_activation(self, module_id: str, context: Dict[str, Any]):
        """Record module activation with context."""
        await self.db.execute("""
            INSERT INTO module_activation_log 
            (module_id, timestamp, hour_of_day, day_of_week, 
             active_app, recent_activities, trigger_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, module_id, datetime.utcnow(), context['hour'], 
            context['day_of_week'], context['active_app'],
            json.dumps(context['recent_activities']), context['trigger_type'])
    
    async def train_model(self):
        """Train predictive model on historical activations."""
        # Fetch training data (last 30 days)
        data = await self.db.fetch("""
            SELECT 
                module_id,
                EXTRACT(HOUR FROM timestamp) as hour,
                EXTRACT(DOW FROM timestamp) as day_of_week,
                active_app,
                recent_activities,
                LAG(timestamp) OVER (PARTITION BY module_id ORDER BY timestamp) as prev_activation
            FROM module_activation_log
            WHERE timestamp > NOW() - INTERVAL '30 days'
            ORDER BY timestamp
        """)
        
        # Feature engineering
        features = []
        labels = []
        for row in data:
            # Features: [hour, day_of_week, time_since_last_activation, active_app_encoded, ...]
            feature_vec = self._extract_features(row)
            features.append(feature_vec)
            labels.append(row['module_id'])
        
        # Train multi-class classifier: context → module_id
        # Or: train per-module binary classifiers: context → will_activate_soon (0/1)
        self.model = LightGBMClassifier()
        self.model.fit(features, labels)
        
        logger.info(f"Pattern learner trained on {len(data)} samples")
    
    async def predict_next_activations(self, context: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Predict which modules will be needed soon."""
        if not self.model:
            return []
        
        feature_vec = self._extract_features(context)
        
        # Get probability distribution over all modules
        probabilities = self.model.predict_proba([feature_vec])[0]
        module_ids = self.model.classes_
        
        # Return modules with >70% activation probability (configurable threshold)
        predictions = [
            (module_id, prob)
            for module_id, prob in zip(module_ids, probabilities)
            if prob > 0.70  # Balanced preloading threshold
        ]
        
        return sorted(predictions, key=lambda x: x[1], reverse=True)
```

**Predictive Activation Loop:**
```python
class PredictiveActivationLoop:
    """Background task that pre-activates modules based on predictions."""
    
    async def run(self):
        """Run every 60 seconds."""
        while True:
            try:
                # Get current context
                context = await self.context_manager.get_current_context()
                
                # Predict next activations
                predictions = await self.pattern_learner.predict_next_activations(context)
                
                for module_id, confidence in predictions:
                    current_state = await self.activation_mgr.get_state(module_id)
                    
                    # Pre-load if currently unloaded/hibernated
                    if current_state in [ModuleState.UNLOADED, ModuleState.HIBERNATED]:
                        logger.info(
                            f"Predictive pre-load: {module_id} "
                            f"(confidence={confidence:.2f})"
                        )
                        await self.activation_mgr.activate(
                            module_id,
                            priority=Priority.LOW,  # Background preload
                            reason=f"predictive:{confidence:.2f}",
                            blocking=False
                        )
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Predictive activation loop error: {e}")
                await asyncio.sleep(60)
```

**Training Schedule:**
- **Initial training:** After 7 days of usage (sufficient data)
- **Incremental updates:** Daily at 3am (low-activity time)
- **Full retraining:** Weekly (Sunday 3am)

---

## 4. Eviction Policy (Weighted LRU → Learned)

When memory pressure occurs, the system must unload modules to free space.

### Phase 1: Weighted LRU (MVP)

**Eviction Score Formula:**

```
eviction_score = w1 × recency_score + w2 × frequency_score + w3 × importance_score

Where:
- recency_score = time_since_last_use / max_idle_time
  (Higher = less recently used = more evictable)
  
- frequency_score = 1 / (activations_per_hour + 1)
  (Higher = less frequently used = more evictable)
  
- importance_score = base_importance (per-module constant)
  (Higher = more important = less evictable)

Weights (tuned via experimentation):
- w1 = 0.4 (recency)
- w2 = 0.3 (frequency)
- w3 = 0.3 (importance)
```

**Module Importance Tiers:**
```python
MODULE_IMPORTANCE = {
    # Core (always in minimum active set, never evicted)
    'central_agent': 1.0,
    'working_memory_manager': 1.0,
    'event_bus': 1.0,
    
    # High importance (evict only under severe pressure)
    'language_center': 0.9,
    'skill_executor': 0.9,
    
    # Medium importance
    'visual_agent': 0.6,
    'auditory_agent': 0.6,
    'emotion_regulator': 0.6,
    
    # Lower importance (evict first)
    'voice_synthesis': 0.4,
    'character_animator': 0.4,
}
```

**Implementation:**
```python
class WeightedLRUEvictor:
    """Evicts modules based on weighted score."""
    
    def __init__(self):
        self.w1_recency = 0.4
        self.w2_frequency = 0.3
        self.w3_importance = 0.3
        self.max_idle_time = 3600  # 1 hour
    
    async def calculate_eviction_score(self, module_id: str) -> float:
        """Higher score = more evictable."""
        stats = await self.get_module_stats(module_id)
        
        # Recency score (0-1, higher = older)
        time_since_use = (datetime.utcnow() - stats['last_used']).total_seconds()
        recency_score = min(time_since_use / self.max_idle_time, 1.0)
        
        # Frequency score (0-1, higher = less frequent)
        activations_per_hour = stats['activation_count'] / stats['uptime_hours']
        frequency_score = 1.0 / (activations_per_hour + 1)
        
        # Importance score (0-1, higher = more important = LOWER evictability)
        importance = MODULE_IMPORTANCE.get(module_id, 0.5)
        importance_score = 1.0 - importance  # Invert: high importance = low evictability
        
        # Combined score
        score = (
            self.w1_recency * recency_score +
            self.w2_frequency * frequency_score +
            self.w3_importance * importance_score
        )
        
        return score
    
    async def select_eviction_candidate(
        self, 
        exclude_modules: Set[str]
    ) -> Optional[str]:
        """Select module to evict (highest score)."""
        all_modules = await self.activation_mgr.get_active_modules()
        
        candidates = [
            m for m in all_modules 
            if m not in exclude_modules  # Don't evict minimum active set
        ]
        
        if not candidates:
            return None  # No evictable modules
        
        # Calculate scores
        scores = {}
        for module_id in candidates:
            scores[module_id] = await self.calculate_eviction_score(module_id)
        
        # Return highest-scoring (most evictable) module
        evict_module = max(scores, key=scores.get)
        logger.info(
            f"Eviction candidate: {evict_module} "
            f"(score={scores[evict_module]:.3f})"
        )
        
        return evict_module
```

### Phase 2: Learned Eviction (Future Enhancement)

**Goal:** Use ML model to predict "probability module will be needed in next N minutes"

**Model:**
- **Input features:**
  - Current context (time, active app, recent activities)
  - Module characteristics (type, memory footprint, activation latency)
  - Historical usage patterns (frequency, recency, co-activation with other modules)
  
- **Output:** Probability module will be activated in next 5 minutes (0-1)

- **Training:**
  - Positive examples: Modules activated within 5 minutes of context snapshot
  - Negative examples: Modules NOT activated within 5 minutes
  - Train per-module binary classifiers

**Eviction Strategy:**
- Evict module with LOWEST probability of being needed soon
- Threshold: Only evict if P(needed_soon) < 0.20

**TODO:** Implement after 30+ days of usage data collected.

---

## 5. Dynamic Minimum Active Set

The **minimum active set** is the collection of modules that must stay loaded to maintain system responsiveness.

### 5.1 Core Modules (Always Active)

These never get evicted:

```python
CORE_MODULES = {
    'central_agent',           # Executive control
    'working_memory_manager',  # Redis interface
    'event_bus',               # Message routing
}
```

**Memory footprint:** ~150MB total

### 5.2 Context-Dependent Modules

Additional modules added to minimum active set based on user context:

```python
class DynamicMinimumSet:
    """Manages context-dependent minimum active set."""
    
    def __init__(self):
        self.base_set = CORE_MODULES.copy()
        self.context_rules = {
            # If user in email app, keep language center loaded
            'email_app_active': ['language_center'],
            
            # If screen sharing enabled, keep visual agent loaded
            'screen_sharing_on': ['visual_agent'],
            
            # If voice commands enabled, keep auditory agent loaded
            'voice_commands_enabled': ['auditory_agent'],
            
            # If executing skill, keep skill executor loaded
            'skill_executing': ['skill_executor'],
            
            # If user working (active input), keep language + visual loaded
            'user_working': ['language_center', 'visual_agent'],
        }
    
    async def get_minimum_active_set(self) -> Set[str]:
        """Return current minimum active set based on context."""
        context = await self.context_manager.get_context()
        
        active_set = self.base_set.copy()
        
        # Apply context rules
        for condition, modules in self.context_rules.items():
            if await self._check_condition(condition, context):
                active_set.update(modules)
        
        return active_set
    
    async def _check_condition(self, condition: str, context: Dict) -> bool:
        """Check if context condition is met."""
        if condition == 'email_app_active':
            return context.get('active_app') in ['thunderbird', 'evolution', 'geary']
        elif condition == 'screen_sharing_on':
            return context.get('screen_sharing_enabled', False)
        elif condition == 'voice_commands_enabled':
            return context.get('voice_commands_on', False)
        elif condition == 'skill_executing':
            return len(context.get('active_skills', [])) > 0
        elif condition == 'user_working':
            # User typed or clicked in last 5 minutes
            last_input = context.get('last_user_input_time')
            if last_input:
                idle_time = (datetime.utcnow() - last_input).total_seconds()
                return idle_time < 300  # 5 minutes
            return False
        return False
```

**Memory Overhead:**
- Minimum: 150MB (core only)
- Typical: 400-600MB (core + 2-3 context modules)
- Maximum: 800MB (core + all context modules)

### 5.3 User Overrides

Users can manually pin modules to stay loaded:

```python
# User settings (persisted in PostgreSQL)
user_pinned_modules = {
    'visual_agent',  # User: "I want screen awareness always on"
}

# Activation manager respects pinned modules
async def is_pinned(module_id: str) -> bool:
    return module_id in user_pinned_modules
```

---

## 6. Thrashing Prevention

**Thrashing:** Rapid load/unload cycles that waste CPU and delay responsiveness.

### 6.1 Hysteresis (Different Activation/Deactivation Thresholds)

**Concept:** Make it easier to stay loaded than to get loaded.

```python
class HysteresisPolicy:
    """Prevent oscillation with separate activation/deactivation thresholds."""
    
    ACTIVATION_THRESHOLD = 0.70   # Load if predicted need > 70%
    DEACTIVATION_THRESHOLD = 0.30  # Unload if predicted need < 30%
    
    # Gap of 40% prevents rapid oscillation
    
    async def should_activate(self, module_id: str, predicted_prob: float) -> bool:
        """Decide if module should be activated."""
        current_state = await self.activation_mgr.get_state(module_id)
        
        if current_state in [ModuleState.UNLOADED, ModuleState.HIBERNATED]:
            # Need strong signal to activate
            return predicted_prob > self.ACTIVATION_THRESHOLD
        elif current_state in [ModuleState.STANDBY, ModuleState.ACTIVE]:
            # Already loaded, keep it unless signal very weak
            return predicted_prob > self.DEACTIVATION_THRESHOLD
        
        return False
    
    async def should_deactivate(self, module_id: str, predicted_prob: float) -> bool:
        """Decide if module should be deactivated."""
        current_state = await self.activation_mgr.get_state(module_id)
        
        if current_state in [ModuleState.ACTIVE, ModuleState.STANDBY]:
            # Only unload if signal very weak
            return predicted_prob < self.DEACTIVATION_THRESHOLD
        
        return False
```

**Example Timeline:**
```
t=0s:   predicted_prob = 0.75 → ACTIVATE (> 0.70)
t=60s:  predicted_prob = 0.60 → KEEP LOADED (> 0.30)
t=120s: predicted_prob = 0.45 → KEEP LOADED (> 0.30)
t=180s: predicted_prob = 0.25 → DEACTIVATE (< 0.30)

Without hysteresis:
t=0s:   prob=0.75 → ACTIVATE
t=60s:  prob=0.60 → DEACTIVATE (< 0.70)
t=120s: prob=0.65 → ACTIVATE (> 0.70)
t=180s: prob=0.68 → KEEP
[THRASHING: load/unload/load cycles]
```

### 6.2 Cost-Based Eviction

**Principle:** Only evict if benefit outweighs cost.

```python
class CostBasedEvictor:
    """Only evict if memory savings justify reload cost."""
    
    async def should_evict(
        self,
        module_id: str,
        memory_urgency: float  # 0-1, how badly we need memory
    ) -> bool:
        """Decide if eviction is worth the cost."""
        # Benefit: Memory freed
        memory_footprint = await self.get_module_memory(module_id)
        benefit = memory_footprint * memory_urgency
        
        # Cost: Reload latency if needed again
        reload_latency = await self.get_module_reload_latency(module_id)
        predicted_reuse_prob = await self.predict_reuse_probability(module_id)
        expected_cost = reload_latency * predicted_reuse_prob
        
        # Evict if benefit > cost
        return benefit > expected_cost
    
    async def predict_reuse_probability(self, module_id: str) -> float:
        """Probability module will be needed in next 10 minutes."""
        # Use pattern learner or simple heuristic
        stats = await self.get_module_stats(module_id)
        
        # Simple heuristic: based on recent activation frequency
        recent_activations = stats['activations_last_hour']
        if recent_activations > 10:
            return 0.9  # Very likely to be reused
        elif recent_activations > 5:
            return 0.6
        elif recent_activations > 1:
            return 0.3
        else:
            return 0.1  # Unlikely to be reused soon
```

### 6.3 Cooldown Period

**Minimum loaded time:** After activation, module stays loaded for minimum duration.

```python
class ActivationManager:
    """Manages module lifecycle."""
    
    COOLDOWN_PERIOD = {
        'default': 300,  # 5 minutes
        'visual_agent': 600,  # 10 minutes (expensive to reload)
        'language_center': 180,  # 3 minutes (cheaper to reload)
    }
    
    async def activate(self, module_id: str, **kwargs):
        """Activate module and record activation time."""
        await self._load_module(module_id)
        
        # Record activation time
        await self.redis.hset(
            f"module:{module_id}:state",
            "last_activated_at",
            datetime.utcnow().isoformat()
        )
    
    async def can_deactivate(self, module_id: str) -> bool:
        """Check if enough time has passed since activation."""
        last_activated = await self.redis.hget(
            f"module:{module_id}:state",
            "last_activated_at"
        )
        
        if not last_activated:
            return True
        
        cooldown = self.COOLDOWN_PERIOD.get(module_id, self.COOLDOWN_PERIOD['default'])
        elapsed = (datetime.utcnow() - datetime.fromisoformat(last_activated)).total_seconds()
        
        return elapsed > cooldown
```

---

## 7. Preloading Strategy

**Goal:** Load modules before they're needed to minimize user-perceived latency.

### 7.1 Confidence Threshold

**Balanced Approach:** Preload if ≥70% confident module will be needed (user-configurable).

```python
class PreloadingManager:
    """Manages predictive preloading."""
    
    def __init__(self, config: Dict[str, Any]):
        self.confidence_threshold = config.get('preload_threshold', 0.70)
        self.max_preloaded_modules = config.get('max_preloaded', 3)
    
    async def preload_predicted_modules(self):
        """Preload modules based on predictions."""
        context = await self.context_manager.get_context()
        predictions = await self.pattern_learner.predict_next_activations(context)
        
        preload_count = 0
        for module_id, confidence in predictions:
            if confidence < self.confidence_threshold:
                continue  # Not confident enough
            
            if preload_count >= self.max_preloaded_modules:
                break  # Don't overload memory
            
            current_state = await self.activation_mgr.get_state(module_id)
            
            # Only preload if unloaded or hibernated
            if current_state in [ModuleState.UNLOADED, ModuleState.HIBERNATED]:
                logger.info(
                    f"Preloading {module_id} (confidence={confidence:.2f})"
                )
                await self.activation_mgr.activate(
                    module_id,
                    priority=Priority.LOW,  # Background load
                    reason=f"preload:{confidence:.2f}",
                    blocking=False
                )
                preload_count += 1
```

### 7.2 User-Configurable Aggressiveness

**Three presets:**

```python
PRELOAD_PROFILES = {
    'conservative': {
        'confidence_threshold': 0.90,
        'max_preloaded': 1,
        'description': 'Only preload when very confident, minimize memory usage'
    },
    'balanced': {
        'confidence_threshold': 0.70,
        'max_preloaded': 3,
        'description': 'Good tradeoff between responsiveness and memory (DEFAULT)'
    },
    'aggressive': {
        'confidence_threshold': 0.50,
        'max_preloaded': 5,
        'description': 'Maximum responsiveness, higher memory usage'
    }
}
```

**User setting:**
```python
# User can change in UI
user_preload_profile = 'balanced'  # Default
```

### 7.3 Preload Budgeting

**Memory constraint:** Preloading must not exceed memory budget.

```python
async def can_preload(self, module_id: str) -> bool:
    """Check if we have memory budget for preloading."""
    current_usage = await self.get_total_memory_usage()
    module_size = await self.get_module_memory(module_id)
    
    # Leave 20% headroom for dynamic allocations
    max_preload_usage = TOTAL_MEMORY_BUDGET * 0.80
    
    return (current_usage + module_size) < max_preload_usage
```

---

## 8. Power Management Integration

**Goal:** Adapt activation strategy to power state (battery vs. plugged in).

### 8.1 Power States

```python
class PowerState(Enum):
    PLUGGED_IN = 'plugged_in'    # AC power, no constraints
    BATTERY_HIGH = 'battery_high'  # > 50% battery
    BATTERY_MEDIUM = 'battery_medium'  # 20-50% battery
    BATTERY_LOW = 'battery_low'  # < 20% battery
    BATTERY_CRITICAL = 'battery_critical'  # < 5% battery
```

### 8.2 Power-Adaptive Policies

```python
class PowerAwareActivationPolicy:
    """Adjusts activation strategy based on power state."""
    
    POLICIES = {
        PowerState.PLUGGED_IN: {
            'max_active_modules': 10,
            'idle_timeout_multiplier': 1.0,  # Normal timeouts
            'preload_enabled': True,
            'preload_threshold': 0.70,
            'aggressive_eviction': False,
        },
        PowerState.BATTERY_HIGH: {
            'max_active_modules': 8,
            'idle_timeout_multiplier': 1.0,
            'preload_enabled': True,
            'preload_threshold': 0.75,  # Slightly more conservative
            'aggressive_eviction': False,
        },
        PowerState.BATTERY_MEDIUM: {
            'max_active_modules': 5,
            'idle_timeout_multiplier': 0.75,  # Faster timeouts
            'preload_enabled': True,
            'preload_threshold': 0.85,  # Much more conservative
            'aggressive_eviction': True,
        },
        PowerState.BATTERY_LOW: {
            'max_active_modules': 3,
            'idle_timeout_multiplier': 0.5,  # 2x faster unload
            'preload_enabled': False,  # Disable preloading
            'preload_threshold': None,
            'aggressive_eviction': True,
        },
        PowerState.BATTERY_CRITICAL: {
            'max_active_modules': 1,  # Only core modules
            'idle_timeout_multiplier': 0.25,  # 4x faster unload
            'preload_enabled': False,
            'preload_threshold': None,
            'aggressive_eviction': True,
        },
    }
    
    async def get_current_policy(self) -> Dict[str, Any]:
        """Get policy for current power state."""
        power_state = await self.power_monitor.get_state()
        return self.POLICIES[power_state]
    
    async def apply_power_policy(self):
        """Adjust activation manager settings based on power state."""
        policy = await self.get_current_policy()
        
        # Update activation manager
        self.activation_mgr.max_active_modules = policy['max_active_modules']
        self.activation_mgr.idle_timeout_multiplier = policy['idle_timeout_multiplier']
        
        # Update preloading
        self.preload_mgr.enabled = policy['preload_enabled']
        if policy['preload_threshold']:
            self.preload_mgr.confidence_threshold = policy['preload_threshold']
        
        # If aggressive eviction needed, trigger eviction pass
        if policy['aggressive_eviction']:
            await self.trigger_aggressive_eviction()
```

### 8.3 Power Monitoring

```python
class PowerMonitor:
    """Monitors power state via UPower (Linux)."""
    
    async def get_state(self) -> PowerState:
        """Get current power state."""
        # Query UPower via D-Bus
        output = await self.run_command("upower -i /org/freedesktop/UPower/devices/battery_BAT0")
        
        if "state: discharging" in output:
            # On battery
            percentage = self._parse_percentage(output)
            if percentage > 50:
                return PowerState.BATTERY_HIGH
            elif percentage > 20:
                return PowerState.BATTERY_MEDIUM
            elif percentage > 5:
                return PowerState.BATTERY_LOW
            else:
                return PowerState.BATTERY_CRITICAL
        else:
            # Plugged in
            return PowerState.PLUGGED_IN
    
    async def monitor_power_changes(self):
        """Background task: react to power state changes."""
        last_state = await self.get_state()
        
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            current_state = await self.get_state()
            
            if current_state != last_state:
                logger.info(f"Power state changed: {last_state} → {current_state}")
                await self.policy.apply_power_policy()
                last_state = current_state
```

### 8.4 Hybrid Mode (Auto + Manual Override)

**User can override automatic power management:**

```python
class PowerManagementSettings:
    """User-configurable power settings."""
    
    def __init__(self):
        self.mode = 'auto'  # 'auto' or 'manual'
        self.manual_profile = 'balanced'  # If manual mode
    
    async def get_effective_policy(self) -> Dict[str, Any]:
        """Get policy considering user override."""
        if self.mode == 'manual':
            # User manually selected a profile
            return self._get_manual_policy(self.manual_profile)
        else:
            # Auto-detect power state
            return await self.power_policy.get_current_policy()
    
    def _get_manual_policy(self, profile: str) -> Dict[str, Any]:
        """User-selected profiles."""
        profiles = {
            'maximum_performance': {
                # Equivalent to plugged-in policy
                'max_active_modules': 10,
                'idle_timeout_multiplier': 1.0,
                'preload_enabled': True,
                'preload_threshold': 0.70,
                'aggressive_eviction': False,
            },
            'balanced': {
                # Equivalent to battery-high policy
                'max_active_modules': 8,
                'idle_timeout_multiplier': 1.0,
                'preload_enabled': True,
                'preload_threshold': 0.75,
                'aggressive_eviction': False,
            },
            'power_saver': {
                # Equivalent to battery-medium policy
                'max_active_modules': 5,
                'idle_timeout_multiplier': 0.75,
                'preload_enabled': True,
                'preload_threshold': 0.85,
                'aggressive_eviction': True,
            },
        }
        return profiles[profile]
```

---

## 9. Staged Loading

**Goal:** Minimize user-perceived latency by loading critical components first.

### 9.1 Loading Stages

Each module is loaded in stages:

**Stage 1: Critical Path (50-100ms)**
- Load core inference engine
- Initialize minimal runtime state
- Module becomes **partially functional** (can process simple inputs)

**Stage 2: Full Functionality (200-500ms)**
- Load auxiliary models (if any)
- Warm up caches
- Module becomes **fully functional**

**Stage 3: Optimization (background, 1-3s)**
- Preload frequent assets
- Build indexes
- Module reaches **optimal performance**

### 9.2 Implementation

```python
class StagedModuleLoader:
    """Loads modules in stages for minimal perceived latency."""
    
    async def load_module(self, module_id: str, urgency: Priority) -> None:
        """Load module with staged approach."""
        module_config = await self.get_module_config(module_id)
        
        # Stage 1: Critical path (blocking)
        logger.info(f"Loading {module_id}: Stage 1 (critical)")
        await self._load_stage1(module_id, module_config)
        
        # Module is now minimally functional
        await self.activation_mgr.set_state(module_id, ModuleState.STANDBY)
        
        if urgency == Priority.HIGH:
            # For urgent loads, also block on Stage 2
            logger.info(f"Loading {module_id}: Stage 2 (full functionality)")
            await self._load_stage2(module_id, module_config)
            await self.activation_mgr.set_state(module_id, ModuleState.ACTIVE)
        else:
            # For non-urgent loads, do Stage 2 + 3 in background
            asyncio.create_task(self._load_stages2_and_3(module_id, module_config))
    
    async def _load_stage1(self, module_id: str, config: Dict[str, Any]):
        """Stage 1: Critical path."""
        # Load primary model
        model_path = config['primary_model']
        model = await self.model_loader.load_model(model_path)
        
        # Initialize minimal state
        state = await self.state_manager.init_minimal_state(module_id)
        
        # Register with message bus
        await self.message_bus.register_handler(module_id)
        
        # Store in module registry
        self.registry[module_id] = {
            'model': model,
            'state': state,
            'stage': 1,
        }
    
    async def _load_stage2(self, module_id: str, config: Dict[str, Any]):
        """Stage 2: Full functionality."""
        module = self.registry[module_id]
        
        # Load auxiliary models (if any)
        for aux_model_path in config.get('auxiliary_models', []):
            aux_model = await self.model_loader.load_model(aux_model_path)
            module['auxiliary_models'] = module.get('auxiliary_models', [])
            module['auxiliary_models'].append(aux_model)
        
        # Initialize full state
        await self.state_manager.init_full_state(module_id)
        
        # Warm up caches (run dummy inference)
        await self._warmup_cache(module_id)
        
        module['stage'] = 2
    
    async def _load_stage3(self, module_id: str, config: Dict[str, Any]):
        """Stage 3: Optimization (background)."""
        module = self.registry[module_id]
        
        # Preload frequently used assets
        for asset in config.get('frequent_assets', []):
            await self.asset_loader.preload(asset)
        
        # Build indexes (e.g., skill lookup tables)
        if 'index_builder' in config:
            await config['index_builder'].build()
        
        module['stage'] = 3
        logger.info(f"{module_id} reached optimal performance (Stage 3)")
    
    async def _load_stages2_and_3(self, module_id: str, config: Dict[str, Any]):
        """Background loading of stages 2 and 3."""
        try:
            await self._load_stage2(module_id, config)
            await self.activation_mgr.set_state(module_id, ModuleState.ACTIVE)
            
            await self._load_stage3(module_id, config)
        except Exception as e:
            logger.error(f"Background loading failed for {module_id}: {e}")
```

### 9.3 Degraded Operation

**If Stage 1 loaded but Stage 2 pending:**

```python
class VisualAgentPartial:
    """Visual agent with only Stage 1 loaded."""
    
    async def process_frame(self, frame: np.ndarray):
        """Process with degraded capability."""
        if self.stage == 1:
            # Only basic object detection available
            objects = await self.basic_detector.detect(frame)
            return {'objects': objects, 'degraded': True}
        elif self.stage >= 2:
            # Full processing: object detection + OCR + scene understanding
            objects = await self.advanced_detector.detect(frame)
            text = await self.ocr.extract_text(frame)
            scene = await self.scene_classifier.classify(frame)
            return {'objects': objects, 'text': text, 'scene': scene, 'degraded': False}
```

**User notification:**
```
"Visual Agent is starting up (basic mode), full capabilities in 3 seconds..."
```

---

## 10. Module Registry Schema

**Stores metadata about all modules.**

### PostgreSQL Schema

```sql
-- Module definitions
CREATE TABLE modules (
    module_id VARCHAR(64) PRIMARY KEY,
    module_name VARCHAR(128) NOT NULL,
    module_type VARCHAR(32) NOT NULL,  -- 'cognitive', 'sensory', 'motor', 'utility'
    
    -- Resource requirements
    memory_footprint_mb INT NOT NULL,  -- MB when fully loaded
    gpu_memory_mb INT DEFAULT 0,       -- GPU memory (future)
    power_draw_watts FLOAT DEFAULT 0,  -- Estimated power draw when active
    
    -- Loading characteristics
    stage1_latency_ms INT NOT NULL,    -- Critical path load time
    stage2_latency_ms INT NOT NULL,    -- Full functionality load time
    stage3_latency_ms INT DEFAULT 0,   -- Optimization time
    
    -- Importance
    base_importance FLOAT NOT NULL,    -- 0-1, used in eviction scoring
    
    -- Configuration
    config JSONB NOT NULL,             -- Module-specific config
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Module activation history
CREATE TABLE module_activation_log (
    id BIGSERIAL PRIMARY KEY,
    module_id VARCHAR(64) REFERENCES modules(module_id),
    timestamp TIMESTAMP NOT NULL,
    
    -- Context at activation time
    hour_of_day INT NOT NULL,
    day_of_week INT NOT NULL,
    active_app VARCHAR(128),
    recent_activities JSONB,  -- Last 5 user activities
    
    -- Activation details
    trigger_type VARCHAR(32) NOT NULL,  -- 'input_driven', 'goal_driven', 'predictive'
    priority VARCHAR(16) NOT NULL,      -- 'low', 'medium', 'high'
    reason VARCHAR(256),
    
    -- Performance metrics
    load_latency_ms INT,               -- Actual load time
    was_preloaded BOOLEAN DEFAULT FALSE,
    
    INDEX idx_module_timestamp (module_id, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- Module state transitions
CREATE TABLE module_state_transitions (
    id BIGSERIAL PRIMARY KEY,
    module_id VARCHAR(64) REFERENCES modules(module_id),
    timestamp TIMESTAMP NOT NULL,
    
    from_state VARCHAR(16) NOT NULL,  -- 'active', 'standby', 'hibernated', etc.
    to_state VARCHAR(16) NOT NULL,
    reason VARCHAR(256),
    
    INDEX idx_module_timestamp (module_id, timestamp)
);

-- Module runtime stats (rolling window)
CREATE TABLE module_stats (
    module_id VARCHAR(64) PRIMARY KEY REFERENCES modules(module_id),
    
    -- Activation metrics
    total_activations BIGINT DEFAULT 0,
    activations_last_hour INT DEFAULT 0,
    activations_last_day INT DEFAULT 0,
    last_activated_at TIMESTAMP,
    
    -- Usage metrics
    total_uptime_seconds BIGINT DEFAULT 0,
    average_session_duration_seconds INT,
    
    -- Performance metrics
    average_load_latency_ms INT,
    p95_load_latency_ms INT,
    
    -- Eviction metrics
    total_evictions INT DEFAULT 0,
    
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Redis State (Real-Time)

```python
# Current state for each module
# Key: module:{module_id}:state
# Value: Hash
{
    'state': 'active',  # 'active', 'standby', 'hibernated', 'suspended', 'unloaded'
    'stage': 2,         # Loading stage (1-3)
    'last_activated_at': '2026-02-21T02:30:00Z',
    'last_used_at': '2026-02-21T02:31:00Z',
    'activation_count': 42,
    'uptime_seconds': 1800,
    'is_pinned': 'false',  # User-pinned
}

# Current memory usage
# Key: memory:usage
# Value: Hash
{
    'total_mb': 650,
    'core_modules_mb': 150,
    'cognitive_modules_mb': 400,
    'other_mb': 100,
    'budget_mb': 1000,
    'utilization': 0.65,
}

# Minimum active set (dynamically updated)
# Key: activation:minimum_active_set
# Value: Set
['central_agent', 'working_memory_manager', 'event_bus', 'language_center', 'visual_agent']
```

---

## 11. Activation Manager Implementation

**Core orchestrator for module lifecycle.**

```python
class ActivationManager:
    """Manages module activation, eviction, and state transitions."""
    
    def __init__(
        self,
        redis: Redis,
        db: PostgreSQL,
        loader: StagedModuleLoader,
        evictor: WeightedLRUEvictor,
        power_policy: PowerAwareActivationPolicy,
    ):
        self.redis = redis
        self.db = db
        self.loader = loader
        self.evictor = evictor
        self.power_policy = power_policy
        
        self.registry = {}  # In-memory module objects
        
    # ===== State Management =====
    
    async def get_state(self, module_id: str) -> ModuleState:
        """Get current state of module."""
        state_str = await self.redis.hget(f"module:{module_id}:state", "state")
        if not state_str:
            return ModuleState.UNLOADED
        return ModuleState(state_str)
    
    async def set_state(self, module_id: str, state: ModuleState):
        """Set module state and log transition."""
        old_state = await self.get_state(module_id)
        
        await self.redis.hset(
            f"module:{module_id}:state",
            "state",
            state.value
        )
        
        # Log transition
        await self.db.execute("""
            INSERT INTO module_state_transitions (module_id, timestamp, from_state, to_state)
            VALUES ($1, $2, $3, $4)
        """, module_id, datetime.utcnow(), old_state.value, state.value)
        
        logger.info(f"Module {module_id}: {old_state.value} → {state.value}")
    
    # ===== Activation =====
    
    async def activate(
        self,
        module_id: str,
        priority: Priority = Priority.MEDIUM,
        reason: str = "",
        blocking: bool = True
    ) -> bool:
        """Activate a module."""
        current_state = await self.get_state(module_id)
        
        # If already active, just wake up
        if current_state == ModuleState.ACTIVE:
            await self._update_usage_stats(module_id)
            return True
        
        # If in standby, quick wake
        if current_state == ModuleState.STANDBY:
            await self._wake_from_standby(module_id)
            return True
        
        # Otherwise, need to load
        logger.info(f"Activating {module_id} (priority={priority}, reason={reason})")
        
        # Check memory budget
        if not await self._check_memory_budget(module_id):
            # Need to evict
            await self._evict_to_make_room(module_id)
        
        # Load module (staged)
        start_time = time.time()
        await self.loader.load_module(module_id, priority)
        load_latency = int((time.time() - start_time) * 1000)
        
        # Log activation
        await self._log_activation(module_id, priority, reason, load_latency)
        
        # Update stats
        await self._update_activation_stats(module_id)
        
        return True
    
    async def _wake_from_standby(self, module_id: str):
        """Wake module from standby to active."""
        await self.set_state(module_id, ModuleState.ACTIVE)
        
        # Notify module to resume processing
        await self.message_bus.publish(
            f"module.{module_id}.wake",
            {}
        )
        
        await self._update_usage_stats(module_id)
    
    # ===== Deactivation =====
    
    async def deactivate(
        self,
        module_id: str,
        target_state: ModuleState = ModuleState.STANDBY,
        reason: str = ""
    ):
        """Deactivate a module."""
        current_state = await self.get_state(module_id)
        
        # Check if in minimum active set
        min_set = await self._get_minimum_active_set()
        if module_id in min_set:
            logger.warning(f"Cannot deactivate {module_id}: in minimum active set")
            return
        
        # Check if pinned
        is_pinned = await self.redis.hget(f"module:{module_id}:state", "is_pinned")
        if is_pinned == 'true':
            logger.warning(f"Cannot deactivate {module_id}: user-pinned")
            return
        
        # Check cooldown
        if not await self._can_deactivate(module_id):
            logger.info(f"Cannot deactivate {module_id}: in cooldown period")
            return
        
        logger.info(f"Deactivating {module_id} → {target_state.value} (reason={reason})")
        
        if target_state == ModuleState.STANDBY:
            # Keep in memory, stop processing
            await self.message_bus.publish(f"module.{module_id}.pause", {})
            await self.set_state(module_id, ModuleState.STANDBY)
        
        elif target_state == ModuleState.HIBERNATED:
            # Save state, unload models
            await self._hibernate_module(module_id)
            await self.set_state(module_id, ModuleState.HIBERNATED)
        
        elif target_state == ModuleState.UNLOADED:
            # Fully unload
            await self._unload_module(module_id)
            await self.set_state(module_id, ModuleState.UNLOADED)
    
    async def _hibernate_module(self, module_id: str):
        """Hibernate: save state, unload models."""
        module = self.registry.get(module_id)
        if not module:
            return
        
        # Save state to Redis
        state = module['state']
        await self.redis.set(
            f"module:{module_id}:hibernated_state",
            pickle.dumps(state),
            ex=3600  # 1 hour TTL
        )
        
        # Unload models from memory
        del module['model']
        if 'auxiliary_models' in module:
            del module['auxiliary_models']
        
        # Keep minimal metadata
        module['stage'] = 0
    
    async def _unload_module(self, module_id: str):
        """Fully unload module."""
        if module_id in self.registry:
            del self.registry[module_id]
        
        await self.redis.delete(f"module:{module_id}:hibernated_state")
    
    # ===== Memory Management =====
    
    async def _check_memory_budget(self, module_id: str) -> bool:
        """Check if there's room to load module."""
        module_meta = await self.db.fetchrow(
            "SELECT memory_footprint_mb FROM modules WHERE module_id = $1",
            module_id
        )
        
        required_mb = module_meta['memory_footprint_mb']
        
        current_usage = await self._get_total_memory_usage()
        policy = await self.power_policy.get_current_policy()
        budget_mb = 1000  # Total budget (from resource allocation)
        
        return (current_usage + required_mb) < budget_mb
    
    async def _evict_to_make_room(self, new_module_id: str):
        """Evict modules until there's room for new module."""
        module_meta = await self.db.fetchrow(
            "SELECT memory_footprint_mb FROM modules WHERE module_id = $1",
            new_module_id
        )
        required_mb = module_meta['memory_footprint_mb']
        
        min_set = await self._get_minimum_active_set()
        
        while not await self._check_memory_budget(new_module_id):
            # Select eviction candidate
            evict_module = await self.evictor.select_eviction_candidate(
                exclude_modules=min_set
            )
            
            if not evict_module:
                raise MemoryError(f"Cannot free memory for {new_module_id}")
            
            # Evict
            await self.deactivate(
                evict_module,
                target_state=ModuleState.HIBERNATED,
                reason=f"evicted_for:{new_module_id}"
            )
            
            logger.info(f"Evicted {evict_module} to make room for {new_module_id}")
    
    async def _get_total_memory_usage(self) -> int:
        """Get total memory usage in MB."""
        usage = await self.redis.hget("memory:usage", "total_mb")
        return int(usage) if usage else 0
    
    async def _get_minimum_active_set(self) -> Set[str]:
        """Get current minimum active set."""
        members = await self.redis.smembers("activation:minimum_active_set")
        return set(members)
    
    # ===== Stats & Logging =====
    
    async def _log_activation(
        self,
        module_id: str,
        priority: Priority,
        reason: str,
        load_latency: int
    ):
        """Log activation to PostgreSQL."""
        context = await self.context_manager.get_context()
        
        await self.db.execute("""
            INSERT INTO module_activation_log
            (module_id, timestamp, hour_of_day, day_of_week, active_app,
             recent_activities, trigger_type, priority, reason, load_latency_ms)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, 
            module_id,
            datetime.utcnow(),
            datetime.utcnow().hour,
            datetime.utcnow().weekday(),
            context.get('active_app'),
            json.dumps(context.get('recent_activities', [])),
            reason.split(':')[0] if ':' in reason else 'manual',
            priority.value,
            reason,
            load_latency
        )
    
    async def _update_activation_stats(self, module_id: str):
        """Update module activation stats."""
        await self.db.execute("""
            INSERT INTO module_stats (module_id, total_activations, last_activated_at, updated_at)
            VALUES ($1, 1, $2, $2)
            ON CONFLICT (module_id) DO UPDATE SET
                total_activations = module_stats.total_activations + 1,
                last_activated_at = $2,
                updated_at = $2
        """, module_id, datetime.utcnow())
        
        await self.redis.hincrby(f"module:{module_id}:state", "activation_count", 1)
        await self.redis.hset(
            f"module:{module_id}:state",
            "last_activated_at",
            datetime.utcnow().isoformat()
        )
    
    async def _update_usage_stats(self, module_id: str):
        """Update last_used timestamp."""
        await self.redis.hset(
            f"module:{module_id}:state",
            "last_used_at",
            datetime.utcnow().isoformat()
        )
    
    async def _can_deactivate(self, module_id: str) -> bool:
        """Check if cooldown period has passed."""
        last_activated = await self.redis.hget(
            f"module:{module_id}:state",
            "last_activated_at"
        )
        
        if not last_activated:
            return True
        
        cooldown = 300  # 5 minutes default
        elapsed = (datetime.utcnow() - datetime.fromisoformat(last_activated)).total_seconds()
        
        return elapsed > cooldown
```

---

## 12. Memory Budget Allocation

**Total available:** 8GB RAM on RPi5

**System overhead:** ~2GB (OS, Docker, databases)

**Available for modules:** ~6GB

**Allocation strategy:**

```python
MEMORY_BUDGET = {
    # Core (always loaded)
    'central_agent': 100,          # MB
    'working_memory_manager': 30,
    'event_bus': 20,
    
    # Cognitive modules (load on demand)
    'language_center': 150,        # DistilBERT + runtime
    'skill_executor': 200,         # Models + skill cache
    'emotion_regulator': 80,
    
    # Sensory modules
    'visual_agent': 180,           # Object detection + OCR
    'auditory_agent': 120,         # Whisper-tiny + VAD
    
    # Motor modules
    'voice_synthesis': 100,        # Piper TTS
    'character_animator': 60,
    
    # Utility
    'tool_plugin_system': 50,
    
    # Shared resources
    'model_cache': 200,            # Shared model weights (quantized)
    'runtime_buffers': 100,        # Dynamic allocations
    
    # Headroom
    'reserved': 300,               # Safety margin for spikes
}

TOTAL_ALLOCATED = sum(MEMORY_BUDGET.values())  # ~1690 MB
```

**Dynamic budget tracking:**

```python
class MemoryBudgetTracker:
    """Tracks memory usage against budget."""
    
    async def update_usage(self):
        """Update current memory usage in Redis."""
        # Query actual memory usage
        core_usage = sum([
            await self._get_module_memory('central_agent'),
            await self._get_module_memory('working_memory_manager'),
            await self._get_module_memory('event_bus'),
        ])
        
        cognitive_usage = sum([
            await self._get_module_memory(m)
            for m in ['language_center', 'skill_executor', 'emotion_regulator']
            if await self.activation_mgr.get_state(m) != ModuleState.UNLOADED
        ])
        
        # ... similar for other categories
        
        total = core_usage + cognitive_usage + sensory_usage + motor_usage + other_usage
        
        await self.redis.hmset("memory:usage", {
            'total_mb': total,
            'core_modules_mb': core_usage,
            'cognitive_modules_mb': cognitive_usage,
            'budget_mb': 1690,
            'utilization': total / 1690,
        })
    
    async def get_available_memory(self) -> int:
        """Get available memory in MB."""
        total = int(await self.redis.hget("memory:usage", "total_mb") or 0)
        budget = 1690
        return budget - total
```

---

## 13. Monitoring & Metrics

**Dashboards for observability:**

### 13.1 Real-Time Metrics (Redis + Prometheus)

```python
# Expose metrics for Prometheus scraping
class ActivationMetrics:
    """Prometheus metrics for module activation."""
    
    def __init__(self):
        self.activation_counter = Counter(
            'module_activations_total',
            'Total module activations',
            ['module_id', 'trigger_type']
        )
        
        self.deactivation_counter = Counter(
            'module_deactivations_total',
            'Total module deactivations',
            ['module_id', 'reason']
        )
        
        self.state_gauge = Gauge(
            'module_state',
            'Current module state (0=unloaded, 1=hibernated, 2=standby, 3=active)',
            ['module_id']
        )
        
        self.memory_gauge = Gauge(
            'module_memory_mb',
            'Memory used by module',
            ['module_id']
        )
        
        self.load_latency_histogram = Histogram(
            'module_load_latency_seconds',
            'Module load latency',
            ['module_id', 'stage']
        )
        
        self.eviction_counter = Counter(
            'module_evictions_total',
            'Total module evictions',
            ['module_id']
        )
```

### 13.2 Logs

**Structured logging:**
```json
{
  "timestamp": "2026-02-21T02:31:45Z",
  "level": "INFO",
  "component": "activation_manager",
  "event": "module_activated",
  "module_id": "visual_agent",
  "trigger_type": "input_driven",
  "priority": "high",
  "load_latency_ms": 312,
  "current_memory_mb": 680,
  "memory_utilization": 0.67
}
```

### 13.3 User-Facing Dashboard

**Show in UI:**
- Active modules (with state badges: 🟢 Active, 🟡 Standby, ⚪ Unloaded)
- Memory usage bar (650 MB / 1000 MB)
- Power state (🔌 Plugged In | 🔋 Battery 78%)
- Recent activations timeline

---

## 14. Resource Estimates

### Memory Footprint

**Core modules (always loaded):**
- Central Agent: 100 MB
- Working Memory Manager: 30 MB
- Event Bus: 20 MB
- **Subtotal: 150 MB**

**Typical active set (user working):**
- Core: 150 MB
- Language Center: 150 MB
- Visual Agent: 180 MB
- **Subtotal: 480 MB**

**Maximum active set (all modules):**
- Core + All Cognitive + All Sensory + All Motor: ~1200 MB

**Average utilization:** 500-700 MB (50-70% of budget)

### CPU Usage

**Active modules:**
- Visual Agent (5 FPS): ~15% CPU
- Auditory Agent (continuous VAD): ~8% CPU
- Language Center (on-demand): ~20% CPU during inference
- Central Agent (decision loop): ~5% CPU

**Idle modules:** <1% CPU (just message bus listening)

### Power Consumption

**Plugged in:** 12-18W (depends on active modules)
**Battery (balanced):** 8-12W
**Battery (power saver):** 5-8W

**Module-specific:**
- Visual Agent (active): ~3W
- Auditory Agent (active): ~2W
- Language Center (inference): ~4W

### Storage

**Module models:** ~800 MB total
**Activation logs:** ~50 MB/month (compressed)
**Hibernated states:** ~100 MB (transient)

---

## 15. Summary & Next Steps

### Design Complete ✅

**Module Activation Strategy includes:**
1. ✅ 5-state FSM (Active, Standby, Hibernated, Suspended, Unloaded)
2. ✅ Triple activation triggers (Input, Goal, Predictive)
3. ✅ Weighted LRU eviction (upgradeable to learned)
4. ✅ Dynamic minimum active set
5. ✅ Thrashing prevention (hysteresis + cost-based)
6. ✅ Balanced preloading (70% threshold, user-configurable)
7. ✅ Hybrid power management (auto + manual override)
8. ✅ Staged loading (3 stages)

### TODOs (Implementation Phase)

**Phase 1 (MVP):**
- [ ] Implement ActivationManager core
- [ ] Implement StagedModuleLoader
- [ ] Implement WeightedLRUEvictor
- [ ] Integrate with existing Central Agent

**Phase 2 (Optimization):**
- [ ] Implement PatternLearner (predictive activation)
- [ ] Train prediction models (after 30 days usage)
- [ ] Implement cost-based eviction
- [ ] Add power management integration

**Phase 3 (Advanced):**
- [ ] Upgrade to learned eviction policy
- [ ] Add GPU memory management (future)
- [ ] Optimize stage loading times

### Integration Points

**With Central Agent:**
- Goal-driven activation requests
- Working memory state queries

**With Memory Consolidation:**
- Hibernate/unload triggers during consolidation
- Memory pressure signals

**With Skill Tree:**
- Skill Executor activation on skill execution
- Model loading for skill-specific models

**With Tool Plugin System:**
- Tool plugin activation on tool access
- Sandbox container lifecycle

---

**Design Status:** ✅ COMPLETE  
**Ready for:** Implementation Phase 1  
**Estimated Implementation Time:** 3-4 weeks
