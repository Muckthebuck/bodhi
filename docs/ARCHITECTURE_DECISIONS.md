# Bodhi - Consolidated Architectural Decisions

**Last Updated:** 2026-02-14  
**Status:** Foundation Phase - Core Architecture Defined

---

## 1. Learning & Skill Acquisition System

### 1.1 Three-Tier Memory System
**Mimicking human memory structure:**

| Memory Type | Database | Purpose | Retention | Update Frequency |
|-------------|----------|---------|-----------|------------------|
| **Working Memory** | Redis | Active context, current conversation, immediate state | Seconds to minutes | Real-time (ms) |
| **Short-term Memory** | Qdrant (Vector DB) | Recent interactions, semantic search, episodic memory | Hours to days | Every interaction |
| **Long-term Memory** | PostgreSQL | User preferences, learned behaviors, historical data, skills | Permanent | Consolidation cycles |

### 1.2 Learning Modalities (All Three Active)

**Procedural Memory (Skills & Habits)**
- Motor skills: Character animation, gesture control, screen interaction
- Automated routines: Morning email check, document organization
- Storage: Skill tree in PostgreSQL + trained model weights
- Practice: During downtime with simulation

**Declarative Memory (Facts & Knowledge)**
- Semantic: General knowledge, concepts, relationships
- Episodic: User-specific events, conversations, preferences
- Storage: Structured data in PostgreSQL + embeddings in Qdrant
- Retrieval: Semantic search for context-aware responses

**Meta-Learning (Learning to Learn)**
- Curriculum design: Trainer agent optimizes learning paths
- Transfer learning: Apply knowledge from one domain to another
- Skill reuse: Identify when existing skills apply to new tasks
- Storage: Learning strategies in PostgreSQL, meta-parameters

---

## 2. Downtime Learning & Sleep Cycles

### 2.1 Hybrid Sleep Model (Scheduled + Opportunistic)

**Scheduled Sleep (Circadian Rhythm)**
- Companion matches **user's sleep schedule**
- User configures sleep hours (e.g., 2am-6am)
- Deep consolidation tasks: Memory transfer, skill training, model updates
- Cannot be interrupted (unless emergency override)

**Opportunistic Learning**
- Triggers:
  - User inactivity (no input for configurable threshold, e.g., 15 min)
  - System load is low (CPU/RAM below threshold)
  - No high-priority tasks pending
- Light tasks: Quick skill practice, memory consolidation, log analysis
- Interruptible: Immediately wake if user returns

