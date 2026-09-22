"""Bounded natural-language inventory query translation and execution."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional


class SecurityQueryEngine:
    def parse(self, query: str) -> Dict[str, Any]:
        text = query.strip().lower()
        if not text or len(text) > 300:
            return {"status": "UNSUPPORTED_QUERY", "reason": "empty_or_too_long"}
        filters: Dict[str, Any] = {}
        if "rsa" in text:
            filters["algorithm"] = "RSA"
        elif "sha-1" in text or "sha1" in text:
            filters["algorithm"] = "SHA-1"
        elif "quantum" in text and ("vulnerable" in text or "risk" in text):
            filters["quantum_vulnerable"] = True
        elif "expired" in text and "certificate" in text:
            filters["certificate_status"] = "EXPIRED"
        else:
            match = re.search(r"migration\s+(discovered|assessed|planned|ready|in_progress|migrated|verified)", text)
            if match:
                filters["migration_state"] = match.group(1).upper()
            else:
                recent = re.search(r"(?:last|past)\s+(\d+)\s+days?", text)
                if recent and "discover" in text:
                    filters["discovered_after"] = (datetime.now(timezone.utc) - timedelta(days=int(recent.group(1)))).isoformat()
                else:
                    return {"status": "UNSUPPORTED_QUERY", "reason": "intent_not_allowlisted"}
        repository = re.search(r"(?:repository|repo)\s+([\w.-]+)", text)
        if repository:
            filters["repo_id"] = repository.group(1)
        return {"status": "SUPPORTED", "filter": filters}

    def execute(
        self,
        query: str,
        assets: Iterable[Dict[str, Any]],
        certificates: Iterable[Dict[str, Any]] = (),
        page: int = 1,
        page_size: int = 50,
        repo_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        parsed = self.parse(query)
        if parsed["status"] != "SUPPORTED":
            return parsed
        if page < 1 or page_size < 1 or page_size > 200:
            return {"status": "UNSUPPORTED_QUERY", "reason": "invalid_pagination"}
        filters = dict(parsed["filter"])
        if repo_id:
            filters["repo_id"] = repo_id
        items: List[Dict[str, Any]] = list(assets)
        if "algorithm" in filters:
            target = filters["algorithm"]
            items = [item for item in items if item.get("algorithm", "").upper() == target]
        if filters.get("quantum_vulnerable"):
            items = [item for item in items if item.get("hndl_vulnerable") or item.get("quantum_risk_tier", "").upper() in {"HIGH", "CRITICAL"}]
        if "migration_state" in filters:
            target = filters["migration_state"]
            items = [item for item in items if item.get("migration_status", item.get("current_state", "")).upper() == target]
        if "repo_id" in filters:
            items = [item for item in items if item.get("repo_id") == filters["repo_id"]]
        if "discovered_after" in filters:
            threshold = datetime.fromisoformat(filters["discovered_after"])
            def is_recent(item: Dict[str, Any]) -> bool:
                value = item.get("first_seen")
                try:
                    return bool(value) and datetime.fromisoformat(value).astimezone(timezone.utc) >= threshold
                except ValueError:
                    return False
            items = [item for item in items if is_recent(item)]
        if filters.get("certificate_status") == "EXPIRED":
            expired_ids = {certificate.get("asset_id") for certificate in certificates if certificate.get("is_expired")}
            items = [item for item in items if item.get("asset_id") in expired_ids]
        start = (page - 1) * page_size
        return {"status": "OK", "query": {"status": "SUPPORTED", "filter": filters}, "total": len(items), "page": page, "page_size": page_size, "results": items[start:start + page_size]}
