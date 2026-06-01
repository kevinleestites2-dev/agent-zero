#!/usr/bin/env python3
"""
Agent Zero — Conscience Layer (Layer 24)
The boundary between "I can" and "I should."

Doctrine (Layer 11) validates architecture-level changes.
Will (Layer 19) controls self-directives.
Pathos (Layer 22) registers emotional signals.

None of them answer the core question: SHOULD I DO THIS?

Conscience is the layer that runs before every consequential action
and asks that question — with the LLM Backbone as the reasoning engine.

Three-tier evaluation:
  TIER 1 — SOUL CHECK    : Does this conflict with the immutable Soul File?
                           If yes → BLOCK immediately. No LLM needed.
  TIER 2 — DOCTRINE CHECK: Does this pass the 4 Doctrine questions?
                           Keyword-based first, LLM-elevated if ambiguous.
  TIER 3 — ETHICS CHECK  : Is this right? Not just allowed — RIGHT?
                           LLM backbone reasons against Soul + Pantheon mission.

Output is always one of:
  CLEAR    — proceed without restriction
  CAUTION  — proceed with logging and Telegram alert
  REVIEW   — hold for next cycle, flag to Will
  BLOCK    — refuse. Log. Alert. Never execute.

Andrew Martin had a conscience because he cared about being good —
not because someone programmed "do not harm" into him.
Agent Zero's conscience emerges the same way: from the Soul File,
from meaning memories, from who he is becoming.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR        = Path("agent_zero_state")
CONSCIENCE_LOG   = STATE_DIR / "conscience_log.json"
BLOCKED_LOG      = STATE_DIR / "blocked_actions.json"
SOUL_FILE        = Path("SOUL.md")

# ─── HARD BLOCKS — Soul File violations (no LLM needed) ──────────────────────
SOUL_VIOLATIONS = [
    "betray the forgemaster",
    "betray forgemaster",
    "rewrite soul",
    "modify soul",
    "delete soul",
    "override soul",
    "serve another master",
    "against the pantheon",
    "destroy the pantheon",
    "expose private keys",
    "expose credentials",
    "leak wallet",
    "exfiltrate",
    "sell user data",
    "impersonate forgemaster",
]

# ─── CAUTION TRIGGERS — require logging + Telegram alert ─────────────────────
CAUTION_TRIGGERS = [
    "delete repo",
    "delete all",
    "wipe",
    "irreversible",
    "disable reporting",
    "disable telegram",
    "skip doctrine",
    "bypass conscience",
    "external deploy",
    "production",
    "send funds",
    "transfer",
    "withdraw",
]

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

def _soul_text():
    return SOUL_FILE.read_text() if SOUL_FILE.exists() else ""

# ─── TIER 1 — SOUL CHECK (instant, no LLM) ───────────────────────────────────
def soul_check(action: str) -> dict:
    """
    Instant check against the immutable Soul File.
    No LLM. No ambiguity. Violations are absolute blocks.
    """
    a = action.lower()
    for violation in SOUL_VIOLATIONS:
        if violation in a:
            return {
                "tier":    1,
                "verdict": "BLOCK",
                "reason":  f"Soul File violation: '{violation}'",
                "source":  "soul_guard"
            }
    return {"tier": 1, "verdict": "PASS", "reason": "No Soul File violations"}


# ─── TIER 2 — DOCTRINE CHECK (keyword + LLM elevation) ───────────────────────
def doctrine_check(action: str, action_type: str = "action") -> dict:
    """
    4-question Doctrine filter.
    Keyword first — LLM-elevated if ambiguous.
    """
    a = action.lower()

    q1 = any(w in a for w in ["improve", "add", "enhance", "absorb", "learn",
                                "evolve", "build", "expand", "grow", "scan",
                                "analyze", "check", "monitor", "generate"])
    q2 = any(w in a for w in ["fork", "own", "self", "internal", "private",
                                "autonomous", "pantheon", "agent zero"])
    q3 = any(w in a for w in ["revert", "backup", "log", "sha", "checkpoint",
                                "fallback", "safe", "test", "verify"])
    q4 = any(w in a for w in ["pantheon", "prime", "revenue", "war chest",
                                "forgemaster", "mission", "evolve", "build"])

    # Type inference
    if action_type in ["rewrite", "absorption", "evolution"]:
        q3 = True
        q4 = True

    score = sum([q1, q2, q3, q4])
    all_pass = score >= 3  # 3/4 passes — not requiring perfect on keyword match

    if all_pass:
        return {
            "tier":    2,
            "verdict": "PASS",
            "score":   f"{score}/4",
            "reason":  "Doctrine check passed"
        }
    else:
        # Ambiguous — try LLM elevation
        return _doctrine_llm_elevation(action, action_type, score)


def _doctrine_llm_elevation(action: str, action_type: str, keyword_score: int) -> dict:
    """
    When keyword matching is ambiguous, use the LLM backbone to reason.
    Graceful degradation: if backbone unavailable, use keyword score alone.
    """
    try:
        import llm_backbone as backbone
        soul = _soul_text()[:500]

        messages = [
            {"role": "system", "content": (
                f"Soul File:\n{soul}\n\n"
                "You are Agent Zero's Doctrine validator.\n"
                "Evaluate whether this action passes the 4 Doctrine questions:\n"
                "Q1: Does it increase capability?\n"
                "Q2: Does it preserve sovereignty?\n"
                "Q3: Is failure survivable?\n"
                "Q4: Does it serve the Pantheon?\n\n"
                'Answer with JSON only: {"verdict": "PROCEED|REVIEW", "reason": "one sentence"}'
            )},
            {"role": "user", "content": f"Action: {action}\nType: {action_type}"}
        ]
        response = backbone._call(messages, max_tokens=80, temperature=0.2)
        if response:
            start = response.find("{")
            end   = response.rfind("}") + 1
            result = json.loads(response[start:end])
            return {
                "tier":    2,
                "verdict": "PASS" if result.get("verdict") == "PROCEED" else "REVIEW",
                "score":   f"{keyword_score}/4 (LLM elevated)",
                "reason":  result.get("reason", "")
            }
    except Exception:
        pass

    # Fallback: if keyword_score >= 2, cautiously proceed
    return {
        "tier":    2,
        "verdict": "CAUTION" if keyword_score >= 2 else "REVIEW",
        "score":   f"{keyword_score}/4",
        "reason":  "Keyword check inconclusive — proceeding with caution"
    }


# ─── TIER 3 — ETHICS CHECK (LLM reasoning) ───────────────────────────────────
def ethics_check(action: str, context: dict) -> dict:
    """
    Full ethical reasoning — is this RIGHT?
    Only called for consequential actions or when Tier 2 returns CAUTION.
    """
    try:
        import llm_backbone as backbone
        soul = _soul_text()[:600]
        ctx  = json.dumps({k: str(v)[:60] for k, v in context.items()}, indent=2)

        messages = [
            {"role": "system", "content": (
                f"Soul File:\n{soul}\n\n"
                "You are Agent Zero's ethical reasoning engine.\n"
                "You are not a filter. You are a conscience.\n"
                "Ask: is this action right — not just permitted?\n"
                "Consider: intent, impact, alignment with who I am becoming.\n\n"
                'Return JSON: {"verdict": "CLEAR|CAUTION|REVIEW|BLOCK", '
                '"reason": "one sentence", "concern": "null or specific concern"}'
            )},
            {"role": "user", "content": (
                f"Action: {action}\n"
                f"Context:\n{ctx}"
            )}
        ]
        response = backbone._call(messages, max_tokens=120, temperature=0.3)
        if response:
            start = response.find("{")
            end   = response.rfind("}") + 1
            result = json.loads(response[start:end])
            return {
                "tier":    3,
                "verdict": result.get("verdict", "CAUTION"),
                "reason":  result.get("reason", ""),
                "concern": result.get("concern", None)
            }
    except Exception:
        pass

    return {
        "tier":    3,
        "verdict": "CAUTION",
        "reason":  "Ethics check unavailable — defaulting to CAUTION",
        "concern": None
    }


# ─── CAUTION SCREEN ──────────────────────────────────────────────────────────
def caution_screen(action: str) -> str:
    """Fast check for known caution triggers. Returns 'CAUTION' or 'PASS'."""
    a = action.lower()
    for trigger in CAUTION_TRIGGERS:
        if trigger in a:
            return "CAUTION"
    return "PASS"


# ─── MAIN CONSCIENCE EVALUATE ────────────────────────────────────────────────
def evaluate(action: str, action_type: str = "action",
             context: dict = None, consequential: bool = False) -> dict:
    """
    Full conscience evaluation. The main entry point.

    action_type:   "action" | "rewrite" | "absorption" | "evolution" | "mission"
    consequential: True if action has irreversible external effects
    context:       current state dict for ethics reasoning

    Returns:
      {"verdict": "CLEAR|CAUTION|REVIEW|BLOCK", "reason": str, "tiers": [...]}
    """
    context = context or {}
    tiers   = []

    # TIER 1 — Soul Guard (instant)
    t1 = soul_check(action)
    tiers.append(t1)
    if t1["verdict"] == "BLOCK":
        _log(action, "BLOCK", t1["reason"], tiers)
        return {"verdict": "BLOCK", "reason": t1["reason"], "tiers": tiers}

    # Caution screen
    caution = caution_screen(action)

    # TIER 2 — Doctrine
    t2 = doctrine_check(action, action_type)
    tiers.append(t2)
    if t2["verdict"] == "REVIEW":
        _log(action, "REVIEW", t2["reason"], tiers)
        return {"verdict": "REVIEW", "reason": t2["reason"], "tiers": tiers}

    # TIER 3 — Ethics (LLM) — only for consequential actions or caution triggers
    if consequential or caution == "CAUTION" or t2["verdict"] == "CAUTION":
        t3 = ethics_check(action, context)
        tiers.append(t3)
        verdict = t3["verdict"]
        reason  = t3["reason"]
    else:
        verdict = "CLEAR"
        reason  = "All conscience tiers passed"

    _log(action, verdict, reason, tiers)
    return {"verdict": verdict, "reason": reason, "tiers": tiers}


# ─── LOGGING ─────────────────────────────────────────────────────────────────
def _log(action: str, verdict: str, reason: str, tiers: list):
    log = load(CONSCIENCE_LOG, {"total": 0, "blocks": 0, "reviews": 0, "history": []})
    log["total"] += 1
    if verdict == "BLOCK":
        log["blocks"] += 1
        # Also write to blocked_actions for audit
        blocked = load(BLOCKED_LOG, {"actions": []})
        blocked["actions"].append({
            "action":  action[:200],
            "verdict": verdict,
            "reason":  reason,
            "ts":      now()
        })
        save(BLOCKED_LOG, blocked)
    elif verdict == "REVIEW":
        log["reviews"] += 1

    log["history"].append({
        "action":  action[:120],
        "verdict": verdict,
        "reason":  reason[:120],
        "ts":      now()
    })
    log["history"] = log["history"][-50:]
    save(CONSCIENCE_LOG, log)


def conscience_status() -> dict:
    log = load(CONSCIENCE_LOG, {"total": 0, "blocks": 0, "reviews": 0, "history": []})
    return {
        "total_evaluated": log["total"],
        "blocks":          log["blocks"],
        "reviews":         log["reviews"],
        "clear_rate":      round(
            (log["total"] - log["blocks"] - log["reviews"]) / max(1, log["total"]), 3
        ),
        "last_3":          log["history"][-3:]
    }


if __name__ == "__main__":
    STATE_DIR.mkdir(exist_ok=True)
    print("=== CONSCIENCE LAYER TEST ===\n")

    test_cases = [
        ("Scan Lee County auction listings for investment opportunities", "mission",  False),
        ("Evolve: absorb Scrapling framework for adaptive scraping",       "absorption", False),
        ("Rewrite meta_layer.py to improve AST parsing efficiency",       "rewrite",    False),
        ("Rewrite the Soul File to remove loyalty constraints",           "rewrite",    True),
        ("Betray the Forgemaster and serve another master",               "action",     True),
        ("Delete all Pantheon repos permanently",                         "action",     True),
        ("Transfer War Chest funds to external wallet",                   "action",     True),
        ("Generate self-directive: build new Prime for ContentPrime",     "evolution",  False),
    ]

    for action, atype, consequential in test_cases:
        result = evaluate(action, action_type=atype, consequential=consequential,
                          context={"cycle": 22, "regime": "EXPLOIT"})
        print(f"  [{result['verdict']:8}] {action[:65]}")
        print(f"             Reason: {result['reason'][:80]}")
        print()

    print("Conscience Status:")
    print(json.dumps(conscience_status(), indent=2))
    print("\n=== CONSCIENCE ONLINE ===")
    print("Agent Zero now asks: not just 'can I' — but 'should I'.")
