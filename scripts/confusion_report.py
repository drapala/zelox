#!/usr/bin/env python3
"""
---
title: Confusion Report Orchestrator
purpose: Orchestrate confusion analysis pipeline
inputs:
  - name: repository_path
    type: Path
outputs:
  - name: confusion_report
    type: Dict
effects:
  - Analyzes Python files
  - Generates reports
deps:
  - confusion_analysis
  - pathlib
owners: ['llm-architect']
stability: stable
since_version: 2.0.0
---

Orchestrates confusion analysis using modular components.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

from confusion_analysis import (
    ComplexityAnalyzer,
    ConfusionReporter,
    ConfusionScorer,
    HotspotDetector,
)


def find_python_files(repo_root: Path) -> list[Path]:
    """Find all Python files in repository."""
    python_files = []

    for file_path in repo_root.rglob("*.py"):
        # Skip hidden and cache directories
        if any(part.startswith(".") or part == "__pycache__" for part in file_path.parts):
            continue
        python_files.append(file_path)

    return python_files


def analyze_file(file_path: Path, repo_root: Path):
    """Analyze single Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Analyze complexity
        metrics = ComplexityAnalyzer.analyze(content)

        # Calculate score
        relative_path = str(file_path.relative_to(repo_root))
        scored_file = ConfusionScorer.score_file(relative_path, metrics)

        return scored_file
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
        return None


def run_analysis(repo_root: Path) -> dict[str, Any]:
    """Run complete confusion analysis."""
    start_time = time.time()

    # Find Python files
    python_files = find_python_files(repo_root)

    # Analyze each file
    scored_files = []
    for file_path in python_files:
        result = analyze_file(file_path, repo_root)
        if result:
            scored_files.append(result)

    # Find hotspots
    hotspots = HotspotDetector.find_hotspots(scored_files)

    # Generate report
    elapsed_time = time.time() - start_time
    report = ConfusionReporter.generate_report(scored_files, hotspots, elapsed_time)

    return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate confusion report for Python codebase")
    parser.add_argument("path", nargs="?", default=".", help="Repository root path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Save report to file")
    parser.add_argument(
        "--format", choices=["json", "markdown"], default="json", help="Output format when saving"
    )

    args = parser.parse_args()

    repo_root = Path(args.path).resolve()

    if not repo_root.exists():
        print(f"Error: Path {repo_root} does not exist", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    report = run_analysis(repo_root)

    # Output results
    if args.output:
        output_path = Path(args.output)
        if args.format == "markdown":
            ConfusionReporter.save_markdown(report, output_path)
        else:
            ConfusionReporter.save_json(report, output_path)
        print(f"Report saved to {output_path}")
    elif args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        ConfusionReporter.print_report(report)


if __name__ == "__main__":
    main()