**System Load Awareness**
- Client vs Host architecture consideration:
  - **Same machine**: Conservative (don't interfere with user tasks)
  - **Separate host**: Aggressive (can use full resources when user not interacting)
- Monitor: CPU, RAM, disk I/O, network bandwidth
- Dynamic throttling: Reduce training intensity if system under pressure

### 2.2 Sleep States

| State | Trigger | Active Processes | Power |
|-------|---------|------------------|-------|
| **Awake** | User present | All modules active | 15-20W |
| **Light Sleep** | 15 min idle | Background consolidation, sensory agents paused | 8-12W |
| **Deep Sleep** | Scheduled sleep hours | Intensive training, memory consolidation | 5-8W |
| **Hibernate** | User manual toggle | Only core services, minimal logging | 3-5W |

---

## 3. Simulation Environment (Hybrid Approach)

**All three simulation methods used contextually:**

### 3.1 World Model (Model-Based RL)
**Use cases:** Complex, multi-step tasks (e.g., email workflow automation)

- Companion builds internal model of:
  - User behavior patterns (what user does when)
  - System responses (UI interactions, API results)
  - Causal relationships (action → outcome)
- Train policies in simulated environment
- Validate in real world → update world model iteratively
- **Storage:** ~200-500MB model (quantized), retrained weekly

### 3.2 Replay Buffer (Experience Replay)
**Use cases:** Reinforcement of known skills, pattern refinement

- Store past experiences: (state, action, outcome, reward)
- Replay during downtime for policy improvement
- Prioritized replay: Focus on rare/important experiences
- **Storage:** Rolling buffer (last 10k experiences, ~50MB)

### 3.3 Synthetic Scenarios (Procedural Generation)
**Use cases:** Novel situations, creativity training, edge cases

- Generate hypothetical contexts: "What if user asks X?"
- Combine known patterns in new ways
- Test robustness of learned skills
- **Evaluation:** User feedback on synthetic responses

**Orchestration:** Trainer Agent selects simulation method based on skill being learned

---

## 4. Skill Tree Architecture

### 4.1 Core Principles

**Skills are compositional:**
- High-level skills decompose into mid-level, then atomic actions
- Example: "Manage Email" → "Categorize" + "Draft Reply" → "Read" + "Classify" + "Generate Text"

**Skills are reusable:**
- Sub-skills shared across domains (e.g., "Text Classification" in email AND documents)
- Transfer learning: Apply learned skills to new contexts

**Skills are root-context dependent:**
- Same skill tree structure, but root goal changes by domain
- "Manage User's Email" is root goal in email domain
- But "Email Management" is sub-skill in "Productivity Assistant" domain

**Skills level up:**
- Metrics: Success rate, user satisfaction, usage frequency
- Levels: Novice (0-50%) → Competent (50-80%) → Expert (80-95%) → Master (95%+)
- Level affects: Confidence in using skill, autonomy (expert skills need less approval)

### 4.2 Skill Representation (To Be Refined)

**Current considerations:**
- **Hierarchical Graph (DAG):** For skill dependencies and composition
- **Behavior Trees:** For execution logic (sequence, fallback, parallel)
- **Neural Modules:** For learned components (inference models)

**Deferred decision:** Exact schema needs prototyping, revisit in implementation phase

### 4.3 Skill Lifecycle

```
1. IDENTIFY GAP
   User needs capability → Companion lacks skill
   ↓
2. TRAINER AGENT DESIGNS CURRICULUM
   Prerequisites → Core skill → Refinements
   ↓
3. ACQUIRE TRAINING DATA
   Observe user, synthetic generation, transfer learning
   ↓
4. PRACTICE IN SIMULATION
   During downtime, test in world model/replay/synthetic
   ↓
5. VALIDATE IN REAL WORLD
   Low-risk trial with user approval
   ↓
6. CERTIFICATION
   Success rate > threshold → Mark skill as competent
   ↓
7. CONTINUOUS IMPROVEMENT
   Ongoing practice, user feedback integration
```

---

## 5. Module Activation Strategy

### 5.1 Brain-Inspired Selective Activation

**Not all modules active at all times (energy efficiency like human brain):**

**Input-Driven Activation (Bottom-Up)**
- Visual input → Activate Visual Agent
- Audio input → Activate Auditory Agent  
- No input for threshold → Deactivate sensory agents

**Goal-Driven Activation (Top-Down)**
- User asks question → Activate Language + Memory
- Need to respond → Activate Emotion + Voice
- Task complete → Deactivate task-specific modules

**Hybrid Attention Budget**
- Central Agent manages compute allocation
- Prioritizes modules based on:
  - Input salience (important event detected)
  - Current goal priority (what companion is trying to do)
  - Resource constraints (CPU/RAM/power limits)

### 5.2 Module States

**Fully Loaded (Active)**
- Model in RAM, processing inputs, consuming CPU/GPU
- State: Responding to events in real-time
- Power: 2-5W per module (depending on model size)

**Idle (Loaded but Paused)**
- Model in RAM but not processing
- State: Can resume instantly (<10ms)
- Power: 0.5-1W per module (memory overhead)

**Unloaded (Deactivated)**
- Model not in RAM, stored on disk
- State: Requires loading (1-5 seconds depending on size)
- Power: 0W

### 5.3 Thrashing Prevention

**LRU (Least Recently Used) Eviction**
- Modules idle for >X minutes eligible for unload
- Exception: Frequently used modules stay loaded (user pattern analysis)

**Minimum Active Set**
- Always loaded: Central Agent, Hippocampus (memory manager), Evaluation Agent
- Context-dependent: If user writing code, keep Language Agent loaded even if idle

**Adaptive Loading**
- Learn user patterns: "User usually checks email at 9am" → Pre-load email modules at 8:55am
- Predictive activation: Anticipate next action based on current context

**Deferred refinement:** Exact thresholds and heuristics TBD during profiling

---

## 6. Trainer Agent Architecture

### 6.1 Deployment: Separate Container (Decided)

**Rationale:**
- **Isolation:** Training doesn't interfere with real-time inference
- **Resource allocation:** Can throttle training when main system under load
- **Fault tolerance:** Training crash doesn't affect companion's operation
- **Scalability:** Can offload training to more powerful host machine

**vs. Part of Central Agent (Rejected):**
- Would compete for resources with real-time decision-making
- Training bugs could destabilize main system
- Harder to distribute training load

### 6.2 Trainer Agent Responsibilities

**1. Skill Gap Analysis**
- Detect when user needs capability companion lacks
- Trigger: User explicitly requests, or repeated task companion can't help with
- Output: Skill requirement specification

**2. Curriculum Design**
- Break skill into learnable sub-components
- Sequence learning (prerequisites first)
- Estimate training time and data requirements

**3. Training Orchestration**
- Schedule training during downtime slots
- Select simulation method (world model, replay, synthetic)
- Monitor progress, adjust hyperparameters

**4. Progress Tracking**
- Metrics: Success rate, user satisfaction, convergence rate
- Intermediate checkpoints: Save model every N training steps
- Report to user: Silent (background), progress bar (foreground), detailed report (client app)

**5. Skill Certification**
- Threshold: Success rate >X% (skill-dependent, e.g., 90% for critical tasks)
- Validation: Test on held-out scenarios, user acceptance test
- Deployment: Mark skill as "ready," enable in production

### 6.3 Training Methods (Hybrid, Context-Dependent)

**Fine-Tune Existing Models (LoRA)**
- Use case: Adapt language model to user's writing style
- Size: ~10-50MB per adaptation
- Time: 1-4 hours on RPi5 (or offload to PC)

**Train Skill-Specific Models**
- Use case: Custom email classifier, document tagger
- Size: ~20-100MB (small neural nets)
- Time: 30 min - 2 hours

**Prompt Engineering (No Weight Updates)**
- Use case: Simple task variations, instruction following
- Size: 0MB (just text prompts)
- Time: Instant (test prompt quality)

### 6.4 Training Data Sources

**Observed Data (Primary)**
- User actions, screen capture, interactions
- Privacy: Requires explicit user permission per data type

**Historical Data (If Provided)**
- User imports past emails, documents, logs
- Opt-in: User decides what to share

**Synthetic Data**
- Generated by companion's world model
- Augmentation: Variations on real data

**Transfer Learning**
- Pre-trained models adapted to user's context
- Open-source models (BERT, GPT, Vision models)

### 6.5 Training Progress Reporting

**Silent Mode (User Not Active)**
- No UI, just logging
- Triggered: During scheduled sleep, user away

**Progress Bar (User Present)**
- Visible notification: "Learning email management: 45%"
- Dismissible, non-intrusive
- Triggered: Opportunistic learning while user working

**Detailed Report (Client App)**
- Full training log: Accuracy curves, examples, validation results
- Available on-demand in companion's settings
- Delivered after: Training session completes

---

## 7. Tool Access & Permission Architecture

### 7.1 Hybrid Model (Capability + Plugin + Sandbox)

**Principle: Least Privilege**
- Default: Companion has NO access to tools
- Explicit grant: User approves each capability
- Granular scopes: Read-only, specific folders, time-limited

### 7.2 Tool Categories

**Always-Granted (Low-Risk)**
- System time/date
- Weather (if API key provided)
- Calculator, unit conversion
- Public knowledge queries

**User-Approved on First Use (Medium-Risk)**
- File system (read-only, specific directories)
- Screen capture (active window only)
- Clipboard read
- Notification display

**Explicit Approval Every Time (High-Risk)**
- Email send, file delete
- Screen control (click, type)
- System commands (shell access)
- Network requests (external APIs)

### 7.3 Architecture: Plugin System + Sandbox

**Plugin Interface**
```python
class ToolPlugin:
    def name(self) -> str:
        """Email Client"""
    
    def capabilities(self) -> List[str]:
        """["email.read", "email.send", "email.categorize"]"""
    
    def request_permission(self, capability: str) -> bool:
        """UI prompt, returns user approval"""
    
    def execute(self, action: str, params: dict) -> Result:
        """Execute with permission check"""
```

**Sandbox Execution**
- Every tool action runs in sandboxed context
- Seccomp filters, cgroups, AppArmor/SELinux profiles
- Resource limits: CPU, memory, network bandwidth
- Timeout: Actions must complete within threshold

**Approval Workflow**
```
1. Companion wants to send email
   ↓
2. Check permission cache (has user granted email.send?)
   ↓
3. If not granted:
   a. Show preview to user: "Send to: boss@company.com, Subject: Status Update"
   b. User approves/denies/edits
   c. Cache decision (with scope: always approve emails to boss)
   ↓
4. Execute in sandbox
   ↓
5. Log action (audit trail)
   ↓
6. Learn from feedback (user's approval patterns)
```

### 7.4 Future: Online Skills Library (Noted for Later)

**Vision:** Companions share learned skills across devices
- Federated learning: Aggregate knowledge without sharing raw data
- Skill marketplace: Users contribute/download skills
- Privacy-preserving: Only share model weights, not user data

**Not in MVP, but architecture should support:**
- Skill versioning (semantic versioning)
- Skill provenance (who trained it, on what data)
- Skill compatibility (which companion versions support it)

---

## 8. Embodiment Abstraction (VLA Approach)

### 8.1 Universal Action Primitives (Defined Now)

**Goal:** Same reasoning layer, different embodiments

**Perception Abstraction**
```python
class Observation:
    modality: str  # "screen", "camera", "joint_angles", "tactile"
    data: Any      # RGB frame, depth map, sensor values
    timestamp: float
    embodiment: str  # "screen_character", "robot_arm", "mobile_base"
```

**Action Abstraction**
```python
class Action:
    type: str      # "point_at", "move_to", "grasp", "speak"
    target: Dict   # Coordinates, object ID, or text
    embodiment: str
    parameters: Dict  # Speed, force, duration, etc.
```

### 8.2 Embodiment Plugins (Modular)

**On-Screen Character**
- Perception: Screen capture (2D RGB), cursor position, active window
- Actions: {move_to(x,y), animate(gesture), point_at(object), speak(text)}
- Latency: <50ms (real-time)

**Physical Robot (Future)**
- Perception: RGB-D camera, joint encoders, IMU, tactile sensors
- Actions: {move_arm(joints), grasp(), navigate(x,y,z), manipulate()}
- Latency: <100ms (control loop)

**Cross-Embodiment Transfer**
- Shared: Language understanding, task planning, memory
- Embodiment-specific: Motor policies (screen vs robot have different action spaces)
- Training: Sim-to-real pipeline (train in simulation, fine-tune on real hardware)

### 8.3 Sim-to-Real Strategy (Deferred, But Planned)

**Phase 1:** Realistic simulation (physics engine, sensor noise modeling)
**Phase 2:** System identification (calibrate sim parameters to match real)
**Phase 3:** Domain randomization (train on varied sim conditions)
**Phase 4:** Real-world fine-tuning (small dataset on actual hardware)

**Not immediate concern:** Focus on screen character first, robot later

### 8.4 Latent Language Reasoning Layer

**Concept:** Language as universal abstraction
- Task description: "Pick up the cup" (language)
- Embodiment translates: Screen character points at cup, robot grasps it
- Reasoning: Central Agent thinks in language, embodiment adapts

**Architecture:**
```
Central Agent (Language-based reasoning)
    ↓ (language instructions)
Embodiment Adapter (translates to actions)
    ↓ (embodiment-specific commands)
Motor Controller (executes)
```

**Benefit:** New embodiments just need adapter, not new reasoning system

---

## 9. Creativity Module

### 9.1 Architecture: Separate Module with Multi-Mode Operation

**When Invoked:**
- User explicitly requests: "Think creatively about this"
- Task requires exploration: "Find a new way to organize my files"
- Companion detects stagnation: "Past approaches not working"

**Inputs:** All information from other modules (sensory, memory, skills, personality)

**Outputs:** Novel solutions, alternative approaches, conceptual blends

### 9.2 Creativity Modes (All Four, Context-Dependent)

**Mode 1: Novelty Search**
- Generate variations on known solutions
- Measure distance from past behaviors (embedding space)
- Reward discovering new action sequences

**Mode 2: Conceptual Blending**
- Combine ideas from different domains
- Example: "Email management" + "Game mechanics" → Gamified inbox with points/rewards
- Graph traversal: Find non-obvious connections in knowledge graph

**Mode 3: Constraint Relaxation**
- Normally: Follow user's established patterns
- Creative mode: "What if I break this rule?"
- Gradually relax constraints until novel (but acceptable) solution emerges

**Mode 4: Generative Sampling**
- Sample from latent space of generative model
- User feedback shapes distribution (reward creative ideas user likes)
- Diversity enforcement: Penalize repetitive suggestions

### 9.3 Measuring Creativity

**User Approval (Primary Metric)**
- Explicit: User marks idea as "creative" or "useful"
- Implicit: User adopts suggested approach

**Novelty Score (Secondary)**
- Distance from past solutions (cosine similarity in embedding space)
- Diversity within generated set (variety of ideas)

**Usefulness Score (Secondary)**
- Does solution achieve goal?
- Efficiency compared to baseline

### 9.4 Deferred Refinement

Exact implementation TBD. For MVP:
- Simple novelty search (random exploration)
- User feedback loop
- Expand to full multi-mode system later

---

## 10. Orthogonal Learning & Transfer

### 10.1 Principle: Reuse + Specialize

**Reuse Existing Skills When Possible**
- Identify sub-skills that apply to new tasks
- Example: "Text classification" learned for email, reused for document tagging
- Avoid re-learning from scratch

**Master Truly New Skills When Necessary**
- If no existing skill applies, learn from ground up
- Example: Learning to control robot arm (no prior motor skill like this)

**Specialize Skills for New Domains**
- Base skill frozen, add domain-specific adaptation
- Example: "Text classification" base frozen, fine-tune for legal documents

### 10.2 Architecture: Hybrid (Mixture of Experts + Modular + LoRA)

**Base Model (Frozen)**
- Shared knowledge: Language understanding, visual perception, reasoning
- Pre-trained, large, never fine-tuned (prevents catastrophic forgetting)

**Expert Modules (Per Skill Domain)**
- Email management expert, document editing expert, coding assistant expert
- Lightweight, skill-specific models (~50-200MB each)
- Independently trainable (orthogonal)

**Routing Network**
- Central Agent decides which expert(s) to activate
- Can combine multiple experts (ensemble)
- Learned routing: Which expert for which task?

**LoRA Adapters (Parameter-Efficient Fine-Tuning)**
- Skill = Base Model + LoRA adapter (~10MB)
- Add new skill without touching base model
- Orthogonality: Each adapter is independent

### 10.3 Preventing Catastrophic Forgetting

**Frozen Base:** Never update shared parameters
**Independent Adapters:** Each skill has own parameters
**Rehearsal:** Periodically test old skills, retrain if degraded
**Elastic Weight Consolidation (EWC):** Penalize changes to important parameters (if needed)

---

## 11. Personality System

### 11.1 Internal: Big Five Model

**Five continuous parameters (0.0 to 1.0):**

1. **Openness**: Conservative (0.0) ↔ Creative/Curious (1.0)
2. **Conscientiousness**: Spontaneous (0.0) ↔ Organized/Disciplined (1.0)
3. **Extraversion**: Reserved (0.0) ↔ Outgoing/Energetic (1.0)
4. **Agreeableness**: Challenging (0.0) ↔ Cooperative/Empathetic (1.0)
5. **Neuroticism**: Calm (0.0) ↔ Emotionally Reactive (1.0)

**Additional Parameters (Specific to Companion):**

6. **Humor**: Serious (0.0) ↔ Playful/Witty (1.0)
7. **Verbosity**: Concise (0.0) ↔ Detailed/Explanatory (1.0)

**Stored in:** PostgreSQL user preferences table
**Adjustable:** Via client UI (sliders)
**Effect:** Modulates response generation, emotion expression, proactivity

### 11.2 External: Myers-Briggs (Display Only)

**UI Gimmick:** Show MBTI type as companion's "personality tag"
- Map Big Five to MBTI (approximate conversion)
- Example: High openness + low neuroticism → ENTP
- Displayed in companion profile: "Your companion is an INTJ"

**Not used internally:** All behavior driven by Big Five parameters

### 11.3 Personality Influence on Behavior

| Trait | Low Value Behavior | High Value Behavior |
|-------|-------------------|---------------------|
| Openness | Stick to tried methods, resist new ideas | Suggest creative solutions, explore alternatives |
| Conscientiousness | Flexible with rules, spontaneous | Structured, detailed plans, reminders |
| Extraversion | Wait for user to initiate, quiet | Proactively start conversations, enthusiastic |
| Agreeableness | Direct, critical feedback | Supportive, encouraging, empathetic |
| Neuroticism | Even-toned, stable | Expressive, emotionally reactive |
| Humor | Formal, professional | Jokes, puns, playful interactions |
| Verbosity | Brief responses | Detailed explanations, context |

---

## 12. Client-Host Architecture

### 12.1 Separation of Concerns

**Host Device (RPi5 or other)**
- Runs AI models, core services
- Handles: Inference, memory management, skill training
- Stores: All user data, models, logs
- Network: Local-only by default (no internet required)

**Client Devices (Laptop, Phone, Desktop)**
- UI for interaction
- Displays: Character, chat interface, settings
- Sends: User input (text, voice, screen share)
- Receives: Companion responses, notifications

### 12.2 Communication

**Protocol:** gRPC over mTLS (mutual TLS)
- Encrypted: All traffic encrypted end-to-end
- Authenticated: Client has token, host verifies
- Local network: mDNS discovery (host.local)

**Message Types:**
- User input: Text, audio, screen frame
- Companion output: Response, animation command, voice
- Control: Permission grants, settings updates
- Telemetry: Performance metrics (optional)

### 12.3 Load Considerations

**Same Machine (Host = Client Device)**
- Conservative resource use (don't interfere with user tasks)
- Downtime learning: Only when system idle
- Real-time priority: User tasks > companion training

**Separate Host (Dedicated RPi5)**
- Aggressive resource use (host is only running companion)
- Downtime learning: More frequent, longer sessions
- Real-time priority: Companion always responsive

**Configuration:** User selects deployment mode in settings

---

## 13. Data Flow Summary

### 13.1 Real-Time Interaction Loop

```
USER ACTION (speak, type, click)
    ↓
CLIENT captures input
    ↓
SEND to HOST (gRPC)
    ↓
SENSORY AGENTS (audio/visual/input)
    ↓
Publish event to REDIS (working memory)
    ↓
CENTRAL AGENT (reasoning)
    - Retrieve context from Qdrant (short-term)
    - Retrieve facts from PostgreSQL (long-term)
    - Current personality state
    - Active skills
    ↓
DECISION: What to do?
    ↓
LANGUAGE CENTER: Generate response
EMOTION CENTER: Modulate tone
    ↓
MOTOR AGENTS (voice, gesture, screen action)
    ↓
SEND to CLIENT (gRPC)
    ↓
CLIENT renders: Character speaks, animates
    ↓
USER perceives response
    ↓
(Loop)
```

**Latency Target:** <500ms (perception to response)

### 13.2 Background Learning Loop

```
DOWNTIME DETECTED (user idle, scheduled sleep)
    ↓
TRAINER AGENT activates
    ↓
Load pending skill training tasks from queue
    ↓
SELECT SIMULATION METHOD
    - World model for complex skills
    - Replay buffer for refinement
    - Synthetic scenarios for edge cases
    ↓
TRAINING LOOP (iterate for N steps)
    ↓
CHECKPOINT: Save intermediate model
    ↓
VALIDATE: Test skill on held-out data
    ↓
If success rate > threshold:
    - CERTIFY skill
    - Deploy to production
    - Notify user (report)
    ↓
HIPPOCAMPUS consolidates:
    - Redis → Qdrant (episodic)
    - Qdrant → PostgreSQL (long-term)
    ↓
Return to idle
```

**Frequency:** Every sleep cycle + opportunistic when idle

---

## 14. Open Questions & Deferred Decisions

### To Be Resolved in Next Phase:

1. **Skill Tree Exact Schema**
   - Hierarchical graph, behavior tree, or neural modules?
   - Prototype needed to evaluate trade-offs

2. **Module Activation Thresholds**
   - Exact timings for idle → unload
   - LRU cache size, thrashing prevention heuristics
   - Requires profiling on real hardware

3. **Creativity Module Implementation Details**
   - Which creativity mode for which task type?
   - How to combine modes (sequential, parallel, hybrid)?
   - Needs experimentation

4. **Training Hyperparameters**
   - Learning rates, batch sizes, convergence criteria
   - Skill-dependent, will be empirically tuned

5. **Remote Access Strategy**
   - Tailscale vs WireGuard vs Cloudflare Tunnel
   - Deferred until local system proven

6. **Monitoring & Observability**
   - Prometheus + Grafana? Logging strategy?
   - Define once core system running

---

## 15. Architectural Principles Summary

**Core Tenets (Immutable):**

1. **Privacy First:** All data local, user controls permissions
2. **Offline Capable:** No cloud dependencies, works without internet
3. **Resource Efficient:** Designed for RPi5 constraints (8GB RAM, 15W power)
4. **Modular:** Components loosely coupled, independently evolvable
5. **Brain-Inspired:** Cognitive architecture mirrors human neuroscience
6. **Learning Over Time:** Companion improves through experience
7. **User-Centric:** Personality customizable, transparent behavior
8. **Safety:** Least privilege, sandbox execution, audit logs

---

## Next Steps

1. **Validate with User:** Review this document, confirm alignment
2. **Create Visual Diagrams:** System architecture, data flow, skill tree
3. **Define APIs:** Inter-agent communication specs (gRPC schemas)
4. **Technology Stack Finalization:** Pick specific models, frameworks, libraries
5. **MVP Scope:** Define Phase 1 minimal viable product
6. **Implementation Roadmap:** Timeline, milestones, dependencies

---

**Document Status:** Foundation complete, ready for detailed design phase.
