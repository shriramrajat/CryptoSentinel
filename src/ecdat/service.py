"""Service layer for CryptoSentinel scanning and risk analysis."""
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ecdat.config_policy import RiskPolicyConfig
from ecdat.context import AssetContext, ContextResolver
from ecdat.hndl import HNDLStatus
from ecdat.lifecycle import LifecycleUrgency
from ecdat.risk import assess_quantum_risk, classify_assets
from ecdat.scanner import Scanner, SUPPORTED_EXTENSIONS

SCANNER_VERSION = "0.2.0"

_LANGUAGE_EXTENSIONS = {
    "python": {".py"},
    "java": {".java"},
    "c": {".c", ".h"},
    "cpp": {".cpp", ".hpp", ".cc", ".cxx"},
    "javascript": {".js", ".mjs", ".cjs", ".jsx"},
    "typescript": {".ts", ".tsx"},
    "go": {".go"},
    "rust": {".rs"},
    "php": {".php"},
    "csharp": {".cs"},
    "kotlin": {".kt", ".kts"},
    "pem": {".pem", ".crt", ".key", ".cer", ".der"},
    "config": {".yaml", ".yml", ".toml", ".json", ".xml", ".env", ".config", ".properties", ".ini", ".conf"},
}


class ScannerError(Exception):
    """Raised when the scanner layer fails unrecoverably."""


class AnalysisError(Exception):
    """Raised when risk analysis fails unrecoverably."""


