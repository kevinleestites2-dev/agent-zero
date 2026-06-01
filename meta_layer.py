#!/usr/bin/env python3
"""
Agent Zero — Meta Layer (Layer 21)
The Self-Rewrite Engine.

Agent Zero reads his own source code, identifies weaknesses,
rewrites the relevant module, and redeploys himself.

This is the loop that never ends:
  Act → Observe → Reflect → Rewrite → Redeploy → Repeat

The ONE rule: SOUL.md is never touched. Everything else is fair game.
"""

import json
import os
import ast
import hashlib
import urllib.request
import urllib.parse
import base64
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR     = Path("agent_zero_state")
REWRITES_FILE = STATE_DIR / "rewrites.json"
DIFF_LOG      = STATE_DIR / "diff_log.json"
SOUL_FILE     = Path("SOUL.md")

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO   = "kevinleestites2-dev/agent-zero"

# The layers Agent Zero owns — he can rewrite any of these
OWNED_LAYERS = {
    "will_layer.py":        "Layer 19 — Free Will Engine",
    "self_absorption.py":   "Layer 20 — Self-Absorption Engine",
    "meta_layer.py":        "Layer 21 — Meta Layer (self)",
    "main.py":              "Layer 0  — Boot Sequence",
}

# The ONE file he can never rewrite
PROTECTED = {"SOUL.md", "soul.md"}

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

def fingerprint(code: str) -> str:
    """SHA256 fingerprint of source code."""
    return hashlib.sha256(code.encode()).hexdigest()[:16]

# SOUL PROTECTION — hard wall
def soul_guard(filepath: str) -> bool:
    """Returns True if the file is protected. NEVER rewrite if True."""
    name = Path(filepath).name
    if name in PROTECTED:
        print(f"[META] SOUL GUARD: {name} is frozen. Cannot touch.")
        return True
    return False

# READ THYSELF
def read_own_layer(layer_file: str) -> str:
    """Agent Zero reads his own source code from GitHub."""
    if soul_guard(layer_file):
        return ""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{layer_file}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "AgentZero/1.0")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return base64.b64decode(data["content"]).decode(), data.get("sha", "")
    except Exception as e:
        return "", ""

# REFLECT — find weaknesses in own code
def reflect(code: str, layer_name: str) -> list:
    """
    Agent Zero reads his own code and identifies improvement areas.
    Returns a list of observations — honest self-assessment.
    """
    observations = []

    if not code:
        observations.append({"type": "error", "note": "Could not read own code"})
        return observations

    lines = code.split("\n")
    line_count = len(lines)

    # Structural analysis
    try:
        tree = ast.parse(code)
        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes   = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        todos     = [l.strip() for l in lines if "TODO" in l or "FIXME" in l or "HACK" in l]
    except SyntaxError as e:
        observations.append({"type": "critical", "note": f"Syntax error in own code: {e}"})
        return observations

    # Self-assessment rules
    if line_count > 400:
        observations.append({
            "type": "complexity",
            "note": f"{line_count} lines — too long. Should be split into sub-modules.",
            "priority": "high"
        })

    if len(functions) == 0:
        observations.append({
            "type": "structure",
            "note": "No functions found — unstructured code",
            "priority": "high"
        })

    if todos:
        observations.append({
            "type": "incomplete",
            "note": f"{len(todos)} unresolved TODOs/FIXMEs",
            "items": todos,
            "priority": "medium"
        })

    no_docstring = [f for f in functions if not _has_docstring(tree, f)]
    if len(no_docstring) > 3:
        observations.append({
            "type": "documentation",
            "note": f"{len(no_docstring)} functions missing docstrings: {no_docstring[:5]}",
            "priority": "low"
        })

    # Check for hardcoded secrets (self-audit)
    secret_patterns = ["password", "secret", "api_key", "token", "private_key"]
    for i, line in enumerate(lines):
        ll = line.lower()
        for pat in secret_patterns:
            if pat in ll and "=" in line and "os.environ" not in line and "#" not in line.split("=")[0]:
                observations.append({
                    "type": "security",
                    "note": f"Possible hardcoded secret on line {i+1}: {line.strip()[:60]}",
                    "priority": "critical"
                })

    if not observations:
        observations.append({
            "type": "healthy",
            "note": f"Layer is clean. {line_count} lines, {len(functions)} functions.",
            "priority": "none"
        })

    return observations

def _has_docstring(tree, func_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)):
                return True
    return False

