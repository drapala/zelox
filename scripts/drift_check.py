#!/usr/bin/env python3
"""
title: Drift Check - Simplified Main Entry Point
purpose: Coordinate drift detection using modular components
inputs: [{"name": "repo_root", "type": "path"}, {"name": "format", "type": "str"}]
outputs: [{"name": "report", "type": "str|json"}, {"name": "exit_code", "type": "int"}]
effects: ["validation", "reporting"]
deps: ["pathlib", "json", "argparse"]
owners: ["drapala"]
stability: stable
since_version: "0.4.0"
complexity: low
"""

import argparse
import json
import sys
from pathlib import Path

from drift_detection import BlockFinder, DriftCalculator, DriftReporter


def main() -> int:
    """Main entry point for drift checking."""
    parser = argparse.ArgumentParser(
        description="Check for controlled duplication drift",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check current repository
  %(prog)s
  
  # Generate JSON report
  %(prog)s --format json
  
  # Check specific directory
  %(prog)s --repo-root /path/to/repo
  
  # Generate markdown report
  %(prog)s --format markdown > drift_report.md
        """,
    )

    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory)",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "ci"],
        default="ci",
        help="Output format (default: ci)",
    )

    parser.add_argument("--output", type=Path, help="Output file (default: stdout)")

    args = parser.parse_args()

    # Run drift check
    try:
        exit_code = run_drift_check(
            repo_root=args.repo_root, format=args.format, output_file=args.output
        )
        return exit_code
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def run_drift_check(repo_root: Path, format: str = "ci", output_file: Path | None = None) -> int:
    """Run drift check with specified parameters."""
    # Step 1: Find blocks
    finder = BlockFinder(repo_root)
    blocks = finder.find_all()

    if not blocks:
        if format == "ci":
            print("✅ No duplicate blocks found")
        return 0

    # Step 2: Calculate drift
    calculator = DriftCalculator()
    results = calculator.calculate_all(blocks)
    stats = calculator.get_summary_stats(results)

    # Step 3: Generate report
    output = sys.stdout if output_file is None else open(output_file, "w")
    reporter = DriftReporter(output)

    try:
        if format == "json":
            report = reporter.report_json(results, stats)
            json.dump(report, output, indent=2)
            return 0 if stats["drifted_count"] == 0 else 1
        elif format == "text":
            text = reporter.report_text(results, stats)
            print(text, file=output)
            return 0 if stats["drifted_count"] == 0 else 1
        elif format == "markdown":
            markdown = reporter.report_markdown(results, stats)
            print(markdown, file=output)
            return 0 if stats["drifted_count"] == 0 else 1
        else:  # ci format
            return reporter.report_ci(results, stats)
    finally:
        if output_file and output != sys.stdout:
            output.close()


if __name__ == "__main__":
    sys.exit(main())
