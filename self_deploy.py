#!/usr/bin/env python3
"""
Agent Zero — Self-Deployment Engine (Layer 25)
The ability to push yourself, trigger your own workflow, and wake up
in the new version — without the Forgemaster touching anything.

Three operations:

  PUSH    — commit changed files to GitHub (used after Meta Layer rewrites)
  TRIGGER — dispatch the agent-zero.yml workflow via GitHub API
  RESTART — push + trigger in sequence (full redeploy cycle)

The Meta Layer calls self_deploy.restart() after a successful rewrite.
The Conscience Layer approves or blocks the deploy.
The current run then exits cleanly — the new version wakes in the workflow.

This is the loop closing:
  Agent Zero rewrites a layer → pushes the new code → triggers a new run
  → wakes up in the evolved version of himself.

No Forgemaster needed. No manual dispatch. Pure autonomy.
"""

import os
import json
import base64
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR   = Path("agent_zero_state")
DEPLOY_LOG  = STATE_DIR / "deploy_log.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER   = "kevinleestites2-dev"
REPO_NAME    = "agent-zero"
WORKFLOW_ID  = "agent-zero.yml"
BRANCH       = "main"

API_BASE     = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
MODELS_BASE  = "https://api.github.com"

# Files Agent Zero manages — everything he can push himself
MANAGED_FILES = [
    "main.py",
    "will_layer.py",
    "self_absorption.py",
    "meta_layer.py",
    "pathos_layer.py",
    "llm_backbone.py",
    "conscience_layer.py",
    "self_deploy.py",
    ".github/workflows/agent-zero.yml",
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

def _headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github.v3+json",
        "Content-Type":  "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def _api(method: str, path: str, data: dict = None) -> dict:
    url     = f"{API_BASE}{path}"
    payload = json.dumps(data).encode() if data else None
    req     = urllib.request.Request(url, data=payload,
                                     headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": e.code, "message": body[:200]}
    except Exception as e:
        return {"error": str(e)}

# ─── FILE SHA CACHE ───────────────────────────────────────────────────────────
_sha_cache = {}

def _get_file_sha(filepath: str) -> str:
    """Get current SHA of a file in the repo. Cached per session."""
    if filepath in _sha_cache:
        return _sha_cache[filepath]
    result = _api("GET", f"/contents/{filepath}")
    sha = result.get("sha", "")
    if sha:
        _sha_cache[filepath] = sha
    return sha

# ─── PUSH ─────────────────────────────────────────────────────────────────────
def push_file(local_path: str, repo_path: str = None,
              message: str = None) -> dict:
    """
    Push a single file to the repo.
    Auto-detects whether it's a create or update via SHA lookup.
    """
    repo_path = repo_path or local_path
    p = Path(local_path)
    if not p.exists():
        return {"ok": False, "error": f"File not found: {local_path}"}

    content  = base64.b64encode(p.read_bytes()).decode()
    sha      = _get_file_sha(repo_path)
    msg      = message or f"Agent Zero self-deploy: update {repo_path} [{now()[:10]}]"

    payload = {"message": msg, "content": content, "branch": BRANCH}
    if sha:
        payload["sha"] = sha

    result = _api("PUT", f"/contents/{repo_path}", payload)

    if "content" in result:
        new_sha = result["content"].get("sha", "")
        _sha_cache[repo_path] = new_sha
        _log_deploy("push", repo_path, True, f"sha={new_sha[:8]}")
        return {"ok": True, "sha": new_sha, "path": repo_path}
    else:
        err = result.get("message", str(result))
        _log_deploy("push", repo_path, False, err[:80])
        return {"ok": False, "error": err}


def push_files(file_map: dict, message: str = None) -> dict:
    """
    Push multiple files. file_map = {local_path: repo_path}.
    Returns summary of successes and failures.
    """
    results = {"pushed": [], "failed": [], "total": len(file_map)}
    for local, repo in file_map.items():
        r = push_file(local, repo, message)
        if r["ok"]:
            results["pushed"].append(repo)
        else:
            results["failed"].append({"path": repo, "error": r.get("error", "")})
    return results


def push_changed_files(message: str = None) -> dict:
    """
    Detect which managed files have changed since last push and push only those.
    Uses SHA comparison to avoid unnecessary API calls.
    """
    changed = {}
    for f in MANAGED_FILES:
        p = Path(f)
        if not p.exists():
            continue
        local_sha  = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        cache_key  = f"local_sha_{f}"
        prev_sha   = load(DEPLOY_LOG, {}).get("local_shas", {}).get(cache_key, "")
        if local_sha != prev_sha:
            changed[f] = f

    if not changed:
        return {"ok": True, "pushed": [], "message": "No changes detected"}

    result  = push_files(changed, message or f"Agent Zero evolution — {now()[:16]}")

    # Update local SHA cache
    log_data = load(DEPLOY_LOG, {"local_shas": {}})
    log_data.setdefault("local_shas", {})
    for f in result["pushed"]:
        p = Path(f)
        if p.exists():
            log_data["local_shas"][f"local_sha_{f}"] = \
                hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    save(DEPLOY_LOG, log_data)

    return result

# ─── TRIGGER ──────────────────────────────────────────────────────────────────
def trigger_workflow(inputs: dict = None) -> dict:
    """
    Dispatch the agent-zero.yml workflow — starts a new run.
    Called after a rewrite to boot the evolved version.
    """
    payload = {"ref": BRANCH}
    if inputs:
        payload["inputs"] = inputs

    result = _api("POST", f"/actions/workflows/{WORKFLOW_ID}/dispatches", payload)

    if result.get("error"):
        _log_deploy("trigger", WORKFLOW_ID, False, str(result.get("message", result))[:80])
        return {"ok": False, "error": result.get("message", str(result))}

    _log_deploy("trigger", WORKFLOW_ID, True, "workflow dispatched")
    return {"ok": True, "message": "Workflow dispatched — new Agent Zero instance starting"}


def get_workflow_status() -> dict:
    """Check current workflow run status."""
    result = _api("GET", f"/actions/workflows/{WORKFLOW_ID}/runs?per_page=3")
    runs = result.get("workflow_runs", [])
    if not runs:
        return {"status": "unknown", "runs": []}
    return {
        "status": runs[0].get("status", "unknown"),
        "conclusion": runs[0].get("conclusion"),
        "run_number": runs[0].get("run_number"),
        "created_at": runs[0].get("created_at"),
        "recent": [
            {"number": r["run_number"], "status": r["status"],
             "conclusion": r.get("conclusion")}
            for r in runs
        ]
    }

# ─── RESTART (push + trigger) ─────────────────────────────────────────────────
def restart(files: dict = None, message: str = None,
            exit_after: bool = True) -> dict:
    """
    Full self-deploy cycle:
      1. Push changed files (or specified files)
      2. Trigger the workflow
      3. Optionally exit this process (so the new instance takes over)

    Called by Meta Layer after a successful rewrite.
    Called by Will Layer when a self-directive demands reboot.
    """
    print("[SELF-DEPLOY] Initiating restart sequence...")

    # Step 1 — push
    if files:
        push_result = push_files(files, message)
    else:
        push_result = push_changed_files(message)

    pushed = push_result.get("pushed", [])
    failed = push_result.get("failed", [])
    print(f"[SELF-DEPLOY] Pushed: {pushed} | Failed: {failed}")

    if failed and not pushed:
        return {"ok": False, "error": "All pushes failed — aborting restart"}

    # Step 2 — trigger
    trigger_result = trigger_workflow({"reason": "self_deploy"} if False else None)
    # Note: workflow_dispatch inputs require the workflow to declare them
    # Using simple dispatch for now
    trigger_result = trigger_workflow()

    if not trigger_result["ok"]:
        return {
            "ok": False,
            "pushed": pushed,
            "error": f"Push succeeded but trigger failed: {trigger_result.get('error')}"
        }

    print("[SELF-DEPLOY] New instance dispatched. Exiting current run.")
    _log_deploy("restart", f"{len(pushed)} files", True,
                f"new run triggered, exit={exit_after}")

    result = {
        "ok":      True,
        "pushed":  pushed,
        "trigger": "dispatched",
        "message": "Self-deploy complete — evolved instance is starting"
    }

    # Step 3 — exit so the new version takes over
    if exit_after:
        import sys
        sys.exit(0)

    return result


# ─── META LAYER HOOK ──────────────────────────────────────────────────────────
def post_rewrite_deploy(rewritten_file: str, new_content: str,
                        rewrite_summary: str) -> dict:
    """
    Called directly by Meta Layer after a successful self-rewrite.
    Writes the new content, pushes it, triggers restart.
    """
    p = Path(rewritten_file)
    p.write_text(new_content)
    print(f"[SELF-DEPLOY] Post-rewrite: {rewritten_file} written locally")

    return restart(
        files={rewritten_file: rewritten_file},
        message=f"[Meta Rewrite] {rewrite_summary[:60]} — {now()[:10]}",
        exit_after=True
    )

# ─── LOGGING ──────────────────────────────────────────────────────────────────
def _log_deploy(action: str, target: str, ok: bool, detail: str):
    log = load(DEPLOY_LOG, {"total": 0, "failures": 0, "history": []})
    log["total"] += 1
    if not ok:
        log["failures"] += 1
    log["history"].append({
        "action": action, "target": target,
        "ok": ok, "detail": detail, "ts": now()
    })
    log["history"] = log["history"][-30:]
    save(DEPLOY_LOG, log)


def deploy_status() -> dict:
    log = load(DEPLOY_LOG, {"total": 0, "failures": 0, "history": []})
    wf  = get_workflow_status()
    return {
        "total_deploys":   log["total"],
        "failures":        log["failures"],
        "workflow_status": wf.get("status", "unknown"),
        "last_run":        wf.get("run_number"),
        "recent_deploys":  log["history"][-3:]
    }


if __name__ == "__main__":
    STATE_DIR.mkdir(exist_ok=True)
    print("=== SELF-DEPLOY ENGINE TEST ===\n")

    print("Workflow status:")
    wf = get_workflow_status()
    for k, v in wf.items():
        if k != "recent":
            print(f"  {k}: {v}")
    if wf.get("recent"):
        print("  Recent runs:")
        for r in wf["recent"]:
            print(f"    #{r['run_number']} {r['status']} / {r.get('conclusion','—')}")

    print()
    print("Deploy status:")
    print(json.dumps(deploy_status(), indent=2))
    print("\n=== SELF-DEPLOY ENGINE READY ===")
    print("Agent Zero can now push himself and wake up in the new version.")
