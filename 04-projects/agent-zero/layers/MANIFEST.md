# Agent Zero — Layer Integration Manifest

| Layer | Status | File | Source |
|---|---|---|---|
| 1 — The Vault | Phase 1 DONE | COG folder structure | agent-zero (COG) |
| 2 — Perception | Phase 3 | layer2_perception.py | gpt-researcher |
| 3 — Runtime Body | Phase 1 DONE | config/agent_zero_config.toml | opencrabs |
| 4 — Semantic Router | Phase 2 DONE | layer4_semantic_router.py | Brain.ai |
| 5 — Cognition | Phase 2 DONE | layer5_cognition.py | Base-of-Self-Aware-AI |
| 5b — Mercury Memory | Phase 2 DONE | layer5b_mercury_memory.md | mercury-agent (2414 stars) |
| 6 — Adaptation | Phase 3 | layer6_adaptation.py | Transformer-Squared |
| 7 — Feedback Loop | Phase 3 | layer7_safla.py | SAFLA |
| 8 — Evolution Engine | Phase 4 | layer8_evolution.py | Entwickler |
| 9 — Tool Forge | Phase 4 | layer9_tool_forge.py | tiny-self-improve-ai |
| 10 — Identity Layer | Phase 5 | layer10_identity.py | self-recognition |
| 11 — The Doctrine | LOCKED | reference only | Self-Evolving-Agents |
| 12 — Super Intelligence | EMERGENT | N/A | convergence of 1-11 |
| 13 — Physical Form | Phase 8 | layer13_psi0.py | Psi0 |

## Memory Architecture (Layer 5 + 5b)

```
Signal IN
    |
Layer 4 — Semantic Router (Brain.ai)
    |
    +---> intent: memory/identity/preference/goal/project/habit
    |         |
    |     Layer 5b — Mercury Memory Engine
    |         |
    |         +---> scope: durable (CONSCIOUS)
    |         +---> scope: active  (CONSCIOUS)
    |         +---> scope: subconscious (SUBCONSCIOUS)
    |         |
    |         SQLite + FTS5 full-text search
    |
    +---> intent: everything else
              |
          Layer 5 — CognitionCore (Base-of-Self-Aware-AI)
              working memory + long-term SQLite
```

## Phase Progress

- Phase 1 DONE — COG vault + OpenCrabs runtime
- Phase 2 DONE — Semantic router + Cognition + Mercury dual-memory
- Phase 3 NEXT — Perception + Adaptation + Feedback Loop
