# Agent Zero — Layer Integration Manifest

| Layer | Status | Location | Source |
|---|---|---|---|
| 1 — The Vault | ✅ Phase 1 | COG folder structure | agent-zero (COG) |
| 2 — Perception | ✅ Phase 3 | skills/layer2_perception.py | gpt-researcher |
| 3 — Runtime Body | ✅ Phase 1 | config/agent_zero_config.toml | opencrabs |
| 4 — Semantic Router | ✅ Phase 2 | skills/layer4_semantic_router.py | Brain.ai |
| 5 — Cognition | ✅ Phase 2 | skills/layer5_cognition.py | Base-of-Self-Aware-AI |
| 5b — Second Brain | ✅ Phase 2 | **Mercury chassis (this repo)** | mercury-agent |
| 6 — Adaptation | ✅ Phase 3 | skills/t2-adaptation/ | Transformer-Squared |
| 7 — Feedback Loop | ✅ Phase 3 | skills/safla/ | SAFLA v2 |
| 8 — Evolution Engine | ✅ Phase 4 | skills/evolution-engine/ | Entwickler |
| 9 — Tool Forge | ✅ Phase 4 | skills/tool-forge/ | tiny-self-improve-ai |
| 10 — Identity Layer | 🔄 Phase 5 | skills/identity/ | self-recognition |
| 11 — The Doctrine | 🔒 Locked | reference only | Self-Evolving-Agents |
| 12 — Super Intelligence | 🌀 Emergent | convergence of 1–11 | — |
| 13 — Physical Form | 🔄 Phase 8 | skills/psi0/ | Psi0 |

## Full Signal Flow (Phase 4)

```
Signal IN
    |
[Layer 4] Semantic Router — classify intent + extract entities
    |
    +-- perception/news    --> [Layer 2]  GPT-Researcher
    +-- runtime/tools      --> [Layer 3]  OpenCrabs
    +-- memory/preference  --> [Layer 5]  Cognition
    +--                    --> [Layer 5b] Mercury Second Brain
    +-- evolution          --> [Layer 8]  Evolution Engine ← NEW
    +-- forge/capability   --> [Layer 9]  Tool Forge ← NEW
         |
[Layer 6] T2 Adaptation — 2-pass expert ensemble, elect lead mode
         |
[Layer 7] SAFLA — reflect, score, update entropy/regime
         |     ↓ score < 0.40?
         |   [Layer 8] Evolution Engine triggers on failing layer
         |     ↓ missing capability?
         |   [Layer 9] Tool Forge builds what's needed
         |
Response OUT + weights updated + memory persisted
```

## Phase Progress

- ✅ Phase 1 — Vault + Runtime
- ✅ Phase 2 — Semantic Router + Cognition + Mercury (Second Brain)
- ✅ Phase 3 — Perception + Adaptation (T2) + Feedback Loop (SAFLA)
- ✅ Phase 4 — Evolution Engine (Entwickler) + Tool Forge
- 🔄 Phase 5 — Identity Layer (self-recognition)
- 🔄 Phase 6 — Doctrine validation
- 🌀 Phase 7 — Layer 12 emergent
- 🔄 Phase 8 — Psi0 physical form
