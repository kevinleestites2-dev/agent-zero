"""
Agent Zero — Layer 2: Perception
Source: gpt-researcher (assafelovic/gpt-researcher, forked to kevinleestites2-dev)

Autonomous signal-hunting engine. Given any query, this layer:
1. Decomposes the question into sub-queries
2. Hunts the web concurrently for relevant sources
3. Scrapes, curates, and de-duplicates content
4. Produces a structured research report with citations

Agent Zero uses this as its "eyes" — whenever Layer 4 routes
a signal with intent: summarization | news | maps_api, it lands here.
"""

import os
from typing import Optional


class PerceptionLayer:
    """
    Layer 2 — The Perception Engine.
    Wraps GPTResearcher for use inside Agent Zero.
    Routes: summarization, news, maps_api, any external signal.
    """

    def __init__(self, github_token: str):
        self.github_token = github_token
        # GPT-Researcher uses OPENAI_API_KEY by default
        # We route through GitHub Models endpoint for zero-cost inference
        os.environ.setdefault("OPENAI_API_KEY", github_token)
        os.environ.setdefault(
            "OPENAI_BASE_URL",
            "https://models.inference.ai.azure.com"
        )
        os.environ.setdefault("FAST_LLM", "openai:gpt-4o-mini")
        os.environ.setdefault("SMART_LLM", "openai:gpt-4o")

    async def research(self, query: str, report_type: str = "research_report") -> dict:
        """
        Run a full autonomous research cycle.
        Returns: { "query": ..., "report": ..., "sources": [...] }
        """
        try:
            from gpt_researcher import GPTResearcher
            researcher = GPTResearcher(query=query, report_type=report_type)
            await researcher.conduct_research()
            report = await researcher.write_report()
            return {
                "query": query,
                "report": report,
                "sources": researcher.get_source_urls(),
                "status": "ok"
            }
        except ImportError:
            # Fallback: lightweight web search via GitHub Models
            return await self._lightweight_research(query)
        except Exception as e:
            return {"query": query, "error": str(e), "status": "error"}

    async def _lightweight_research(self, query: str) -> dict:
        """Fallback when gpt_researcher not installed. Uses GPT-4o directly."""
        import urllib.request
        import json as _json
        import asyncio

        payload = _json.dumps({
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": (
                    "You are a research engine. Given a query, produce a "
                    "concise, accurate research summary with key facts and sources."
                )},
                {"role": "user", "content": query}
            ],
            "max_tokens": 800
        }).encode()

        req = urllib.request.Request(
            "https://models.inference.ai.azure.com/chat/completions",
            data=payload, method="POST",
            headers={
                "Authorization": f"Bearer {self.github_token}",
                "Content-Type": "application/json"
            }
        )
        loop = asyncio.get_event_loop()

        def _call():
            with urllib.request.urlopen(req) as resp:
                return _json.loads(resp.read())

        d = await loop.run_in_executor(None, _call)
        return {
            "query": query,
            "report": d["choices"][0]["message"]["content"],
            "sources": [],
            "status": "ok_lightweight"
        }


# Quick sync wrapper for non-async callers
def perceive(query: str, github_token: str) -> dict:
    import asyncio
    layer = PerceptionLayer(github_token=github_token)
    return asyncio.run(layer.research(query))


if __name__ == "__main__":
    import os
    tok = os.environ.get("GITHUB_TOKEN", "")
    result = perceive("Latest breakthroughs in self-evolving AI agents 2025", tok)
    print(f"STATUS: {result['status']}")
    print(f"REPORT (first 500 chars):")
    print(result.get("report", "")[:500])
