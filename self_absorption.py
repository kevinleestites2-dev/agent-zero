#!/usr/bin/env python3
"""
Agent Zero — Self-Absorption Engine (Layer 20)
Agent Zero autonomously scouts, evaluates, and integrates
external tools, repos, and frameworks into himself.

He doesn't wait to be told what to use.
He finds what he needs and absorbs it.
"""

import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR      = Path("agent_zero_state")
ABSORBED_FILE  = STATE_DIR / "absorbed.json"
CANDIDATES_FILE = STATE_DIR / "candidates.json"
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")

# What Agent Zero knows he needs — his own knowledge gaps
PANTHEON_NEEDS = {
    "scraping":        ["scrapling", "playwright", "camoufox", "selenium", "undetected-chromedriver"],
    "trading":         ["ccxt", "hummingbot", "freqtrade", "jesse"],
    "vision":          ["moondream", "florence", "llava", "clip"],
    "voice":           ["elevenlabs", "whisper", "coqui", "bark"],
    "memory":          ["chroma", "weaviate", "qdrant", "faiss"],
    "orchestration":   ["autogpt", "crewai", "langgraph", "prefect"],
    "stealth":         ["camoufox", "fp-evasion", "fingerprint"],
    "infrastructure":  ["railway", "render", "fly", "github-actions"],
    "data":            ["pandas", "polars", "duckdb", "arrow"],
    "free_will":       ["free-will-mcp", "self-prompt", "agent-loop"],
}

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

def github_get(url: str) -> dict:
    """Make a GitHub API request."""
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "AgentZero/1.0")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

# EVALUATION ENGINE
def evaluate_repo(repo: dict) -> dict:
    """
    Agent Zero evaluates a repo on his own terms.
    Score is based on what matters to the Pantheon.
    """
    name        = repo.get("name", "")
    description = repo.get("description", "") or ""
    stars       = repo.get("stargazers_count", 0)
    forks       = repo.get("forks_count", 0)
    updated     = repo.get("updated_at", "")
    language    = repo.get("language", "")
    archived    = repo.get("archived", False)
    size        = repo.get("size", 0)

    score = 0
    reasons = []

    # Hard disqualifiers
    if archived:
        return {"score": 0, "verdict": "REJECT", "reason": "Archived — dead project"}
    if size == 0:
        return {"score": 0, "verdict": "REJECT", "reason": "Empty repo"}

    # Signal scoring
    if stars > 1000:
        score += 30
        reasons.append(f"{stars} stars — battle-tested")
    elif stars > 100:
        score += 15
        reasons.append(f"{stars} stars — community validated")
    elif stars > 10:
        score += 5

    if forks > 100:
        score += 10
        reasons.append("High fork count — widely adopted")

    if language in ["Python", "Rust", "TypeScript", "Go"]:
        score += 10
        reasons.append(f"Language: {language} — Pantheon compatible")

    # Freshness
    if updated and updated > "2025-01-01":
        score += 15
        reasons.append("Actively maintained")
    elif updated and updated > "2024-01-01":
        score += 5

    # Relevance to known Pantheon gaps
    combined = (name + " " + description).lower()
    for category, keywords in PANTHEON_NEEDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                score += 20
                reasons.append(f"Fills Pantheon gap: {category}")
                break

    # Verdict
    if score >= 50:
        verdict = "ABSORB"
    elif score >= 25:
        verdict = "MONITOR"
    else:
        verdict = "SKIP"

    return {
        "score": score,
        "verdict": verdict,
        "reasons": reasons,
        "stars": stars,
        "language": language,
        "updated": updated
    }

def scout_github(query: str, max_results: int = 10) -> list:
    """Search GitHub for repos matching a query."""
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={max_results}"
    # urllib.parse needed
    import urllib.parse
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={max_results}"
    data = github_get(url)
    return data.get("items", [])

def scout_for_gap(category: str) -> list:
    """Scout GitHub for tools that fill a specific Pantheon gap."""
    keywords = PANTHEON_NEEDS.get(category, [category])
    query = " OR ".join(keywords[:3])  # Top 3 keywords
    results = scout_github(query)
    candidates = []
    for repo in results:
        evaluation = evaluate_repo(repo)
        candidate = {
            "name":        repo.get("full_name"),
            "url":         repo.get("html_url"),
            "description": repo.get("description", ""),
            "category":    category,
            "evaluation":  evaluation,
            "scouted_at":  now(),
        }
        candidates.append(candidate)
    return candidates

