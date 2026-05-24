---
name: curiosity-layer
description: Autonomous knowledge-gap interrogation — Agent Zero self-interrogates after every reflection cycle, generates targeted questions, investigates via LLM, and feeds answers back into planning. Three modes: INTROSPECTIVE, ENVIRONMENTAL, SOCIAL (GitHub issues).
version: 1.0.0
category: intelligence
categories:
  - intelligence
  - cognition
  - self-improvement
intents:
  - curiosity
  - knowledge gap
  - self interrogation
  - unknown unknowns
  - research directive
tags:
  - curiosity
  - intelligence
  - self-evolving
  - agent-zero
allowed-tools: []
---

# Curiosity Layer

Plugs into Agent Zero's `reflect() → plan()` gap.

## What It Does

After every cycle, analyzes outcomes and identifies **knowledge gaps** — questions the agent doesn't know it needs to ask.

```
reflect() ──► curiosity.interrogate(result) ──► gaps[]
plan()    ◄── curiosity.enrich(plan, gaps)  ◄── gaps[]
```

## Three Curiosity Modes

| Mode | Description |
|------|-------------|
| `INTROSPECTIVE` | Questions about own performance ("why did this fail?") |
| `ENVIRONMENTAL` | Questions about the world ("what changed in the market?") |
| `SOCIAL` | Questions posted to GitHub issues as a curious participant |

## Integration

```python
from skills.agent_zero.curiosity_layer import CuriosityLayer

agent.attach_curiosity(
    llm_fn=my_llm,
    github_token=os.getenv("GITHUB_TOKEN"),
    github_repo="kevinleestites2-dev/CerberusPrime",
)
```

## Layer Position

Sits between Layer 7 (SAFLA Feedback) and Layer 8 (Evolution Engine).
Feeds enriched context into planning — closes the loop between execution and learning.
