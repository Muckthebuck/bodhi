# Bodhi

> *Sanskrit: "awakening" or "enlightenment"*

A brain-inspired, privacy-first AI companion designed to run locally on edge devices (Raspberry Pi 5 and beyond). Bodhi learns, remembers, and grows with you — entirely on your hardware, entirely under your control.

---

## ✨ What is Bodhi?

Bodhi is a modular AI companion system inspired by the architecture of the human brain. It runs locally on low-power hardware, learns from your interactions, expresses personality, and can see your screen, hear your voice, and take actions on your behalf — all without sending your data to the cloud.

### Key Principles

- 🔒 **Privacy-first** — All processing happens locally by default. No data leaves your device without explicit consent.
- 🧠 **Brain-inspired** — Each system maps to a brain region (memory = hippocampus, skills = basal ganglia, reasoning = prefrontal cortex).
- 📦 **Modular** — Systems load and unload dynamically based on what's needed, fitting within an 8 GB RAM budget.
- 🌱 **Learns & grows** — Bodhi improves over time through a skill tree, memory consolidation, and experience.
- 🎭 **Has personality** — Big Five personality model drives how Bodhi speaks, animates, and responds.
- 🌐 **Offline-capable** — Works without internet. Cloud integrations are optional and use your own API keys.

---

## 🏗️ Architecture

Bodhi is composed of 11 major systems:

| System | Brain Analogy | Description |
|--------|--------------|-------------|
| Central Agent | Prefrontal Cortex | Executive control, decision-making, attention |
| Skill Tree | Basal Ganglia | Procedural memory, skill execution & learning |
| Memory Consolidation | Hippocampus | Three-tier memory (Redis → Qdrant → PostgreSQL) |
| Module Activation | Thalamus | Dynamic loading/unloading of agents |
| Tool Plugin System | Motor Cortex | Safe execution of external tools |
| Screen Awareness | Visual Cortex | On-demand screen understanding with privacy |
| Character Animation | Cerebellum | On-screen character, expressions, lip-sync |
| Voice Pipeline | Auditory/Broca | Local STT/TTS with emotional modulation |
| Sub-Agents | Cortical Columns | 9 specialized cognitive agents |
| System Integration | Brainstem | Docker, gRPC, monitoring, deployment |

---

## 🖥️ Hardware Targets

| Device | Status | RAM | Storage |
|--------|--------|-----|---------|
| Raspberry Pi 5 (8 GB) | Primary target | 8 GB | 32 GB+ SD |
| Any Linux x86_64 | Supported | 8 GB+ | 20 GB+ |
| macOS (Apple Silicon) | Planned | 8 GB+ | 20 GB+ |
| Windows (WSL2) | Planned | 8 GB+ | 20 GB+ |

---

## 🧱 Technology Stack

| Layer | Technology |
|-------|-----------|
| Containerization | Docker + Docker Compose |
| Skill Graph | Neo4j |
| Long-term Memory | PostgreSQL + Qdrant (vectors) |
| Working Memory | Redis |
| STT | Whisper (local, tiny/base/small) |
| TTS | Piper (local, 10+ voices) |
| NLU | DistilBERT-tiny (quantized INT8) |
| Object Detection | YOLO-Nano |
| Communication | gRPC + mTLS |
| Monitoring | Prometheus + Grafana + Loki |

---

## 📁 Repository Structure

```
bodhi/
├── docs/                    # Architecture design documents
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── ARCHITECTURE_DIAGRAMS.md
│   ├── SKILL_TREE_DESIGN.md
│   ├── MEMORY_CONSOLIDATION_DESIGN.md
│   ├── CENTRAL_AGENT_DESIGN.md
│   ├── MODULE_ACTIVATION_STRATEGY.md
│   ├── TOOL_PLUGIN_SYSTEM.md
│   ├── SCREEN_AWARENESS_PIPELINE.md
│   ├── CHARACTER_ANIMATION_SYSTEM.md
│   ├── VOICE_PIPELINE.md
│   ├── SUB_AGENT_DESIGNS.md
│   └── SYSTEM_INTEGRATION.md
├── services/                # Individual service implementations (coming soon)
├── protos/                  # gRPC protobuf definitions (coming soon)
├── config/                  # Configuration files (coming soon)
├── monitoring/              # Prometheus/Grafana configs (coming soon)
├── scripts/                 # Setup, update, backup scripts (coming soon)
└── README.md
```

---

## 🚀 Current Status

**Phase:** Architecture Design ✅ Complete  
**Next:** Phase 1 — Infrastructure Implementation

### Implementation Roadmap

- [ ] **Phase 1** — Infrastructure (Docker, databases, monitoring)
- [ ] **Phase 2** — Core agents (Central Agent, Memory, Language, Emotion)
- [ ] **Phase 3** — Sensory & Motor (Visual, Auditory, Voice, Motor)
- [ ] **Phase 4** — Advanced features (Skills, Tools, Character, Screen)
- [ ] **Phase 5** — Integration, testing & hardening

---

## 📖 Documentation

All architecture design documents are in the [`docs/`](./docs/) folder. Start with:

1. [`ARCHITECTURE_DECISIONS.md`](./docs/ARCHITECTURE_DECISIONS.md) — foundational decisions
2. [`ARCHITECTURE_DIAGRAMS.md`](./docs/ARCHITECTURE_DIAGRAMS.md) — visual system diagrams
3. [`SYSTEM_INTEGRATION.md`](./docs/SYSTEM_INTEGRATION.md) — how it all fits together

---

## 🤝 Contributing

Bodhi is in early architecture/design phase. Contributions, feedback, and ideas are welcome!

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

*"Just as a lamp dispels darkness, Bodhi dispels ignorance."*
