"""
Agent Zero — Layer 7: Feedback Loop
Source: safla-v2 (kevinleestites2-dev/safla-v2)

SAFLA = Self-Adaptive Feedback Loop Algorithm
The neural spine of Agent Zero's evolution.

After every cycle, SAFLA:
1. reflect()    — scores the cycle outcome (0.0 to 1.0)
2. rebalance()  — updates entropy + regime state
3. signal()     — tells Layer 6 (T2) which expert to reinforce
4. persist()    — saves weights/memory to disk

Regime states: EXPLORE | EXPLOIT | CONSOLIDATE | HIBERNATE | ESCALATE
The regime drives how aggressively the adaptation layer rewrites itself.
"""

import json, time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


REGIMES = {
    "EXPLORE":      {"entropy_range": (0.0, 0.30), "lr_multiplier": 1.5, "risk": "high"},
    "EXPLOIT":      {"entropy_range": (0.30, 0.60), "lr_multiplier": 1.0, "risk": "medium"},
    "CONSOLIDATE":  {"entropy_range": (0.60, 0.75), "lr_multiplier": 0.5, "risk": "low"},
    "HIBERNATE":    {"entropy_range": (0.75, 1.00), "lr_multiplier": 0.1, "risk": "none"},
    "ESCALATE":     {"entropy_range": None, "lr_multiplier": 2.0, "risk": "critical"},
}


class SAFLACore:
    """
    Layer 7 — The Feedback Spine.
    Observes every cycle, scores it, updates regime, signals adaptation.
    """

    STATE_FILE = "agent_zero_safla_state.json"

    def __init__(self, project_id: str = "agent_zero"):
        self.project_id = project_id
        self.state = self._load_state()
        self.cycle_history: list = []

    def _load_state(self) -> dict:
        p = Path(self.STATE_FILE)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return {
            "entropy": 0.0,
            "regime": "EXPLORE",
            "total_cycles": 0,
            "last_reflection": None,
            "best_mode": None,
            "best_score": 0.0
        }

    def _save_state(self):
        Path(self.STATE_FILE).write_text(json.dumps(self.state, indent=2))

    def reflect(self, cycle_data: dict) -> dict:
        """
        Score a completed cycle.
        cycle_data keys: intent, route, lead_mode, outcome (success|failure|partial)
        Returns: { score, entropy_delta, new_regime, feedback_signal }
        """
        outcome = cycle_data.get("outcome", "partial")
        score_map = {"success": 1.0, "partial": 0.6, "failure": 0.1}
        score = score_map.get(outcome, 0.5)

        # Entropy: rises on failures, falls on successes
        entropy_delta = -0.05 if score > 0.7 else 0.08 if score < 0.3 else 0.01
        new_entropy = max(0.0, min(1.0, self.state["entropy"] + entropy_delta))

        # Regime selection
        new_regime = "EXPLOIT"
        for regime, params in REGIMES.items():
            if params["entropy_range"] and params["entropy_range"][0] <= new_entropy < params["entropy_range"][1]:
                new_regime = regime
                break

        # Update state
        self.state["entropy"] = round(new_entropy, 4)
        self.state["regime"] = new_regime
        self.state["total_cycles"] += 1
        self.state["last_reflection"] = datetime.now().isoformat()

        if score > self.state.get("best_score", 0):
            self.state["best_mode"] = cycle_data.get("lead_mode")
            self.state["best_score"] = score

        self._save_state()

        reflection = {
            "cycle": self.state["total_cycles"],
            "score": score,
            "entropy": new_entropy,
            "entropy_delta": entropy_delta,
            "regime": new_regime,
            "feedback_signal": {
                "lead_mode": cycle_data.get("lead_mode"),
                "outcome_score": score,
                "lr_multiplier": REGIMES[new_regime]["lr_multiplier"]
            }
        }
        self.cycle_history.append(reflection)
        return reflection

    def status(self) -> str:
        return (
            f"SAFLA [{self.project_id}] | "
            f"Regime: {self.state['regime']} | "
            f"Entropy: {self.state['entropy']:.3f} | "
            f"Cycles: {self.state['total_cycles']} | "
            f"Best mode: {self.state.get('best_mode', 'none')} "
            f"({self.state.get('best_score', 0):.2f})"
        )

    def rebalance(self, adaptation_layer) -> dict:
        """
        Full cycle: reflect on last event, then signal T2 to adapt.
        Requires last cycle_data to have been stored.
        """
        if not self.cycle_history:
            return {"status": "no cycles yet"}
        last = self.cycle_history[-1]
        feedback = last["feedback_signal"]
        adaptation_layer.feedback(
            lead_mode=feedback["lead_mode"],
            outcome_score=feedback["outcome_score"]
        )
        return {"rebalanced": True, "regime": self.state["regime"],
                "entropy": self.state["entropy"]}


if __name__ == "__main__":
    safla = SAFLACore("agent_zero")
    print("Initial:", safla.status())

    # Simulate 3 cycles
    cycles = [
        {"intent": "news", "route": "layer2_perception", "lead_mode": "analyst", "outcome": "success"},
        {"intent": "memory", "route": "layer5_cognition", "lead_mode": "synthesizer", "outcome": "partial"},
        {"intent": "evolution", "route": "layer8_evolution", "lead_mode": "executor", "outcome": "success"},
    ]
    for c in cycles:
        r = safla.reflect(c)
        print(f"Cycle {r['cycle']}: score={r['score']} | regime={r['regime']} | entropy={r['entropy']:.3f}")

    print("
Final:", safla.status())
