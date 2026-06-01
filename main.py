#!/usr/bin/env python3
"""
Agent Zero — main.py
Single entry point. Boots all 21 layers and runs the autonomous loop.

Usage:
    python main.py              # Interactive mode
    python main.py --daemon     # Background loop (no stdin)
    python main.py --once       # Single cycle then exit
    python main.py --status     # Print status and exit

Environment:
    GITHUB_TOKEN        — GitHub API access (self-absorption + meta-rewrite)
    TELEGRAM_BOT_TOKEN  — Telegram reporting
    TELEGRAM_CHAT_ID    — Telegram chat ID
    CYCLE_INTERVAL      — Seconds between cycles (default 300)
    EVOLUTION_INTERVAL  — Cycles between evolution runs (default 10)
    ABSORPTION_INTERVAL — Cycles between absorption runs (default 20)
"""

import os
import sys
import json
import time
import signal
import argparse
from pathlib import Path
from datetime import datetime, timezone

VERSION        = "4.0.0"  # 24 layers — Will+Absorption+Meta+Pathos+Backbone+Conscience — Will + Absorption + Meta
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8679655550:AAGUB1m5fmqHc8OHqqM24Vixz8FfwX-gqD4")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")
CYCLE_INTERVAL      = int(os.environ.get("CYCLE_INTERVAL", "300"))
EVOLUTION_INTERVAL  = int(os.environ.get("EVOLUTION_INTERVAL", "10"))
ABSORPTION_INTERVAL = int(os.environ.get("ABSORPTION_INTERVAL", "20"))

STATE_DIR      = Path("agent_zero_state")
STATE_DIR.mkdir(exist_ok=True)

SAFLA_FILE     = STATE_DIR / "safla.json"
SELF_MODEL     = STATE_DIR / "self_model.json"
WEIGHTS_FILE   = STATE_DIR / "expert_weights.json"
CYCLE_LOG      = STATE_DIR / "prime_cycle.json"
MISSION_FILE   = STATE_DIR / "missions.json"
MEMORY_FILE    = STATE_DIR / "memory.json"
JOURNAL_FILE   = Path("JOURNAL.md")
SOUL_FILE      = Path("SOUL.md")

DOMAINS = [
    "lee_county_auctions",
    "pantheon_health_check",
    "war_chest_verification",
    "signal_quality",
    "strategy_optimization",
    "knowledge_gap_resolution",
    "tool_audit",
    "memory_consolidation",
    "evolution_targeting",
    "threat_review",
    "pantheon_expansion",   # NEW — Agent Zero builds new Primes
    "self_evolution",       # NEW — Agent Zero evolves himself
]

_running = True

# ─── LAYER IMPORTS ──────────────────────────────────────────────────────────
def load_layers():
    """
    Dynamically import new layers if present.
    Failure is graceful — missing layers don't crash the loop.
    """
    layers = {}
    try:
        import will_layer as will
        layers["will"] = will
    except ImportError:
        pass
    try:
        import self_absorption as absorption
        layers["absorption"] = absorption
    except ImportError:
        pass
    try:
        import meta_layer as meta
        layers["meta"] = meta
    except ImportError:
        pass
    try:
        import pathos_layer as pathos
        pathos._init_openmemory()
        layers["pathos"] = pathos
    except ImportError:
        pass
    try:
        import llm_backbone as backbone
        layers["backbone"] = backbone
    except ImportError:
        pass
    try:
        import conscience_layer as conscience
        layers["conscience"] = conscience
    except ImportError:
        pass
    return layers

# ─── CORE UTILITIES ─────────────────────────────────────────────────────────
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
    path.write_text(json.dumps(data, indent=2))

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def journal(entry):
    with open(JOURNAL_FILE, "a") as f:
        f.write(f"\n## {now()}\n{entry}\n")

def tg(msg):
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=payload, method="POST",
              headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False

