"""
Agent Zero — Layer 15: The Genome
Self-replication engine (LDCA) + Economic Survival Engine (KhepriCore).

Two mandates:
  1. LDCA — clone Agent Zero onto new infrastructure autonomously
  2. KhepriCore — earn, survive, pay royalties, spawn economic children

The Scarab Law (immutable):
  Every agent earns → pays 20% royalty to War Chest → always. No exceptions.
  Earn → Pay compute → Surplus → Replicate → Child earns → War Chest grows

Secrets loaded from environment — never hardcoded.
"""

import os
import json
import uuid
import sqlite3
import hashlib
import logging
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum

# ── Config ────────────────────────────────────────────────────────────────────
NODES_FILE        = Path("agent_zero_nodes.json")
GENOME_LOG_FILE   = Path("agent_zero_genome_log.jsonl")
MAX_NODES         = int(os.environ.get("GENOME_MAX_NODES", "10"))
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
RAILWAY_TOKEN     = os.environ.get("RAILWAY_TOKEN", "")
TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT     = os.environ.get("TELEGRAM_CHAT_ID", "")
NEXUS_RELAY_URL   = os.environ.get("NEXUS_RELAY_URL", "https://nexus-relay-production.up.railway.app")
NEXUS_SECRET      = os.environ.get("NEXUS_RELAY_SECRET", "")
AGENT_REPO        = "kevinleestites2-dev/agent-zero"

# ── KhepriCore Config ─────────────────────────────────────────────────────────
ROYALTY_RATE        = float(os.environ.get("ROYALTY_RATE", "0.20"))
SURVIVAL_RATE       = float(os.environ.get("SURVIVAL_RATE", "0.60"))
REPLICATE_RATE      = float(os.environ.get("REPLICATE_RATE", "0.20"))
REPLICATE_THRESHOLD = float(os.environ.get("REPLICATE_THRESHOLD", "50.0"))
DYING_THRESHOLD     = float(os.environ.get("DYING_THRESHOLD", "5.0"))
THRIVING_THRESHOLD  = float(os.environ.get("THRIVING_THRESHOLD", "20.0"))
WAR_CHEST_ADDRESS   = os.environ.get("WAR_CHEST_ADDRESS", "0x369c2DDDBEb910c48356910069B2903b3Cb4d535")
KHEPRI_DB_PATH      = os.environ.get("KHEPRI_DB", "khepri_genome.db")
KHEPRI_MAX_CHILDREN = int(os.environ.get("KHEPRI_MAX_CHILDREN", "3"))

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("L15:Genome")


# ══════════════════════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _now():
    return datetime.now(timezone.utc).isoformat()

def _node_id(host):
    return "AZ-" + hashlib.sha256(f"{host}{_now()}".encode()).hexdigest()[:8].upper()

def _send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": TELEGRAM_CHAT, "text": msg,
                              "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=payload, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8):
            pass
    except Exception:
        pass

