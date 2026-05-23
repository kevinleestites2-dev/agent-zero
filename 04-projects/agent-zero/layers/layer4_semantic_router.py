"""
Agent Zero - Layer 4: Semantic Router (Brain.ai)
Routes every signal via ensemble classifier + NER + coreference resolution.
"""
import json, urllib.request
from typing import Optional

ROUTE_MAP = {
    "summarization": "layer2_perception",
    "news": "layer2_perception",
    "maps_api": "layer2_perception",
    "unit_conversion": "layer3_runtime",
    "alarm_api": "layer3_runtime",
    "memory": "layer5_cognition",
    "identity": "layer10_identity",
    "evolution": "layer8_evolution",
    "unknown": "layer5_cognition",
}

class SemanticRouter:
    def __init__(self, github_token: str, model: str = "gpt-4o"):
        self.token = github_token
        self.model = model
        self.base_url = "https://models.inference.ai.azure.com/chat/completions"
        self.context_entities = {}

    def route(self, signal: str) -> dict:
        resolved = self._resolve_coreference(signal)
        intent, entities = self._classify(resolved)
        route = ROUTE_MAP.get(intent, ROUTE_MAP["unknown"])
        self.context_entities.update(entities)
        return {"route": route, "intent": intent, "entities": entities,
                "resolved": resolved, "original": signal}

    def _classify(self, text: str) -> tuple:
        system_prompt = (
            "You are a semantic router for Agent Zero. "
            "Return JSON only: "
            '{"intent": "one of [summarization,news,maps_api,unit_conversion,alarm_api,memory,identity,evolution,unknown]", '
            '"entities": {"PERSON": [], "PLACE": [], "ORG": [], "DATE": [], "OTHER": []}}'
        )
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": text}],
            "max_tokens": 200,
            "response_format": {"type": "json_object"}
        }).encode()
        req = urllib.request.Request(self.base_url, data=payload, method="POST",
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                d = json.loads(resp.read())
                result = json.loads(d["choices"][0]["message"]["content"])
                return result.get("intent", "unknown"), result.get("entities", {})
        except Exception:
            return "unknown", {}

    def _resolve_coreference(self, text: str) -> str:
        pronouns = ["his", "her", "their", "its", "he", "she", "they", "it", "him"]
        for pronoun in pronouns:
            if pronoun in text.lower().split() and self.context_entities.get("PERSON"):
                text = text.replace(pronoun, self.context_entities["PERSON"][-1])
        return text
