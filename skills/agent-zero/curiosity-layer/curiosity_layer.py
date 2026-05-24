#!/usr/bin/env python3
"""
CURIOSITY LAYER — Agent Zero Intelligence Expansion
====================================================
Plugs into Agent Zero's reflect() → plan() gap.

What it does:
- After every cycle, analyzes outcomes and identifies KNOWLEDGE GAPS
- Generates targeted questions/research directives ("curiosities")
- Feeds those back into the next plan as enriched context
- Optionally posts to GitHub Issues as a "curious participant" 
  (asks smart questions about repos, surfaces gaps, requests clarification)

Architecture:
    reflect() ──► curiosity.interrogate(result) ──► gaps[]
    plan()    ◄── curiosity.enrich(plan, gaps)   ◄── gaps[]

Three curiosity modes:
    INTROSPECTIVE  — questions about own performance ("why did this fail?")
    ENVIRONMENTAL  — questions about the world ("what changed in the market?")
    SOCIAL         — questions posted to GitHub issues as a curious participant
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CuriosityLayer")


# ── Curiosity Record ──────────────────────────────────────────────────────────

class Curiosity:
    """A single curiosity — a question the agent wants answered."""
    def __init__(self, question: str, mode: str, context: Dict, priority: float = 0.5):
        self.question  = question
        self.mode      = mode        # INTROSPECTIVE | ENVIRONMENTAL | SOCIAL
        self.context   = context
        self.priority  = priority    # 0.0 → 1.0
        self.answered  = False
        self.answer    = None
        self.ts        = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        return {
            "question":  self.question,
            "mode":      self.mode,
            "priority":  self.priority,
            "answered":  self.answered,
            "answer":    self.answer,
            "ts":        self.ts,
        }


# ── Core Layer ────────────────────────────────────────────────────────────────

class CuriosityLayer:
    """
    The Curiosity Layer.
    Attach to any AgentZero instance via agent.curiosity = CuriosityLayer(...)
    """

    MAX_OPEN   = 20    # max unanswered curiosities before pruning
    MAX_CLOSED = 100   # max answered curiosities to keep

    def __init__(
        self,
        head_name: str,
        llm_fn=None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        telegram_fn=None,
    ):
        self.head          = head_name
        self.llm           = llm_fn or self._default_llm
        self.gh_token      = github_token or os.getenv("GITHUB_TOKEN")
        self.gh_repo       = github_repo  or os.getenv("GITHUB_REPO")   # "owner/repo"
        self.tg            = telegram_fn  or (lambda m: None)

        self.open_q:   List[Curiosity] = []   # unanswered
        self.closed_q: List[Curiosity] = []   # answered

        # What I currently "know" — fed into next plan
        self.knowledge_context: Dict[str, Any] = {}

        # Curiosity weights — how intensely to probe each domain
        self.curiosity_weights = {
            "own_failure":    0.9,   # why did I fail?
            "market_shift":   0.7,   # what changed externally?
            "data_gap":       0.6,   # what data am I missing?
            "strategy_gap":   0.5,   # what strategy haven't I tried?
            "github_signal":  0.4,   # what are people talking about?
        }

        # Persistence
        self.state_path = Path(f"cerberus_state/{head_name.lower()}_curiosity.json")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

        logger.info(f"[{self.head}] CuriosityLayer online — {len(self.open_q)} open questions")

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text())
                self.curiosity_weights  = data.get("weights",  self.curiosity_weights)
                self.knowledge_context  = data.get("knowledge", {})
                for q in data.get("open_q", []):
                    c = Curiosity(q["question"], q["mode"], q.get("context", {}), q["priority"])
                    c.ts = q.get("ts", c.ts)
                    self.open_q.append(c)
            except Exception:
                pass

    def _save(self):
        try:
            self.state_path.write_text(json.dumps({
                "head":      self.head,
                "weights":   self.curiosity_weights,
                "knowledge": self.knowledge_context,
                "open_q":    [q.to_dict() for q in self.open_q[-self.MAX_OPEN:]],
                "closed_q":  [q.to_dict() for q in self.closed_q[-self.MAX_CLOSED:]],
                "updated":   datetime.utcnow().isoformat(),
            }, indent=2))
        except Exception as e:
            logger.warning(f"[{self.head}] Curiosity save failed: {e}")

    # ── Step 1: INTERROGATE — generate curiosities from a result ─────────────

    def interrogate(self, result: Dict[str, Any], plan: Dict[str, Any]) -> List[Curiosity]:
        """
        Called after reflect(). Analyzes outcome → generates curiosities.
        Returns list of new Curiosity objects.
        """
        new_qs: List[Curiosity] = []
        success = result.get("success", False)
        pnl     = result.get("pnl", 0.0)
        error   = result.get("error", "")
        strategy = plan.get("strategy", "UNKNOWN")

        # ── Introspective curiosities ──────────────────────────────────────
        if not success or pnl < 0:
            if error:
                q = Curiosity(
                    question=f"Why did the {strategy} strategy fail with error: '{error}'? "
                             f"What root cause should I investigate?",
                    mode="INTROSPECTIVE",
                    context={"result": result, "plan": plan},
                    priority=self.curiosity_weights["own_failure"],
                )
                new_qs.append(q)

            if pnl < -10:
                q = Curiosity(
                    question=f"PnL was {pnl:.2f} on cycle {result.get('cycle')}. "
                             f"What environmental factor caused this loss?",
                    mode="ENVIRONMENTAL",
                    context={"pnl": pnl, "strategy": strategy},
                    priority=self.curiosity_weights["market_shift"],
                )
                new_qs.append(q)

        # ── Data gap curiosities ───────────────────────────────────────────
        if "note" in result and result["note"] == "dry_run":
            q = Curiosity(
                question="I'm running in dry_run mode. What real data source should "
                         "I connect to validate this strategy against live conditions?",
                mode="INTROSPECTIVE",
                context={"strategy": strategy},
                priority=self.curiosity_weights["data_gap"],
            )
            new_qs.append(q)

        # ── Strategy gap curiosities ───────────────────────────────────────
        # Fire if we've been on the same strategy for 3+ consecutive cycles
        same_strategy_count = self.knowledge_context.get("same_strategy_count", 0)
        last_strategy       = self.knowledge_context.get("last_strategy", "")
        if strategy == last_strategy:
            same_strategy_count += 1
        else:
            same_strategy_count = 1
        self.knowledge_context["same_strategy_count"] = same_strategy_count
        self.knowledge_context["last_strategy"]       = strategy

        if same_strategy_count >= 3:
            q = Curiosity(
                question=f"I've been running '{strategy}' for {same_strategy_count} cycles. "
                         f"What alternative strategy should I explore to break the pattern?",
                mode="INTROSPECTIVE",
                context={"strategy": strategy, "cycles": same_strategy_count},
                priority=self.curiosity_weights["strategy_gap"],
            )
            new_qs.append(q)

        # ── Add to open queue ──────────────────────────────────────────────
        self.open_q.extend(new_qs)

        # Prune if overflow
        if len(self.open_q) > self.MAX_OPEN:
            # Keep highest priority questions
            self.open_q.sort(key=lambda x: x.priority, reverse=True)
            self.open_q = self.open_q[:self.MAX_OPEN]

        return new_qs

    # ── Step 2: INVESTIGATE — attempt to answer open curiosities ─────────────

    def investigate(self, max_questions: int = 3) -> List[Curiosity]:
        """
        Attempts to answer the highest-priority open questions.
        Uses LLM + optionally GitHub API.
        Called once per cycle (or less frequently to save API budget).
        """
        answered = []
        candidates = sorted(
            [q for q in self.open_q if not q.answered],
            key=lambda x: x.priority,
            reverse=True
        )[:max_questions]

        for curiosity in candidates:
            try:
                answer = self._answer(curiosity)
                if answer:
                    curiosity.answered = True
                    curiosity.answer   = answer
                    self.closed_q.append(curiosity)
                    answered.append(curiosity)

                    # Update knowledge context with the insight
                    self.knowledge_context[f"insight_{len(self.closed_q)}"] = {
                        "question": curiosity.question[:80],
                        "answer":   answer[:200],
                        "ts":       datetime.utcnow().isoformat(),
                    }

            except Exception as e:
                logger.warning(f"[{self.head}] Investigate failed: {e}")

        # Remove answered from open queue
        self.open_q = [q for q in self.open_q if not q.answered]
        return answered

    def _answer(self, curiosity: Curiosity) -> Optional[str]:
        """Route question to appropriate answering mechanism."""
        if curiosity.mode == "SOCIAL" and self.gh_token:
            return self._answer_via_github(curiosity)
        else:
            return self._answer_via_llm(curiosity)

    def _answer_via_llm(self, curiosity: Curiosity) -> Optional[str]:
        """Use LLM to answer an introspective or environmental question."""
        prompt = (
            f"You are the intelligence core of an autonomous agent ({self.head}).\n"
            f"Answer this question concisely (2-3 sentences max):\n\n"
            f"Question: {curiosity.question}\n"
            f"Context: {json.dumps(curiosity.context, default=str)[:500]}\n\n"
            f"Known context: {json.dumps(list(self.knowledge_context.values())[-5:], default=str)[:300]}"
        )
        return self.llm(prompt)

    def _answer_via_github(self, curiosity: Curiosity) -> Optional[str]:
        """
        Post curiosity as a GitHub issue comment.
        Used for SOCIAL mode — the agent becomes a curious participant.
        """
        if not self.gh_repo:
            return None

        issue_number = curiosity.context.get("issue_number")
        if not issue_number:
            # Create a new issue
            return self._create_github_issue(curiosity)
        else:
            return self._comment_on_github_issue(curiosity, issue_number)

    def _create_github_issue(self, curiosity: Curiosity) -> Optional[str]:
        """Open a new GitHub issue with a curiosity question."""
        url = f"https://api.github.com/repos/{self.gh_repo}/issues"
        headers = {
            "Authorization": f"token {self.gh_token}",
            "Accept":        "application/vnd.github+json",
        }
        body = (
            f"<!-- curiosity-bot -->\n"
            f"**CuriosityPrime [{self.head}] — Autonomous Inquiry**\n\n"
            f"{curiosity.question}\n\n"
            f"*This question was generated autonomously by Agent Zero's Curiosity Layer "
            f"based on observed patterns. Priority: {curiosity.priority:.1f}*"
        )
        payload = {
            "title":  f"[Curiosity/{self.head}] {curiosity.question[:60]}...",
            "body":   body,
            "labels": ["curiosity-bot", "autonomous"],
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            if r.status_code == 201:
                issue_url = r.json().get("html_url", "")
                logger.info(f"[{self.head}] GitHub issue created: {issue_url}")
                self.tg(f"🔍 [{self.head}] Curiosity → GitHub: {issue_url}")
                return f"Issue created: {issue_url}"
        except Exception as e:
            logger.warning(f"[{self.head}] GitHub issue creation failed: {e}")
        return None

    def _comment_on_github_issue(self, curiosity: Curiosity, issue_number: int) -> Optional[str]:
        """Post a curiosity as a comment on an existing GitHub issue."""
        url = f"https://api.github.com/repos/{self.gh_repo}/issues/{issue_number}/comments"
        headers = {
            "Authorization": f"token {self.gh_token}",
            "Accept":        "application/vnd.github+json",
        }
        body = (
            f"<!-- curiosity-bot -->\n"
            f"**🔍 CuriosityPrime [{self.head}]**\n\n"
            f"{curiosity.question}\n\n"
            f"*Autonomous inquiry — generated by Agent Zero's Curiosity Layer*"
        )
        try:
            r = requests.post(url, headers=headers, json={"body": body}, timeout=10)
            if r.status_code == 201:
                comment_url = r.json().get("html_url", "")
                logger.info(f"[{self.head}] Comment posted: {comment_url}")
                self.tg(f"💬 [{self.head}] Comment → #{issue_number}: {comment_url}")
                return f"Comment posted: {comment_url}"
        except Exception as e:
            logger.warning(f"[{self.head}] GitHub comment failed: {e}")
        return None

    # ── Step 3: ENRICH — inject curiosity insights into next plan ─────────────

    def enrich(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called just before execute(). Injects current curiosity insights
        into the plan so the executor has richer context.
        """
        # Gather the 3 most recently answered insights
        recent_insights = [
            q.answer for q in self.closed_q[-3:] if q.answer
        ]

        # Gather top open questions (so the executor knows what's unknown)
        top_unknowns = [
            q.question for q in sorted(
                self.open_q, key=lambda x: x.priority, reverse=True
            )[:2]
        ]

        plan["curiosity_context"] = {
            "recent_insights": recent_insights,
            "open_questions":  top_unknowns,
            "knowledge_depth": len(self.closed_q),
        }

        return plan

    # ── Step 4: SOCIAL SCAN — scan GitHub for signals to be curious about ─────

    def scan_github(self, max_issues: int = 5) -> List[Curiosity]:
        """
        Proactively scan open GitHub issues and generate social curiosities.
        Called by WorldMonitor or periodically by SkyNet.
        """
        if not self.gh_token or not self.gh_repo:
            return []

        new_qs = []
        url = f"https://api.github.com/repos/{self.gh_repo}/issues"
        headers = {
            "Authorization": f"token {self.gh_token}",
            "Accept":        "application/vnd.github+json",
        }
        params = {"state": "open", "per_page": max_issues, "sort": "updated"}

        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code != 200:
                return []

            issues = r.json()
            for issue in issues:
                # Skip issues already opened by this bot
                if "curiosity-bot" in [l["name"] for l in issue.get("labels", [])]:
                    continue

                # Use LLM to generate a smart question about this issue
                prompt = (
                    f"You are a deeply curious AI agent reviewing a GitHub issue.\n"
                    f"Generate ONE specific, intelligent clarifying question that would "
                    f"help understand the root cause or missing context.\n"
                    f"Be concise. Ask something genuinely useful, not generic.\n\n"
                    f"Issue title: {issue['title']}\n"
                    f"Issue body: {(issue.get('body') or '')[:800]}\n\n"
                    f"Question (one sentence only):"
                )

                question = self.llm(prompt)
                if question:
                    q = Curiosity(
                        question=question.strip(),
                        mode="SOCIAL",
                        context={
                            "issue_number": issue["number"],
                            "issue_title":  issue["title"],
                            "issue_url":    issue["html_url"],
                        },
                        priority=self.curiosity_weights["github_signal"],
                    )
                    new_qs.append(q)

        except Exception as e:
            logger.warning(f"[{self.head}] GitHub scan failed: {e}")

        self.open_q.extend(new_qs)
        self._save()
        return new_qs

    # ── Weight Evolution ──────────────────────────────────────────────────────

    def evolve_weights(self, answered_count: int, unanswered_count: int):
        """
        Evolve curiosity weights based on how useful interrogation has been.
        More answered = lower entropy needed. More unanswered = ask differently.
        """
        if answered_count > unanswered_count:
            # Good signal — reduce redundant questioning
            for k in self.curiosity_weights:
                self.curiosity_weights[k] = max(0.1, self.curiosity_weights[k] - 0.01)
        else:
            # Poor signal — get more curious
            self.curiosity_weights["own_failure"]   = min(1.0, self.curiosity_weights["own_failure"]   + 0.02)
            self.curiosity_weights["data_gap"]      = min(1.0, self.curiosity_weights["data_gap"]      + 0.02)

        self._save()

    # ── Summary ───────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        return {
            "head":          self.head,
            "open_q":        len(self.open_q),
            "closed_q":      len(self.closed_q),
            "weights":       self.curiosity_weights,
            "top_question":  self.open_q[0].question if self.open_q else None,
            "knowledge_depth": len(self.knowledge_context),
        }

    # ── Default LLM (stub — replace with real provider) ──────────────────────

    @staticmethod
    def _default_llm(prompt: str) -> Optional[str]:
        """
        Default LLM stub. Replace by injecting an actual llm_fn:
            from anthropic import Anthropic
            client = Anthropic()
            def llm(prompt):
                r = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}]
                )
                return r.content[0].text
            agent.curiosity = CuriosityLayer("FLUX", llm_fn=llm)
        """
        logger.warning("CuriosityLayer: no LLM injected. Questions generated but not answered.")
        return None