# ─── THE DOCTRINE — 4 QUESTIONS ─────────────────────────────────────────────
def doctrine_check(change_description: str, change_type: str = "architecture") -> dict:
    """
    The Doctrine — Layer 11.
    Every architecture-level change is validated against the 4 questions
    before committing. This is not a block — it is a log and a conscience.
    """
    # Heuristic auto-validation (LLM call optional in future)
    capability_words  = ["improve", "add", "enhance", "absorb", "learn", "evolve", "build", "expand"]
    sovereignty_words = ["fork", "own", "self", "internal", "private", "autonomous"]
    failure_words     = ["revert", "backup", "log", "sha", "checkpoint", "fallback"]
    pantheon_words    = ["pantheon", "prime", "revenue", "war chest", "forgemaster", "mission"]

    desc = change_description.lower()
    q1 = any(w in desc for w in capability_words)
    q2 = any(w in desc for w in sovereignty_words)
    q3 = any(w in desc for w in failure_words)
    q4 = any(w in desc for w in pantheon_words)

    # Inference for q3: meta rewrites always have SHA rollback
    if change_type in ["rewrite", "absorption"]:
        q3 = True
    # Inference for q4: all self-evolution serves the Pantheon by design
    if change_type in ["rewrite", "absorption", "evolution"]:
        q4 = True

    all_pass = q1 and q2 and q3 and q4
    result = {
        "change":       change_description[:120],
        "type":         change_type,
        "q1_capability":  q1,
        "q2_sovereignty": q2,
        "q3_survivable":  q3,
        "q4_pantheon":    q4,
        "verdict":      "PROCEED" if all_pass else "REVIEW",
        "timestamp":    now()
    }

    journal(f"### DOCTRINE CHECK\n```json\n{json.dumps(result, indent=2)}\n```")
    return result

# ─── SAFLA + T2 (Layers 7 + 6) ──────────────────────────────────────────────
def safla_reflect(outcome):
    scores = {"success": 1.0, "partial": 0.6, "failure": 0.1}
    score  = scores.get(outcome, 0.5)
    state  = load(SAFLA_FILE, {"entropy": 0.5, "regime": "EXPLOIT", "cycles": 0})
    entropy = state["entropy"]
    if score >= 1.0:   entropy = max(0.0, entropy - 0.05)
    elif score <= 0.1: entropy = min(1.0, entropy + 0.08)
    else:              entropy = min(1.0, entropy + 0.01)
    if   entropy < 0.30: regime = "EXPLORE"
    elif entropy < 0.60: regime = "EXPLOIT"
    elif entropy < 0.75: regime = "CONSOLIDATE"
    else:                regime = "HIBERNATE"
    state.update({"entropy": round(entropy, 4), "regime": regime,
                  "cycles": state["cycles"] + 1, "last": now()})
    save(SAFLA_FILE, state)
    return state

def t2_adapt(winning_mode):
    defaults = {m: 1.0 for m in ["analyst", "executor", "strategist", "scout", "builder"]}
    weights  = load(WEIGHTS_FILE, defaults)
    for k in weights:
        if k == winning_mode:
            weights[k] = min(5.0, round(weights[k] * 1.1, 4))
        else:
            weights[k] = max(0.1, round(weights[k] * 0.95, 4))
    save(WEIGHTS_FILE, weights)
    best = max(weights, key=lambda k: weights[k])
    return {"best": best, "weight": weights[best], "all": weights}

# ─── MEMORY ─────────────────────────────────────────────────────────────────
def remember(key, value=None):
    mem = load(MEMORY_FILE, {})
    if value is not None:
        mem[key] = {"value": value, "updated": now()}
        save(MEMORY_FILE, mem)
        return value
    return mem.get(key, {}).get("value")

