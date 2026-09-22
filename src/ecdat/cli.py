"""
CryptoSentinel / ECDAT Command-Line Interface.

Usage:
    python -m ecdat.cli scan <target> [--format human|json|cbom] [--out <file>] [--lang python,java]

Examples:
    python -m ecdat.cli scan ./project
    python -m ecdat.cli scan ./project --format json
    python -m ecdat.cli scan ./project --format cbom --out cbom.json
    python -m ecdat.cli scan ./project --lang python,java --format json
"""

import argparse
import json
import sys
from pathlib import Path


def cmd_scan(args: argparse.Namespace) -> None:
    """Execute a crypto discovery scan and output results."""
    src_dir = Path(__file__).resolve().parent.parent.parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from ecdat.service import ScanService, ScannerError, AnalysisError

    target = args.target
    fmt = args.format.lower()
    output_file = args.out
    language_filters = [l.strip() for l in args.lang.split(",")] if args.lang else None
    generate_cbom = fmt == "cbom"

    service = ScanService()
    try:
        result = service.run_scan(
            target,
            language_filters=language_filters,
            generate_cbom=generate_cbom,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (ScannerError, AnalysisError) as exc:
        print(f"Scanner error: {exc}", file=sys.stderr)
        sys.exit(2)

    if fmt == "cbom":
        output_data = _format_cbom(result)
    elif fmt == "json":
        output_data = json.dumps(result, indent=2, default=str)
    else:
        output_data = _format_human(result)

    if output_file:
        Path(output_file).write_text(output_data, encoding="utf-8")
        print(f"Output written to: {output_file}", file=sys.stderr)
    else:
        print(output_data)


def _format_cbom(result: dict) -> str:
    cbom = result.get("cbom")
    if cbom is None:
        err = result.get("cbom_error", "CBOM generation failed.")
        print(f"CBOM error: {err}", file=sys.stderr)
        sys.exit(3)
    return json.dumps(cbom, indent=2, default=str)


def _format_human(result: dict) -> str:
    lines = []
    summary = result.get("summary", {})
    metadata = result.get("metadata", {})
    findings = result.get("findings", [])

    lines.append("=" * 70)
    lines.append("  CryptoSentinel — Cryptographic Discovery Report")
    lines.append("=" * 70)
    lines.append(f"  Target:         {metadata.get('target', 'unknown')}")
    lines.append(f"  Scanner:        v{metadata.get('scanner_version', '?')}")
    lines.append(f"  Scan Duration:  {metadata.get('scan_duration_ms', 0)}ms")
    lines.append(f"  Files Scanned:  {summary.get('total_files_scanned', 0)} / {summary.get('total_files_discovered', 0)}")
    lines.append(f"  Crypto Assets:  {summary.get('total_crypto_assets', 0)}")
    lines.append("")

    # Severity summary
    sc = summary.get("severity_counts", {})
    lines.append("  Risk Severity Breakdown:")
    for sev in ("critical", "high", "medium", "low", "info"):
        count = sc.get(sev, 0)
        bar = "█" * min(count, 40)
        lines.append(f"    {sev.upper():<10} {count:>4}  {bar}")
    lines.append("")

    # Algorithm distribution
    algo_dist = summary.get("algorithm_distribution", {})
    if algo_dist:
        lines.append("  Algorithm Distribution:")
        for algo, count in sorted(algo_dist.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"    {algo:<20} {count:>4}")
        lines.append("")

    # Language distribution
    lang_dist = summary.get("language_distribution", {})
    if lang_dist:
        lines.append("  Language Distribution:")
        for lang, count in sorted(lang_dist.items(), key=lambda x: -x[1]):
            lines.append(f"    {lang:<20} {count:>4}")
        lines.append("")

    # Findings
    lines.append(f"  Findings ({len(findings)} total):")
    lines.append("-" * 70)
    for idx, finding in enumerate(findings[:50], start=1):  # Limit to 50 in human mode
        algo = finding.get("algorithm", "?")
        cat = finding.get("category", "?")
        sev = finding.get("risk", {}).get("severity", "?").upper()
        loc = finding.get("file_location", {})
        purpose = finding.get("purpose") or "unknown"
        lib = finding.get("library", "?")
        file_path = loc.get("file_path", "?")
        lineno = loc.get("line_number", 0)
        snippet = finding.get("evidence", {}).get("code_snippet", "")[:80]
        lines.append(f"  [{idx:>3}] {sev:<10} {algo:<12} ({cat})")
        lines.append(f"        Purpose: {purpose}  Library: {lib}")
        lines.append(f"        Location: {file_path}:{lineno}")
        lines.append(f"        Evidence: {snippet}")
        lines.append("")

    if len(findings) > 50:
        lines.append(f"  ... and {len(findings) - 50} more findings (use --format json for full output)")
        lines.append("")

    lines.append("=" * 70)
    if summary.get("quantum_vulnerable_assets", 0) > 0:
        lines.append(f"  ⚠  {summary['quantum_vulnerable_assets']} quantum-vulnerable assets detected.")
    lines.append("  Run with --format cbom to export CycloneDX v1.6 CBOM.")
    lines.append("=" * 70)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ecdat",
        description="CryptoSentinel ECDAT — Enterprise Cryptographic Discovery & Analysis Tool",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Scan a target for cryptographic assets")
    scan_parser.add_argument("target", help="Path to scan (file or directory)")
    scan_parser.add_argument(
        "--format", "-f",
        choices=["human", "json", "cbom"],
        default="human",
        help="Output format: human-readable (default), JSON, or CycloneDX CBOM",
    )
    scan_parser.add_argument(
        "--out", "-o",
        default=None,
        help="Write output to this file instead of stdout",
    )
    scan_parser.add_argument(
        "--lang", "-l",
        default=None,
        help="Comma-separated list of languages to scan (e.g. python,java,go)",
    )
    scan_parser.set_defaults(func=cmd_scan)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
