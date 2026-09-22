"""Safe Git metadata and baseline comparison primitives."""

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .discovery.base import DiscoveryError
from .scanner import Scanner


class GitInspector:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def metadata(self, repository: str, commit: str = "HEAD") -> Dict[str, Any]:
        root = self._repo(repository)
        return {
            "repository": root.as_posix(), "branch": self._run(root, "branch", "--show-current"),
            "commit_sha": self._run(root, "rev-parse", commit), "author": self._run(root, "show", "-s", "--format=%an", commit),
            "timestamp": self._run(root, "show", "-s", "--format=%cI", commit), "changed_files": self.changed_files(str(root), commit),
        }

    def changed_files(self, repository: str, commit: str = "HEAD") -> List[str]:
        root = self._repo(repository)
        output = self._run(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
        return [line for line in output.splitlines() if line]

    def compare(self, repository: str, baseline: str, current: str = "HEAD") -> Dict[str, Any]:
        root = self._repo(repository)
        output = self._run(root, "diff", "--name-status", baseline, current)
        files = [{"status": line.split("\t", 1)[0], "path": line.split("\t", 1)[1]} for line in output.splitlines() if "\t" in line]
        base_assets = self._discover_commit_files(root, baseline, files)
        current_assets = self._discover_commit_files(root, current, files)
        comparison = self.compare_findings(base_assets, current_assets)
        comparison.update({"baseline": baseline, "current": current, "changed_files": files})
        return comparison

    def compare_findings(self, baseline_assets: List[Dict[str, Any]], current_assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        def key(item: Dict[str, Any]) -> tuple:
            return (item.get("file_path"), item.get("algorithm"), item.get("key_length"), item.get("mode"))
        baseline_keys, current_keys = {key(item): item for item in baseline_assets}, {key(item): item for item in current_assets}
        added = [current_keys[item] for item in current_keys.keys() - baseline_keys.keys()]
        removed = [baseline_keys[item] for item in baseline_keys.keys() - current_keys.keys()]
        regressions = []
        for added_item in added:
            if added_item.get("algorithm") == "AES" and (added_item.get("key_length") or 0) < 256:
                regressions.append(added_item)
        events = ([{"event_type": "NEW_CRYPTO_ASSET", "evidence": added}] if added else []) + ([{"event_type": "REMOVED_CRYPTO_ASSET", "evidence": removed}] if removed else []) + ([{"event_type": "CRYPTO_REGRESSION", "evidence": regressions}] if regressions else [])
        return {"status": "CRYPTO_REGRESSION" if regressions else "CHANGES_DETECTED" if events else "NO_REGRESSION", "findings": {"new": added, "removed": removed, "regressions": regressions}, "events": events, "policy_result": "REVIEW_REQUIRED" if events else "PASS"}

    def _discover_commit_files(self, root: Path, commit: str, changed_files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        scanner = Scanner(root_dir=root)
        assets: List[Dict[str, Any]] = []
        for entry in changed_files:
            path = entry["path"]
            if Path(path).suffix.lower() not in {".py", ".java", ".c", ".cpp", ".h", ".hpp", ".pem", ".crt", ".key"}:
                continue
            try:
                content = self._run(root, "show", f"{commit}:{path}")
            except DiscoveryError:
                continue
            if len(content.encode("utf-8")) > 1_048_576:
                continue
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / Path(path).name
                target.write_text(content, encoding="utf-8")
                for asset in scanner.scan(target):
                    assets.append({"file_path": path, "algorithm": asset.algorithm, "key_length": asset.key_length, "mode": asset.mode, "asset_id": asset.asset_id})
        return assets

    def _repo(self, repository: str) -> Path:
        root = Path(repository).resolve()
        if not root.is_dir() or not (root / ".git").exists():
            raise DiscoveryError("Repository is not a Git working tree")
        return root

    def _run(self, cwd: Path, *args: str) -> str:
        try:
            completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True, timeout=self.timeout_seconds)
        except (OSError, subprocess.SubprocessError) as exc:
            raise DiscoveryError(f"Git operation failed: {exc}") from exc
        return completed.stdout.strip()