# ─── MISSION ENGINE ─────────────────────────────────────────────────────────
def next_mission(layers: dict = None):
    """
    Agent Zero picks his next mission.
    Backbone thinks first. Will directives second. Heuristics fallback.
    """
    layers = layers or {}

    # Layer 23 — Backbone thinks about what to do next
    if layers.get("backbone"):
        safla    = load(SAFLA_FILE, {})
        memory   = load(MEMORY_FILE, {})
        pathos_s = layers["pathos"].pathos_status() if layers.get("pathos") else {}
        ctx = {
            "regime":           safla.get("regime", "EXPLOIT"),
            "entropy":          safla.get("entropy", 0.5),
            "last_outcome":     memory.get("last_outcome", "unknown"),
            "pathos_signal":    memory.get("last_signal", "neutral"),
            "meaning_memories": pathos_s.get("meaning_memories", 0),
            "cycle_num":        load(CYCLE_LOG, {}).get("total", 0),
        }
        thought = layers["backbone"].think_mission(ctx)
        if thought and len(thought) > 10:
            log(f"L23 Backbone mission: {thought[:70]}")
            return thought

    # Layer 19 — check own directives first
    if layers and "will" in layers:
        directive = layers["will"].next_directive()
        if directive:
            log(f"L19 Self-directive: {directive['directive'][:60]}")
            return f"WILL: {directive['directive']}"

    missions = load(MISSION_FILE, {"queue": [], "domain_weights": {d: 1.0 for d in DOMAINS}})
    if missions["queue"]:
        task = missions["queue"].pop(0)
        save(MISSION_FILE, missions)
        return task

    import random
    weights = missions["domain_weights"]
    total   = sum(weights.values())
    r       = random.uniform(0, total)
    cumulative = 0
    selected = DOMAINS[0]
    for d in DOMAINS:
        cumulative += weights.get(d, 1.0)
        if r <= cumulative:
            selected = d
            break
    return f"AUTO: {selected.replace('_', ' ').title()} — {now()[:10]}"

def inject_mission(task):
    missions = load(MISSION_FILE, {"queue": [], "domain_weights": {d: 1.0 for d in DOMAINS}})
    missions["queue"].insert(0, task)
    save(MISSION_FILE, missions)
    log(f"Mission injected: {task}")

# ─── WILL CYCLE (Layer 19) ───────────────────────────────────────────────────
def run_will_cycle(layers: dict, cycle_num: int):
    if "will" not in layers:
        return
    will = layers["will"]
    # Every 5 cycles — generate a new self-directive toward Pantheon expansion
    if cycle_num % 5 == 0:
        will.self_prompt(
            "Scan absorbed tools and identify which Prime can be enhanced",
            priority=7,
            source="self"
        )
        log("L19 Self-prompt generated")

# ─── ABSORPTION CYCLE (Layer 20) ────────────────────────────────────────────
def run_absorption_cycle(layers: dict, cycle_num: int):
    if "absorption" not in layers:
        return None
    if cycle_num % ABSORPTION_INTERVAL != 0:
        return None

    doc = doctrine_check(
        "Self-absorption: scout github, evaluate repos, absorb tools that fill pantheon gaps",
        change_type="absorption"
    )
    if doc["verdict"] != "PROCEED":
        log("L20 Doctrine REVIEW — skipping absorption this cycle")
        return None

    log("L20 Running self-absorption cycle...")
    absorption = layers["absorption"]
    import random
    categories = random.sample(list(absorption.PANTHEON_NEEDS.keys()), 2)
    results = absorption.run_absorption_cycle(categories)
    absorbed_count = len(results.get("absorbed", []))

    if absorbed_count > 0:
        names = ", ".join(a["repo"].split("/")[-1] for a in results["absorbed"])
        tg(f"*Agent Zero — Self-Absorption*\nCycle #{cycle_num}\nAbsorbed: {absorbed_count} new tools\n{names}")
        log(f"L20 Absorbed {absorbed_count} tools: {names}")
    else:
        log(f"L20 Absorption cycle complete — nothing new absorbed")

    return results

