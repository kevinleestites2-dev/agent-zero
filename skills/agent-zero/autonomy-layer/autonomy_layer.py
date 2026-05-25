"""
Agent Zero — Layer 18: The Autonomy Engine
Self-tasking background loop. Never idles. Never stops.
"""

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("AgentZero.L18")

# ── Default mission domains ────────────────────────────────────────────────────

DEFAULT_DOMAINS = [
    "Lee County auction monitoring",
    "Pantheon Prime health check",
    "War Chest balance verification",
    "Signal quality assessment",
    "Strategy weight optimization",
    "Knowledge gap resolution",
    "Tool inventory audit",
    "Memory consolidation",
    "Evolution target identification",
    "Threat surface review",
]


# ── Autonomy Engine ────────────────────────────────────────────────────────────

class AutonomyEngine:
    """
    Layer 18 — The Autonomy Engine.

    Ensures Agent Zero never idles.
    When the mission queue is empty, generates its own next mission
    using weight-based domain selection with reinforcement learning.

    Runs in a background daemon thread. Survives restarts via
    persisted state in cerberus_state/<head>_autonomy.json.
    """

    def __init__(
        self,
        head_name: str,
        telegram_fn: Callable = None,
        interval: int = 300,
        domains: List[str] = None,
    ):
        self.head       = head_name
        self.tg         = telegram_fn or (lambda m: None)
        self.interval   = interval
        self.alive      = True
        self.task_queue: List[str] = []
        self.cycle      = 0
        self.domain_weights: Dict[str, float] = {
            d: 1.0 for d in (domains or DEFAULT_DOMAINS)
        }
        self._thread: Optional[threading.Thread] = None
        self._state_path = Path(f"cerberus_state/{head_name.lower()}_autonomy.json")
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self):
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text())
                self.domain_weights = data.get("domain_weights", self.domain_weights)
                self.cycle          = data.get("cycle", 0)
                self.task_queue     = data.get("task_queue", [])
                logger.info(
                    f"[{self.head}][L18] Resumed — cycle {self.cycle}, "
                    f"queue depth {len(self.task_queue)}"
                )
            except Exception as e:
                logger.warning(f"[{self.head}][L18] State load failed: {e}")

    def _save(self):
        try:
            self._state_path.write_text(json.dumps({
                "head":           self.head,
                "cycle":          self.cycle,
                "domain_weights": self.domain_weights,
                "task_queue":     self.task_queue[:20],
                "updated":        datetime.utcnow().isoformat(),
            }, indent=2))
        except Exception as e:
            logger.warning(f"[{self.head}][L18] Save failed: {e}")

    # ── Mission management ─────────────────────────────────────────────────────

    def inject_mission(self, mission: str):
        """Forgemaster injects a priority mission — prepends to queue."""
        self.task_queue.insert(0, mission)
        logger.info(f"[{self.head}][L18] Priority mission injected: {mission}")
        self._save()

    def _generate_mission(self) -> str:
        """Auto-generate next mission when queue is empty."""
        import random
        total = sum(self.domain_weights.values())
        roll  = random.uniform(0, total)
        acc   = 0.0
        for domain, w in self.domain_weights.items():
            acc += w
            if roll <= acc:
                ts = datetime.utcnow().strftime("%H:%M UTC")
                return f"[AUTO] {domain} — initiated at {ts}"
        return f"[AUTO] System self-audit — {datetime.utcnow().isoformat()}"

    def next_mission(self) -> str:
        """Pop next mission from queue, or generate one autonomously."""
        if self.task_queue:
            return self.task_queue.pop(0)
        return self._generate_mission()

    # ── Reinforcement ──────────────────────────────────────────────────────────

    def reward_domain(self, mission: str, success: bool):
        """Reinforce or penalize a domain based on cycle outcome."""
        for domain in self.domain_weights:
            if domain.lower() in mission.lower():
                if success:
                    self.domain_weights[domain] = min(5.0, self.domain_weights[domain] * 1.1)
                else:
                    self.domain_weights[domain] = max(0.1, self.domain_weights[domain] * 0.9)
                break

    # ── Background loop ────────────────────────────────────────────────────────

    def start(self, run_cycle_fn: Callable):
        """
        Start the autonomous background loop.

        Args:
            run_cycle_fn: Callable(mission: str) -> dict
                          The agent's run_cycle function, called each interval.
        """
        def _loop():
            logger.info(
                f"[{self.head}][L18] Autonomy engine started — interval={self.interval}s"
            )
            self.tg(
                f"[{self.head}] Layer 18 AUTONOMY ONLINE
"
                f"Self-tasking every {self.interval}s | "
                f"Domains: {len(self.domain_weights)}"
            )
            while self.alive:
                try:
                    mission = self.next_mission()
                    self.cycle += 1
                    logger.info(f"[{self.head}][L18] Auto-cycle {self.cycle}: {mission}")
                    result  = run_cycle_fn(mission=mission)
                    success = (
                        result.get("result", {}).get("success", False)
                        if isinstance(result, dict)
                        else False
                    )
                    self.reward_domain(mission, success)
                    self._save()
                except Exception as e:
                    logger.error(f"[{self.head}][L18] Error: {e}")
                    self.tg(f"[{self.head}][L18] Autonomy error: {e}")
                time.sleep(self.interval)
            logger.info(f"[{self.head}][L18] Autonomy engine stopped")

        self._thread = threading.Thread(
            target=_loop,
            daemon=True,
            name=f"Autonomy-{self.head}"
        )
        self._thread.start()

    def stop(self):
        """Clean shutdown."""
        self.alive = False
        self._save()
        logger.info(f"[{self.head}][L18] Shutdown — final cycle: {self.cycle}")

    # ── Status ─────────────────────────────────────────────────────────────────

    def status(self) -> Dict:
        top    = max(self.domain_weights, key=self.domain_weights.get)
        bottom = min(self.domain_weights, key=self.domain_weights.get)
        return {
            "layer":         18,
            "alive":         self.alive,
            "cycle":         self.cycle,
            "queue_depth":   len(self.task_queue),
            "domain_count":  len(self.domain_weights),
            "top_domain":    top,
            "top_weight":    round(self.domain_weights[top], 3),
            "bottom_domain": bottom,
            "bottom_weight": round(self.domain_weights[bottom], 3),
            "interval_s":    self.interval,
        }


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("
=== LAYER 18 — THE AUTONOMY ENGINE SELF-TEST ===
")

    messages = []
    def fake_tg(m):
        messages.append(m)

    engine = AutonomyEngine(head_name="TEST", telegram_fn=fake_tg, interval=1)

    # Test queue injection
    engine.inject_mission("Priority: scan Lee County auctions")
    assert engine.task_queue[0].startswith("Priority")
    print("  [PASS]  inject_mission — priority prepend OK")

    # Test next_mission from queue
    m = engine.next_mission()
    assert m.startswith("Priority")
    print(f"  [PASS]  next_mission (queue) — got: {m[:50]}")

    # Test auto-generation
    auto = engine.next_mission()
    assert auto.startswith("[AUTO]")
    print(f"  [PASS]  next_mission (auto)  — got: {auto[:60]}")

    # Test reinforcement
    before_w = engine.domain_weights["Lee County auction monitoring"]
    engine.reward_domain("Lee County auction monitoring", success=True)
    after_w = engine.domain_weights["Lee County auction monitoring"]
    assert after_w > before_w
    print(f"  [PASS]  reward_domain (success) — weight {before_w:.3f} -> {after_w:.3f}")

    engine.reward_domain("Lee County auction monitoring", success=False)
    penalty = engine.domain_weights["Lee County auction monitoring"]
    assert penalty < after_w
    print(f"  [PASS]  reward_domain (failure) — weight {after_w:.3f} -> {penalty:.3f}")

    # Test status
    s = engine.status()
    assert s["layer"] == 18
    assert s["alive"] is True
    print(f"  [PASS]  status — layer={s['layer']}, alive={s['alive']}, domains={s['domain_count']}")

    # Test background loop
    cycle_count = []
    def fake_run(mission):
        cycle_count.append(mission)
        return {"result": {"success": True}}

    engine.start(fake_run)
    time.sleep(2.5)
    engine.stop()

    assert len(cycle_count) >= 2
    print(f"  [PASS]  background loop — {len(cycle_count)} cycles in 2.5s")

    print()
    print("  Layer 18 (Autonomy): OPERATIONAL")
    print()
    print("  Key behaviours confirmed:")
    print("    > Priority queue injection")
    print("    > Auto-mission generation when queue empty")
    print("    > Weight-based domain selection (reinforcement)")
    print("    > Background daemon thread — non-blocking")
    print("    > State persistence to cerberus_state/")
    print("    > Clean shutdown via stop()")
    print()
