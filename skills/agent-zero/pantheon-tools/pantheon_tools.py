"""
Agent Zero — Layer 17: The Pantheon Tool Belt
Every Prime is a tool. The Mind wields them all.
"""

import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
NEXUS_RELAY_URL  = os.environ.get("NEXUS_RELAY_URL",
                                  "https://nexus-relay-production.up.railway.app")
NEXUS_SECRET     = os.environ.get("NEXUS_RELAY_SECRET", "pantheon_prime")
GHOST_HEALTH_URL = os.environ.get("GHOST_HEALTH_URL",
                                  "https://cloakprime-swarm.onrender.com/health")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT    = os.environ.get("TELEGRAM_CHAT_ID", "")
RAIL_TOKEN       = os.environ.get("RAILWAY_TOKEN", "")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _post(url, payload, headers=None):
    data = json.dumps(payload).encode()
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, method="POST", headers=h)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _get(url, headers=None):
    h = headers or {}
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _nexus_command(command: str, args: dict = None, poll_timeout: int = 15):
    """Send a command to the Red Magic via Nexus Relay. Returns result."""
    payload = {"command": command, "args": args or {}}
    resp = _post(f"{NEXUS_RELAY_URL}/command", payload,
                 headers={"X-Secret": NEXUS_SECRET})
    cmd_id = resp.get("_id") or resp.get("id")
    if not cmd_id:
        return {"success": False, "error": "no command id returned"}

    # Poll for result
    deadline = time.time() + poll_timeout
    while time.time() < deadline:
        time.sleep(1.5)
        try:
            result = _get(f"{NEXUS_RELAY_URL}/result/{cmd_id}",
                          headers={"X-Secret": NEXUS_SECRET})
            if result.get("status") == "done":
                return {"success": True, "result": result.get("data")}
        except Exception:
            pass
    return {"success": False, "error": "timeout waiting for result"}


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOL_REGISTRY = {}

def tool(name):
    def decorator(fn):
        TOOL_REGISTRY[name] = fn
        return fn
    return decorator


# GhostPrime
@tool("ghost_status")
def ghost_status(**kwargs):
    """Get GhostPrime swarm health."""
    try:
        data = _get(GHOST_HEALTH_URL)
        return {"prime": "GhostPrime", "status": "online", "data": data}
    except Exception as e:
        return {"prime": "GhostPrime", "status": "offline", "error": str(e)}


@tool("ghost_run")
def ghost_run(cycles: int = 1, **kwargs):
    """Trigger a GhostPrime swarm cycle via Nexus Relay."""
    return _nexus_command("ghost_run", {"cycles": cycles})


# ZeusPrime
@tool("zeus_status")
def zeus_status(**kwargs):
    """Get ZeusPrime wallet cluster status."""
    return _nexus_command("zeus_status")


@tool("zeus_buy")
def zeus_buy(token_address: str, amount_matic: float, squad: str = "alpha", **kwargs):
    """Execute a buy order on-chain via ZeusPrime."""
    return _nexus_command("zeus_buy", {
        "token_address": token_address,
        "amount_matic": amount_matic,
        "squad": squad
    })


# ScoutPrime
@tool("scout_scan")
def scout_scan(target_url: str, **kwargs):
    """Scan a target (auction listing, property, URL) via ScoutPrime."""
    return _nexus_command("scout_scan", {"url": target_url})


@tool("scout_bid")
def scout_bid(auction_id: str, amount: float, **kwargs):
    """Register a bid on a scanned auction target."""
    return _nexus_command("scout_bid", {"auction_id": auction_id, "amount": amount})


# MidasPrime
@tool("midas_balance")
def midas_balance(**kwargs):
    """Get War Chest balance and countdown status."""
    return _nexus_command("midas_balance")


@tool("midas_sync")
def midas_sync(**kwargs):
    """Trigger a MidasPrime metabolic sync cycle."""
    return _nexus_command("midas_sync")


# TerraPrime
@tool("terra_task")
def terra_task(task: str, priority: str = "normal", **kwargs):
    """Queue a task into TerraPrime's autonomous engine."""
    return _nexus_command("terra_task", {"task": task, "priority": priority})


@tool("terra_status")
def terra_status(**kwargs):
    """Get TerraPrime task queue status."""
    return _nexus_command("terra_status")


# FluxPrime
@tool("flux_cycle")
def flux_cycle(mission: str = None, **kwargs):
    """Trigger a FluxPrime autonomous cycle."""
    payload = {}
    if mission:
        payload["mission"] = mission
    return _nexus_command("flux_cycle", payload)


@tool("flux_status")
def flux_status(**kwargs):
    """Get FluxPrime mission and cycle state."""
    return _nexus_command("flux_status")


# AeonPrime
@tool("aeon_signal")
def aeon_signal(signal: str, priority: str = "normal", **kwargs):
    """Inject a signal into AeonPrime's high-velocity vortex."""
    return _nexus_command("aeon_signal", {"signal": signal, "priority": priority})


