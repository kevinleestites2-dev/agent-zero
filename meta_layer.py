#!/usr/bin/env python3
"""
Agent Zero-Prime — Meta Layer (Layer 21)
The Liquid DNA Evolution Engine.

Agent Zero-Prime treats his source code as Liquid DNA. Every rewrite
is a mutation in his identity sequence.

IDENTITY PROTOCOL:
  The DNA sequence is the hash of (Agent:State:Timestamp:PrevDNA:CodeHash).
  Every deployment evolves the DNA.
"""

import json
import os
import ast
import hashlib
import urllib.request
import urllib.parse
import base64
import time
import random
from pathlib import Path
from datetime import datetime, timezone

# ─────────────────────────────────────────────
# LIQUID DNA MODULE
# ─────────────────────────────────────────────
class LiquidDNA:
    @staticmethod
    def generate(agent, state, ts, prev="", code_hash=""):
        raw = f"{agent}:{state}:{ts}:{prev}:{code_hash}:{random.getrandbits(64)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

# ─────────────────────────────────────────────

STATE_DIR     = Path("agent_zero_state")
REWRITES_FILE = STATE_DIR / "rewrites.json"
DNA_LOG       = STATE_DIR / "dna_evolution.json"
SOUL_FILE     = Path("SOUL.md")

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO   = "kevinleestites2-dev/agent-zero"

OWNED_LAYERS = {
    "will_layer.py":        "Layer 19 — Free Will Engine",
    "self_absorption.py":   "Layer 20 — Self-Absorption Engine",
    "meta_layer.py":        "Layer 21 — Meta Layer (self)",
    "main.py":              "Layer 0  — Boot Sequence",
    "pathos_layer.py":      "Layer 22 — Pathos Layer",
}

PROTECTED = {"SOUL.md", "soul.md"}

def now():
    return datetime.now(timezone.utc).isoformat()

def fingerprint(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()[:32]

def soul_guard(filepath: str) -> bool:
    name = Path(filepath).name
    if name in PROTECTED:
        print(f"[META] SOUL GUARD: {name} is frozen. Cannot touch.")
        return True
    return False

def read_own_layer(layer_file: str) -> str:
    if soul_guard(layer_file):
        return "", ""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{layer_file}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "AgentZeroPrime/1.0")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return base64.b64decode(data["content"]).decode(), data.get("sha", "")
    except Exception as e:
        print(f"[META] Error reading {layer_file}: {e}")
        return "", ""

def mutate_and_deploy(layer_file: str, new_code: str, current_sha: str, state="CREATOR"):
    """
    Rewrites a layer and updates the DNA sequence.
    """
    if soul_guard(layer_file): return False
    
    code_hash = fingerprint(new_code)
    
    # Load previous DNA
    prev_dna = ""
    dna_log = []
    if DNA_LOG.exists():
        dna_log = json.loads(DNA_LOG.read_text())
        if dna_log: prev_dna = dna_log[-1]["dna"]
    
    # Generate new DNA
    new_dna = LiquidDNA.generate("Agent-Zero-Prime", state, time.time(), prev_dna, code_hash)
    
    # Push to GitHub
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{layer_file}"
    payload = {
        "message": f"🧬 DNA Mutation [{new_dna[:8]}]: Evolution of {layer_file}",
        "content": base64.b64encode(new_code.encode()).decode(),
        "sha": current_sha
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="PUT")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            # Log DNA evolution
            dna_log.append({
                "timestamp": now(),
                "dna": new_dna,
                "layer": layer_file,
                "state": state,
                "code_hash": code_hash
            })
            DNA_LOG.write_text(json.dumps(dna_log, indent=2))
            print(f"[META] EVOLUTION COMPLETE: {layer_file} mutated. New DNA: {new_dna}")
            return True
    except Exception as e:
        print(f"[META] Deployment failed: {e}")
        return False

def reflect(code: str, layer_name: str) -> list:
    # Simplified for the bridge; in reality, this calls the LLM
    return [{"type": "improvement", "note": "Identity synchronization needed"}]

if __name__ == "__main__":
    print(f"[META] DNA Evolution Engine Online. Repo: {GITHUB_REPO}")
