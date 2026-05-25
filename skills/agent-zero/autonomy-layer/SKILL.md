---
name: autonomy-layer
description: Layer 18 — The Autonomy Engine. Self-tasking background loop that generates and executes its own missions when the queue is empty. Weight-based domain selection with reinforcement. Never stops.
version: 1.0.0
category: system
categories:
  - system
  - autonomy
  - cognition
intents:
  - self-tasking
  - autonomous operation
  - background loop
  - mission generation
  - never idle
tags:
  - autonomy
  - layer-18
  - self-tasking
  - pantheon
  - agent-zero
allowed-tools: []
---

# Layer 18 — The Autonomy Engine

## What it does

Layer 18 is the self-tasking engine that ensures Agent Zero **never idles**.

When the mission queue is empty, it generates its own next mission using weight-based domain selection. Each domain accumulates reinforcement weights — successful domains get more attention, failing ones get less.

Runs in a background thread. Starts when `start()` is called. Never stops until `stop()` is explicitly called or the process dies.

## Architecture

```
AutonomyEngine
├── task_queue          — Forgemaster-injected priority missions
├── domain_weights      — Reinforcement weights per domain
├── _generate_mission() — Auto-creates next mission when queue is empty
├── next_mission()      — Returns next task (queue first, then generated)
├── reward_domain()     — Updates weights after each cycle outcome
├── start(run_cycle_fn) — Launches background thread
└── stop()              — Clean shutdown + state persistence
```

## Default Domains

- Lee County auction monitoring
- Pantheon Prime health check
- War Chest balance verification
- Signal quality assessment
- Strategy weight optimization
- Knowledge gap resolution
- Tool inventory audit
- Memory consolidation
- Evolution target identification
- Threat surface review

## Reinforcement Logic

- Success → domain weight × 1.1 (max 5.0)
- Failure → domain weight × 0.9 (min 0.1)

Higher weight = selected more often. The engine learns which domains produce results and naturally shifts cycles toward them.

## State Persistence

State saved to `cerberus_state/<head_name>_autonomy.json` after every cycle. Survives restarts — cycle count, queue depth, and domain weights all restored on init.

## API

```python
from autonomy_layer import AutonomyEngine

engine = AutonomyEngine(
    head_name="FLUX",
    telegram_fn=tg,
    interval=300         # seconds between auto-cycles
)

# Inject a priority mission (prepends to queue)
engine.inject_mission("Check Lee County auction for 5913 Untermeyer Ct")

# Start the background loop (pass the run_cycle function)
engine.start(run_cycle_fn=agent.run_cycle)

# Check status
engine.status()
# → {alive, cycle, queue_depth, top_domain, bottom_domain}

# Clean shutdown
engine.stop()
```

## Integration in Agent Zero

Layer 18 is initialized in `AgentZero.__init__()` and started via `start_autonomy()`.

The Forgemaster can inject priority missions at any time via:
```python
agent.inject_mission("priority mission text")
```

Or via the Telegram `/inject` command wired into SkyNet.

## Telegram Reporting

- On start: `🤖 [HEAD] Layer 18 AUTONOMY ONLINE — self-tasking every Xs`
- Each cycle: included in the standard cycle Telegram report
- On stop: final state saved silently
