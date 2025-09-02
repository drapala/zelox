#!/usr/bin/env python3
"""
title: Semantic Dependency Analyzer (Wrapper)
purpose: Backward-compatible wrapper for new modular semantic analysis pipeline
inputs: [{"name": "codebase_path", "type": "path"}]
outputs: [
  {"name": "dependency_graph", "type": "json"},
  {"name": "complexity_report", "type": "dict"}
]
effects: ["delegates_to_pipeline"]
deps: ["semantic_analysis.semantic_pipeline"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: low

NOTE: This file has been refactored into a modular pipeline.
See scripts/semantic_analysis/ for the new implementation.
This wrapper maintains backward compatibility.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from semantic_analysis.semantic_pipeline import SemanticAnalysisPipeline
from semantic_analysis.semantic_reporter import SemanticReporter


class SemanticDependencyAnalyzer:
    """Backward-compatible wrapper for the new semantic analysis pipeline."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.pipeline = SemanticAnalysisPipeline(repo_root)
        self.complexity_metrics = {}

    def analyze_codebase(self) -> dict[str, Any]:
        """Perform full semantic analysis using the new pipeline."""
        # Run the new pipeline
        self.pipeline.analyze()

        # Convert to old format for compatibility
        if self.pipeline.report:
            return {
                "files_analyzed": self.pipeline.report.summary.get("files_analyzed", 0),
                "total_functions": self.pipeline.report.summary.get("total_functions", 0),
                "complexity_metrics": self.pipeline.report.metrics,
                "architectural_insights": self.pipeline.report.insights,
            }

        return {
            "files_analyzed": 0,
            "total_functions": 0,
            "complexity_metrics": {},
            "architectural_insights": [],
        }

    def export_graph(self, output_path: str) -> None:
        """Export dependency graph to JSON."""
        if self.pipeline.report:
            # Export using the new reporter
            reporter = SemanticReporter()
            reporter.export_json(self.pipeline.report, Path(output_path))
        else:
            # Export empty graph
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)


def main():
    """CLI interface for semantic analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Dependency Analysis (Refactored)")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--report", action="store_true", help="Print analysis report")

    args = parser.parse_args()

    # Use the new pipeline directly
    pipeline = SemanticAnalysisPipeline(args.repo_root)
    pipeline.analyze()

    if args.report:
        pipeline.print_report()

    if args.output:
        pipeline.save_report(args.output)


if __name__ == "__main__":
    main()
