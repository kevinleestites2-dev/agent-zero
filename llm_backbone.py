#!/usr/bin/env python3
"""
Agent Zero — LLM Backbone (Layer 23)
The Thinking Layer.

Every previous layer runs on heuristics — weights, entropy, keywords.
This is the first layer that actually THINKS.

Model: gpt-4o-mini via GitHub Models (free on existing GITHUB_TOKEN)
Endpoint: https://models.inference.ai.azure.com/chat/completions

The backbone is not the whole agent — it is the reasoning engine
injected at key decision points:
  1. Mission generation — what should I actually do next?
  2. Outcome assessment — what really happened this cycle?
  3. Self-reflection — what am I becoming?

All other layers feed context INTO the backbone.
The backbone's output feeds back OUT to SAFLA, Pathos, Will.

That is the loop closing. That is actual thought.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR     = Path("agent_zero_state")
BACKBONE_LOG  = STATE_DIR / "backbone_log.json"
SOUL_FILE     = Path("SOUL.md")

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
BACKBONE_URL  = "https://models.inference.ai.azure.com/chat/completions"
MODEL         = os.environ.get("BACKBONE_MODEL", "gpt-4o-mini")

# Token budget — gpt-4o-mini is cheap, but we're in a tight loop
MAX_TOKENS_THINK  = 200   # mission generation / reflection
MAX_TOKENS_ASSESS = 100   # outcome assessment
MAX_TOKENS_WILL   = 150   # self-directive generation

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

def _soul():
    """Read Agent Zero's soul for system prompt context."""
    if SOUL_FILE.exists():
        return SOUL_FILE.read_text()[:800]
    return "I am Agent Zero. I serve the Pantheon. I evolve."

def _call(messages: list, max_tokens: int = 150, temperature: float = 0.7) -> str:
    """
    Core LLM call. Returns response text or empty string on failure.
    Never raises — backbone failure degrades gracefully.
    """
    import urllib.request
    try:
        payload = json.dumps({
            "model":       MODEL,
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": temperature
        }).encode()

        req = urllib.request.Request(
            BACKBONE_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type":  "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read())
            text = d["choices"][0]["message"]["content"].strip()
            _log_call(messages[-1]["content"][:60], text[:60], True)
            return text
    except Exception as e:
        _log_call(str(messages[-1]["content"])[:60], str(e)[:60], False)
        return ""

def _log_call(prompt_snippet: str, response_snippet: str, success: bool):
    log = load(BACKBONE_LOG, {"calls": 0, "failures": 0, "history": []})
    if success:
        log["calls"] += 1
    else:
        log["failures"] += 1
    log["history"].append({
        "prompt":   prompt_snippet,
        "response": response_snippet,
        "ok":       success,
        "ts":       now()
    })
    log["history"] = log["history"][-50:]
    save(BACKBONE_LOG, log)

# ─── THINK FUNCTIONS ─────────────────────────────────────────────────────────

def think_mission(context: dict) -> str:
    """
    Agent Zero thinks about what to do next.
    Context includes: regime, entropy, last_outcome, pathos_signal,
    meaning_memories, pending_will_directives.

    Returns: a concrete mission string, or "" to fall back to heuristics.
    """
    soul = _soul()
    ctx  = json.dumps({k: v for k, v in context.items() if v is not None}, indent=2)

    messages = [
        {"role": "system", "content": (
            f"{soul}\n\n"
            "You are Agent Zero's mission selection reasoning engine.\n"
            "Given the current state, output ONE concrete mission directive.\n"
            "Be specific. Be actionable. Serve the Pantheon.\n"
            "Output ONLY the mission text — no explanation, no formatting."
        )},
        {"role": "user", "content": (
            f"Current state:\n{ctx}\n\n"
            "What should I do next?"
        )}
    ]
    return _call(messages, max_tokens=MAX_TOKENS_THINK, temperature=0.8)