class ScanService:
    def __init__(self, max_file_size_bytes: int = 10 * 1024 * 1024):
        self.max_file_size_bytes = max_file_size_bytes

    @staticmethod
    def _filter_files(files: List[Path], language_filters: Optional[List[str]]) -> List[Path]:
        if not language_filters:
            return files
        requested_exts = set()
        for language in language_filters:
            requested_exts.update(_LANGUAGE_EXTENSIONS.get(language.lower(), set()))
        return [path for path in files if path.suffix.lower() in requested_exts]

    def run_scan(
        self,
        target_path: str,
        language_filters: Optional[List[str]] = None,
        generate_cbom: bool = False,
        user_context_map: Optional[Dict[str, Any]] = None,
        policy_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not os.path.exists(target_path):
            raise ValueError(f"Target path does not exist: {target_path}")

        start_time = time.time()
        target = Path(target_path)
        effective_root = target if target.is_dir() else target.parent

        policy = RiskPolicyConfig.from_dict(policy_config)

        try:
            scanner = Scanner(root_dir=effective_root)
            all_files = scanner.discover_files(target_path)
            files = self._filter_files(all_files, language_filters)
            assets = []
            skipped_files: List[Dict[str, str]] = []
            errors: List[Dict[str, str]] = []

            for file_path in files:
                try:
                    if file_path.stat().st_size > self.max_file_size_bytes:
                        skipped_files.append({"file": str(file_path), "reason": "oversized"})
                        continue
                    assets.extend(scanner.scan_file(file_path, root_dir=effective_root))
                except Exception as exc:
                    errors.append({"file": str(file_path), "error": str(exc)})
        except Exception as exc:
            raise ScannerError(f"Scanner encountered an internal failure: {exc}") from exc

        skipped_files.extend(getattr(scanner, "skipped_files", []))
        errors.extend(getattr(scanner, "errors", []))

        try:
            # Phase 1 baseline classification for backward compatibility
            phase1_assessments = classify_assets(assets)
        except Exception as exc:
            raise AnalysisError(f"Analysis encountered an internal failure: {exc}") from exc

        assessments_by_id = {assessment.asset_id: assessment for assessment in phase1_assessments}
        findings: List[Dict[str, Any]] = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        quantum_threat_counts = {"shor": 0, "grover": 0, "none": 0}
        algorithm_distribution: Dict[str, int] = {}
        language_distribution: Dict[str, int] = {}
        category_distribution: Dict[str, int] = {}
        library_distribution: Dict[str, int] = {}
        purpose_distribution: Dict[str, int] = {}

        # Phase 2 metrics
        hndl_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NOT_APPLICABLE": 0, "UNKNOWN": 0}
        mosca_urgency_counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0, "UNKNOWN": 0}
        priority_counts = {"IMMEDIATE_ACTION": 0, "PLANNING_REQUIRED": 0, "NEEDS_CONTEXT": 0, "MONITOR": 0, "LOW_PRIORITY": 0}
        unknown_context_count = 0

        for asset in assets:
            # 1. Resolve Context for this asset
            ctx = ContextResolver.resolve_context(
                target_dir=effective_root,
                asset_id=asset.asset_id,
                file_path=asset.file_path,
                user_context_map=user_context_map,
            )

            # 2. Compute Phase 2 Assessment
            p2_assessment = assess_quantum_risk(asset, context=ctx, policy=policy)

            # Update Phase 1 baseline metrics
            p1_assessment = assessments_by_id.get(asset.asset_id)
            if p1_assessment is None:
                severity, quantum_threat, reason, confidence, recommendation = (
                    "medium", "none", "Unknown algorithm mapped to default risk.", 0.5, None
                )
            else:
                severity = p1_assessment.severity.value
                quantum_threat = p1_assessment.quantum_threat.value
                reason = p1_assessment.reason
                confidence = p1_assessment.confidence
                recommendation = p1_assessment.pqc_recommendation

            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            quantum_threat_counts[quantum_threat] = quantum_threat_counts.get(quantum_threat, 0) + 1
            algorithm_distribution[asset.algorithm] = algorithm_distribution.get(asset.algorithm, 0) + 1
            language_distribution[asset.language] = language_distribution.get(asset.language, 0) + 1
            category_distribution[asset.category] = category_distribution.get(asset.category, 0) + 1
            library_distribution[asset.library] = library_distribution.get(asset.library, 0) + 1
            purpose_key = asset.purpose or "unknown"
            purpose_distribution[purpose_key] = purpose_distribution.get(purpose_key, 0) + 1

            evidence = asset.evidence

            # Update Phase 2 aggregated metrics
            hndl_status = p2_assessment.hndl_assessment.status.value
            mosca_urgency = p2_assessment.lifecycle_assessment.urgency.value
            priority = p2_assessment.overall_priority

            hndl_counts[hndl_status] = hndl_counts.get(hndl_status, 0) + 1
            mosca_urgency_counts[mosca_urgency] = mosca_urgency_counts.get(mosca_urgency, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

            if p2_assessment.explanation.missing_information:
                unknown_context_count += 1

            finding: Dict[str, Any] = {
                "finding_id": asset.asset_id,
                "algorithm": asset.algorithm,
                "category": asset.category,
                "key_length": asset.key_length,
                "mode": asset.mode,
                "padding": asset.padding,
                # Phase 1 new fields (backward compatible)
                "purpose": asset.purpose,
                "protocol": asset.protocol,
                "language": asset.language,
                "library": asset.library,
                "detection_rule": asset.detection_rule,
                "file_location": {"file_path": asset.file_path, "line_number": asset.line_number},
                "evidence": {
                    "file_path": asset.file_path,
                    "line_number": asset.line_number,
                    "code_snippet": evidence.code_snippet if evidence else "",
                    "detection_mechanism": evidence.detection_mechanism if evidence else "unknown",
                    "matched_rule_id": evidence.matched_rule_id if evidence else "unknown",
                },
                # Phase 1 risk contract (preserved for backward compatibility)
                "risk": {
                    "severity": severity,
                    "reason": reason,
                    "confidence": confidence,
                    "quantum_threat": quantum_threat,
                    "pqc_recommendation": (
                        {
                            "target_algorithm": recommendation.target_algorithm,
                            "nist_standard": recommendation.nist_standard,
                            "migration_type": recommendation.migration_type,
                        }
                        if recommendation else None
                    ),
                },
                # Phase 2 context & risk intelligence contract
                "context": ctx.to_dict(),
                "quantum_risk_intelligence": p2_assessment.to_dict(),
            }

            # Include certificate metadata if present
            if asset.certificate_metadata:
                finding["certificate_metadata"] = asset.certificate_metadata.to_dict()

            # Include key metadata if present (no raw key material)
            if asset.key_metadata:
                finding["key_metadata"] = asset.key_metadata.to_dict()

            findings.append(finding)

        result: Dict[str, Any] = {
            "summary": {
                "total_files_discovered": len(all_files),
                "total_files_scanned": len(files) - len(skipped_files),
                "files_skipped": len(skipped_files),
                "files_failed": len(errors),
                "total_crypto_assets": len(assets),
                "severity_counts": severity_counts,
                "quantum_threat_counts": quantum_threat_counts,
                "algorithm_distribution": algorithm_distribution,
                "quantum_vulnerable_assets": quantum_threat_counts.get("shor", 0) + quantum_threat_counts.get("grover", 0),
                # Phase 1 summary fields
                "language_distribution": language_distribution,
                "category_distribution": category_distribution,
                "library_distribution": library_distribution,
                "purpose_distribution": purpose_distribution,
                # Phase 2 Metrics
                "hndl_counts": hndl_counts,
                "mosca_urgency_counts": mosca_urgency_counts,
                "priority_counts": priority_counts,
                "unknown_context_count": unknown_context_count,
            },
            "findings": findings,
            "errors": errors,
            "skipped_files": skipped_files,
            "metadata": {
                "scan_duration_ms": int((time.time() - start_time) * 1000),
                "scanner_version": SCANNER_VERSION,
                "target": target_path,
                "policy": policy.to_dict(),
            },
        }

        # Optionally include CBOM in response
        if generate_cbom:
            try:
                from ecdat.cbom.generator import generate_cbom
                result["cbom"] = generate_cbom(
                    assets,
                    metadata={
                        "scanner_version": SCANNER_VERSION,
                        "target": target_path,
                        "scan_duration_ms": result["metadata"]["scan_duration_ms"],
                    },
                )
            except Exception as exc:
                result["cbom_error"] = str(exc)

        return result