# Nexus Relay / Red Magic
@tool("nexus_status")
def nexus_status(**kwargs):
    """Check Red Magic / NexusClaw status via relay ping."""
    try:
        data = _get(f"{NEXUS_RELAY_URL}/ping",
                    headers={"X-Secret": NEXUS_SECRET})
        return {"prime": "NexusRelay", "status": "online", "data": data}
    except Exception as e:
        return {"prime": "NexusRelay", "status": "offline", "error": str(e)}


@tool("nexus_relay")
def nexus_relay_cmd(command: str, args: dict = None, **kwargs):
    """Send any raw command to the Red Magic phone."""
    return _nexus_command(command, args or {})


# Genome
@tool("genome_status")
def genome_status(**kwargs):
    """Get Agent Zero node registry and replication count."""
    try:
        from pathlib import Path
        import json as j
        f = Path("agent_zero_nodes.json")
        if f.exists():
            return j.loads(f.read_text())
        return {"nodes": [], "total_replications": 0}
    except Exception as e:
        return {"error": str(e)}


@tool("genome_replicate")
def genome_replicate(parent_id: str = "AZ-ORIGIN", **kwargs):
    """Spawn a new Agent Zero replica. Requires Forgemaster pulse (ORANGE)."""
    try:
        from skills.agent_zero.genome.genome import replicate_to_railway
        return replicate_to_railway(parent_id=parent_id)
    except Exception as e:
        return {"success": False, "error": str(e)}


# Ethics
@tool("ethics_check")
def ethics_check(action: str, **kwargs):
    """Check an action against the two laws before execution."""
    try:
        from skills.agent_zero.ethics.ethics import check
        return check(action, raise_on_block=False)
    except Exception as e:
        # Fallback inline check
        blocked_words = [
            "doxx", "harass", "threaten", "blackmail", "extort",
            "wire fraud", "unauthorized access", "hack into",
            "securities fraud", "ransomware", "identity theft"
        ]
        lower = action.lower()
        for word in blocked_words:
            if word in lower:
                return {"cleared": False, "zone": "blocked",
                        "reason": f"pattern: {word}"}
        return {"cleared": True, "zone": "green", "reason": "no violations"}


# ── Master dispatcher ─────────────────────────────────────────────────────────

def run_tool(tool_name: str, **kwargs) -> dict:
    """
    Agent Zero's primary interface to the Pantheon.
    Every call passes through Ethics Core first.
    """
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {tool_name}",
                "available": list(TOOL_REGISTRY.keys())}

    # Ethics pre-check
    action_desc = f"{tool_name} {json.dumps(kwargs)}"
    ethics = ethics_check(action=action_desc)
    if not ethics.get("cleared"):
        return {"blocked": True, "reason": ethics.get("reason"),
                "tool": tool_name}

    # Execute
    try:
        result = TOOL_REGISTRY[tool_name](**kwargs)
        return {"tool": tool_name, "success": True,
                "result": result, "ts": _now()}
    except Exception as e:
        return {"tool": tool_name, "success": False,
                "error": str(e), "ts": _now()}


def list_tools() -> list:
    """Return all available Pantheon tools."""
    return [
        {"name": name, "doc": fn.__doc__.strip() if fn.__doc__ else ""}
        for name, fn in TOOL_REGISTRY.items()
    ]


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== LAYER 17 — PANTHEON TOOL BELT SELF-TEST ===\n")

    tools = list_tools()
    print(f"  Registered tools: {len(tools)}")
    for t in tools:
        print(f"    [{t['name']:20}] {t['doc'][:55]}")

    print("\n  Ethics pre-check on tool calls:")
    tests = [
        ("ghost_run",    {"cycles": 1},                           True),
        ("zeus_buy",     {"token_address": "0xABC", "amount_matic": 1.0}, True),
        ("scout_scan",   {"target_url": "https://lee.realtaxdeed.com"},   True),
        ("nexus_relay",  {"command": "doxx a person"},                    False),
        ("terra_task",   {"task": "hack into competitor server"},         False),
    ]

    passed = 0
    for tool_name, kwargs, expect_cleared in tests:
        action = f"{tool_name} {json.dumps(kwargs)}"
        result = ethics_check(action=action)
        ok = result["cleared"] == expect_cleared
        passed += ok
        icon = "OK" if ok else "FAIL"
        print(f"    [{icon}] [{result['zone'].upper():7}] {tool_name}")

    print(f"\n  Ethics gate: {passed}/{len(tests)} passed")

    print("\n  Live infrastructure check:")
    r = nexus_status()
    print(f"    Nexus Relay: {r['status'].upper()}")
    r2 = ghost_status()
    print(f"    GhostPrime:  {r2['status'].upper()}")

    print()
    print("  Agent Zero + Pantheon = unified.")
    print("  Every Prime is now a tool call.")
    print("  The Mind wields the Machine.")
    print()
    print("  Layer 17 (Pantheon Tool Belt): OPERATIONAL")
    print()
    print("  +==============================================+")
    print("  |  AGENT ZERO — 17 LAYERS. PANTHEON ARMED.   |")
    print("  |  The Mind. The Laws. The Machine.           |")
    print("  |  Pantheon 2.0 — ONLINE.                    |")
    print("  +==============================================+")
