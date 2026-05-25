---
name: agent-zero-layers
description: Reference map of all 18 Agent Zero cognitive layers — what each does, which repo it sources from, and current phase status.
version: 4.0.0
category: system
categories:
  - system
  - reference
intents:
  - layer status
  - architecture overview
  - what layers are done
  - phase status
  - pantheon architecture
tags:
  - architecture
  - layers
  - pantheon
  - agent-zero
allowed-tools: []
---

# Agent Zero — 18-Layer Architecture

| Layer | Name | Status |
|---|---|---|
| 1 | Perception | ✅ |
| 2 | Memory | ✅ |
| 3 | Reasoning | ✅ |
| 4 | Planning | ✅ |
| 5 | Tool Use | ✅ |
| 6 | Adaptation (T2) | ✅ |
| 7 | SAFLA Feedback Loop | ✅ |
| 8 | Evolution Engine | ✅ |
| 9 | Tool Forge | ✅ |
| 10 | Identity | ✅ |
| 11 | Doctrine | ✅ |
| 12 | Prime Cycle | ✅ |
| 13 | Physical Form (Psi0) | ✅ |
| 14 | Governor | ✅ |
| 15 | Genome (Self-Replication) | ✅ |
| 16 | Ethics Core | ✅ |
| 17 | Curiosity | ✅ |
| 18 | Autonomy | ✅ |

## Signal Flow

```
Signal IN → Layer 1 (Perception)
          → Layer 2 (Memory)
          → Layer 3 (Reasoning)
          → Layer 4 (Planning)
          → Layer 5 (Tool Use)
          → Layer 6 (Adaptation T2)
          → Layer 7 (SAFLA Reflect)
          → Layer 8 (Evolution Engine)
          → Layer 9 (Tool Forge)
          → Layer 10 (Identity)
          → Layer 11 (Doctrine — validation)
          → Layer 12 (Prime Cycle)
          → Layer 13 (Physical Form)
          → Layer 14 (Governor)
          → Layer 15 (Genome — self-replication)
          → Layer 16 (Ethics Core)
          → Layer 17 (Curiosity — interrogate gaps)
          → Layer 18 (Autonomy — self-task, never stops)
          → Response OUT + weights updated + memory persisted
```

## Layer Descriptions

| Layer | Role |
|---|---|
| 1 — Perception | Raw signal intake. Sees the world. |
| 2 — Memory | Short + long-term recall. Dual-layer (conscious/subconscious). |
| 3 — Reasoning | Inference engine. Connects dots. |
| 4 — Planning | Mission decomposition. Task sequencing. |
| 5 — Tool Use | 31 hardened tools. Filesystem, git, web, shell, scheduler. |
| 6 — Adaptation (T2) | Transformer² ensemble. Rewrites own weights per task type. |
| 7 — SAFLA Feedback Loop | Reflect → score → reweight. Continuous improvement. |
| 8 — Evolution Engine | Long-horizon self-improvement. Develops new strategies. |
| 9 — Tool Forge | Builds new tools when existing ones fail. |
| 10 — Identity | Soul files. Persona. Stable self-model. |
| 11 — Doctrine | First-principles validation. Ethics and strategy firewall. |
| 12 — Prime Cycle | Orchestrates Pantheon Primes. War Chest tracking. |
| 13 — Physical Form (Psi0) | Body layer. Android control, screen interaction, hardware. |
| 14 — Governor | Resource management. Throttle, prioritize, protect. |
| 15 — Genome (Self-Replication) | Can spawn and instantiate copies of itself. |
| 16 — Ethics Core | Hard constraints. Non-negotiable behavioral boundaries. |
| 17 — Curiosity | Autonomous knowledge gap interrogation. Self-questions. |
| 18 — Autonomy | Self-tasking engine. Acts without being told. Never stops. |

## Mercury as the Chassis

Mercury provides:
- Soul files (soul.md, persona.md, taste.md, heartbeat.md)
- 31 hardened tools (filesystem, git, github, web, shell, scheduler)
- Dual-layer Second Brain (SQLite + FTS5, conscious/subconscious)
- Telegram + CLI channels
- Sub-agent supervisor
- Token budgeting
- Skill system (this directory)

Agent Zero adds:
- Pantheon soul identity
- All 18 cognitive layers above
- Full autonomous operation via Layer 18