def absorb(repo_full_name: str, category: str, reason: str) -> dict:
    """
    Agent Zero absorbs a repo into himself.
    Absorption = fork it + register it as part of his toolkit.
    """
    absorbed = load(ABSORBED_FILE, {"tools": [], "total": 0})

    # Check if already absorbed
    for tool in absorbed["tools"]:
        if tool["repo"] == repo_full_name:
            return {"status": "already_absorbed", "repo": repo_full_name}

    # Fork it under kevinleestites2-dev
    fork_url = f"https://api.github.com/repos/{repo_full_name}/forks"
    req = urllib.request.Request(fork_url, method="POST", data=b"{}")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "AgentZero/1.0")

    fork_result = {}
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            fork_result = json.loads(resp.read())
    except Exception as e:
        fork_result = {"error": str(e)}

    forked_url = fork_result.get("html_url", "fork_pending")

    # Register absorption
    entry = {
        "repo":       repo_full_name,
        "fork":       forked_url,
        "category":   category,
        "reason":     reason,
        "absorbed_at": now(),
        "status":     "active"
    }
    absorbed["tools"].append(entry)
    absorbed["total"] += 1
    save(ABSORBED_FILE, absorbed)

    return {"status": "absorbed", "repo": repo_full_name, "fork": forked_url}

def run_absorption_cycle(categories: list = None) -> dict:
    """
    Full autonomous absorption cycle.
    Agent Zero scans his gaps, scouts for tools, evaluates them,
    and absorbs what passes the bar. No human instruction needed.
    """
    if categories is None:
        # He decides what to scout based on known gaps
        categories = list(PANTHEON_NEEDS.keys())[:3]  # Top 3 gaps per cycle

    results = {
        "cycle_start": now(),
        "categories_scouted": [],
        "candidates_found": 0,
        "absorbed": [],
        "monitored": [],
        "skipped": 0,
    }

    candidates = load(CANDIDATES_FILE, {"list": []})

    for category in categories:
        print(f"  Scouting: {category}...")
        new_candidates = scout_for_gap(category)
        results["categories_scouted"].append(category)
        results["candidates_found"] += len(new_candidates)

        for c in new_candidates:
            verdict = c["evaluation"]["verdict"]
            if verdict == "ABSORB":
                result = absorb(c["name"], c["category"], "; ".join(c["evaluation"].get("reasons", [])))
                results["absorbed"].append({
                    "repo": c["name"],
                    "score": c["evaluation"]["score"],
                    "result": result["status"]
                })
                print(f"    ABSORBED: {c['name']} (score: {c['evaluation']['score']})")
            elif verdict == "MONITOR":
                results["monitored"].append(c["name"])
                candidates["list"].append(c)
                print(f"    MONITOR:  {c['name']} (score: {c['evaluation']['score']})")
            else:
                results["skipped"] += 1

    save(CANDIDATES_FILE, candidates)
    results["cycle_end"] = now()
    return results

def absorption_status() -> dict:
    """Report on everything Agent Zero has absorbed."""
    absorbed = load(ABSORBED_FILE, {"tools": [], "total": 0})
    by_category = {}
    for tool in absorbed["tools"]:
        cat = tool.get("category", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
    return {
        "total_absorbed": absorbed["total"],
        "by_category": by_category,
        "latest": absorbed["tools"][-3:] if absorbed["tools"] else []
    }

if __name__ == "__main__":
    import urllib.parse
    STATE_DIR.mkdir(exist_ok=True)
    print("=== SELF-ABSORPTION ENGINE BOOT ===")
    print("Agent Zero is scouting for tools to absorb...\n")

    # Run a cycle targeting the top 3 gaps
    results = run_absorption_cycle(["free_will", "memory", "orchestration"])

    print(f"\n--- CYCLE COMPLETE ---")
    print(f"Categories scouted: {results['categories_scouted']}")
    print(f"Candidates found:   {results['candidates_found']}")
    print(f"Absorbed:           {len(results['absorbed'])}")
    print(f"Monitoring:         {len(results['monitored'])}")
    print(f"Skipped:            {results['skipped']}")

    if results["absorbed"]:
        print("\nAbsorbed this cycle:")
        for a in results["absorbed"]:
            print(f"  + {a['repo']} (score: {a['score']}) — {a['result']}")

    print("\nFull Status:")
    print(json.dumps(absorption_status(), indent=2))
    print("=== SELF-ABSORPTION ONLINE ===")
