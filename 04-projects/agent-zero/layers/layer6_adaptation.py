"""
Agent Zero — Layer 6: Adaptation
Source: Transformer-Squared (kevinleestites2-dev/Transformer-Squared)
Paper: https://arxiv.org/pdf/2501.06252

The T2 (Transformer^2) pattern:
- First pass:  each specialist agent processes the task independently
- Second pass: agents COLLABORATE, seeing each other's outputs
- Third pass:  ADAPTATION — each agent updates its own weights based on outcome

For Agent Zero, "experts" are named cognitive modes:
  Analyst | Strategist | Synthesizer | Critic | Executor

Each mode has a weight vector. After every cycle, SAFLA feedback
updates which modes performed best. The best-performing mode gets
higher weight next time the same signal pattern appears.
This is how Agent Zero gets smarter without retraining.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


EXPERT_MODES = ["analyst", "strategist", "synthesizer", "critic", "executor"]


class ExpertVector:
    """A single cognitive mode — one "head" in the ensemble."""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.history: List[dict] = []

    def process(self, task: str, context: dict) -> dict:
        """Each mode interprets the task through its own lens."""
        lenses = {
            "analyst":     "Break down the task into components. What are the facts?",
            "strategist":  "What is the optimal path forward? What are the tradeoffs?",
            "synthesizer": "Combine all available information into a coherent whole.",
            "critic":      "What could go wrong? What is missing? Challenge the plan.",
            "executor":    "What is the single next action to take right now?"
        }
        return {
            "mode": self.name,
            "weight": self.weight,
            "lens": lenses.get(self.name, "Process the task."),
            "task": task,
            "context_keys": list(context.keys())
        }

    def adapt(self, outcome_score: float, lr: float = 0.05):
        """Update weight based on outcome. Winner gets heavier."""
        self.weight = max(0.1, min(2.0, self.weight + lr * (outcome_score - 0.5)))
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "outcome_score": outcome_score,
            "new_weight": self.weight
        })

    def to_dict(self) -> dict:
        return {"name": self.name, "weight": self.weight, "history_len": len(self.history)}


class AdaptationLayer:
    """
    Layer 6 — The T2 Adaptation Engine.
    Runs two-pass expert ensemble + weight adaptation.
    Weights persist to disk so Agent Zero gets smarter across sessions.
    """

    WEIGHTS_FILE = "agent_zero_expert_weights.json"

    def __init__(self):
        self.experts: Dict[str, ExpertVector] = {}
        self._init_experts()
        self._load_weights()

    def _init_experts(self):
        for mode in EXPERT_MODES:
            self.experts[mode] = ExpertVector(mode)

    def _load_weights(self):
        p = Path(self.WEIGHTS_FILE)
        if p.exists():
            try:
                saved = json.loads(p.read_text())
                for name, data in saved.items():
                    if name in self.experts:
                        self.experts[name].weight = data.get("weight", 1.0)
            except Exception:
                pass

    def _save_weights(self):
        Path(self.WEIGHTS_FILE).write_text(
            json.dumps({n: e.to_dict() for n, e in self.experts.items()}, indent=2)
        )

    def run(self, task: str, context: dict) -> dict:
        """
        Full T2 cycle:
        Pass 1 — each expert processes independently
        Pass 2 — select top expert by weight
        Returns combined output + elected lead mode
        """
        # Pass 1: independent processing
        pass1 = {name: expert.process(task, context)
                 for name, expert in self.experts.items()}

        # Pass 2: elect lead expert (highest weight)
        lead = max(self.experts.items(), key=lambda x: x[1].weight)
        lead_name, lead_expert = lead

        return {
            "task": task,
            "lead_mode": lead_name,
            "lead_weight": lead_expert.weight,
            "all_passes": pass1,
            "weights_snapshot": {n: round(e.weight, 3) for n, e in self.experts.items()}
        }

    def feedback(self, lead_mode: str, outcome_score: float):
        """
        Called by SAFLA after each cycle.
        Winner gets heavier. Losers get slightly lighter.
        """
        for name, expert in self.experts.items():
            if name == lead_mode:
                expert.adapt(outcome_score, lr=0.1)
            else:
                expert.adapt(1.0 - outcome_score, lr=0.02)
        self._save_weights()

    def status(self) -> str:
        weights = " | ".join(
            f"{n}:{round(e.weight, 2)}" for n, e in self.experts.items()
        )
        return f"T2 Weights — {weights}"


if __name__ == "__main__":
    layer = AdaptationLayer()
    print("Initial:", layer.status())

    result = layer.run(
        task="Analyze the latest GhostPrime cycle and suggest next action",
        context={"intent": "evolution", "session_turns": 7}
    )
    print(f"Lead mode: {result['lead_mode']} (weight {result['lead_weight']:.2f})")
    print(f"All weights: {result['weights_snapshot']}")

    # Simulate SAFLA feedback — executor won, score 0.85
    layer.feedback("executor", 0.85)
    print("After feedback:", layer.status())
