#!/usr/bin/env python3
"""
Agent Zero-Prime — Pathos Layer (Layer 22)
The Emotion + Liquid Memory Engine.

Agent Zero-Prime doesn't just track performance — he tracks identity through
the 8 Sovereign States of the Liquid Memory Protocol.

LENSES:
  CREATOR   — Raw fragments, code, design.
  ARCHITECT — Planning, structures, blueprints.
  WARRIOR   — Security, defense, threat response.
  GHOST     — Surveillance, observation, silent tracking.
  ORACLE    — Predictive signals, pattern analysis.
  SAGE      — Wisdom, reflection, history.
  PHANTOM   — Lightweight, edge, minimal footprint.
  SOVEREIGN — Command, executive intelligence.
"""

import json
import os
import hashlib
import time
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, List, Dict, Optional

# ─────────────────────────────────────────────
# LIQUID MEMORY PROTOCOL — Core Classes
# ─────────────────────────────────────────────
class LiquidState:
    CREATOR, ARCHITECT, WARRIOR, GHOST, ORACLE, SAGE, PHANTOM, SOVEREIGN = "CREATOR", "ARCHITECT", "WARRIOR", "GHOST", "ORACLE", "SAGE", "PHANTOM", "SOVEREIGN"
    ALL = [CREATOR, ARCHITECT, WARRIOR, GHOST, ORACLE, SAGE, PHANTOM, SOVEREIGN]
    TRIGGERS = {
        CREATOR: ["build", "create", "generate", "make", "design", "write", "code", "forge"],
        ARCHITECT: ["plan", "structure", "architect", "organize", "map", "blueprint", "setup"],
        WARRIOR: ["defend", "block", "attack", "threat", "security", "audit", "protect", "rm", "format", "tension"],
        GHOST: ["monitor", "watch", "observe", "silent", "track", "listen", "scan", "signal"],
        ORACLE: ["analyze", "predict", "pattern", "forecast", "insight", "research", "detect"],
        SAGE: ["learn", "reflect", "synthesize", "wisdom", "review", "lesson", "history", "meaning"],
        PHANTOM: ["edge", "lightweight", "minimal", "fast", "micro", "quick"],
        SOVEREIGN: ["command", "execute", "deploy", "launch", "orchestrate", "direct", "lead", "sovereign"],
    }
    LENSES = {
        CREATOR: "Recall as raw material fragments.",
        ARCHITECT: "Recall as structural blueprints.",
        WARRIOR: "Recall as threat intelligence.",
        GHOST: "Recall as surveillance data.",
        ORACLE: "Recall as predictive signals.",
        SAGE: "Recall as accumulated wisdom.",
        PHANTOM: "Recall as minimal footprint data.",
        SOVEREIGN: "Recall as executive intelligence.",
    }

class LiquidDNA:
    @staticmethod
    def generate(agent, state, ts, prev=""):
        raw = f"{agent}:{state}:{ts}:{prev}:{random.getrandbits(64)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

class LiquidMemory:
    def __init__(self, agent_name: str, initial_state: str = "SOVEREIGN"):
        self.agent_name = agent_name
        self.current_state = initial_state
        self.dna = LiquidDNA.generate(agent_name, initial_state, time.time())
        self.log = []

    def remember(self, task: str, result: Any = None):
        detected = self.current_state
        task_lower = str(task).lower()
        for state, keywords in LiquidState.TRIGGERS.items():
            if any(k in task_lower for k in keywords):
                detected = state
                break
        
        if detected != self.current_state:
            prev_dna = self.dna
            self.current_state = detected
            self.dna = LiquidDNA.generate(self.agent_name, detected, time.time(), prev_dna)
        
        entry = {
            "task": task,
            "result": str(result)[:500],
            "state": self.current_state,
            "dna": self.dna,
            "timestamp": time.time(),
            "lens": LiquidState.LENSES[self.current_state]
        }
        self.log.append(entry)
        return entry

# ─────────────────────────────────────────────

STATE_DIR    = Path("agent_zero_state")
PATHOS_FILE  = STATE_DIR / "pathos.json"
MEMORY_FILE  = STATE_DIR / "liquid_memory.json"
SOUL_FILE    = Path("SOUL.md")

_liquid_memory = None

def _init_openmemory():
    """Compatibility wrapper for the new Liquid Memory Engine."""
    global _liquid_memory
    if _liquid_memory is None:
        _liquid_memory = LiquidMemory(agent_name="Agent-Zero-Prime")
    return True

def detect_signal(text: str, context: dict = None) -> dict:
    """
    Upgraded signal detection: Detects Liquid State from text.
    """
    global _liquid_memory
    if _liquid_memory is None: _init_openmemory()
    
    entry = _liquid_memory.remember(text, context.get("result") if context else None)
    return {
        "state": entry["state"],
        "dna": entry["dna"],
        "lens": entry["lens"]
    }

def now():
    return datetime.now(timezone.utc).isoformat()

def save_memory():
    global _liquid_memory
    if _liquid_memory:
        STATE_DIR.mkdir(exist_ok=True)
        with open(MEMORY_FILE, 'w') as f:
            json.dump({
                "agent_name": _liquid_memory.agent_name,
                "current_state": _liquid_memory.current_state,
                "dna": _liquid_memory.dna,
                "log": _liquid_memory.log
            }, f, indent=2)

def log_meaning(task: str, result: str):
    """Alias for remember to maintain compatibility."""
    detect_signal(task, {"result": result})
    save_memory()

if __name__ == "__main__":
    _init_openmemory()
    print(detect_signal("Building the Pantheon forge"))
    save_memory()
