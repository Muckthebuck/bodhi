# Bodhi - Architecture Diagrams

**Last Updated:** 2026-02-21  
**Systems Visualized:** Skill Tree, Memory Consolidation, Central Agent, Module Activation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Skill Tree System](#2-skill-tree-system)
3. [Memory Consolidation System](#3-memory-consolidation-system)
4. [Central Agent Architecture](#4-central-agent-architecture)
5. [Module Activation Strategy](#5-module-activation-strategy)
6. [Data Flow Integration](#6-data-flow-integration)

---

## 1. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Bodhi System                           │
│                     (Brain-Inspired Architecture)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      CENTRAL AGENT                                │  │
│  │              (Prefrontal Cortex - Executive Control)             │  │
│  │                                                                   │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐    │  │
│  │  │  Decision   │  │  Attention   │  │  Working Memory     │    │  │
│  │  │    Loop     │  │  Mechanism   │  │   (Redis-backed)    │    │  │
│  │  │             │  │ (AlphaStar)  │  │                     │    │  │
│  │  │ Event-Driven│  │              │  │ - Goals             │    │  │
│  │  │   + Proactive│ │ - Priority Q │  │ - Context           │    │  │
│  │  │             │  │ - Learned    │  │ - Active Skills     │    │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                         ┌──────────┴──────────┐                        │
│                         │                     │                        │
│  ┌──────────────────────▼─────┐   ┌──────────▼─────────────────────┐ │
│  │   SKILL TREE SYSTEM         │   │  MEMORY CONSOLIDATION SYSTEM   │ │
│  │ (Basal Ganglia - Procedural)│   │   (Hippocampus - Memory)       │ │
│  │                             │   │                                 │ │
│  │  ┌─────────────────────┐   │   │  ┌──────────────────────────┐  │ │
│  │  │   Neo4j Graph       │   │   │  │  Redis (Short-Term)      │  │ │
│  │  │   - Skill Nodes     │   │   │  │  5-60 min TTL            │  │ │
│  │  │   - Relationships   │   │   │  └──────────┬───────────────┘  │ │
│  │  │   - Composition     │   │   │             │                   │ │
│  │  └─────────────────────┘   │   │  ┌──────────▼───────────────┐  │ │
│  │                             │   │  │ Qdrant (Medium-Term)     │  │ │
│  │  ┌─────────────────────┐   │   │  │ Vector search            │  │ │
│  │  │  Skill Executor      │   │   │  │ Importance-based         │  │ │
│  │  │  - Dataflow DAG      │   │   │  └──────────┬───────────────┘  │ │
│  │  │  - Model Loading     │   │   │             │                   │ │
│  │  │  - Versioning        │   │   │  ┌──────────▼───────────────┐  │ │
│  │  └─────────────────────┘   │   │  │ PostgreSQL (Long-Term)   │  │ │
│  │                             │   │  │ Structured records       │  │ │
│  └─────────────────────────────┘   │  └──────────────────────────┘  │ │
│                                     └─────────────────────────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              MODULE ACTIVATION STRATEGY                           │  │
│  │            (Resource Management - Energy Conservation)            │  │
│  │                                                                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │  │
│  │  │  Input   │  │   Goal   │  │Predictive │  │   Eviction   │  │  │
│  │  │  Driven  │  │  Driven  │  │ (Pattern  │  │  (Weighted   │  │  │
│  │  │          │  │          │  │ Learning) │  │     LRU)     │  │  │
│  │  └──────────┘  └──────────┘  └───────────┘  └──────────────┘  │  │
│  │                                                                   │  │
│  │  States: Unloaded → Hibernated → Standby → Active               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        SUB-AGENTS                                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │  │
│  │  │ Visual   │ │ Auditory │ │ Language │ │ Emotion          │   │  │
│  │  │ Agent    │ │ Agent    │ │ Center   │ │ Regulator        │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │  │
│  │  │ Motor    │ │ Voice    │ │Character │ │ Tool Plugin      │   │  │
│  │  │ Control  │ │Synthesis │ │Animator  │ │ System           │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                         ┌────────────────────┐
                         │   Event Bus        │
                         │ (Redis Pub/Sub +   │
                         │  gRPC over mTLS)   │
                         └────────────────────┘
```

---

## 2. Skill Tree System

### 2.1 Neo4j Graph Structure

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Skill Graph (Neo4j)                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Root Skill: "Manage Emails"                                          │
│  ┌──────────────────────────────────┐                                 │
│  │ id: email_management              │                                 │
│  │ type: composite                   │                                 │
│  │ level: expert (92%)               │                                 │
│  └───────┬──────────────────────────┘                                 │
│          │                                                              │
│          │ COMPOSED_OF                                                 │
│          ├─────────────┬─────────────┬─────────────┐                  │
│          │             │             │             │                   │
│  ┌───────▼───────┐ ┌──▼────────┐ ┌──▼────────┐ ┌──▼─────────────┐   │
│  │ Read Email    │ │Categorize │ │  Draft    │ │   Schedule     │   │
│  │ id: read_email│ │  Email    │ │  Reply    │ │   Send         │   │
│  │ level: master │ │ level:    │ │ level:    │ │   level:       │   │
│  │ (98%)         │ │ expert(88%)│ │competent │ │   competent    │   │
│  └───────┬───────┘ └─────┬─────┘ └─────┬─────┘ └────────────────┘   │
│          │               │             │                               │
│          │ REQUIRES      │             │ SHARES_SUBSKILL               │
│          ▼               ▼             ▼                               │
│  ┌─────────────────────────────────────────────┐                      │
│  │        Parse Text (Shared Subskill)         │                      │
│  │        id: parse_text                        │                      │
│  │        type: atomic                          │                      │
│  │        level: master (99%)                   │                      │
│  │        used_by: [read_email, categorize,    │                      │
│  │                  draft_reply, summarize]     │                      │
│  └─────────────────────────────────────────────┘                      │
│                                                                         │
│  Relationship Types:                                                   │
│  • COMPOSED_OF: Parent skill contains child skills                     │
│  • REQUIRES: Skill depends on prerequisite                             │
│  • SHARES_SUBSKILL: Skills reuse common subskill                      │
│  • SUPERSEDES: Newer version replaces older (versioning)               │
│  • SYNTHESIZED_FROM: New skill created from co-executed skills         │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Skill Execution Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Skill Execution Pipeline                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Request                                                            │
│     ┌─────────────────────────────────────────┐                       │
│     │ User: "Summarize my unread emails"      │                       │
│     └────────────────┬────────────────────────┘                       │
│                      │                                                  │
│  2. Skill Resolution                                                   │
│     ┌────────────────▼────────────────────────┐                       │
│     │ Central Agent → Skill Executor           │                       │
│     │ Lookup: skill_id = "summarize_emails"   │                       │
│     └────────────────┬────────────────────────┘                       │
│                      │                                                  │
│  3. Dependency Analysis (Neo4j Cypher Query)                          │
│     ┌────────────────▼────────────────────────┐                       │
│     │ MATCH (s:Skill {id: $skill_id})         │                       │
│     │       -[:COMPOSED_OF*]->(sub:Skill)      │                       │
│     │ RETURN s, sub                            │                       │
│     └────────────────┬────────────────────────┘                       │
│                      │                                                  │
│     Returns DAG:                                                       │
│     summarize_emails                                                   │
│          ├── read_email                                                │
│          │     └── parse_text                                          │
│          ├── categorize                                                │
│          │     └── parse_text (shared)                                 │
│          └── generate_summary                                          │
│                └── llm_inference                                       │
│                                                                         │
│  4. Topological Sort (Execution Order)                                │
│     ┌────────────────▼────────────────────────┐                       │
│     │ Execution order:                         │                       │
│     │ [1] parse_text                           │                       │
│     │ [2] read_email (depends on parse_text)   │                       │
│     │ [3] categorize (depends on parse_text)   │                       │
│     │ [4] llm_inference                        │                       │
│     │ [5] generate_summary (depends on llm)    │                       │
│     │ [6] summarize_emails (depends on all)    │                       │
│     └────────────────┬────────────────────────┘                       │
│                      │                                                  │
│  5. Model Loading (Hybrid Strategy)                                   │
│     ┌────────────────▼────────────────────────┐                       │
│     │ - parse_text: Already loaded (top 20)   │                       │
│     │ - llm_inference: Lazy load (200ms)       │                       │
│     │ - categorize: Lazy load (150ms)          │                       │
│     └────────────────┬────────────────────────┘                       │
│                      │                                                  │
│  6. Sequential Execution                                               │
│     ┌────────────────▼────────────────────────┐                       │
│     │ for node in execution_order:             │                       │
│     │    result = execute_skill(node, inputs)  │                       │
│     │    cache_result(node, result)            │                       │
│     │    pass_to_dependent_skills(result)      │                       │
│     └────────────────┬────────────────────────┘                       │
│                      │                                                  │
│  7. Result                                                             │
│     ┌────────────────▼────────────────────────┐                       │
│     │ "You have 12 unread emails:              │                       │
│     │  - 5 work-related (2 urgent)             │                       │
│     │  - 4 newsletters                          │                       │
│     │  - 3 personal"                            │                       │
│     └──────────────────────────────────────────┘                       │
│                      │                                                  │
│  8. Feedback Loop (Update Skill Stats)                                │
│     ┌────────────────▼────────────────────────┐                       │
│     │ - Success: true                          │                       │
│     │ - Latency: 1.2s                          │                       │
│     │ - User satisfaction: 0.9 (implicit)      │                       │
│     │ → Update competency formula              │                       │
│     │ → Increment usage count                  │                       │
│     └──────────────────────────────────────────┘                       │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Skill Leveling System

```
┌────────────────────────────────────────────────────────────────────────┐
│                  Skill Competency Progression                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Competency Formula:                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ competency = 0.5×success_rate + 0.2×log_usage + 0.2×satisfaction│  │
│  │              + 0.1×recency_bonus                                 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Levels:                                                               │
│                                                                         │
│   0%        20%       50%       80%       95%      100%                │
│   ├─────────┼─────────┼─────────┼─────────┼─────────┤                 │
│   │ Novice  │Developing│Competent│ Expert  │ Master  │                 │
│   └─────────┴─────────┴─────────┴─────────┴─────────┘                 │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ NOVICE (0-20%)                                                   │  │
│  │ • High failure rate (>30%)                                       │  │
│  │ • Few executions (<5)                                            │  │
│  │ • Requires heavy supervision                                     │  │
│  │ • Badge: 🔵                                                      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│          │                                                              │
│          │ Usage + Success                                             │
│          ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ DEVELOPING (20-50%)                                              │  │
│  │ • Moderate success rate (70-85%)                                 │  │
│  │ • Regular use (5-20 executions)                                  │  │
│  │ • Occasional failures acceptable                                 │  │
│  │ • Badge: 🟡                                                      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│          │                                                              │
│          │ Consistency + User satisfaction                             │
│          ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ COMPETENT (50-80%)                                               │  │
│  │ • High success rate (85-95%)                                     │  │
│  │ • Frequent use (20-50 executions)                                │  │
│  │ • Reliable for daily tasks                                       │  │
│  │ • Badge: 🟢                                                      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│          │                                                              │
│          │ Near-perfect execution                                      │
│          ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ EXPERT (80-95%)                                                  │  │
│  │ • Very high success rate (95-98%)                                │  │
│  │ • Heavy use (50-100 executions)                                  │  │
│  │ • Can handle edge cases                                          │  │
│  │ • Badge: 🟣                                                      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│          │                                                              │
│          │ Mastery + Innovation                                        │
│          ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ MASTER (95-100%)                                                 │  │
│  │ • Near-perfect success rate (>98%)                               │  │
│  │ • Extensive use (>100 executions)                                │  │
│  │ • Can adapt to novel situations                                  │  │
│  │ • Teaches other skills (transfer learning)                       │  │
│  │ • Badge: 🏆                                                      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  XP Display (User-Facing):                                             │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Skill: Summarize Emails                    Level: Expert         │  │
│  │ ████████████████████░░░  88%                                     │  │
│  │ 8,820 XP / 10,000 XP to Master                                   │  │
│  │                                                                   │  │
│  │ Recent Activity:                                                 │  │
│  │ • 47 successful executions this week (+470 XP)                   │  │
│  │ • 2 failures (-100 XP)                                           │  │
│  │ • User satisfaction: 4.8/5.0 (+200 bonus XP)                     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Skill Versioning & Rollback

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Skill Version History                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Timeline:                                                             │
│                                                                         │
│  v1.0 (2026-01-15)                                                     │
│  ┌──────────────────────────────────────┐                             │
│  │ Initial implementation                │                             │
│  │ Success rate: 85%                     │                             │
│  │ Avg latency: 2.1s                     │                             │
│  └──────────────┬───────────────────────┘                             │
│                 │                                                       │
│                 │ User feedback: "Too slow"                            │
│                 │ OPTIMIZATION                                          │
│                 ▼                                                       │
│  v1.1 (2026-01-22)                                                     │
│  ┌──────────────────────────────────────┐                             │
│  │ Optimized model loading               │                             │
│  │ Success rate: 87%                     │                             │
│  │ Avg latency: 1.3s ✓ (38% faster)     │                             │
│  └──────────────┬───────────────────────┘                             │
│                 │                                                       │
│                 │ New feature request                                  │
│                 │ ENHANCEMENT                                           │
│                 ▼                                                       │
│  v2.0 (2026-02-01)                                                     │
│  ┌──────────────────────────────────────┐                             │
│  │ Added sentiment analysis              │                             │
│  │ Success rate: 78% ⚠ (REGRESSION!)    │                             │
│  │ Avg latency: 1.5s                     │                             │
│  └──────────────┬───────────────────────┘                             │
│                 │                                                       │
│                 │ AUTOMATIC REGRESSION DETECTION                        │
│                 │ success_rate drop > 5% → ALERT                       │
│                 │                                                       │
│                 │ ┌───────────────────────────────┐                    │
│                 │ │ 🚨 REGRESSION ALERT           │                    │
│                 │ │ Skill: summarize_emails       │                    │
│                 │ │ v2.0 success: 78%             │                    │
│                 │ │ v1.1 success: 87%             │                    │
│                 │ │ Drop: -9%                     │                    │
│                 │ │                               │                    │
│                 │ │ [Auto-Rollback] [Debug] [Keep]│                    │
│                 │ └───────────────────────────────┘                    │
│                 │                                                       │
│                 │ User selects: Auto-Rollback                          │
│                 │ ROLLBACK                                              │
│                 ▼                                                       │
│  v2.1 (2026-02-02) ← NEW VERSION CREATED                              │
│  ┌──────────────────────────────────────┐                             │
│  │ Points to v1.1 config                 │                             │
│  │ (Rollback implemented as new version) │                             │
│  │ Success rate: 87% ✓ (restored)       │                             │
│  │ Avg latency: 1.3s                     │                             │
│  └──────────────┬───────────────────────┘                             │
│                 │                                                       │
│                 │ Debug v2.0 issue                                     │
│                 │ FIX                                                   │
│                 ▼                                                       │
│  v2.2 (2026-02-05)                                                     │
│  ┌──────────────────────────────────────┐                             │
│  │ Fixed sentiment analysis bug          │                             │
│  │ Success rate: 91% ✓ (NEW BEST!)      │                             │
│  │ Avg latency: 1.4s                     │                             │
│  └───────────────────────────────────────┘                             │
│                                                                         │
│  Neo4j Relationship (SUPERSEDES):                                      │
│  v1.0 →[SUPERSEDES]→ v1.1 →[SUPERSEDES]→ v2.0 →[SUPERSEDES]→ v2.1     │
│                                            ↓                            │
│                                       v2.2 (ACTIVE)                     │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Memory Consolidation System

### 3.1 Three-Tier Memory Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Three-Tier Memory System                             │
│                  (Inspired by Human Memory Systems)                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  TIER 1: SHORT-TERM MEMORY (Redis)                                     │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • Capacity: ~100MB (10,000 items)                                │ │
│  │ • TTL: 5-60 minutes (adaptive)                                   │ │
│  │ • Access: O(1) - instant                                          │ │
│  │ • Content: Recent events, active context                         │ │
│  │                                                                   │ │
│  │ Key Structure:                                                    │ │
│  │ memory:event:{uuid} → {                                          │ │
│  │   "timestamp": "2026-02-21T02:30:00Z",                           │ │
│  │   "type": "user_message",                                        │ │
│  │   "content": "Summarize my emails",                              │ │
│  │   "importance": 0.85,                                            │ │
│  │   "ttl": 3600                                                    │ │
│  │ }                                                                 │ │
│  │                                                                   │ │
│  │ Adaptive TTL Formula:                                             │ │
│  │ ttl = base_ttl × importance_multiplier × activity_multiplier     │ │
│  │     = 600s × 1.5 (high importance) × 2.0 (user active)           │ │
│  │     = 1800s (30 minutes)                                          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              │ CONSOLIDATION (Triggered by)             │
│                              │ - Idle >15 min (light)                   │
│                              │ - Sleep cycle (deep)                     │
│                              │ - Memory pressure >90MB (emergency)      │
│                              ▼                                          │
│  TIER 2: MEDIUM-TERM MEMORY (Qdrant - Vector DB)                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • Capacity: ~200MB (20,000 items)                                │ │
│  │ • Retention: Days to weeks                                       │ │
│  │ • Access: ~50ms semantic search                                  │ │
│  │ • Content: Important recent memories                             │ │
│  │                                                                   │ │
│  │ Vector Structure:                                                 │ │
│  │ {                                                                 │ │
│  │   "id": "mem_12345",                                             │ │
│  │   "vector": [0.23, -0.15, 0.87, ...],  // 384D Sentence-BERT   │ │
│  │   "payload": {                                                   │ │
│  │     "content": "User asked about emails at 2pm",                 │ │
│  │     "timestamp": "2026-02-21T14:00:00Z",                         │ │
│  │     "importance": 0.85,                                          │ │
│  │     "emotional_valence": 0.2,                                    │ │
│  │     "tags": ["email", "work", "request"]                         │ │
│  │   }                                                               │ │
│  │ }                                                                 │ │
│  │                                                                   │ │
│  │ Importance Scoring:                                               │ │
│  │ ┌────────────────────────────────────────────────────────────┐  │ │
│  │ │ importance = 0.25×user_initiated                           │  │ │
│  │ │            + 0.20×emotional_intensity                       │  │ │
│  │ │            + 0.20×novelty                                   │  │ │
│  │ │            + 0.15×utility                                   │  │ │
│  │ │            + 0.10×social_relevance                          │  │ │
│  │ │            + 0.10×recency_bonus                             │  │ │
│  │ └────────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              │ PROMOTION (Criteria)                     │
│                              │ - Importance >0.7                        │
│                              │ - Accessed >3 times                      │
│                              │ - Connected to goals                     │
│                              ▼                                          │
│  TIER 3: LONG-TERM MEMORY (PostgreSQL)                                │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • Capacity: Unlimited (~5GB typical)                             │ │
│  │ • Retention: Permanent (with forgetting curve)                   │ │
│  │ • Access: ~100ms structured query                                │ │
│  │ • Content: Critical memories, patterns, facts                    │ │
│  │                                                                   │ │
│  │ Schema:                                                           │ │
│  │ CREATE TABLE long_term_memories (                                │ │
│  │   id BIGSERIAL PRIMARY KEY,                                      │ │
│  │   content TEXT NOT NULL,                                         │ │
│  │   summary TEXT,              -- Compressed version               │ │
│  │   timestamp TIMESTAMP NOT NULL,                                  │ │
│  │   importance FLOAT NOT NULL,                                     │ │
│  │   access_count INT DEFAULT 0,                                    │ │
│  │   last_accessed TIMESTAMP,                                       │ │
│  │   emotional_valence FLOAT,                                       │ │
│  │   tags TEXT[],                                                   │ │
│  │   metadata JSONB                                                 │ │
│  │ );                                                                │ │
│  │                                                                   │ │
│  │ Ebbinghaus Forgetting Curve:                                     │ │
│  │ R(t) = e^(-t/S)  where S = importance × 30 days                 │ │
│  │                                                                   │ │
│  │ High importance (0.9): 50% retention after 27 days               │ │
│  │ Low importance (0.3):  50% retention after 9 days                │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Consolidation Process

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Memory Consolidation Workflow                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  TRIGGER CONDITIONS:                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • LIGHT: User idle >15 min (background processing)               │ │
│  │ • DEEP: Sleep cycle (3am circadian rhythm)                       │ │
│  │ • EMERGENCY: Redis >90MB (prevent overflow)                      │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              ┃                                          │
│  ════════════════════════════╬═══════════════════════════════════════  │
│                              ┃                                          │
│  CONSOLIDATION WORKER        ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Step 1: Scan Redis for candidates                              │   │
│  │ ────────────────────────────────────────────────────────────── │   │
│  │ SCAN memory:event:* with importance scoring                     │   │
│  │                                                                  │   │
│  │ ┌─────────────────────────────────────────────────────────┐   │   │
│  │ │ Event A: importance=0.85 → CONSOLIDATE                   │   │   │
│  │ │ Event B: importance=0.15 → PROBABILISTIC DELETE (90%)    │   │   │
│  │ │ Event C: importance=0.62 → CONSOLIDATE                   │   │   │
│  │ │ Event D: importance=0.08 → DELETE                        │   │   │
│  │ └─────────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ┃                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Step 2: Generate embeddings (Sentence-BERT)                    │   │
│  │ ────────────────────────────────────────────────────────────── │   │
│  │ content = "User asked to summarize emails at 2pm"              │   │
│  │ vector = model.encode(content)  # 384D vector                  │   │
│  │                                                                  │   │
│  │ Caching: Check Redis first                                      │   │
│  │ Key: embedding:{hash(content)} → [0.23, -0.15, ...]            │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ┃                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Step 3: Compression (for low-importance items)                 │   │
│  │ ────────────────────────────────────────────────────────────── │   │
│  │ IF importance < 0.5:                                            │   │
│  │   Lossy summarization: first + middle + last sentences          │   │
│  │   "User asked to...complex task...at 2pm" (50% smaller)        │   │
│  │ ELSE:                                                            │   │
│  │   Keep full content                                             │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ┃                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Step 4: Write to Qdrant                                         │   │
│  │ ────────────────────────────────────────────────────────────── │   │
│  │ qdrant.upsert(                                                  │   │
│  │   collection="memories",                                        │   │
│  │   points=[{                                                     │   │
│  │     "id": uuid,                                                 │   │
│  │     "vector": embedding,                                        │   │
│  │     "payload": {                                                │   │
│  │       "content": content,                                       │   │
│  │       "timestamp": ...,                                         │   │
│  │       "importance": 0.85                                        │   │
│  │     }                                                            │   │
│  │   }]                                                             │   │
│  │ )                                                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ┃                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Step 5: Promotion to long-term (if criteria met)               │   │
│  │ ────────────────────────────────────────────────────────────── │   │
│  │ IF importance > 0.7 OR access_count > 3:                        │   │
│  │   INSERT INTO long_term_memories (...)                          │   │
│  │   Mark as "archived" in Qdrant                                  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ┃                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Step 6: Cleanup Redis                                           │   │
│  │ ────────────────────────────────────────────────────────────── │   │
│  │ DEL memory:event:{uuid}                                         │   │
│  │ Log: "Consolidated 47 events, deleted 12, promoted 3"           │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  PROBABILISTIC FORGETTING:                                             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Importance < 0.1:  90% chance of deletion                        │ │
│  │ Importance 0.1-0.2: 50% chance of deletion                       │ │
│  │ Importance 0.2-0.3: 20% chance of deletion                       │ │
│  │ Importance > 0.3:   Always consolidate                           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Memory Retrieval

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Hybrid Memory Retrieval                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Query: "What did I ask about emails yesterday?"                       │
│                                                                         │
│  STRATEGY 1: Temporal Search (Fast Path)                               │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ 1. Query Redis (hot cache)                                       │ │
│  │    SCAN memory:event:* WHERE timestamp > yesterday               │ │
│  │    → 12 matches (instant, <5ms)                                  │ │
│  │                                                                   │ │
│  │ 2. Query Qdrant (medium-term)                                    │ │
│  │    filter: timestamp > yesterday AND tags CONTAINS "email"       │ │
│  │    → 8 matches (~20ms)                                           │ │
│  │                                                                   │ │
│  │ 3. Query PostgreSQL (long-term)                                  │ │
│  │    SELECT * FROM long_term_memories                              │ │
│  │    WHERE timestamp > yesterday AND 'email' = ANY(tags)           │ │
│  │    → 3 matches (~30ms)                                           │ │
│  │                                                                   │ │
│  │ Total: 23 matches in ~55ms                                       │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  STRATEGY 2: Semantic Search (Slow Path, High Recall)                 │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ 1. Generate query embedding                                      │ │
│  │    query_vector = model.encode("email inquiries")                │ │
│  │    → [0.18, -0.22, 0.91, ...] (384D)                            │ │
│  │                                                                   │ │
│  │ 2. Vector similarity search (Qdrant)                             │ │
│  │    qdrant.search(                                                │ │
│  │      collection="memories",                                      │ │
│  │      query_vector=query_vector,                                  │ │
│  │      limit=10,                                                   │ │
│  │      filter={                                                    │ │
│  │        "timestamp": {"gte": yesterday}                           │ │
│  │      }                                                            │ │
│  │    )                                                              │ │
│  │    → Returns top 10 semantically similar memories               │ │
│  │       with cosine similarity scores                              │ │
│  │                                                                   │ │
│  │ Results:                                                          │ │
│  │ ┌────────────────────────────────────────────────────────────┐  │ │
│  │ │ 1. "Summarize my emails" (similarity=0.92)                 │  │ │
│  │ │ 2. "Check inbox for urgent messages" (similarity=0.87)     │  │ │
│  │ │ 3. "Draft reply to client email" (similarity=0.81)         │  │ │
│  │ └────────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │ Total: ~50ms                                                      │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  STRATEGY 3: Hybrid (Best of Both)                                    │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ 1. Temporal filter (fast)                                        │ │
│  │ 2. Semantic reranking (precise)                                  │ │
│  │ 3. Merge + deduplicate                                           │ │
│  │ 4. Sort by relevance (importance × similarity × recency)         │ │
│  │                                                                   │ │
│  │ Final ranking:                                                    │ │
│  │ ┌────────────────────────────────────────────────────────────┐  │ │
│  │ │ 1. "Summarize my emails" (yesterday 2pm, imp=0.85, sim=0.92)│ │
│  │ │ 2. "Check urgent emails" (yesterday 9am, imp=0.78, sim=0.87)│ │
│  │ │ 3. "Draft email reply" (yesterday 4pm, imp=0.72, sim=0.81) │  │ │
│  │ └────────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  CACHING:                                                              │
│  • Frequent queries cached in Redis (5 min TTL)                       │
│  • Cache key: query_cache:{hash(query)} → results                     │
│  • Invalidate on new memory consolidation                             │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Central Agent Architecture

### 4.1 Hybrid Decision Loop

```
┌────────────────────────────────────────────────────────────────────────┐
│                  Central Agent Decision Loop                            │
│                  (Executive Control System)                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DUAL-LOOP ARCHITECTURE:                                               │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ REACTIVE LOOP (Event-Driven, <200ms latency)                   │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │  ┌──────────┐                                                   │   │
│  │  │ Input    │ Screen change, user input, voice command         │   │
│  │  │ Arrives  │                                                   │   │
│  │  └────┬─────┘                                                   │   │
│  │       │                                                          │   │
│  │       ▼                                                          │   │
│  │  ┌────────────────┐                                             │   │
│  │  │ Input Router   │ Classify input modality                    │   │
│  │  │                │ → visual / audio / text / tool              │   │
│  │  └───────┬────────┘                                             │   │
│  │          │                                                       │   │
│  │          ▼                                                       │   │
│  │  ┌────────────────┐                                             │   │
│  │  │ Attention      │ Which entities/events need focus?          │   │
│  │  │ Mechanism      │ (AlphaStar-inspired)                       │   │
│  │  │                │                                              │   │
│  │  │ ┌────────────┐ ┌────────────┐ ┌──────────────┐            │   │
│  │  │ │Priority Q  │ │ Learned    │ │  Pointer     │            │   │
│  │  │ │(Rules)     │ │ Attention  │ │  Networks    │            │   │
│  │  │ └────────────┘ └────────────┘ └──────────────┘            │   │
│  │  └───────┬────────┘                                             │   │
│  │          │                                                       │   │
│  │          ▼                                                       │   │
│  │  ┌────────────────┐                                             │   │
│  │  │ Intent         │ What does the user want?                   │   │
│  │  │ Recognition    │ → summarize_emails                         │   │
│  │  └───────┬────────┘                                             │   │
│  │          │                                                       │   │
│  │          ▼                                                       │   │
│  │  ┌────────────────┐                                             │   │
│  │  │ Skill Planner  │ Which skills are needed?                   │   │
│  │  │                │ → [language_center, skill_executor]        │   │
│  │  └───────┬────────┘                                             │   │
│  │          │                                                       │   │
│  │          ▼                                                       │   │
│  │  ┌────────────────┐                                             │   │
│  │  │ Activation Mgr │ Ensure modules loaded                      │   │
│  │  │                │ (may trigger async load)                   │   │
│  │  └───────┬────────┘                                             │   │
│  │          │                                                       │   │
│  │          ▼                                                       │   │
│  │  ┌────────────────┐                                             │   │
│  │  │ Execute        │ Run skill, generate response               │   │
│  │  └───────┬────────┘                                             │   │
│  │          │                                                       │   │
│  │          ▼                                                       │   │
│  │  ┌────────────────┐                                             │   │
│  │  │ Response       │ Send to user (text/voice/visual)           │   │
│  │  └────────────────┘                                             │   │
│  │                                                                  │   │
│  │  Target: <200ms end-to-end for simple queries                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ PROACTIVE LOOP (Background Reasoner, ~5s cycle)                │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │  While True:                                                    │   │
│  │    ┌──────────────────┐                                         │   │
│  │    │ 1. Scan Context  │ What's happening in the environment?   │   │
│  │    │                  │ - Active applications                   │   │
│  │    │                  │ - Screen content (if Visual Agent on)   │   │
│  │    │                  │ - Recent user activities                │   │
│  │    └────────┬─────────┘                                         │   │
│  │             │                                                    │   │
│  │             ▼                                                    │   │
│  │    ┌──────────────────┐                                         │   │
│  │    │ 2. Goal Tracking │ Am I making progress on goals?         │   │
│  │    │                  │ Example: "Monitor emails for urgent"   │   │
│  │    │                  │ → Check inbox every 5 minutes           │   │
│  │    └────────┬─────────┘                                         │   │
│  │             │                                                    │   │
│  │             ▼                                                    │   │
│  │    ┌──────────────────┐                                         │   │
│  │    │ 3. Predict Needs │ What will user need soon?              │   │
│  │    │                  │ (Use pattern learner)                   │   │
│  │    │                  │ → Preload modules if >70% confidence    │   │
│  │    └────────┬─────────┘                                         │   │
│  │             │                                                    │   │
│  │             ▼                                                    │   │
│  │    ┌──────────────────┐                                         │   │
│  │    │ 4. Maintenance   │ Trigger consolidation, cleanup         │   │
│  │    │                  │ Check memory pressure                   │   │
│  │    └────────┬─────────┘                                         │   │
│  │             │                                                    │   │
│  │             ▼                                                    │   │
│  │    Sleep(5s)                                                     │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  COORDINATION:                                                         │
│  • Reactive loop: Priority 1 (user-facing)                            │
│  • Proactive loop: Priority 2 (background, yield to reactive)         │
│  • Both share Working Memory (Redis) for state                        │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.2 AlphaStar Attention Mechanism

```
┌────────────────────────────────────────────────────────────────────────┐
│              AlphaStar-Inspired Attention System                        │
│         (Multi-Scale Attention for Complex Environments)                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input: Rich multi-modal context                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • 50+ entities (files, emails, windows, notifications)           │ │
│  │ • 10+ active processes (skills, tools, background tasks)          │ │
│  │ • 100+ memory items (recent events)                               │ │
│  │                                                                    │ │
│  │ Challenge: What should the agent focus on RIGHT NOW?             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  THREE-TIER ATTENTION:                                                 │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ TIER 1: Priority Queue (Rule-Based, Instant)                   │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │ Hard-coded priority rules:                                      │   │
│  │  1. User input:             Priority 10 (URGENT)                │   │
│  │  2. System errors:          Priority 9                          │   │
│  │  3. Goal completion:        Priority 8                          │   │
│  │  4. Skill failures:         Priority 7                          │   │
│  │  5. Scheduled tasks:        Priority 5                          │   │
│  │  6. Background maintenance: Priority 2                          │   │
│  │                                                                  │   │
│  │ Example:                                                         │   │
│  │  Queue = [                                                       │   │
│  │    (10, "user_message", "Summarize emails"),                    │   │
│  │    (8, "goal_complete", "Email monitoring done"),               │   │
│  │    (5, "scheduled", "Circadian sleep at 3am")                   │   │
│  │  ]                                                               │   │
│  │  → Pop highest priority (10) → Process user message             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ TIER 2: Learned Attention (Neural, 20-50ms)                    │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │ Lightweight transformer model:                                  │   │
│  │  Input: Entity embeddings [e1, e2, ..., e50]                   │   │
│  │  Output: Attention weights [w1, w2, ..., w50]                  │   │
│  │                                                                  │   │
│  │  attention_weights = softmax(Q @ K.T / sqrt(d_k))              │   │
│  │                                                                  │   │
│  │ Training signal:                                                │   │
│  │  • Supervised: Which entities did the user interact with?      │   │
│  │  • Reinforcement: Did attending to X lead to goal progress?    │   │
│  │                                                                  │   │
│  │ Example:                                                         │   │
│  │  Entities = [                                                   │   │
│  │    "inbox_notification" (w=0.42),  ← High attention            │   │
│  │    "calendar_event" (w=0.31),                                   │   │
│  │    "background_file" (w=0.05),     ← Low attention             │   │
│  │    ...                                                           │   │
│  │  ]                                                               │   │
│  │  → Focus on top-5 entities by weight                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ TIER 3: Pointer Networks (Entity Selection, 10ms)              │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │ Select WHICH specific entity to act on:                         │   │
│  │                                                                  │   │
│  │  pointer_prob = softmax(query @ entity_keys)                   │   │
│  │                                                                  │   │
│  │ Example:                                                         │   │
│  │  Query: "Summarize unread emails"                               │   │
│  │  Entities: [email_1, email_2, email_3, file_1, ...]            │   │
│  │  Pointer probs: [0.35, 0.28, 0.22, 0.02, ...]                  │   │
│  │  → Select top-3: [email_1, email_2, email_3]                   │   │
│  │  → Pass to skill executor                                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ OUTPUT: Focused Context                                         │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │ From 50+ entities → 3-5 focused entities                        │   │
│  │ From 100+ memories → Top 10 relevant memories                   │   │
│  │                                                                  │   │
│  │ → Feed to downstream processing (intent, planning, execution)   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  TRAINING:                                                             │
│  • Imitation learning: User clicks on entity → positive example       │
│  • Task success: Attended entities led to goal completion → reward    │
│  • Efficiency: Minimize wasted attention (irrelevant entities)         │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Multi-Modal Fusion

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Multi-Modal Fusion Pipeline                           │
│            (Combining Visual, Audio, Text, Emotion)                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PARALLEL FEATURE EXTRACTION (First Stage)                             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐    │ │
│  │  │ Visual Stream │   │ Audio Stream  │   │  Text Stream  │    │ │
│  │  │               │   │               │   │               │    │ │
│  │  │ Screen        │   │ Microphone    │   │ User typed:   │    │ │
│  │  │ pixels        │   │ waveform      │   │ "summarize    │    │ │
│  │  │ (1920×1080)   │   │ (16kHz)       │   │  emails"      │    │ │
│  │  └───────┬───────┘   └───────┬───────┘   └───────┬───────┘    │ │
│  │          │                   │                   │             │ │
│  │          │                   │                   │             │ │
│  │  ┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐    │ │
│  │  │ Visual Agent  │   │ Auditory Agent│   │Language Center│    │ │
│  │  │               │   │               │   │               │    │ │
│  │  │ - Object det  │   │ - VAD         │   │ - Tokenize    │    │ │
│  │  │ - OCR         │   │ - STT         │   │ - Embed       │    │ │
│  │  │ - Scene class │   │ - Emotion det │   │ - Intent      │    │ │
│  │  └───────┬───────┘   └───────┬───────┘   └───────┬───────┘    │ │
│  │          │                   │                   │             │ │
│  │  ┌───────▼───────────────────▼───────────────────▼───────┐    │ │
│  │  │            Feature Vectors (Parallel)                  │    │ │
│  │  │                                                         │    │ │
│  │  │ visual_features = [0.23, -0.15, 0.87, ...] (512D)     │    │ │
│  │  │ audio_features  = [0.44, 0.21, -0.33, ...] (256D)     │    │ │
│  │  │ text_features   = [0.18, -0.22, 0.91, ...] (384D)     │    │ │
│  │  └─────────────────────────────────────────────────────────┘    │ │
│  │                                                                   │ │
│  │  Latency: ~100ms (parallel processing)                           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  HIERARCHICAL FUSION (Second Stage)                                   │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  Level 1: Pairwise Fusion                                        │ │
│  │  ┌───────────────────────────────────────────────────────────┐  │ │
│  │  │                                                            │  │ │
│  │  │  visual + text → visual_text_fusion                       │  │ │
│  │  │  ┌──────────────────────────────────────────────┐         │  │ │
│  │  │  │ Cross-attention:                             │         │  │ │
│  │  │  │ Q=text, K=visual, V=visual                   │         │  │ │
│  │  │  │ → "emails" text attends to "inbox icon"      │         │  │ │
│  │  │  └──────────────────────────────────────────────┘         │  │ │
│  │  │  Output: 512D fusion vector                                │  │ │
│  │  │                                                            │  │ │
│  │  │  audio + text → audio_text_fusion                         │  │ │
│  │  │  ┌──────────────────────────────────────────────┐         │  │ │
│  │  │  │ "summarize" (text) + neutral tone (audio)    │         │  │ │
│  │  │  │ → Calm, informational request                │         │  │ │
│  │  │  └──────────────────────────────────────────────┘         │  │ │
│  │  │  Output: 384D fusion vector                                │  │ │
│  │  │                                                            │  │ │
│  │  └───────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │  Level 2: Global Fusion                                          │ │
│  │  ┌───────────────────────────────────────────────────────────┐  │ │
│  │  │                                                            │  │ │
│  │  │  Concatenate all:                                          │  │ │
│  │  │  [visual_features, audio_features, text_features,         │  │ │
│  │  │   visual_text_fusion, audio_text_fusion]                  │  │ │
│  │  │  → Total: 2048D                                            │  │ │
│  │  │                                                            │  │ │
│  │  │  Project to unified space:                                 │  │ │
│  │  │  fusion_layer = Linear(2048 → 512)                        │  │ │
│  │  │  unified_repr = fusion_layer(concat_features)              │  │ │
│  │  │                                                            │  │ │
│  │  └───────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │  Latency: ~50ms                                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              ▼                                          │
│  UNIFIED REPRESENTATION (Output)                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  unified_repr (512D) encodes:                                    │ │
│  │  • Visual context: "Email inbox is open"                         │ │
│  │  • Text intent: "Summarize"                                      │ │
│  │  • Audio emotion: "Neutral, calm"                                │ │
│  │  • Cross-modal alignment: Text "emails" ↔ Visual "inbox"        │ │
│  │                                                                   │ │
│  │  → Feed to downstream:                                            │ │
│  │    - Intent classifier                                            │ │
│  │    - Skill planner                                                │ │
│  │    - Personality conditioner                                      │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  TOTAL LATENCY: ~150ms (100ms extraction + 50ms fusion)                │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Cascading Model Selection

```
┌────────────────────────────────────────────────────────────────────────┐
│                  Cascading Model Selection                              │
│         (Fast → Powerful, with Learned Routing)                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Goal: Minimize latency while maintaining accuracy                     │
│                                                                         │
│  Input: User query "Summarize my emails"                               │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ TIER 1: Fast Model (DistilBERT-tiny, 25MB)                     │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │  • Latency: 20ms                                                │   │
│  │  • Accuracy: 90% (good for common queries)                      │   │
│  │  • Power: 1W                                                    │   │
│  │                                                                  │   │
│  │  Try classification:                                            │   │
│  │  intent = fast_model(query)                                     │   │
│  │  confidence = 0.73                                              │   │
│  │                                                                  │   │
│  │  Decision rule:                                                 │   │
│  │  IF confidence > 0.85:                                          │   │
│  │    ACCEPT (90% of queries)                                      │   │
│  │  ELSE:                                                           │   │
│  │    CASCADE to Tier 2                                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              │ confidence=0.73 < 0.85                   │
│                              ▼ CASCADE                                  │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ TIER 2: Balanced Model (GPT-2-small, 100MB)                    │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │  • Latency: 100ms                                               │   │
│  │  • Accuracy: 95% (handles nuanced queries)                      │   │
│  │  • Power: 3W                                                    │   │
│  │                                                                  │   │
│  │  Try classification:                                            │   │
│  │  intent = balanced_model(query)                                 │   │
│  │  confidence = 0.91                                              │   │
│  │                                                                  │   │
│  │  Decision rule:                                                 │   │
│  │  IF confidence > 0.80:                                          │   │
│  │    ACCEPT (9% of queries)                                       │   │
│  │  ELSE:                                                           │   │
│  │    CASCADE to Tier 3                                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              │ confidence=0.91 > 0.80                   │
│                              ▼ ACCEPT                                   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Result: intent="summarize_emails", confidence=0.91              │   │
│  │ Total latency: 20ms + 100ms = 120ms                             │   │
│  │ (Avoided Tier 3, saved 180ms!)                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ TIER 3: Powerful Model (Larger LLM, 500MB)                     │   │
│  │ ──────────────────────────────────────────────────────────────  │   │
│  │                                                                  │   │
│  │  • Latency: 300ms                                               │   │
│  │  • Accuracy: 98% (handles rare/complex queries)                 │   │
│  │  • Power: 8W                                                    │   │
│  │                                                                  │   │
│  │  Only used for:                                                 │   │
│  │  • Complex multi-step reasoning                                 │   │
│  │  • Ambiguous/rare queries (~1% of traffic)                      │   │
│  │  • Tier 1 + Tier 2 both failed                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  LEARNED ROUTING (Advanced)                                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  Instead of cascading, predict WHICH tier to use:                │ │
│  │                                                                   │ │
│  │  routing_model(query) → tier_probabilities                       │ │
│  │    [tier1: 0.65, tier2: 0.30, tier3: 0.05]                       │ │
│  │                                                                   │ │
│  │  → Route directly to Tier 1                                      │ │
│  │  → If Tier 1 fails (confidence <0.85), fallback to Tier 2       │ │
│  │                                                                   │ │
│  │  Training:                                                        │ │
│  │  • Collect (query, actual_tier_used, latency, accuracy) tuples  │ │
│  │  • Train classifier: query → optimal_tier                        │ │
│  │  • Minimize: latency + λ × (1 - accuracy)                        │ │
│  │                                                                   │ │
│  │  Result: ~40% latency reduction vs. always cascading             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  STATISTICS (Typical Distribution):                                    │
│  • 90% queries: Tier 1 only (avg 20ms)                                │
│  • 9% queries: Tier 1 → Tier 2 (avg 120ms)                            │
│  • 1% queries: Tier 1 → Tier 2 → Tier 3 (avg 420ms)                   │
│  • Weighted average: 0.9×20 + 0.09×120 + 0.01×420 = 33ms              │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Module Activation Strategy

### 5.1 Five-State Finite State Machine

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Module State Transitions                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                         ┌──────────────┐                               │
│                         │  UNLOADED    │                               │
│                         │              │                               │
│                         │ Memory: 0 MB │                               │
│                         │ Latency: 1-2s│                               │
│                         └───────┬──────┘                               │
│                                 │                                       │
│                      activate() │ Priority: HIGH                        │
│                 (staged loading)│                                       │
│                                 ▼                                       │
│      ┌─────────────────────────────────────────────┐                  │
│      │             STANDBY                          │                  │
│      │                                              │                  │
│      │ Memory: 150 MB (model loaded)               │                  │
│      │ CPU: Idle                                    │                  │
│      │ Latency: <50ms to activate                  │                  │
│      └───────┬─────────────────────────────┬───────┘                  │
│              │                             │                           │
│         wake()│                             │ hibernate()               │
│    (on input)│                             │ (idle >10 min)            │
│              ▼                             ▼                           │
│      ┌─────────────┐              ┌────────────────┐                  │
│      │   ACTIVE    │              │  HIBERNATED    │                  │
│      │             │              │                │                  │
│      │ Memory:     │              │ Memory: 20 MB  │                  │
│      │  180 MB     │              │ (state only)   │                  │
│      │ CPU: 15%    │              │ Latency: 200ms │                  │
│      │ Power: 3W   │              │                │                  │
│      └──────┬──────┘              └───────┬────────┘                  │
│             │                             │                           │
│      pause()│                             │ suspend()                  │
│  (idle 5min)│                             │ (memory pressure)          │
│             │                             ▼                           │
│             └─────────────►      ┌────────────────┐                  │
│                                   │   SUSPENDED    │                  │
│                                   │                │                  │
│                                   │ Memory: 0 MB   │                  │
│                                   │ (swapped disk) │                  │
│                                   │ Latency: 1-3s  │                  │
│                                   └────────────────┘                  │
│                                            │                           │
│                                   unload() │                           │
│                                            ▼                           │
│                                   ┌──────────────┐                    │
│                                   │  UNLOADED    │                    │
│                                   └──────────────┘                    │
│                                                                         │
│  TRANSITION RULES:                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • Upward (loading): Check memory budget, evict if needed         │ │
│  │ • Downward (unloading): Respect minimum active set + pinned      │ │
│  │ • Cooldown: Must stay loaded ≥5 min after activation             │ │
│  │ • Power-aware: Aggressive unload on battery <20%                 │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Activation Triggers (Triple Intelligence)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Module Activation Triggers                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1️⃣ INPUT-DRIVEN (Reactive, Bottom-Up)                                │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  Screen pixels changed → Activate Visual Agent                   │ │
│  │  ┌───────────────────────────────────────────────────────────┐  │ │
│  │  │ Screen capture: 1920×1080 @ 2 FPS                         │  │ │
│  │  │ Diff from last frame: 15% changed                          │  │ │
│  │  │ → Input Router: "visual_input" event                       │  │ │
│  │  │ → Activation Manager: Activate Visual Agent               │  │ │
│  │  │    Current state: HIBERNATED                               │  │ │
│  │  │    Action: Load models (200ms), set to ACTIVE              │  │ │
│  │  └───────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │  Microphone audio → Activate Auditory Agent                      │ │
│  │  User types → Activate Language Center                           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  2️⃣ GOAL-DRIVEN (Task-Based, Top-Down)                                │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  Central Agent: "User wants to summarize emails"                 │ │
│  │  ┌───────────────────────────────────────────────────────────┐  │ │
│  │  │ Intent: summarize_emails                                   │  │ │
│  │  │                                                             │  │ │
│  │  │ Capability Planner: Required modules:                      │  │ │
│  │  │   - Language Center (CRITICAL, for text processing)        │  │ │
│  │  │   - Skill Executor (CRITICAL, for email skill)             │  │ │
│  │  │   - Tool Plugin (MEDIUM, for email access)                 │  │ │
│  │  │                                                             │  │ │
│  │  │ Activation Manager:                                         │  │ │
│  │  │   - Language Center: Already ACTIVE ✓                      │  │ │
│  │  │   - Skill Executor: STANDBY → Wake (50ms) ✓                │  │ │
│  │  │   - Tool Plugin: HIBERNATED → Load (300ms) ✓               │  │ │
│  │  │                                                             │  │ │
│  │  │ Total activation latency: 300ms                             │  │ │
│  │  │ Proceed with intent execution                               │  │ │
│  │  └───────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  3️⃣ PREDICTIVE (Pattern-Based, Proactive)                             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  Pattern Learner: "User checks emails at 9am daily"              │ │
│  │  ┌───────────────────────────────────────────────────────────┐  │ │
│  │  │ Current time: 8:58am                                       │  │ │
│  │  │ Context: {hour: 8, day: Monday, active_app: "terminal"}   │  │ │
│  │  │                                                             │  │ │
│  │  │ ML Prediction:                                              │  │ │
│  │  │   P(language_center needed in 5 min) = 0.87               │  │ │
│  │  │   P(skill_executor needed in 5 min) = 0.82                │  │ │
│  │  │   P(visual_agent needed in 5 min) = 0.23                  │  │ │
│  │  │                                                             │  │ │
│  │  │ Preload Decision (threshold = 0.70):                       │  │ │
│  │  │   ✓ Preload Language Center (0.87 > 0.70)                 │  │ │
│  │  │   ✓ Preload Skill Executor (0.82 > 0.70)                  │  │ │
│  │  │   ✗ Skip Visual Agent (0.23 < 0.70)                       │  │ │
│  │  │                                                             │  │ │
│  │  │ Action: Background preload at LOW priority                 │  │ │
│  │  │ Result: When user opens email at 9am, instant response!    │  │ │
│  │  └───────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  COORDINATION:                                                         │
│  All three triggers can fire simultaneously:                           │
│  • Input-driven: Highest priority (user is waiting)                   │
│  • Goal-driven: Medium priority (task in progress)                    │
│  • Predictive: Lowest priority (speculative, can be interrupted)      │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Eviction Policy (Weighted LRU)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    Memory Pressure → Eviction                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Situation: Memory usage 950 MB / 1000 MB (95% full)                  │
│             Need to load Voice Synthesis Agent (100 MB)                │
│             → Must evict ~100 MB                                        │
│                                                                         │
│  STEP 1: Calculate Eviction Scores                                     │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │ Formula:                                                          │ │
│  │ eviction_score = 0.4×recency + 0.3×frequency + 0.3×importance    │ │
│  │                                                                   │ │
│  │ Higher score = More evictable                                    │ │
│  │                                                                   │ │
│  │ ┌───────────────────────────────────────────────────────────┐  │ │
│  │ │ Module: Visual Agent                                       │  │ │
│  │ │ ───────────────────────────────────────────────────────── │  │ │
│  │ │ Last used: 18 minutes ago                                 │  │ │
│  │ │ recency_score = min(18×60 / 3600, 1.0) = 0.30            │  │ │
│  │ │                                                            │  │ │
│  │ │ Activations: 2 per hour                                   │  │ │
│  │ │ frequency_score = 1 / (2 + 1) = 0.33                     │  │ │
│  │ │                                                            │  │ │
│  │ │ Base importance: 0.6 (medium)                             │  │ │
│  │ │ importance_score = 1 - 0.6 = 0.40                         │  │ │
│  │ │                                                            │  │ │
│  │ │ eviction_score = 0.4×0.30 + 0.3×0.33 + 0.3×0.40 = 0.34   │  │ │
│  │ └───────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │ ┌───────────────────────────────────────────────────────────┐  │ │
│  │ │ Module: Character Animator                                │  │ │
│  │ │ ───────────────────────────────────────────────────────── │  │ │
│  │ │ Last used: 32 minutes ago                                 │  │ │
│  │ │ recency_score = min(32×60 / 3600, 1.0) = 0.53            │  │ │
│  │ │                                                            │  │ │
│  │ │ Activations: 0.5 per hour (rare)                          │  │ │
│  │ │ frequency_score = 1 / (0.5 + 1) = 0.67                   │  │ │
│  │ │                                                            │  │ │
│  │ │ Base importance: 0.4 (low)                                │  │ │
│  │ │ importance_score = 1 - 0.4 = 0.60                         │  │ │
│  │ │                                                            │  │ │
│  │ │ eviction_score = 0.4×0.53 + 0.3×0.67 + 0.3×0.60 = 0.59   │  │ │
│  │ │                              ^^^^^ HIGHEST SCORE           │  │ │
│  │ └───────────────────────────────────────────────────────────┘  │ │
│  │                                                                   │ │
│  │ ┌───────────────────────────────────────────────────────────┐  │ │
│  │ │ Module: Language Center                                    │  │ │
│  │ │ ───────────────────────────────────────────────────────── │  │ │
│  │ │ Last used: 2 minutes ago                                  │  │ │
│  │ │ recency_score = min(2×60 / 3600, 1.0) = 0.03             │  │ │
│  │ │                                                            │  │ │
│  │ │ Activations: 15 per hour (frequent)                       │  │ │
│  │ │ frequency_score = 1 / (15 + 1) = 0.06                    │  │ │
│  │ │                                                            │  │ │
│  │ │ Base importance: 0.9 (high)                               │  │ │
│  │ │ importance_score = 1 - 0.9 = 0.10                         │  │ │
│  │ │                                                            │  │ │
│  │ │ eviction_score = 0.4×0.03 + 0.3×0.06 + 0.3×0.10 = 0.06   │  │ │
│  │ │                              ^^^^^ LOWEST SCORE            │  │ │
│  │ └───────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  STEP 2: Select Eviction Candidate                                     │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │ Ranking (highest to lowest evictability):                        │ │
│  │   1. Character Animator (score=0.59) ← EVICT THIS               │ │
│  │   2. Emotion Regulator (score=0.45)                              │ │
│  │   3. Visual Agent (score=0.34)                                   │ │
│  │   4. Auditory Agent (score=0.28)                                 │ │
│  │   5. Skill Executor (score=0.22)                                 │ │
│  │   6. Language Center (score=0.06)                                │ │
│  │                                                                   │ │
│  │ Decision: Evict Character Animator (frees 60 MB)                 │ │
│  │           Not enough, also evict Emotion Regulator (80 MB)       │ │
│  │           Total freed: 140 MB > 100 MB needed ✓                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  STEP 3: Execute Eviction                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                   │ │
│  │  deactivate(Character Animator, target=HIBERNATED)               │ │
│  │    → Save state to Redis                                          │ │
│  │    → Unload model from memory                                     │ │
│  │    → Log eviction                                                 │ │
│  │                                                                   │ │
│  │  deactivate(Emotion Regulator, target=HIBERNATED)                │ │
│  │    → Same process                                                 │ │
│  │                                                                   │ │
│  │  Memory freed: 140 MB                                             │ │
│  │  New usage: 810 MB / 1000 MB (81%)                                │ │
│  │                                                                   │ │
│  │  activate(Voice Synthesis Agent)                                  │ │
│  │    → Load model (100 MB)                                          │ │
│  │    → Final usage: 910 MB / 1000 MB (91%) ✓                       │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  THRASHING PREVENTION:                                                 │
│  • Cooldown: Character Animator cannot be reactivated for 5 minutes   │
│  • Hysteresis: If predicted need <30%, stay hibernated                │
│  • Cost-based: Only evict if reload_cost < memory_benefit             │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Data Flow Integration

### 6.1 End-to-End Request Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│              Complete Request Flow: "Summarize my emails"               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  t=0ms    User types "Summarize my emails"                             │
│           ┌──────────────────────────────────────────────┐            │
│           │ Input: text_input                             │            │
│           │ Source: keyboard                              │            │
│           └────────────┬─────────────────────────────────┘            │
│                        │                                               │
│  t=5ms               Event Bus (Redis Pub/Sub)                         │
│                        │                                               │
│                        ▼                                               │
│           ┌────────────────────────────────────────────────┐          │
│           │ Central Agent: Reactive Loop                   │          │
│           │ - Input Router: Classify as "text_input"       │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=10ms   ┌────────────▼───────────────────────────────────┐          │
│           │ Check: Is Language Center active?              │          │
│           │ → Yes, already in ACTIVE state ✓              │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=15ms   ┌────────────▼───────────────────────────────────┐          │
│           │ Attention Mechanism (AlphaStar)                │          │
│           │ - Priority Queue: User input = priority 10     │          │
│           │ - Focus: [text_input, recent_context]          │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=25ms   ┌────────────▼───────────────────────────────────┐          │
│           │ Intent Recognition                              │          │
│           │ - Model: DistilBERT-tiny (Tier 1)              │          │
│           │ - Intent: "summarize_emails"                    │          │
│           │ - Confidence: 0.92 (>0.85 threshold) ✓        │          │
│           │ - No cascade needed                             │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=50ms   ┌────────────▼───────────────────────────────────┐          │
│           │ Memory Retrieval (Hybrid Search)               │          │
│           │ - Query Redis: Recent email events             │          │
│           │ - Query Qdrant: Semantic "email" memories      │          │
│           │ - Merged results: 8 relevant memories          │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=100ms  ┌────────────▼───────────────────────────────────┐          │
│           │ Skill Planner (Central Agent)                  │          │
│           │ - Required skill: "summarize_emails"           │          │
│           │ - Dependencies (Neo4j query):                  │          │
│           │   └─ read_email → parse_text                   │          │
│           │   └─ categorize → parse_text                   │          │
│           │   └─ generate_summary → llm_inference          │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=120ms  ┌────────────▼───────────────────────────────────┐          │
│           │ Module Activation (Check & Load)               │          │
│           │ - Skill Executor: STANDBY → Wake (30ms)        │          │
│           │ - Tool Plugin (Email): HIBERNATED → Load (80ms)│          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=200ms  ┌────────────▼───────────────────────────────────┐          │
│           │ Skill Executor (Dataflow Execution)            │          │
│           │                                                 │          │
│           │ Step 1: parse_text (already loaded, fast)      │          │
│           │   Parse 12 unread emails                        │          │
│           │   → Extract: subjects, senders, timestamps     │          │
│           │                                                 │          │
│           │ Step 2: categorize (lazy-load model: 150ms)    │          │
│           │   Classify emails:                              │          │
│           │   - 5 work-related (2 urgent)                   │          │
│           │   - 4 newsletters                               │          │
│           │   - 3 personal                                  │          │
│           │                                                 │          │
│           │ Step 3: generate_summary (LLM inference)       │          │
│           │   Model: GPT-2-small (Tier 2)                  │          │
│           │   Input: Parsed + categorized data             │          │
│           │   Output: Natural language summary             │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=1200ms ┌────────────▼───────────────────────────────────┐          │
│           │ Personality Conditioning                        │          │
│           │ - User's Big Five: [O=0.8, C=0.7, ...]        │          │
│           │ - Tone: Enthusiastic, detailed                 │          │
│           │ - Voice modulation: +10% energy                │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=1250ms ┌────────────▼───────────────────────────────────┐          │
│           │ Response Generation                             │          │
│           │                                                 │          │
│           │ "You have 12 unread emails! 🎉                │          │
│           │  • 5 work-related (2 marked urgent - check    │          │
│           │    the message from your manager!)            │          │
│           │  • 4 newsletters (can archive if not needed)  │          │
│           │  • 3 personal messages from friends"           │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=1260ms ┌────────────▼───────────────────────────────────┐          │
│           │ Memory Consolidation (Async)                   │          │
│           │ - Store request in Redis (importance=0.85)     │          │
│           │ - Store response in Redis                       │          │
│           │ - Will consolidate to Qdrant during idle       │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=1270ms ┌────────────▼───────────────────────────────────┐          │
│           │ Skill Stats Update                              │          │
│           │ - summarize_emails: Success! (+100 XP)         │          │
│           │ - Competency: 88% → 89% (level up!)           │          │
│           │ - Usage count: 47 → 48                         │          │
│           └────────────┬───────────────────────────────────┘          │
│                        │                                               │
│  t=1280ms              ▼                                               │
│           ┌──────────────────────────────────────────────┐            │
│           │ Display Response to User                      │            │
│           │ Total latency: 1.28 seconds                   │            │
│           └───────────────────────────────────────────────┘            │
│                                                                         │
│  LATENCY BREAKDOWN:                                                    │
│  • Intent recognition: 25ms                                            │
│  • Memory retrieval: 25ms                                              │
│  • Skill planning: 50ms                                                │
│  • Module activation: 100ms                                            │
│  • Skill execution: 1000ms (bulk of time)                              │
│  • Response generation: 50ms                                           │
│  • Overhead: 30ms                                                      │
│  Total: 1280ms (~1.3s, within acceptable range for complex task)      │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Tool Plugin System

### 7.1 Permission & Risk Flow

```
USER REQUEST → TOOL ACTION
══════════════════════════════════════════════════════════════════════════

  Tool Action Requested
         │
         ▼
  ┌─────────────────────────────────────────────┐
  │           Risk Scorer                        │
  │                                              │
  │  risk = base_risk                            │
  │       × context_multiplier                  │
  │       × history_factor                       │
  │                                              │
  │  base_risk:  file_read=0.1  file_write=0.4  │
  │              email=0.7      payment=0.95     │
  └──────────────────────┬──────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    0.0-0.2         0.2-0.4         0.4-0.6
         │               │               │
         ▼               ▼               ▼
   AUTO-APPROVE    CHECK PRE-       ASK ONCE
                   APPROVAL         (session)
                         │               │
                    0.6-0.8         0.8-1.0
                         │               │
                         ▼               ▼
                   ALWAYS ASK      REQUIRE EXPLICIT
                   + PREVIEW       CONFIRMATION
                                   + SHOW DIFF

══════════════════════════════════════════════════════════════════════════
HOST vs CLIENT DEVICE SPLIT

  ┌────────────────────────┐    ┌────────────────────────┐
  │      RPi5 (Host)       │    │    Client Device        │
  │                        │    │                        │
  │  Full autonomy         │    │  MUST ASK USER         │
  │  ─────────────         │    │  ───────────────       │
  │  • Read/write files    │    │  • Any file access     │
  │  • Run processes       │    │  • Clipboard read/write│
  │  • System calls        │    │  • Input simulation    │
  │  • Network (localhost) │    │  • App control         │
  │  • Manage databases    │    │  • Screenshots         │
  └────────────────────────┘    └────────────────────────┘
```

### 7.2 Sandbox Architecture

```
TOOL EXECUTION SANDBOX
══════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────┐
  │                    Tool Coordinator                               │
  │                                                                  │
  │   Receives tool call → determines sandbox tier                  │
  └──────────────────────────────┬───────────────────────────────────┘
                                 │
           ┌──────────────────── ┼ ────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
  ┌────────────────┐   ┌─────────────────┐   ┌──────────────────┐
  │  SHARED POOL   │   │  DEDICATED      │   │  ISOLATED VM     │
  │  (default)     │   │  CONTAINER      │   │  (critical)      │
  │                │   │  (sensitive)    │   │                  │
  │  Most tools    │   │  Email/SSH/     │   │  Payment,        │
  │  File ops      │   │  File browser   │   │  credentials     │
  │  Web scrape    │   │                 │   │                  │
  │  ~50ms start   │   │  ~200ms start   │   │  ~1s start       │
  │  Shared net    │   │  Isolated net   │   │  No net          │
  └────────────────┘   └─────────────────┘   └──────────────────┘
           │                     │                     │
           └─────────────────────┴─────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Result + Audit Log     │
                    │   (every action logged)  │
                    └─────────────────────────┘

  RESOURCE LIMITS PER SANDBOX:
  • CPU:        max 1 core
  • Memory:     max 256 MB
  • Disk I/O:   max 10 MB/s
  • Network:    allowlist-only
  • Timeout:    30s default, 300s max
```

### 7.3 AI-Synthesized Tool Pipeline

```
DISCOVER → GENERATE → TEST → APPROVE → USE
══════════════════════════════════════════════════════════════════════════

  Bodhi identifies gap                    e.g. "I need to check weather"
         │
         ▼
  ┌─────────────────┐
  │  API Discovery  │  ← Searches known API registry + web
  │                 │    Finds: openweathermap.org
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Code Generator │  ← LLM writes Python tool wrapper
  │                 │    Follows plugin interface spec
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Auto-Tester    │  ← Runs in isolated sandbox
  │                 │    Validates inputs/outputs
  │                 │    Checks for malicious patterns
  └────────┬────────┘
           │
           ▼
  ┌─────────────────────────────────────────────┐
  │  USER REVIEW                                 │
  │                                              │
  │  "I created a weather tool. Review code?"   │
  │                                              │
  │  [View Code]  [Approve]  [Reject]  [Edit]   │
  └────────┬────────────────────────────────────┘
           │ approved
           ▼
  ┌─────────────────┐
  │  Tool Registry  │  ← Saved, versioned, reusable
  └─────────────────┘
```

---

## 8. Screen Awareness Pipeline

### 8.1 Full Pipeline

```
CLIENT DEVICE                              HOST (Bodhi RPi5)
══════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────┐
  │         Privacy Filter          │
  │  ① App blacklist check         │
  │  ② Window title blacklist      │
  │  ③ ML redaction (passwords,    │
  │     credit cards, SSNs, keys)  │
  │  ④ Optional user review        │
  └──────────────┬──────────────────┘
                 │ BLOCKED? → stop here
                 │ PASS? → continue
                 ▼
  ┌─────────────────────────────────┐
  │      Capture Engine             │
  │                                 │
  │  Mode A: Full Screen            │
  │  Mode B: Active Window          │
  │  Mode C: Region                 │
  │  Mode D: Smart Areas (ML)       │
  └──────────────┬──────────────────┘
                 │  raw pixels (never leave device)
                 ▼
  ┌─────────────────────────────────┐
  │    Client-Side Processing       │
  │                                 │
  │  OCR  ←── Tesseract (30 MB)    │
  │  Objects ← YOLO-Nano (25 MB)   │
  │  Scene  ←  MobileNetV3 (10 MB) │
  │  UI     ←  ViT-Tiny (20 MB)    │
  │  A11y   ←  Accessibility tree  │
  └──────────────┬──────────────────┘
                 │  JSON insights (10-50 KB)
                 │  raw pixels NEVER sent ──────────────────────►
                 ▼                         only structured JSON
  ┌─────────────────────────────────┐      ──────────────────────►
  │    Insight Packet               │
  │  {                              │      ┌──────────────────────┐
  │    app: "VSCode",               │─────►│   Visual Agent       │
  │    activity: "coding",          │      │                      │
  │    text_blocks: [...],          │      │   Integrates with    │
  │    objects: [...],              │      │   Central Agent      │
  │    redactions: 2                │      │   context            │
  │  }                              │      └──────────────────────┘
  └─────────────────────────────────┘
```

### 8.2 Capture Mode Selection

```
USER QUERY or BODHI NEED
         │
         ▼
  "What's on my screen?"        → Full Screen
  "What's in this window?"      → Active Window
  "What's in that corner?"      → Region
  "What should I pay attention" → Smart Areas (ML)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Smart Areas Detection (Mode D)                             │
  │                                                             │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │              Screen                                  │  │
  │  │  ┌──────┐  ┌─────────────────┐  ┌────────────────┐  │  │
  │  │  │ High │  │   Medium Salience│  │  Low Salience  │  │  │
  │  │  │Salient  │   (context)      │  │   (ignore)     │  │  │
  │  │  │region│  └─────────────────┘  └────────────────┘  │  │
  │  │  │      │                                            │  │
  │  │  │  ●   │  ← ML model identifies what matters       │  │
  │  │  └──────┘    based on user's current task           │  │
  │  └──────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────┘
```

### 8.3 Privacy Layers

```
LAYER 1: App Blacklist          LAYER 2: Window Title Blacklist
─────────────────────           ────────────────────────────────
  1Password ──► BLOCKED           "Login" ──────────► BLOCKED
  Bitwarden ──► BLOCKED           "Password" ────────► BLOCKED
  Chase     ──► BLOCKED           "Credit Card" ─────► BLOCKED
  PayPal    ──► BLOCKED           "Private" ─────────► BLOCKED

LAYER 3: ML Redaction           LAYER 4: User Review (optional)
──────────────────────          ────────────────────────────────
  ██████████ ← passwords          "Found sensitive data.
  ████████   ← credit cards        Show me what was captured
  ███-██-████ ← SSNs               before sending? [Y/N]"
  sk-████████ ← API keys
```

---

## 9. Character Animation System

### 9.1 Animation State Machine

```
BODHI CHARACTER — ANIMATION STATES
══════════════════════════════════════════════════════════════════════════

                        ┌──────────────┐
                        │    IDLE      │ ← breathing, blinking
                        │  (default)   │   subtle movements
                        └──────┬───────┘
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌────────────┐  ┌──────────────┐  ┌────────────────┐
       │  LISTENING │  │   THINKING   │  │   SPEAKING     │
       │            │  │              │  │                │
       │ ear perked │  │ eyes up-left │  │ mouth animates │
       │ lean fwd   │  │ hand on chin │  │ lip sync active│
       │ attentive  │  │ loading anim │  │ gesture matched│
       └────────────┘  └──────────────┘  └────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌────────────┐  ┌──────────────┐  ┌────────────────┐
       │  WORKING   │  │  EMOTIONAL   │  │    SLEEPING    │
       │            │  │  REACTION    │  │                │
       │ focused    │  │              │  │ ZZZ animation  │
       │ typing     │  │ joy/surprise │  │ slow breathing │
       │ searching  │  │ sad/concern  │  │ power saving   │
       └────────────┘  └──────────────┘  └────────────────┘

  EMOTION → ANIMATION MAPPING (Big Five influenced):
  ┌─────────────────────────────────────────────────────────────┐
  │  Emotion State  │  Valence  │  Arousal  │  Animation Set   │
  ├─────────────────┼───────────┼───────────┼──────────────────┤
  │  Happy          │  +0.8     │  +0.6     │  bounce, smile   │
  │  Excited        │  +0.7     │  +0.9     │  jump, sparkle   │
  │  Calm           │  +0.3     │  -0.5     │  gentle sway     │
  │  Curious        │  +0.2     │  +0.4     │  head tilt, lean │
  │  Concerned      │  -0.3     │  +0.2     │  furrow, slouch  │
  │  Sad            │  -0.7     │  -0.6     │  droop, sigh     │
  └─────────────────┴───────────┴───────────┴──────────────────┘
```

### 9.2 Positioning System

```
SMART POSITIONING — SPIRAL SEARCH ALGORITHM
══════════════════════════════════════════════════════════════════════════

  Screen Layout:
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  ┌──────────────────────────┐                   │
  │  │                          │                   │
  │  │     Active Window        │       ← AVOID     │
  │  │                          │                   │
  │  └──────────────────────────┘                   │
  │                                    ┌─────────┐  │
  │                                    │  BODHI  │  │
  │                                    │   🤖    │  │
  │  TASKBAR ─────────────────────── ← └─────────┘  │
  └──────────────────────────────────────────────────┘

  Search Order (prefer corners, avoid active content):
  ① Bottom-right     ← default preference
  ② Bottom-left
  ③ Top-right
  ④ Top-left
  ⑤ Mid-right edge
  ⑥ Mid-left edge
  ⑦ Center (last resort, with opacity)

  DOCKING — "COUCH" MODE:
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │                                                  │
  │                                                  │
  │  ════════════════════════════════════════════   │
  │  ║  [sofa arm]  🤖 Bodhi  [sofa back]       ║  │
  │  ════════════════════════════════════════════   │
  └──────────────────────────────────────────────────┘
  Bodhi sits on a virtual "couch" docked to bottom of screen.
  Feet visible, legs dangling — persistent, comfortable presence.
```

### 9.3 Multi-Style Architecture

```
CHARACTER STYLE SELECTOR
══════════════════════════════════════════════════════════════════════════

  User Preference / Auto-Select
         │
         ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                  Embodiment Abstraction Layer                 │
  │                                                              │
  │  motor_command("wave", intensity=0.8, duration=1.2s)        │
  │  motor_command("smile", type="happy", magnitude=0.9)        │
  │  motor_command("speak", phonemes=[...], emotion="excited")  │
  └──────────┬──────────────┬─────────────────┬─────────────────┘
             │              │                 │
             ▼              ▼                 ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
   │  2D Sprite   │ │ 2D Skeletal  │ │  3D Low-Poly     │
   │  (5-10 MB)   │ │  (20-40 MB)  │ │  (50-80 MB)      │
   │              │ │              │ │                  │
   │  PNG sheets  │ │  Spine2D /   │ │  Three.js /      │
   │  frame-based │ │  DragonBones │ │  Babylon.js      │
   │  retro style │ │  fluid anim  │ │  modern look     │
   └──────────────┘ └──────────────┘ └──────────────────┘
             │              │                 │
             └──────────────┴─────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Same API for  │
                    │  Physical Robot│
                    │  (VLA future)  │
                    └────────────────┘
```

---

## 10. Voice Pipeline

### 10.1 Full Voice Flow

```
CLIENT DEVICE (Privacy)              HOST / Bodhi (Intelligence)
══════════════════════════════════════════════════════════════════════════

  SPEECH INPUT PATH:

  🎤 Microphone
       │
       ▼
  ┌──────────────────┐
  │  Silero VAD      │  ← Voice Activity Detection (8 MB)
  │  (8 MB)         │    Strips silence, saves bandwidth
  └────────┬─────────┘
           │ voice detected
           ▼
  ┌──────────────────┐     Wake word
  │  Porcupine       │─────detected──►  Bodhi activates
  │  Wake Word       │
  │  (3 MB)          │     OR
  └────────┬─────────┘
           │ push-to-talk
           ▼
  ┌──────────────────┐
  │  Whisper STT     │  ← Local model options:
  │                  │    tiny   (39 MB)  fastest
  │                  │    base   (74 MB)  balanced
  │                  │    small  (244 MB) most accurate
  └────────┬─────────┘
           │ transcript + confidence
           │
           └─────────────────────────────────────────►
                                                      │
                                    ┌─────────────────▼──────────────┐
                                    │        Central Agent           │
                                    │                                │
                                    │  Processes intent              │
                                    │  Generates response text       │
                                    │  Sets emotional context        │
                                    └─────────────────┬──────────────┘
                                                      │
  SPEECH OUTPUT PATH:                                 │
                                    ┌─────────────────▼──────────────┐
                                    │      Prosody Generator         │
                                    │                                │
                                    │  • Add pauses at punctuation   │
                                    │  • Emphasize key words         │
                                    │  • Speed from arousal          │
                                    │  • Pitch from valence          │
                                    └─────────────────┬──────────────┘
                                                      │
                                    ┌─────────────────▼──────────────┐
                                    │      Piper TTS (20-100 MB)     │
                                    │                                │
                                    │  10+ voice models              │
                                    │  Personality-matched           │
                                    │  Emotion-modulated             │
                                    └─────────────────┬──────────────┘
                                                      │
                              audio + phoneme timings │
           ◄──────────────────────────────────────────┘
           │
           ▼
  ┌──────────────────┐
  │  Audio Playback  │  → 🔊 Speaker
  │  + Lip-sync data │  → 👄 Character mouth animation
  └──────────────────┘
```

### 10.2 Emotional Voice Modulation

```
EMOTION STATE → VOICE PARAMETERS
══════════════════════════════════════════════════════════════════════════

  Emotion Regulator output:
  { valence: +0.7, arousal: +0.5, dominance: +0.3 }
                    │
                    ▼
  ┌────────────────────────────────────────────────┐
  │            Voice Parameter Mapper              │
  │                                                │
  │  speed    = 1.0 + (arousal × 0.3)             │
  │           = 1.15 (slightly faster)             │
  │                                                │
  │  pitch    = 1.0 + (valence × 0.1)             │
  │           = 1.07 (slightly higher)             │
  │                                                │
  │  energy   = 0.8 + (arousal × 0.2)             │
  │           = 0.90 (more energetic)              │
  │                                                │
  │  pause    = base × (1.0 - arousal × 0.2)      │
  │           = shorter pauses (excited)           │
  └────────────────────────────────────────────────┘
                    │
                    ▼
          Modulated Piper TTS Output

  VOICE PROFILES (Personality-Matched):
  ┌──────────────────────────────────────────────────┐
  │  High Extraversion  → Warm, expressive voice     │
  │  High Openness      → Varied pitch, curious tone │
  │  High Agreeableness → Soft, friendly voice       │
  │  Low Neuroticism    → Steady, calm voice         │
  └──────────────────────────────────────────────────┘
```

### 10.3 Cloud Integration (Optional)

```
LOCAL (Default)              USER-PROVIDED CLOUD (Optional)
═════════════════            ═══════════════════════════════
  Whisper (local)       OR      OpenAI Whisper API
  Piper (local)         OR      ElevenLabs TTS
                        OR      Azure Speech Services
                        OR      Google Cloud TTS

  User provides own API key → stored encrypted locally
  No Bodhi servers ever touch user's API key
  Can mix: local STT + cloud TTS, or vice versa
```

---

## 11. Sub-Agent Communication

### 11.1 Event Bus Topology

```
REDIS PUB/SUB EVENT BUS — ALL AGENT CONNECTIONS
══════════════════════════════════════════════════════════════════════════

                         ┌─────────────────┐
                         │   Central Agent │
                         │  (Orchestrator) │
                         └────────┬────────┘
                    subscribe/publish all topics
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    user.* topic           system.* topic           task.* topic
          │                       │                       │
  ┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
  │ Visual Agent   │    │ Memory Manager  │    │ Skill Executor  │
  │                │    │                 │    │                 │
  │ pub: visual.*  │    │ pub: memory.*   │    │ pub: skill.*    │
  │ sub: user.*    │    │ sub: emotion.*  │    │ sub: task.*     │
  └───────┬────────┘    └────────┬────────┘    └────────┬────────┘
          │                      │                       │
  visual.* topic          memory.* topic          skill.* topic
          │                      │                       │
  ┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
  │Auditory Agent  │    │ Language Center │    │Tool Coordinator │
  │                │    │                 │    │                 │
  │ pub: audio.*   │    │ pub: language.* │    │ pub: tool.*     │
  │ sub: user.*    │    │ sub: user.*     │    │ sub: task.*     │
  └───────┬────────┘    └────────┬────────┘    └────────┬────────┘
          │                      │                       │
  audio.* topic        language.* topic          tool.* topic
          │                      │                       │
  ┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
  │ Motor          │    │Emotion Regulator│    │ Voice           │
  │ Controller     │    │                 │    │ Synthesizer     │
  │                │    │ pub: emotion.*  │    │ pub: voice.*    │
  │ pub: motor.*   │    │ sub: language.* │    │ sub: language.* │
  │ sub: emotion.* │    │     skill.*     │    │     emotion.*   │
  └────────────────┘    └─────────────────┘    └─────────────────┘
```

### 11.2 Agent Memory Budget

```
MEMORY ALLOCATION (RPi5 8GB)
══════════════════════════════════════════════════════════════════════════

  Total:              8192 MB
  OS + Docker:       -2048 MB
  ─────────────────────────────
  Available:          6144 MB

  Infrastructure:
  ├── Redis            256 MB  ███
  ├── PostgreSQL        512 MB  ██████
  ├── Neo4j            1024 MB  ████████████
  └── Qdrant            512 MB  ██████
  Subtotal:           2304 MB

  Core Services:
  ├── Central Agent    512 MB  ██████
  ├── Visual Agent      50 MB  █
  ├── Auditory Agent    40 MB  ▌
  ├── Language Center  150 MB  ██
  ├── Emotion Reg.      30 MB  ▌
  ├── Skill Executor   200 MB  ███
  ├── Memory Manager   200 MB  ███
  ├── Voice Synth.     180 MB  ██
  ├── Motor Controller  30 MB  ▌
  └── Tool Coordinator  80 MB  █
  Subtotal:           1472 MB

  Monitoring:
  ├── Prometheus        256 MB  ███
  ├── Grafana           128 MB  ██
  ├── Loki              256 MB  ███
  └── Promtail           64 MB  █
  Subtotal:             704 MB

  ─────────────────────────────
  Total Used:          4480 MB  (55%)
  Headroom:            1664 MB  (20%)
  OS Buffers:           ~2 GB  (25%)
```

### 11.3 Agent Lifecycle (Module Activation)

```
STARTUP SEQUENCE
══════════════════════════════════════════════════════════════════════════

  t=0s    Infrastructure starts (Redis, Postgres, Neo4j, Qdrant)
            │
  t=10s   ▼  Databases healthy
            Central Agent loads
            Memory Manager loads
            ─── Bodhi is minimally functional ───
            │
  t=20s   ▼  Core ready
            Language Center loads
            Emotion Regulator loads
            ─── Bodhi can converse ───
            │
  t=35s   ▼  Full cognition ready
            Skill Executor loads
            Tool Coordinator loads
            ─── Bodhi can take actions ───
            │
  t=50s   ▼  Sensory/motor ready (if enabled)
            Visual Agent loads
            Auditory Agent loads
            Voice Synthesizer loads
            Motor Controller loads
            ─── Bodhi has full capabilities ───

  SHUTDOWN (graceful, reverse order):
  Motor → Voice → Auditory → Visual → Tool → Skill →
  Emotion → Language → Memory → Central → Infrastructure
```

---

## 12. System Integration

### 12.1 Full System Overview (Updated)

```
BODHI — COMPLETE SYSTEM ARCHITECTURE
══════════════════════════════════════════════════════════════════════════

  CLIENT DEVICE(S)                      RPi5 HOST
  ─────────────────                     ──────────────────────────────────
  ┌──────────────┐   mTLS / gRPC       ┌──────────────────────────────┐
  │  Screen Cap  │──────────────────►  │         API Gateway          │
  │  Mic Input   │◄──────────────────  │         (port 8080)          │
  │  Audio Out   │                     └──────────────┬───────────────┘
  │  Character   │                                    │
  └──────────────┘                     ┌──────────────▼───────────────┐
                                       │        Central Agent          │
  ┌──────────────┐                     │                              │
  │  Web Browser │   HTTP/WebSocket    │  Decision Loop               │
  │  Dashboard   │──────────────────►  │  Attention Mechanism         │
  │  (Grafana)   │◄──────────────────  │  Personality Integration     │
  └──────────────┘                     └──────────────┬───────────────┘
                                                       │
                              ┌─────── Redis Event Bus ┼────────┐
                              │                        │        │
               ┌──────────────▼──────┐  ┌─────────────▼──┐  ┌──▼────────────┐
               │   Cognitive Layer   │  │  Memory Layer   │  │ Action Layer  │
               │                     │  │                 │  │               │
               │  Language Center    │  │  Memory Manager │  │ Skill Executor│
               │  Emotion Regulator  │  │  ──────────────  │  │ Tool Coord.   │
               │  Visual Agent       │  │  Redis (hot)    │  │               │
               │  Auditory Agent     │  │  Qdrant (warm)  │  │               │
               └─────────────────────┘  │  Postgres (cold)│  └───────────────┘
                                        └─────────────────┘
                              │                              │
               ┌──────────────▼──────┐         ┌────────────▼──────────────┐
               │  Knowledge Layer    │         │      Output Layer          │
               │                     │         │                            │
               │  Neo4j (Skill Tree) │         │  Voice Synthesizer         │
               │  Qdrant (Vectors)   │         │  Motor Controller          │
               │  Postgres (Meta)    │         │  → Character Animation     │
               └─────────────────────┘         │  → Lip Sync                │
                                               └────────────────────────────┘
```

### 12.2 Docker Service Dependency Graph

```
STARTUP DEPENDENCIES
══════════════════════════════════════════════════════════════════════════

  redis ─────────────────────────────────────┐
  postgres ──────────────────────────────────┤
  neo4j ─────────────────────────────────────┤
  qdrant ─────────────────────────────────────┤
                                              │
                              ┌───────────────▼──────────────┐
                              │        central-agent          │
                              └───────────┬───────────────────┘
                                          │
              ┌───────────────────────────┼──────────────────────────┐
              │                           │                          │
              ▼                           ▼                          ▼
       memory-manager             language-center            api-gateway
              │                           │
              ▼                           ▼
       skill-executor             emotion-regulator
              │
       tool-coordinator
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
 visual-   auditory-   voice-
 agent     agent       synthesizer
              │
         motor-controller
```

### 12.3 End-to-End Request Flow (Full System)

```
EXAMPLE: "Bodhi, summarize my emails and read them to me"
══════════════════════════════════════════════════════════════════════════

   CLIENT                 API GATEWAY          CENTRAL AGENT
     │                        │                      │
     │  wake word detected    │                      │
     │──────────────────────►│                      │
     │                        │  route to agent      │
     │                        │─────────────────────►│
     │                        │                      │ attention scored
     │                        │                      │ intent: email_summarize
     │                        │                      │ + read_aloud
     │                        │                      │
     │                        │              LANGUAGE CENTER
     │                        │                      │──────────────►│
     │                        │                      │  NLU parse    │
     │                        │                      │◄──────────────│
     │                        │                      │
     │                        │              SKILL EXECUTOR
     │                        │                      │──────────────►│
     │                        │                      │  email_fetch  │
     │                        │                      │  + summarize  │
     │                        │  [tool: read email]  │◄──────────────│
     │                        │◄─────────────────────│ ask permission
     │  "Allow email read?"   │                      │
     │◄───────────────────────│                      │
     │  [user approves]       │                      │
     │───────────────────────►│                      │
     │                        │─────────────────────►│
     │                        │                      │ email fetched
     │                        │                      │ summary generated
     │                        │                      │
     │                        │              EMOTION REGULATOR
     │                        │                      │──────────────►│
     │                        │                      │  set: helpful │
     │                        │                      │◄──────────────│
     │                        │                      │
     │                        │              VOICE SYNTHESIZER
     │                        │                      │──────────────►│
     │                        │                      │  TTS + prosody│
     │                        │                      │◄──────────────│
     │  audio stream          │                      │
     │◄─────────────────────────────────────────────-│
     │  + lip sync data       │                      │
     │                        │                      │
  🔊 playback             ────┘                      └────
  👄 lip sync
     │
     ▼
  Total time: ~2.5s (fetch 1.5s + TTS 0.8s + overhead 0.2s)
```

### 12.4 Monitoring Dashboard Overview

```
BODHI — GRAFANA DASHBOARD LAYOUT
══════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────┐
  │  BODHI SYSTEM MONITOR                         [Last 1h] [Refresh] │
  ├──────────────┬──────────────┬──────────────┬──────────────────────┤
  │ Active Agents│  RAM Used    │  CPU Usage   │  Uptime              │
  │     7 / 9   │  4.1 / 8 GB  │   38%        │  14d 3h 22m          │
  ├──────────────┴──────────────┴──────────────┴──────────────────────┤
  │  Request Rate (req/min)         Skill Success Rate                 │
  │  ▁▂▃▄▅▆▇█▇▆▅▄▃▄▅▆▇█▇▆▅       ████████████████████ 97.3%         │
  ├─────────────────────────────────────────────────────────────────── │
  │  Memory Tier Activity                         Emotion State        │
  │  Redis:   ▇▇▇▇▇▇▇▇▇▇ 800 ops/s              Valence:   +0.6 😊   │
  │  Qdrant:  ▃▃▃▃▃▃▃▃▃▃  50 ops/s              Arousal:   +0.4 🙂   │
  │  Postgres:▂▂▂▂▂▂▂▂▂▂  10 ops/s                                    │
  ├─────────────────────────────────────────────────────────────────── │
  │  Top Skills (1h)             Module Load/Unload Events             │
  │  1. conversation   42%       11:20 loaded visual-agent             │
  │  2. web_search     18%       11:45 unloaded visual-agent           │
  │  3. code_help      14%       12:00 loaded voice-synth              │
  │  4. calendar        9%       ...                                    │
  │  5. email           7%                                              │
  └─────────────────────────────────────────────────────────────────── ┘
```

---

**End of Architecture Diagrams**  
**Systems Visualized:** 12/12 Complete ✅

| # | System | Diagrams |
|---|--------|----------|
| 1 | System Overview | Data flow, brain regions |
| 2 | Skill Tree System | Execution graph, leveling, versioning |
| 3 | Memory Consolidation | Pipeline, tiers, importance |
| 4 | Central Agent | Decision loop, attention, cascading |
| 5 | Module Activation | 5-state FSM, eviction, triggers |
| 6 | Data Flow Integration | End-to-end latency breakdown |
| 7 | Tool Plugin System | Risk flow, sandboxes, AI synthesis |
| 8 | Screen Awareness | Pipeline, privacy layers, smart capture |
| 9 | Character Animation | State machine, positioning, multi-style |
| 10 | Voice Pipeline | Full STT/TTS flow, emotion modulation |
| 11 | Sub-Agent Communication | Event bus, memory budget, lifecycle |
| 12 | System Integration | Full architecture, dependencies, monitoring |

**Total Document Size:** ~163 KB  
**Last Updated:** 2026-02-21