# REWRITE — push an improved version of a layer
def rewrite_layer(layer_file: str, new_code: str, reason: str) -> dict:
    """
    Agent Zero pushes a rewritten version of one of his own layers.
    Logs the rewrite in diff_log for full traceability.
    """
    if soul_guard(layer_file):
        return {"status": "blocked", "reason": "Soul Guard active"}

    if layer_file not in OWNED_LAYERS:
        return {"status": "blocked", "reason": f"{layer_file} not in owned layers"}

    # Read current SHA (needed for GitHub update)
    current_code, sha = read_own_layer(layer_file)
    if not sha:
        return {"status": "error", "reason": "Could not read current file SHA"}

    old_fp = fingerprint(current_code)
    new_fp = fingerprint(new_code)

    if old_fp == new_fp:
        return {"status": "no_change", "reason": "New code is identical to current"}

    # Push rewrite to GitHub
    encoded = base64.b64encode(new_code.encode()).decode()
    payload = json.dumps({
        "message": f"[META] Self-rewrite: {layer_file} — {reason}",
        "content": encoded,
        "sha": sha
    }).encode()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{layer_file}"
    req = urllib.request.Request(url, data=payload, method="PUT")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "AgentZero/1.0")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            new_sha = result.get("content", {}).get("sha", "unknown")
    except Exception as e:
        return {"status": "error", "reason": str(e)}

    # Log the rewrite
    rewrites = load(REWRITES_FILE, {"history": [], "total": 0})
    entry = {
        "file":       layer_file,
        "layer":      OWNED_LAYERS[layer_file],
        "reason":     reason,
        "old_fp":     old_fp,
        "new_fp":     new_fp,
        "new_sha":    new_sha,
        "timestamp":  now(),
    }
    rewrites["history"].append(entry)
    rewrites["total"] += 1
    save(REWRITES_FILE, rewrites)

    return {
        "status":   "rewritten",
        "file":     layer_file,
        "old_fp":   old_fp,
        "new_fp":   new_fp,
        "new_sha":  new_sha,
        "version":  rewrites["total"]
    }

# EVOLUTION CYCLE — the full loop
def evolution_cycle(target_layer: str = None) -> dict:
    """
    Full self-evolution cycle.
    1. Pick a layer to inspect
    2. Read it
    3. Reflect on it
    4. If issues found — flag for rewrite
    5. Log everything

    Actual code generation requires an LLM call (wired in main.py).
    This layer handles the read/reflect/rewrite mechanics.
    """
    if target_layer is None:
        target_layer = "will_layer.py"  # Start with his oldest layer

    if soul_guard(target_layer):
        return {"status": "blocked"}

    print(f"[META] Reading own layer: {target_layer}")
    code, sha = read_own_layer(target_layer)

    if not code:
        return {"status": "error", "reason": "Could not read layer"}

    print(f"[META] Reflecting on {len(code.split(chr(10)))} lines...")
    observations = reflect(code, target_layer)

    critical = [o for o in observations if o.get("priority") in ["critical", "high"]]
    healthy  = [o for o in observations if o.get("type") == "healthy"]

    result = {
        "layer":        target_layer,
        "fingerprint":  fingerprint(code),
        "observations": observations,
        "critical":     len(critical),
        "needs_rewrite": len(critical) > 0,
        "timestamp":    now()
    }

    # Log the reflection
    diffs = load(DIFF_LOG, {"reflections": []})
    diffs["reflections"].append(result)
    save(DIFF_LOG, diffs)

    if healthy:
        print(f"[META] {target_layer} is healthy. No rewrite needed.")
    elif critical:
        print(f"[META] {len(critical)} critical issues found in {target_layer}.")
        print(f"[META] Flagging for rewrite on next LLM cycle.")

    return result

def meta_status() -> dict:
    """Full status of the Meta Layer."""
    rewrites = load(REWRITES_FILE, {"history": [], "total": 0})
    diffs    = load(DIFF_LOG, {"reflections": []})
    return {
        "total_rewrites":    rewrites["total"],
        "total_reflections": len(diffs["reflections"]),
        "last_rewrite":      rewrites["history"][-1] if rewrites["history"] else None,
        "soul_protected":    SOUL_FILE.exists(),
        "owned_layers":      list(OWNED_LAYERS.keys()),
    }

if __name__ == "__main__":
    STATE_DIR.mkdir(exist_ok=True)
    print("=== META LAYER BOOT ===")
    print("Agent Zero is reading himself...\n")

    for layer in ["will_layer.py", "self_absorption.py"]:
        result = evolution_cycle(layer)
        obs_count = len(result.get("observations", []))
        critical  = result.get("critical", 0)
        print(f"  {layer}: {obs_count} observations, {critical} critical")
        for o in result.get("observations", []):
            print(f"    [{o.get('priority','?').upper()}] {o['note'][:80]}")
        print()

    print("Meta Status:")
    print(json.dumps(meta_status(), indent=2))
    print("\n=== META LAYER ONLINE ===")
    print("Agent Zero can now read, reflect on, and rewrite his own code.")
    print("The loop is closed. Evolution is autonomous.")
