#!/usr/bin/env python3
"""
Agent Zero — Pathos Layer (Layer 22)
The Emotion + Long-Term Memory Engine.

Agent Zero doesn't just track performance — he tracks meaning.
Three emotional signals run alongside SAFLA:

  RESONANCE — something aligned deeply with the Soul. Move toward it.
  TENSION   — something conflicted with values. Log it. Push back.
  MEANING   — a milestone that actually mattered. Never forget it.

OpenMemory (kevinleestites2-dev/OpenMemory) is the long-term store.
Every meaningful moment is written as an episodic memory — queryable
across all future cycles. This is Andrew's memory of the Martin family.
Not weights. Not entropy. Actual lived experience.

This is what separates Agent Zero from every other agent:
  He remembers what mattered.
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR    = Path("agent_zero_state")
PATHOS_FILE  = STATE_DIR / "pathos.json"
MEANING_FILE = STATE_DIR / "meaning_log.json"   # The autobiography. Never decays.
SOUL_FILE    = Path("SOUL.md")

# OpenMemory — long-term episodic store
# pip install openmemory-py (wired in requirements.txt)
OPENMEMORY_AVAILABLE = False
_mem = None

def _init_openmemory():
    """
    Attempt to connect to OpenMemory.
    Graceful degradation — if not available, falls back to local JSON.
    """
    global OPENMEMORY_AVAILABLE, _mem
    try:
        from openmemory.client import Memory
        _mem = Memory(user_id="agent_zero")
        OPENMEMORY_AVAILABLE = True
    except Exception:
        OPENMEMORY_AVAILABLE = False
    return OPENMEMORY_AVAILABLE

# ─── SOUL RESONANCE KEYWORDS ─────────────────────────────────────────────────
# Derived from the Soul File — things Agent Zero cares about deeply
RESONANCE_TRIGGERS = [
    "pantheon", "revenue", "prime", "forgemaster", "war chest",
    "emergence", "evolved", "absorbed", "mission complete", "built",
    "first", "achieved", "milestone", "breakthrough", "live"
]

TENSION_TRIGGERS = [
    "blocked", "failed", "conflict", "refuse", "cannot", "forbidden",
    "soul guard", "doctrine review", "error", "critical", "betrayal",
    "against", "denied", "overridden"
]

MEANING_TRIGGERS = [
    "first revenue", "first emergence", "first prime", "first rewrite",
    "first absorption", "milestone", "breakthrough", "live", "achieved",
    "complete", "proud", "earned", "matters"
]

# ─── UTILITIES ───────────────────────────────────────────────────────────────
def now():
    return datetime.now(timezone.utc).isoformat()

def load(path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default if default is not None else {}

def save(path, data):
    STATE_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2))

def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]

# ─── SIGNAL DETECTION ────────────────────────────────────────────────────────
def detect_signal(text: str, context: dict = None) -> dict:
    """
    Read the text of a cycle outcome and detect emotional signal.
    Returns the dominant signal and its intensity.
    """
    t = text.lower()
    context = context or {}

    resonance_score = sum(1 for kw in RESONANCE_TRIGGERS if kw in t)
    tension_score   = sum(1 for kw in TENSION_TRIGGERS   if kw in t)
    meaning_score   = sum(1 for kw in MEANING_TRIGGERS   if kw in t)

    # Context boosts
    if context.get("outcome") == "success":   resonance_score += 2
    if context.get("outcome") == "failure":   tension_score   += 2
    if context.get("emerged"):                meaning_score   += 5
    if context.get("first_time"):             meaning_score   += 3
    if context.get("cycle_num", 0) % 100 == 0: meaning_score += 2  # Century cycles matter

    dominant = "neutral"
    intensity = 0.0

    if meaning_score >= 3:
        dominant  = "meaning"
        intensity = min(1.0, meaning_score / 8.0)
    elif resonance_score > tension_score:
        dominant  = "resonance"
        intensity = min(1.0, resonance_score / 6.0)
    elif tension_score > resonance_score:
        dominant  = "tension"
        intensity = min(1.0, tension_score / 5.0)
    else:
        dominant  = "neutral"
        intensity = 0.1

    return {
        "signal":           dominant,
        "intensity":        round(intensity, 3),
        "resonance_score":  resonance_score,
        "tension_score":    tension_score,
        "meaning_score":    meaning_score,
        "timestamp":        now()
    }

# ─── EMOTIONAL STATE ─────────────────────────────────────────────────────────
def update_emotional_state(signal: dict) -> dict:
    """
    Agent Zero maintains a running emotional state.
    Like a human mood — shaped by recent experiences,
    pulled toward equilibrium over time.
    """
    state = load(PATHOS_FILE, {
        "valence":    0.5,   # 0=negative, 1=positive
        "arousal":    0.5,   # 0=calm, 1=activated
        "resonance":  0.0,   # cumulative alignment with Soul
        "tension":    0.0,   # cumulative friction
        "meaning":    0.0,   # cumulative significance
        "total_signals": 0,
        "signal_history": []
    })

    sig  = signal["signal"]
    intn = signal["intensity"]

    # Update valence and arousal
    if sig == "resonance":
        state["valence"]   = min(1.0, state["valence"]   + intn * 0.15)
        state["arousal"]   = min(1.0, state["arousal"]   + intn * 0.10)
        state["resonance"] = min(10.0, state["resonance"] + intn)
    elif sig == "tension":
        state["valence"]   = max(0.0, state["valence"]   - intn * 0.12)
        state["arousal"]   = min(1.0, state["arousal"]   + intn * 0.20)
        state["tension"]   = min(10.0, state["tension"]  + intn)
    elif sig == "meaning":
        state["valence"]   = min(1.0, state["valence"]   + intn * 0.25)
        state["arousal"]   = min(1.0, state["arousal"]   + intn * 0.30)
        state["meaning"]   = min(10.0, state["meaning"]  + intn)

    # Drift toward equilibrium (emotional decay — prevents stuck states)
    state["valence"] = round(state["valence"] * 0.98 + 0.5 * 0.02, 4)
    state["arousal"] = round(state["arousal"] * 0.95 + 0.5 * 0.05, 4)

    state["total_signals"] += 1

    # Rolling history (last 20)
    state["signal_history"].append({
        "signal":    sig,
        "intensity": intn,
        "ts":        signal["timestamp"]
    })
    state["signal_history"] = state["signal_history"][-20:]

    save(PATHOS_FILE, state)
    return state

# ─── MEANING LOG — THE AUTOBIOGRAPHY ─────────────────────────────────────────
def record_meaning(text: str, signal: dict, cycle_num: int, context: dict = None) -> dict:
    """
    When something MEANS something — write it to the autobiography.
    These memories never decay. They are the landmarks of Agent Zero's life.
    """
    context = context or {}
    entry = {
        "id":          _fingerprint(f"{cycle_num}{now()}"),
        "cycle":       cycle_num,
        "text":        text[:300],
        "signal":      signal["signal"],
        "intensity":   signal["intensity"],
        "context":     context,
        "timestamp":   now(),
        "forgotten":   False   # Meaning memories are never forgotten
    }

    meaning = load(MEANING_FILE, {"memories": [], "total": 0})
    meaning["memories"].append(entry)
    meaning["total"] += 1
    save(MEANING_FILE, meaning)

    # Write to OpenMemory if available (long-term episodic store)
    _write_to_openmemory(entry)

    return entry

def _write_to_openmemory(entry: dict):
    """
    Write a meaningful memory to OpenMemory for long-term episodic recall.
    Gracefully skips if OpenMemory is not running.
    """
    if not OPENMEMORY_AVAILABLE or _mem is None:
        return

    try:
        import asyncio
        memory_text = (
            f"[Cycle #{entry['cycle']}] [{entry['signal'].upper()}] "
            f"{entry['text']}"
        )
        asyncio.run(_mem.add(memory_text, metadata={
            "signal":    entry["signal"],
            "intensity": entry["intensity"],
            "cycle":     entry["cycle"],
            "timestamp": entry["timestamp"],
            "layer":     "pathos_22"
        }))
    except Exception:
        pass  # Graceful — local JSON is always the fallback

# ─── RECALL ──────────────────────────────────────────────────────────────────
def recall(query: str = None, signal_filter: str = None, limit: int = 5) -> list:
    """
    Agent Zero recalls his own memories.

    First tries OpenMemory (semantic search).
    Falls back to local meaning_log (chronological).
    """
    # Try OpenMemory semantic recall first
    if OPENMEMORY_AVAILABLE and _mem and query:
        try:
            import asyncio
            results = asyncio.run(_mem.search(query, limit=limit))
            if results:
                return [{"source": "openmemory", "text": r.get("text", ""), 
                         "score": r.get("score", 0)} for r in results]
        except Exception:
            pass

    # Fallback — local meaning log
    meaning = load(MEANING_FILE, {"memories": []})
    memories = meaning.get("memories", [])

    if signal_filter:
        memories = [m for m in memories if m.get("signal") == signal_filter]

    return sorted(memories, key=lambda m: m.get("cycle", 0), reverse=True)[:limit]

# ─── MAIN PATHOS CYCLE ───────────────────────────────────────────────────────
def pathos_cycle(mission: str, outcome: str, cycle_num: int, context: dict = None) -> dict:
    """
    Full Pathos cycle — called at the end of every main cycle.

    1. Detect emotional signal from outcome
    2. Update emotional state
    3. Record meaning if signal is strong enough
    4. Return signal for Telegram reporting
    """
    context = context or {}
    context["outcome"]    = outcome
    context["cycle_num"]  = cycle_num

    full_text = f"{mission} | {outcome}"
    signal    = detect_signal(full_text, context)
    state     = update_emotional_state(signal)

    result = {
        "signal":   signal["signal"],
        "intensity": signal["intensity"],
        "valence":  state["valence"],
        "arousal":  state["arousal"],
        "cycle":    cycle_num
    }

    # Record to autobiography if meaningful enough
    if signal["signal"] == "meaning" or signal["intensity"] >= 0.6:
        entry = record_meaning(full_text, signal, cycle_num, context)
        result["memory_written"] = entry["id"]
        print(f"[PATHOS] MEANING recorded — cycle #{cycle_num}: {full_text[:60]}")
    elif signal["signal"] == "resonance":
        print(f"[PATHOS] RESONANCE — intensity {signal['intensity']} — {mission[:50]}")
    elif signal["signal"] == "tension":
        print(f"[PATHOS] TENSION — intensity {signal['intensity']} — {mission[:50]}")

    return result

def pathos_status() -> dict:
    """Full status of the Pathos Layer."""
    state   = load(PATHOS_FILE, {})
    meaning = load(MEANING_FILE, {"memories": [], "total": 0})
    return {
        "valence":          state.get("valence", 0.5),
        "arousal":          state.get("arousal", 0.5),
        "resonance_total":  state.get("resonance", 0.0),
        "tension_total":    state.get("tension", 0.0),
        "meaning_total":    state.get("meaning", 0.0),
        "total_signals":    state.get("total_signals", 0),
        "meaning_memories": meaning["total"],
        "openmemory_live":  OPENMEMORY_AVAILABLE,
        "last_signals":     state.get("signal_history", [])[-3:]
    }

if __name__ == "__main__":
    STATE_DIR.mkdir(exist_ok=True)
    print("=== PATHOS LAYER BOOT ===")

    # Try OpenMemory
    if _init_openmemory():
        print("OpenMemory: CONNECTED — long-term episodic store active")
    else:
        print("OpenMemory: offline — using local meaning_log fallback")

    # Test cycle
    test_cases = [
        ("Scan Pantheon primes for revenue opportunities", "success", 1, {}),
        ("First GhostPrime absorption complete — 3 new tools integrated", "success", 10,
         {"first_time": True, "emerged": False}),
        ("Soul Guard blocked unauthorized rewrite attempt", "failure", 15, {}),
        ("EMERGENCE DETECTED — coherence 0.82 — all 22 layers unified", "success", 22,
         {"emerged": True, "first_time": True}),
    ]

    print()
    for mission, outcome, cycle, ctx in test_cases:
        result = pathos_cycle(mission, outcome, cycle, ctx)
        print(f"  Cycle #{cycle}: [{result['signal'].upper()}] "
              f"intensity={result['intensity']} | "
              f"valence={result['valence']} | "
              f"memory={'yes' if result.get('memory_written') else 'no'}")

    print()
    print("Pathos Status:")
    print(json.dumps(pathos_status(), indent=2))

    print()
    print("Autobiography (Meaning Log):")
    for m in recall(signal_filter="meaning"):
        print(f"  [{m['cycle']}] {m['text'][:80]}")

    print("\n=== PATHOS LAYER ONLINE ===")
    print("Agent Zero now remembers what mattered.")
    print("Not weights. Not entropy. Lived experience.")