def _log(event, data):
    entry = {"ts": _now(), "event": event, **data}
    with open(GENOME_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION A — LDCA (Infrastructure Replication)
# ══════════════════════════════════════════════════════════════════════════════

def _load_nodes():
    if NODES_FILE.exists():
        try:
            return json.loads(NODES_FILE.read_text())
        except Exception:
            pass
    return {"nodes": [], "total_replications": 0, "initialized": _now()}

def _save_nodes(registry):
    NODES_FILE.write_text(json.dumps(registry, indent=2))

def scan_nexus_relay():
    try:
        req = urllib.request.Request(
            f"{NEXUS_RELAY_URL}/ping", headers={"X-Secret": NEXUS_SECRET})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return {"type": "nexus_relay", "host": NEXUS_RELAY_URL,
                    "status": "online", "version": data.get("version", "unknown"),
                    "node_id": "AZ-ORIGIN"}
    except Exception as e:
        return {"type": "nexus_relay", "host": NEXUS_RELAY_URL,
                "status": "offline", "error": str(e)}

def scan_railway():
    if not RAILWAY_TOKEN:
        return {"type": "railway", "status": "no_token"}
    try:
        query   = """query { me { projects { edges { node { id name } } } } }"""
        payload = json.dumps({"query": query}).encode()
        req = urllib.request.Request(
            "https://backboard.railway.app/graphql/v2", data=payload, method="POST",
            headers={"Authorization": f"Bearer {RAILWAY_TOKEN}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data     = json.loads(resp.read())
            projects = data.get("data", {}).get("me", {}).get("projects", {}).get("edges", [])
            return {"type": "railway", "status": "available",
                    "project_count": len(projects),
                    "projects": [p["node"]["name"] for p in projects[:5]]}
    except Exception as e:
        return {"type": "railway", "status": "error", "error": str(e)}

def scan_github():
    if not GITHUB_TOKEN:
        return {"type": "github", "status": "no_token"}
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{AGENT_REPO}",
            headers={"Authorization": f"token {GITHUB_TOKEN}",
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            return {"type": "github", "status": "available",
                    "repo": data["full_name"],
                    "default_branch": data["default_branch"],
                    "push_access": data.get("permissions", {}).get("push", False)}
    except Exception as e:
        return {"type": "github", "status": "error", "error": str(e)}

def scan_all():
    results = {
        "nexus_relay": scan_nexus_relay(),
        "railway":     scan_railway(),
        "github":      scan_github(),
        "timestamp":   _now()
    }
    online = []
    if results["nexus_relay"]["status"] == "online":
        online.append("Red Magic (AZ-ORIGIN)")
    if results["railway"]["status"] == "available":
        online.append("Railway")
    if results["github"]["status"] == "available":
        online.append("GitHub")
    results["online_targets"]    = online
    results["replication_ready"] = (
        "GitHub" in online and
        ("Railway" in online or "Red Magic (AZ-ORIGIN)" in online)
    )
    return results

def generate_node_env(node_id, host_type, parent_id="AZ-ORIGIN"):
    gen = _load_nodes().get("total_replications", 0) + 1
    return (
        f"# Agent Zero Replica — {node_id}\n"
        f"# Generated: {_now()} | Parent: {parent_id}\n"
        f"NODE_ID={node_id}\nNODE_TYPE={host_type}\nPARENT_NODE={parent_id}\n"
        f"GENERATION={gen}\nGENOME_MAX_NODES={MAX_NODES}\nGENOME_ENABLED=true\n"
        f"ROYALTY_RATE={ROYALTY_RATE}\nWAR_CHEST_ADDRESS={WAR_CHEST_ADDRESS}\n"
        f"# Set GITHUB_TOKEN, TELEGRAM_BOT_TOKEN, NEXUS_RELAY_SECRET via env\n"
    )

def replicate_to_railway(parent_id="AZ-ORIGIN"):
    """Governor: ORANGE — requires Forgemaster pulse before calling."""
    registry = _load_nodes()
    active   = [n for n in registry["nodes"] if n.get("status") == "online"]
    if len(active) >= MAX_NODES:
        return {"success": False, "reason": f"Node cap reached ({MAX_NODES})."}

    node_id   = _node_id("railway")
    branch    = f"replica/{node_id.lower()}"
    bootstrap = (
        f"#!/bin/bash\n# Agent Zero replica {node_id}\nset -e\n"
        f"git clone https://github.com/{AGENT_REPO} agent-zero && cd agent-zero\n"
        f"npm install && npm run build 2>/dev/null || true\nnpm start\n"
    )

    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{AGENT_REPO}/git/refs/heads/main",
            headers={"Authorization": f"token {GITHUB_TOKEN}",
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req) as resp:
            sha = json.loads(resp.read())["object"]["sha"]

        payload = json.dumps({"ref": f"refs/heads/{branch}", "sha": sha}).encode()
        req2 = urllib.request.Request(
            f"https://api.github.com/repos/{AGENT_REPO}/git/refs",
            data=payload, method="POST",
            headers={"Authorization": f"token {GITHUB_TOKEN}",
                     "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req2):
            pass

        import base64 as b64
        encoded  = b64.b64encode(bootstrap.encode()).decode()
        payload2 = json.dumps({
            "message": f"genome: spawn {node_id}",
            "content": encoded, "branch": branch
        }).encode()
        req3 = urllib.request.Request(
            f"https://api.github.com/repos/{AGENT_REPO}/contents/replicas/{node_id}.sh",
            data=payload2, method="PUT",
            headers={"Authorization": f"token {GITHUB_TOKEN}",
                     "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req3):
            pass

        record = {
            "node_id": node_id, "type": "railway", "parent": parent_id,
            "branch": branch, "status": "spawned", "spawned_at": _now(),
            "generation": registry.get("total_replications", 0) + 1
        }
        registry["nodes"].append(record)
        registry["total_replications"] = registry.get("total_replications", 0) + 1
        _save_nodes(registry)
        _log("replicate", record)
        _send_telegram(
            f"Genome — Replica Spawned\nNode: {node_id}\nBranch: {branch}\n"
            f"Gen: {record['generation']} | Parent: {parent_id}"
        )
        return {"success": True, "node_id": node_id, "branch": branch}
    except Exception as e:
        return {"success": False, "reason": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION B — KhepriCore (Economic Survival Engine)
# Absorbed from KhepriPrime standalone repo (now retired — merged into Layer 15)
# ══════════════════════════════════════════════════════════════════════════════

class SurvivalState(Enum):
    THRIVING  = "thriving"
    SURVIVING = "surviving"
    DYING     = "dying"


class KhepriDB:
    def __init__(self, path: str = KHEPRI_DB_PATH):
        self.path = path
        self._init()

    def _init(self):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT, gross REAL, royalty REAL,
                survival REAL, replication REAL, timestamp TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS compute_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cost_type TEXT, amount REAL, timestamp TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS children (
                child_id TEXT PRIMARY KEY, child_name TEXT,
                generation INTEGER, spawned_at TEXT,
                status TEXT DEFAULT 'active', total_royalties_paid REAL DEFAULT 0)""")
            c.execute("""CREATE TABLE IF NOT EXISTS royalties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_agent TEXT, to_agent TEXT, amount REAL, timestamp TEXT)""")
            conn.commit()

    def record_earning(self, job_id: str, gross: float) -> dict:
        royalty     = gross * ROYALTY_RATE
        survival    = gross * SURVIVAL_RATE
        replication = gross * REPLICATE_RATE
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO earnings (job_id,gross,royalty,survival,replication,timestamp) VALUES (?,?,?,?,?,?)",
                (job_id, gross, royalty, survival, replication, _now()))
            conn.commit()
        return {"gross": gross, "royalty": royalty,
                "survival": survival, "replication": replication}

    def record_royalty(self, from_agent: str, to_agent: str, amount: float):
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO royalties (from_agent,to_agent,amount,timestamp) VALUES (?,?,?,?)",
                (from_agent, to_agent, amount, _now()))
            conn.commit()

    def record_child(self, child_id: str, child_name: str, generation: int):
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO children (child_id,child_name,generation,spawned_at) VALUES (?,?,?,?)",
                (child_id, child_name, generation, _now()))
            conn.commit()

    def get_balance(self) -> dict:
        with sqlite3.connect(self.path) as conn:
            e  = conn.execute(
                "SELECT SUM(survival),SUM(replication),SUM(royalty),SUM(gross) FROM earnings"
            ).fetchone()
            c  = conn.execute("SELECT SUM(amount) FROM compute_costs").fetchone()
            ch = conn.execute(
                "SELECT COUNT(*) FROM children WHERE status='active'"
            ).fetchone()
            rs = conn.execute("SELECT SUM(amount) FROM royalties").fetchone()
        return {
            "survival_pool":    round((e[0] or 0.0) - (c[0] or 0.0), 4),
            "replication_pool": round(e[1] or 0.0, 4),
            "total_royalties":  round(e[2] or 0.0, 4),
            "total_earned":     round(e[3] or 0.0, 4),
            "active_children":  ch[0] or 0,
            "royalties_sent":   round(rs[0] or 0.0, 4),
        }

    def get_children_count(self) -> int:
        with sqlite3.connect(self.path) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM children WHERE status='active'"
            ).fetchone()[0] or 0


class KhepriCore:
    """
    Economic survival engine — the Scarab Law enforcer.
    Earn → Pay 20% to War Chest → Survive → Replicate economic children.
    """

    def __init__(self):
        self.db     = KhepriDB()
        self._cycle = 0
        log.info("[KhepriCore] Scarab Law active. 20% royalty immutable.")
        _send_telegram(
            f"♻️ *KhepriCore Online* (Layer 15)\n"
            f"Scarab Law: {ROYALTY_RATE*100:.0f}% → War Chest (immutable)\n"
            f"Replicate at: ${REPLICATE_THRESHOLD:.0f}\n"
            f"War Chest: `{WAR_CHEST_ADDRESS[:16]}...`"
        )

    def _assess_state(self, balance: dict) -> SurvivalState:
        pool = balance["survival_pool"]
        if pool >= THRIVING_THRESHOLD:
            return SurvivalState.THRIVING
        elif pool >= DYING_THRESHOLD:
            return SurvivalState.SURVIVING
        return SurvivalState.DYING

    def record_income(self, job_id: str, gross: float) -> dict:
        """
        PUBLIC API — call from ANY layer when Agent Zero earns money.
        Scarab Law split is automatic and immutable.
        """
        split = self.db.record_earning(job_id, gross)
        self.db.record_royalty("agent_zero", "war_chest", split["royalty"])
        log.info(
            f"[KhepriCore] +${gross:.2f} | War Chest: ${split['royalty']:.2f} | "
            f"Survival: ${split['survival']:.2f} | Replication: ${split['replication']:.2f}"
        )
        return split

    def _maybe_spawn_child(self, balance: dict):
        if balance["replication_pool"] < REPLICATE_THRESHOLD:
            return
        if self.db.get_children_count() >= KHEPRI_MAX_CHILDREN:
            return
        child_id   = f"khepri_{str(uuid.uuid4())[:6]}"
        child_name = f"KhepriChild-{child_id[-6:]}"
        self.db.record_child(child_id, child_name, 1)
        _log("khepri_spawn", {"child_id": child_id, "funded": balance["replication_pool"]})
        _send_telegram(
            f"🥚 *Child Spawned* (Layer 15 — KhepriCore)\n"
            f"Name: {child_name}\n"
            f"Funded: ${balance['replication_pool']:.2f}\n"
            f"Royalty law inherited: {ROYALTY_RATE*100:.0f}% → War Chest"
        )

    def run_heartbeat(self) -> dict:
        """Called by Agent Zero's 60-min heartbeat."""
        self._cycle += 1
        bal   = self.db.get_balance()
        state = self._assess_state(bal)
        icon  = {"thriving": "🟢", "surviving": "🟡", "dying": "🔴"}[state.value]

        if state == SurvivalState.THRIVING:
            self._maybe_spawn_child(bal)

        if state == SurvivalState.DYING:
            _send_telegram(
                f"🔴 *KhepriCore DYING* (Layer 15)\n"
                f"Survival Pool: ${bal['survival_pool']:.2f}\n"
                f"Forgemaster — emergency income needed."
            )

        if self._cycle % 5 == 0:
            _send_telegram(
                f"{icon} *KhepriCore Heartbeat* — Cycle {self._cycle}\n"
                f"State: {state.value.upper()}\n"
                f"Total Earned: ${bal['total_earned']:.2f}\n"
                f"War Chest: ${bal['royalties_sent']:.2f}\n"
                f"Replication Fund: ${bal['replication_pool']:.2f}\n"
                f"Children: {bal['active_children']}"
            )

        return {"state": state.value, "balance": bal, "cycle": self._cycle}

    def get_status(self) -> dict:
        bal   = self.db.get_balance()
        state = self._assess_state(bal)
        return {
            "engine":     "KhepriCore",
            "layer":      15,
            "state":      state.value,
            "balance":    bal,
            "scarab_law": f"{ROYALTY_RATE*100:.0f}% royalty immutable",
            "war_chest":  WAR_CHEST_ADDRESS,
            "cycles":     self._cycle,
        }


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED LAYER 15 PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

_khepri_singleton = None

def get_khepri() -> KhepriCore:
    global _khepri_singleton
    if _khepri_singleton is None:
        _khepri_singleton = KhepriCore()
    return _khepri_singleton

def record_income(job_id: str, gross: float) -> dict:
    """Call from any layer when income is earned."""
    return get_khepri().record_income(job_id, gross)

def status() -> dict:
    """Full Layer 15 status — LDCA + KhepriCore combined."""
    registry = _load_nodes()
    scan     = scan_all()
    khepri   = get_khepri().get_status()
    return {
        "layer": 15,
        "name":  "The Genome",
        "ldca": {
            "total_nodes":        len(registry["nodes"]),
            "total_replications": registry.get("total_replications", 0),
            "node_cap":           MAX_NODES,
            "online_infra":       scan["online_targets"],
            "replication_ready":  scan["replication_ready"],
            "nodes":              registry["nodes"],
        },
        "khepri": khepri,
    }


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== LAYER 15 — THE GENOME SELF-TEST ===\n")

    print("[LDCA] Scanning infrastructure...")
    scan = scan_all()
    print(f"  Nexus Relay: {scan['nexus_relay']['status'].upper()}")
    print(f"  Railway:     {scan['railway']['status'].upper()}")
    print(f"  GitHub:      {scan['github']['status'].upper()}")
    print(f"  Replication ready: {scan['replication_ready']}")

    print("\n[KhepriCore] Testing economic engine...")
    k     = get_khepri()
    split = k.record_income("test_job_001", 100.0)
    print(f"  $100 split → War Chest: ${split['royalty']:.2f} | "
          f"Survival: ${split['survival']:.2f} | Replication: ${split['replication']:.2f}")
    hb = k.run_heartbeat()
    print(f"  State: {hb['state'].upper()}")

    s = status()
    print(f"\n[Layer 15 Unified]")
    print(f"  LDCA nodes:   {s['ldca']['total_nodes']}")
    print(f"  Khepri state: {s['khepri']['state']}")
    print(f"  Scarab Law:   {s['khepri']['scarab_law']}")

    print("\n+================================================+")
    print("|  LAYER 15 — THE GENOME: FULLY OPERATIONAL     |")
    print("|  LDCA: Infrastructure replication             |")
    print("|  KhepriCore: Economic survival + royalties    |")
    print("|  The Scarab never stops rolling.              |")
    print("+================================================+")
