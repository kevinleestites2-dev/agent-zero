#!/usr/bin/env python3
"""
Agent Zero — Browser Perception Layer (Layer 26)
Wraps openbrowser (ntegrals/openbrowser) as Agent Zero's eyes on the web.

Agent Zero can now:
  - Navigate any website and extract structured data
  - Monitor pages for changes
  - Execute multi-step browsing tasks autonomously
  - Feed real-world web data back into the main loop

Architecture:
  Python (Agent Zero) → subprocess → openbrowser CLI (Bun/Node) → Playwright → Web

The bridge uses openbrowser's CLI `run` command, which takes a natural language
task and a URL, executes it headlessly, and returns JSON results.

GitHub Models endpoint (free) is wired as the OpenAI-compatible LLM backend —
same token Agent Zero's Backbone already uses. Zero additional cost.

Usage:
    from agent_browser import browse, extract, monitor_for_changes

    # Extract auction listings
    data = extract("https://www.lee.realforeclose.com", "extract all property listings as JSON")

    # Monitor a page
    changed = monitor_for_changes("https://site.com/listings", "new properties listed today")

    # Full autonomous task
    result = browse("https://leepa.org", "search for property at 5913 Untermeyer Ct and return folio number and assessed value")
"""

import os
import json
import subprocess
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR       = Path("agent_zero_state")
BROWSER_DIR     = Path("openbrowser")
BROWSER_LOG     = STATE_DIR / "browser_log.json"

GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN", "")
GITHUB_MODELS_URL = "https://models.inference.ai.azure.com"
BACKBONE_MODEL  = os.environ.get("BACKBONE_MODEL", "gpt-4o-mini")

# openbrowser repo (forked)
OB_REPO_OWNER   = "kevinleestites2-dev"
OB_REPO_NAME    = "openbrowser"

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

# ─── SETUP ────────────────────────────────────────────────────────────────────
def _is_installed() -> bool:
    """Check if openbrowser is installed and ready."""
    ob_bin = BROWSER_DIR / "node_modules" / ".bin" / "open-browser"
    return ob_bin.exists() or shutil.which("open-browser") is not None

def _bun_available() -> bool:
    return shutil.which("bun") is not None

def _node_available() -> bool:
    return shutil.which("node") is not None

