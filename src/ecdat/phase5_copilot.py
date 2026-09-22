"""Evidence-only copilot boundary; providers may explain, never mutate."""

from typing import Any, Dict, Iterable, Optional

from .phase5_query import SecurityQueryEngine


class EvidenceCopilot:
    def __init__(self, provider: Optional[Any] = None) -> None:
        self.provider = provider
        self.query_engine = SecurityQueryEngine()

    def query(self, prompt: str, assets: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        if len(prompt) > 300:
            return {"status": "UNSUPPORTED_QUERY", "reason": "prompt_too_long"}
        result = self.query_engine.execute(prompt, assets)
        return {"status": "OK", "intent": result, "answer": "Deterministic inventory results are authoritative.", "evidence": result.get("results", [])} if result.get("status") == "OK" else result

    def explain(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "OK", "explanation": "Evidence-backed explanation only; risk and inventory state remain deterministic.", "evidence": finding}