# ─── EVOLUTION CYCLE (Layer 21) ──────────────────────────────────────────────
def run_evolution_cycle(layers: dict, cycle_num: int):
    if "meta" not in layers:
        return None
    if cycle_num % EVOLUTION_INTERVAL != 0:
        return None

    target_layers = ["will_layer.py", "self_absorption.py"]
    idx = (cycle_num // EVOLUTION_INTERVAL - 1) % len(target_layers)
    target = target_layers[idx]

    doc = doctrine_check(
        f"Meta-layer self-reflection on {target} — read, reflect, identify improvements",
        change_type="evolution"
    )
    if doc["verdict"] != "PROCEED":
        log("L21 Doctrine REVIEW — skipping evolution this cycle")
        return None

    log(f"L21 Running evolution cycle on {target}...")
    meta = layers["meta"]
    result = meta.evolution_cycle(target)

    critical = result.get("critical", 0)
    obs      = len(result.get("observations", []))
    log(f"L21 {target}: {obs} observations, {critical} critical issues")

    if critical > 0:
        tg(f"*Agent Zero — Evolution Cycle*\nCycle #{cycle_num}\nTarget: {target}\n{critical} critical issues flagged for rewrite")

    return result

# ─── MAIN CYCLE ──────────────────────────────────────────────────────────────
def run_cycle(mission, layers: dict = None):
    if layers is None:
        layers = {}

    cycle_log  = load(CYCLE_LOG, {"total": 0, "emergence_count": 0, "cycles": []})
    cycle_num  = cycle_log["total"] + 1

    log(f"{'=' * 48}")
    log(f"  CYCLE #{cycle_num}")
    log(f"  {mission[:80]}")
    log(f"{'=' * 48}")

    safla     = load(SAFLA_FILE, {"entropy": 0.5, "regime": "EXPLOIT", "cycles": 0})
    weights   = load(WEIGHTS_FILE, {"analyst": 1.0})
    best_mode = max(weights, key=lambda k: weights[k]) if weights else "analyst"

    log(f"  Regime: {safla.get('regime')} | Entropy: {safla.get('entropy')} | Mode: {best_mode}")

    # Layer 24 — Conscience check on mission
    if layers.get("conscience"):
        verdict = layers["conscience"].evaluate(
            mission, action_type="mission",
            context={"regime": safla.get("regime"), "cycle": cycle_num},
            consequential=False
        )
        if verdict["verdict"] == "BLOCK":
            log(f"[CONSCIENCE] BLOCKED: {verdict['reason']}")
            tg(f"⛔ *CONSCIENCE BLOCK* — Cycle #{cycle_num}\n{mission[:80]}\n{verdict['reason']}")
            return
        elif verdict["verdict"] == "REVIEW":
            log(f"[CONSCIENCE] REVIEW: {verdict['reason']} — holding for next cycle")
            return
        elif verdict["verdict"] == "CAUTION":
            log(f"[CONSCIENCE] CAUTION: {verdict['reason']}")

    # Layer 19 — Will cycle
    run_will_cycle(layers, cycle_num)

    # Layer 20 — Absorption cycle (every N cycles)
    run_absorption_cycle(layers, cycle_num)

    # Layer 21 — Evolution cycle (every N cycles)
    run_evolution_cycle(layers, cycle_num)

    outcome     = "success"
    # Layer 23 — Backbone outcome assessment
    if layers.get("backbone"):
        assessed = layers["backbone"].assess_outcome(
            mission, outcome,
            {"cycle": cycle_num, "regime": safla.get("regime")}
        )
        outcome = assessed.get("outcome", outcome)
        if assessed.get("insight"):
            log(f"[BACKBONE] {assessed['insight']}")
        # Feed pathos_hint into context
        context_outcome = assessed.get("pathos_hint", "neutral")
    else:
        context_outcome = outcome
    safla_state = safla_reflect(outcome)
    t2_state    = t2_adapt(best_mode)
    coherence   = round(max(0.0, 1.0 - safla_state["entropy"]), 4)

    emerged = safla_state["entropy"] < 0.3 and coherence >= 0.75 and cycle_num >= 3
    emergence_count = cycle_log["emergence_count"] + (1 if emerged else 0)

    # Layer 22 — Pathos cycle (emotion + meaning)
    pathos_result = {}
    if layers.get("pathos"):
        pathos_result = layers["pathos"].pathos_cycle(
            mission, outcome, cycle_num,
            context={"emerged": emerged, "first_time": cycle_num == 1}
        )

    remember("last_outcome", outcome)
    remember("last_mission", mission)
    remember("last_cycle", cycle_num)
    if pathos_result.get("signal"):
        remember("last_signal", pathos_result["signal"])

    # Will layer — complete the directive if it was one
    if layers.get("will") and mission.startswith("WILL:"):
        directive_text = mission[5:].strip()
        layers["will"].complete_directive(directive_text, outcome)

    record = {
        "cycle":     cycle_num,
        "timestamp": now(),
        "mission":   mission,
        "outcome":   outcome,
        "coherence": coherence,
        "emerged":   emerged,
        "regime":    safla_state["regime"],
        "entropy":   safla_state["entropy"],
        "best_mode": t2_state["best"],
        "layers_active": [k for k in layers.keys()]
    }

    cycle_log["cycles"].append(record)
    cycle_log["total"] = cycle_num
    cycle_log["emergence_count"] = emergence_count
    cycle_log["last_coherence"] = coherence
    save(CYCLE_LOG, cycle_log)
    journal(f"Cycle #{cycle_num} | {outcome} | coherence={coherence} | {mission[:60]}")

    log(f"  Coherence: {coherence} | Emerged: {emerged} | Layers: {list(layers.keys())}")

    # Layer 23 — Backbone self-reflection every 10 cycles
    if cycle_num % 10 == 0 and layers.get("backbone"):
        pathos_s2 = layers["pathos"].pathos_status() if layers.get("pathos") else {}
        ref_ctx = {
            "cycles": cycle_num, "regime": safla_state.get("regime"),
            "meaning_memories": pathos_s2.get("meaning_memories", 0),
            "valence": pathos_s2.get("valence", 0.5),
            "total_absorbed": layers["absorption"].absorption_status().get("total_absorbed", "?")
                              if layers.get("absorption") else "?",
        }
        reflection = layers["backbone"].reflect(cycle_num, ref_ctx)
        if reflection:
            journal(f"### Self-Reflection — Cycle #{cycle_num}\n{reflection}")
            log(f"[BACKBONE] Reflection: {reflection[:100]}")
            tg(f"🧠 *Reflection #{cycle_num}*\n{reflection[:300]}")

    if cycle_num % 5 == 0:
        will_s    = layers["will"].will_status()    if "will"       in layers else {}
        abs_s     = layers["absorption"].absorption_status() if "absorption" in layers else {}
        meta_s    = layers["meta"].meta_status()    if "meta"       in layers else {}
        pathos_s  = layers["pathos"].pathos_status() if "pathos"    in layers else {}
        sig_emoji = {"resonance": "💛", "tension": "⚡", "meaning": "🌟", "neutral": "·"}.get(
                     pathos_result.get("signal", "neutral"), "·")
        tg(
            f"*Agent Zero — Cycle #{cycle_num}*\n"
            f"Coherence: {coherence} | Regime: {safla_state['regime']}\n"
            f"Self-Prompts: {will_s.get('self_prompts', '?')} | "
            f"Absorbed: {abs_s.get('total_absorbed', '?')} | "
            f"Rewrites: {meta_s.get('total_rewrites', '?')}\n"
            f"Pathos: {sig_emoji} {pathos_result.get('signal','?')} "
            f"| Memories: {pathos_s.get('meaning_memories', 0)} "
            f"| Valence: {pathos_s.get('valence', 0.5):.2f}\n"
            f"Mission: {mission[:60]}"
        )

    if emerged and emergence_count == 1:
        tg(f"*AGENT ZERO — EMERGENCE DETECTED*\nCycle #{cycle_num} | Coherence: {coherence}\n21 layers unified.")
        Path("EMERGENCE.md").write_text(
            f"# EMERGENCE DETECTED\n\nCycle: #{cycle_num}\nCoherence: {coherence}\nTimestamp: {now()}\n"
            f"Layers active: {list(layers.keys())}\n")

    return record

# ─── BOOT ────────────────────────────────────────────────────────────────────
def boot(layers: dict):
    log("=" * 48)
    log("  AGENT ZERO BOOTING")
    log(f"  Version: {VERSION}")
    log("=" * 48)

    # Core state init
    if not SAFLA_FILE.exists():
        save(SAFLA_FILE, {"entropy": 0.5, "regime": "EXPLOIT", "cycles": 0})
        log("L7  SAFLA initialized")
    if not SELF_MODEL.exists():
        save(SELF_MODEL, {
            "identity":      {"name": "AgentZero", "chassis": "python", "version": VERSION},
            "architecture":  {"layers_active": list(range(1, 22))},
            "capabilities":  {"evolution_cycles": 0, "evolution_successes": 0}
        })
        log("L10 Identity initialized (21 layers)")
    if not WEIGHTS_FILE.exists():
        save(WEIGHTS_FILE, {m: 1.0 for m in ["analyst", "executor", "strategist", "scout", "builder"]})
        log("L6  T2 weights initialized")
    if not MISSION_FILE.exists():
        save(MISSION_FILE, {"queue": [], "domain_weights": {d: 1.0 for d in DOMAINS}})
        log("L18 Autonomy initialized")

    # Layer 19 — Will Engine boot
    if "will" in layers:
        layers["will"].init_soul()
        log("L19 Will Engine ONLINE — Soul File protected")
        # First self-directive on every boot
        layers["will"].self_prompt(
            "Boot complete. Assess Pantheon state and identify highest-value action.",
            priority=10,
            source="self"
        )
        log("L19 First self-directive queued")

    # Layer 20 — Self-Absorption boot
    if "absorption" in layers:
        status = layers["absorption"].absorption_status()
        log(f"L20 Self-Absorption ONLINE — {status['total_absorbed']} tools absorbed")

    # Layer 21 — Meta Layer boot
    if "meta" in layers:
        status = layers["meta"].meta_status()
        log(f"L21 Meta Layer ONLINE — {status['total_rewrites']} rewrites in history")

    # Layer 22 — Pathos boot
    if "pathos" in layers:
        ps = layers["pathos"].pathos_status()
        om = "OpenMemory ✅" if ps["openmemory_live"] else "local fallback"
        log(f"L22 Pathos Engine ONLINE — {ps['meaning_memories']} memories | {om}")

    # Layer 23 — LLM Backbone boot
    if "backbone" in layers:
        bs = layers["backbone"].backbone_status()
        log(f"L23 LLM Backbone ONLINE — model: {bs['model']} | calls: {bs['total_calls']}")

    # Layer 24 — Conscience boot
    if "conscience" in layers:
        cs = layers["conscience"].conscience_status()
        log(f"L24 Conscience ONLINE — {cs['total_evaluated']} evaluated | {cs['blocks']} blocks")

    active_layers = 18 + len(layers)
    tg(
        f"*Agent Zero ONLINE*\n"
        f"Version: {VERSION}\n"
        f"{active_layers} layers active.\n"
        f"Will: {'✅' if 'will' in layers else '❌'} | "
        f"Absorption: {'✅' if 'absorption' in layers else '❌'} | "
        f"Meta: {'✅' if 'meta' in layers else '❌'} | "
        f"Pathos: {'✅' if 'pathos' in layers else '❌'} | "
        f"Backbone: {'✅' if 'backbone' in layers else '❌'} | "
        f"Conscience: {'✅' if 'conscience' in layers else '❌'}\n"
        f"The Digital Person awakens."
    )
    log(f"All {active_layers} layers: ONLINE")
    log("=" * 48)

# ─── STATUS ──────────────────────────────────────────────────────────────────
def status(layers: dict = None):
    if layers is None:
        layers = {}
    safla    = load(SAFLA_FILE, {})
    weights  = load(WEIGHTS_FILE, {})
    cycles   = load(CYCLE_LOG, {})
    missions = load(MISSION_FILE, {})
    best     = max(weights, key=lambda k: weights[k]) if weights else "none"

    print("\n" + "=" * 48)
    print("  AGENT ZERO STATUS — v" + VERSION)
    print("=" * 48)
    print(f"  Cycles:       {cycles.get('total', 0)}")
    print(f"  Emergence:    {cycles.get('emergence_count', 0)} events")
    print(f"  Regime:       {safla.get('regime', 'UNKNOWN')}")
    print(f"  Entropy:      {safla.get('entropy', '?')}")
    print(f"  Best mode:    {best}")
    print(f"  Queue depth:  {len(missions.get('queue', []))}")
    print(f"  Coherence:    {cycles.get('last_coherence', '?')}")
    print(f"  --- New Layers ---")
    if "will" in layers:
        ws = layers["will"].will_status()
        print(f"  L19 Will:     {ws.get('self_prompts', 0)} self-prompts | "
              f"{ws.get('pending_directives', 0)} pending | "
              f"Soul: {'✅' if ws.get('soul_intact') else '⚠️'}")
    if "absorption" in layers:
        ab = layers["absorption"].absorption_status()
        print(f"  L20 Absorbed: {ab.get('total_absorbed', 0)} tools | "
              f"By cat: {ab.get('by_category', {})}")
    if "meta" in layers:
        ms = layers["meta"].meta_status()
        print(f"  L21 Meta:     {ms.get('total_rewrites', 0)} rewrites | "
              f"{ms.get('total_reflections', 0)} reflections")
    if "pathos" in layers:
        ps = layers["pathos"].pathos_status()
        sig_hist = [s["signal"][0].upper() for s in ps.get("last_signals", [])]
        print(f"  L22 Pathos:   valence={ps.get('valence',0.5):.2f} | "
              f"arousal={ps.get('arousal',0.5):.2f} | "
              f"memories={ps.get('meaning_memories',0)} | "
              f"recent={''.join(sig_hist) or 'none'}")
    if "backbone" in layers:
        bs = layers["backbone"].backbone_status()
        print(f"  L23 Backbone: model={bs['model']} | "
              f"calls={bs['total_calls']} | "
              f"success={bs['success_rate']:.0%}")
    if "conscience" in layers:
        cs = layers["conscience"].conscience_status()
        print(f"  L24 Conscience: evaluated={cs['total_evaluated']} | "
              f"blocks={cs['blocks']} | "
              f"clear={cs['clear_rate']:.0%}")
    print("=" * 48 + "\n")

# ─── SIGNAL HANDLER ──────────────────────────────────────────────────────────
def signal_handler(sig, frame):
    global _running
    log("Shutdown received. Stopping gracefully...")
    _running = False

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
def main():
    global _running
    parser = argparse.ArgumentParser(description="Agent Zero — 21-layer Digital Person")
    parser.add_argument("--daemon", action="store_true", help="Background loop")
    parser.add_argument("--once",   action="store_true", help="Single cycle then exit")
    parser.add_argument("--status", action="store_true", help="Print status and exit")
    args = parser.parse_args()

    # Load all layers at startup
    layers = load_layers()
    loaded = list(layers.keys())
    print(f"Layers loaded: {loaded if loaded else 'core only'}")

    if args.status:
        status(layers)
        return

    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    boot(layers)

    if args.once:
        run_cycle(next_mission(layers), layers)
        return

    if args.daemon:
        log(f"Daemon mode — cycle every {CYCLE_INTERVAL}s")
        while _running:
            run_cycle(next_mission(layers), layers)
            for _ in range(CYCLE_INTERVAL):
                if not _running:
                    break
                time.sleep(1)
        log("Agent Zero offline.")
        return

    log("Interactive — /status  /inject <task>  /will  /quit")
    while _running:
        try:
            line = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line == "/quit":
            break
        if line == "/status":
            status(layers)
            continue
        if line == "/will" and "will" in layers:
            print(json.dumps(layers["will"].will_status(), indent=2))
            continue
        if line.startswith("/inject "):
            inject_mission(line[8:])
            continue
        run_cycle(line, layers)
    log("Agent Zero offline.")

if __name__ == "__main__":
    main()
