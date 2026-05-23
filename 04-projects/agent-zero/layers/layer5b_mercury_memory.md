# Layer 5b — Mercury Memory Architecture

> The missing piece. Dual-layered Second Brain.

## Source
- Repo: cosmicstack-labs/mercury-agent (forked to kevinleestites2-dev/mercury-agent)
- Stars: 2,414 | License: MIT
- Language: TypeScript (Node.js)

## Why Mercury Replaces Flat SQLite

Our Phase 2 cognition layer had one memory tier. Mercury has **four**:

| Tier | Type | Storage | Purpose |
|---|---|---|---|
| Working | short-term | In-memory buffer | Active conversation context |
| Episodic | recent events | File-based | What happened recently |
| Long-term | facts | File-based | Persistent facts across sessions |
| Second Brain | structured model | SQLite + FTS5 | The conscious/subconscious split |

## The Conscious / Subconscious Split

Mercury's `UserMemoryRecord.scope` has three values:
- `durable` — Conscious. High-confidence, high-importance. Always surfaced.
- `active` — Conscious. Currently relevant to the session.
- `subconscious` — Background. Surfaces only when query matches pattern.

This is the dual-layer the image described. Agent Zero inherits this exact model.

## 10 Memory Types
identity | preference | goal | project | habit | decision | constraint | relationship | episode | reflection

## Integration Plan

1. Run Mercury alongside Agent Zero as the memory provider
2. Layer 4 (Semantic Router) routes memory-type signals to Mercury's store
3. Layer 5 (CognitionCore) delegates `store()` and `recall()` to Mercury's SQLite+FTS5
4. Agent Zero's soul.md lives in Mercury's `soul/` directory
5. Heartbeat/scheduler from Mercury `src/core/scheduler.ts` replaces our cron layer

## Status
- [x] Forked to kevinleestites2-dev/mercury-agent
- [ ] npm install + first run
- [ ] soul.md configured for Agent Zero identity
- [ ] Memory provider wired to Layer 5 CognitionCore