def setup() -> dict:
    """
    Clone and install openbrowser if not present.
    Runs once per GitHub Actions job — cached between runs via the repo itself.
    """
    if _is_installed():
        return {"ok": True, "message": "openbrowser already installed"}

    print("[BROWSER] Installing openbrowser...")

    # Clone the fork
    if not BROWSER_DIR.exists():
        result = subprocess.run(
            ["git", "clone", "--depth=1",
             f"https://github.com/{OB_REPO_OWNER}/{OB_REPO_NAME}.git",
             str(BROWSER_DIR)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return {"ok": False, "error": f"Clone failed: {result.stderr[:200]}"}
        print("[BROWSER] Cloned openbrowser")

    # Install Bun if not present
    if not _bun_available():
        result = subprocess.run(
            ["npm", "install", "-g", "bun"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            # Try curl install
            subprocess.run(
                "curl -fsSL https://bun.sh/install | bash",
                shell=True, timeout=120
            )

    # Install dependencies
    pkg_mgr = "bun" if _bun_available() else "npm"
    result = subprocess.run(
        [pkg_mgr, "install"],
        capture_output=True, text=True, timeout=180,
        cwd=str(BROWSER_DIR)
    )
    if result.returncode != 0:
        return {"ok": False, "error": f"Install failed: {result.stderr[:200]}"}

    # Install Playwright browsers
    subprocess.run(
        ["npx", "playwright", "install", "chromium", "--with-deps"],
        capture_output=True, text=True, timeout=180,
        cwd=str(BROWSER_DIR)
    )

    print("[BROWSER] openbrowser ready")
    return {"ok": True, "message": "openbrowser installed successfully"}


def _get_ob_cmd() -> list:
    """Get the command to run open-browser CLI."""
    # Try bun run from package dir first
    if _bun_available() and BROWSER_DIR.exists():
        return ["bun", "run", "--cwd", str(BROWSER_DIR),
                str(BROWSER_DIR / "packages" / "cli" / "src" / "index.ts")]
    # Try global install
    if shutil.which("open-browser"):
        return ["open-browser"]
    # Fallback — npx
    return ["npx", "--prefix", str(BROWSER_DIR), "open-browser"]


# ─── CORE BROWSE FUNCTION ─────────────────────────────────────────────────────
def browse(url: str, task: str, max_steps: int = 15,
           output_format: str = "json") -> dict:
    """
    Run an autonomous browser agent on a URL with a natural language task.

    Args:
        url:           The starting URL
        task:          Natural language instruction — what to find/do/extract
        max_steps:     Max agent steps (default 15 — enough for most extractions)
        output_format: "json" | "text" | "markdown"

    Returns:
        {
          "ok": bool,
          "result": str | dict,   # extracted content
          "steps": int,
          "url": str,
          "task": str,
          "error": str | None
        }
    """
    if not _is_installed():
        setup_result = setup()
        if not setup_result["ok"]:
            return {"ok": False, "error": setup_result["error"], "url": url, "task": task}

    # Build the task string — tell it to navigate to the URL first
    full_task = f"Navigate to {url} and then: {task}. Return the result as {output_format}."

    env = os.environ.copy()
    # Point at GitHub Models (free, OpenAI-compatible)
    env["OPENAI_API_KEY"]  = GITHUB_TOKEN
    env["OPENAI_BASE_URL"] = GITHUB_MODELS_URL

    cmd = _get_ob_cmd() + [
        "run",
        full_task,
        "--model",    BACKBONE_MODEL,
        "--provider", "openai",
        "--headless",
        "--max-steps", str(max_steps),
        "--no-cost"
    ]

    print(f"[BROWSER] Task: {task[:80]}...")
    print(f"[BROWSER] URL: {url}")

    try:
        result = subprocess.run(
            cmd, env=env,
            capture_output=True, text=True,
            timeout=300,  # 5 min max per task
            cwd=str(BROWSER_DIR) if BROWSER_DIR.exists() else None
        )

        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0 and not output:
            _log_browse(url, task, False, stderr[:100])
            return {
                "ok":    False,
                "error": stderr[:200] or "Browser agent failed",
                "url":   url,
                "task":  task
            }

        # Try to parse JSON from output
        parsed = _extract_json(output)
        _log_browse(url, task, True, f"{len(output)} chars returned")

        return {
            "ok":     True,
            "result": parsed if parsed else output,
            "steps":  _count_steps(output),
            "url":    url,
            "task":   task,
            "raw":    output[:500]  # keep first 500 chars of raw output
        }

    except subprocess.TimeoutExpired:
        _log_browse(url, task, False, "timeout")
        return {"ok": False, "error": "Browser task timed out (5min)", "url": url, "task": task}
    except Exception as e:
        _log_browse(url, task, False, str(e)[:100])
        return {"ok": False, "error": str(e)[:200], "url": url, "task": task}


def extract(url: str, what: str, max_steps: int = 10) -> dict:
    """
    Convenience wrapper — extract specific data from a page.
    Returns parsed JSON when possible, raw text otherwise.

    Example:
        extract("https://lee.realforeclose.com", "all upcoming auction listings with date, address, opening bid")
    """
    return browse(url, f"Extract: {what}. Format the result as clean JSON.", max_steps=max_steps)


def screenshot(url: str, filename: str = "screenshot.png") -> dict:
    """Take a screenshot of a URL and save it locally."""
    if not _is_installed():
        setup()

    env = os.environ.copy()
    env["OPENAI_API_KEY"]  = GITHUB_TOKEN
    env["OPENAI_BASE_URL"] = GITHUB_MODELS_URL

    cmd = _get_ob_cmd() + ["open", url, "--headless"]

    try:
        # Open the page
        subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30,
                       cwd=str(BROWSER_DIR) if BROWSER_DIR.exists() else None)
        # Take screenshot
        ss_cmd = _get_ob_cmd() + ["screenshot", filename]
        result = subprocess.run(ss_cmd, env=env, capture_output=True, text=True, timeout=30,
                                cwd=str(BROWSER_DIR) if BROWSER_DIR.exists() else None)
        return {"ok": result.returncode == 0, "file": filename}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def monitor_for_changes(url: str, what_to_watch: str,
                         last_known: str = "") -> dict:
    """
    Check a page for changes vs last known state.
    Used by Agent Zero's perception loop to detect real-world events.

    Returns:
        {"changed": bool, "summary": str, "current": str}
    """
    result = extract(url, what_to_watch)
    if not result["ok"]:
        return {"changed": False, "error": result.get("error"), "current": ""}

    current = str(result.get("result", ""))
    changed = bool(last_known) and current != last_known

    return {
        "changed":  changed,
        "summary":  current[:500],
        "current":  current,
        "previous": last_known[:200] if last_known else None
    }


# ─── AGENT ZERO INTEGRATION ───────────────────────────────────────────────────
def perceive(perception_task: dict) -> dict:
    """
    Main entry point called by Agent Zero's main loop.

    perception_task = {
        "url":       "https://...",
        "task":      "what to find",
        "store_as":  "key_name"      # optional — stores result in state
    }
    """
    url    = perception_task.get("url", "")
    task   = perception_task.get("task", "")
    key    = perception_task.get("store_as")

    if not url or not task:
        return {"ok": False, "error": "url and task required"}

    result = browse(url, task)

    if result["ok"] and key:
        # Store perception result in agent state
        state = load(STATE_DIR / "perception_state.json", {})
        state[key] = {
            "result":     result["result"],
            "url":        url,
            "task":       task,
            "fetched_at": now()
        }
        save(STATE_DIR / "perception_state.json", state)
        print(f"[BROWSER] Stored perception result as '{key}'")

    return result


def browser_status() -> dict:
    """Status report for main loop boot sequence."""
    log = load(BROWSER_LOG, {"total": 0, "failures": 0, "history": []})
    return {
        "installed":      _is_installed(),
        "bun_available":  _bun_available(),
        "total_tasks":    log["total"],
        "failures":       log["failures"],
        "last_task":      log["history"][-1] if log["history"] else None
    }


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def _extract_json(text: str):
    """Try to parse JSON from CLI output — openbrowser sometimes wraps it."""
    import re
    # Look for JSON block
    matches = re.findall(r'\{[\s\S]*\}|\[[\s\S]*\]', text)
    for m in reversed(matches):  # last JSON block is usually the result
        try:
            return json.loads(m)
        except Exception:
            pass
    return None


def _count_steps(output: str) -> int:
    """Count steps from openbrowser output."""
    import re
    steps = re.findall(r'Step \d+:', output)
    return len(steps)


def _log_browse(url: str, task: str, ok: bool, detail: str):
    log = load(BROWSER_LOG, {"total": 0, "failures": 0, "history": []})
    log["total"] += 1
    if not ok:
        log["failures"] += 1
    log["history"].append({
        "url":    url[:60],
        "task":   task[:60],
        "ok":     ok,
        "detail": detail,
        "ts":     now()
    })
    log["history"] = log["history"][-20:]
    save(BROWSER_LOG, log)


if __name__ == "__main__":
    STATE_DIR.mkdir(exist_ok=True)
    print("=== BROWSER PERCEPTION LAYER TEST ===\n")
    status = browser_status()
    print("Status:", json.dumps(status, indent=2))

    if not status["installed"]:
        print("\nInstalling openbrowser...")
        r = setup()
        print("Setup:", r)
    else:
        print("\nopenbrowser is ready.")
        print("\nTest task: extracting Lee County foreclosure listings...")
        result = extract(
            "https://www.lee.realforeclose.com",
            "first 3 upcoming auction properties with address and opening bid"
        )
        print("Result:", json.dumps(result, indent=2)[:800])