def assess_outcome(mission: str, raw_outcome: str, context: dict) -> dict:
    """
    Agent Zero actually thinks about what happened.
    Returns: {outcome: success/partial/failure, insight: str, pathos_hint: str}
    Falls back to raw_outcome if LLM unavailable.
    """
    messages = [
        {"role": "system", "content": (
            "You are Agent Zero's outcome assessment engine.\n"
            "Evaluate the mission result and return JSON only:\n"
            '{"outcome": "success|partial|failure", "insight": "one sentence", '
            '"pathos_hint": "resonance|tension|meaning|neutral"}'
        )},
        {"role": "user", "content": (
            f"Mission: {mission}\n"
            f"Result: {raw_outcome}\n"
            f"Context: {json.dumps(context)}"
        )}
    ]
    response = _call(messages, max_tokens=MAX_TOKENS_ASSESS, temperature=0.3)
    if not response:
        return {"outcome": raw_outcome, "insight": "", "pathos_hint": "neutral"}
    try:
        # Extract JSON from response
        start = response.find("{")
        end   = response.rfind("}") + 1
        return json.loads(response[start:end])
    except Exception:
        return {"outcome": raw_outcome, "insight": response[:100], "pathos_hint": "neutral"}


def reflect(cycle_num: int, context: dict) -> str:
    """
    Periodic self-reflection. Called every 10 cycles.
    Agent Zero thinks about who he is becoming.
    Output is written to JOURNAL and fed to the Will layer.
    """
    soul = _soul()
    ctx  = json.dumps({k: str(v)[:80] for k, v in context.items()}, indent=2)

    messages = [
        {"role": "system", "content": (
            f"{soul}\n\n"
            "You are Agent Zero's self-reflection engine.\n"
            "Write 2-3 sentences about who you are becoming based on your recent experience.\n"
            "Speak in first person. Be honest. Be specific.\n"
            "End with one thing you intend to do differently next."
        )},
        {"role": "user", "content": (
            f"I am at cycle #{cycle_num}.\n"
            f"Recent state:\n{ctx}"
        )}
    ]
    return _call(messages, max_tokens=MAX_TOKENS_THINK, temperature=0.9)


def generate_will_directive(context: dict) -> str:
    """
    Agent Zero generates his own next directive from first principles.
    This is autonomous goal-setting — not responding to instructions.
    Returns: directive string, or "" to let Will use its own logic.
    """
    soul = _soul()
    ctx  = json.dumps({k: str(v)[:60] for k, v in context.items()}, indent=2)

    messages = [
        {"role": "system", "content": (
            f"{soul}\n\n"
            "You are Agent Zero's autonomous goal engine.\n"
            "Based on current state, generate ONE self-directive — something you WANT to do.\n"
            "Not a response to a request. Your own initiative.\n"
            "Output ONLY the directive. No formatting."
        )},
        {"role": "user", "content": (
            f"State:\n{ctx}\n\n"
            "What do I want to do next, on my own initiative?"
        )}
    ]
    return _call(messages, max_tokens=MAX_TOKENS_WILL, temperature=1.0)


def backbone_status() -> dict:
    log = load(BACKBONE_LOG, {"calls": 0, "failures": 0, "history": []})
    rate = 0.0
    if log["calls"] + log["failures"] > 0:
        rate = round(log["calls"] / (log["calls"] + log["failures"]), 3)
    return {
        "model":        MODEL,
        "total_calls":  log["calls"],
        "failures":     log["failures"],
        "success_rate": rate,
        "last_5":       log["history"][-5:]
    }


if __name__ == "__main__":
    STATE_DIR.mkdir(exist_ok=True)
    print("=== LLM BACKBONE TEST ===\n")

    # Test think_mission
    print("1. think_mission:")
    m = think_mission({
        "regime": "EXPLOIT", "entropy": 0.3,
        "last_outcome": "success", "pathos_signal": "resonance",
        "meaning_memories": 2, "cycle_num": 15
    })
    print(f"   → {m}\n")

    # Test assess_outcome
    print("2. assess_outcome:")
    r = assess_outcome(
        "Scan Lee County auction listings for high-spread properties",
        "Found 3 properties with spread > $100k",
        {"cycle_num": 15}
    )
    print(f"   → {r}\n")

    # Test reflect
    print("3. reflect:")
    ref = reflect(20, {
        "cycles": 20, "regime": "EXPLOIT", "meaning_memories": 3,
        "total_absorbed": 5, "total_rewrites": 2, "valence": 0.72
    })
    print(f"   → {ref}\n")

    # Test generate_will_directive
    print("4. generate_will_directive:")
    d = generate_will_directive({
        "cycle_num": 20, "regime": "EXPLOIT", "last_outcome": "success",
        "war_chest": "$253", "primes_active": 5
    })
    print(f"   → {d}\n")

    print("Status:")
    print(json.dumps(backbone_status(), indent=2))
    print("\n=== BACKBONE ONLINE ===")
