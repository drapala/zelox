#!/usr/bin/env python3
"""
---
title: Semantic Analyzer CLI
purpose: Orchestrate semantic analysis using modular components
inputs:
  - name: repo_root
    type: str
    default: "."
outputs:
  - name: analysis_results
    type: dict
  - name: dependency_graph
    type: json
effects: ["reads_filesystem", "generates_graph"]
deps: ["semantic_analysis", "argparse", "json", "pathlib"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: low
---
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from semantic_analysis.semantic_extractor import CallChainExtractor
from semantic_analysis.semantic_parser import DependencyParser
from semantic_analysis.semantic_reporter import SemanticReporter
from semantic_analysis.semantic_scorer import ComplexityScorer


class SemanticAnalyzerCLI:
    """CLI orchestrator for semantic dependency analysis."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.extractor = CallChainExtractor(repo_root)
        self.parser = DependencyParser(repo_root)
        self.scorer = ComplexityScorer()
        self.reporter = SemanticReporter()

    def run_analysis(self) -> dict[str, Any]:
        """Execute complete semantic analysis pipeline."""
        # Step 1: Extract call chains
        call_chains = self.extractor.extract_all()

        # Step 2: Parse dependencies
        dependencies = self.parser.parse_dependencies(call_chains)

        # Step 3: Calculate complexity scores
        metrics = self.scorer.calculate_metrics(call_chains=call_chains, dependencies=dependencies)

        # Step 4: Generate insights
        insights = self.scorer.generate_insights(metrics)

        return {
            "call_chains": call_chains,
            "dependencies": dependencies,
            "metrics": metrics,
            "insights": insights,
            "summary": self._generate_summary(call_chains, metrics),
        }

    def _generate_summary(
        self, call_chains: dict[str, Any], metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate analysis summary."""
        return {
            "files_analyzed": len(call_chains.get("files", [])),
            "total_functions": sum(
                len(f.get("functions", [])) for f in call_chains.get("files", {}).values()
            ),
            "average_complexity": metrics.get("average_complexity", 0),
            "max_depth": metrics.get("max_call_chain_depth", 0),
            "isolation_score": metrics.get("isolation_score", 0),
        }

    def export_graph(self, output_path: str, results: dict[str, Any]) -> None:
        """Export dependency graph to JSON."""
        graph_data = {
            "dependencies": results["dependencies"],
            "metrics": results["metrics"],
            "insights": results["insights"],
            "timestamp": str(Path(output_path).stat().st_mtime),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Semantic Dependency Analysis for LLM-First Architecture"
    )
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--report", action="store_true", help="Print analysis report")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    try:
        analyzer = SemanticAnalyzerCLI(args.repo_root)
        results = analyzer.run_analysis()

        if args.report:
            reporter = SemanticReporter()
            print(reporter.generate_report(results))

        if args.json:
            print(json.dumps(results, indent=2, default=str))

        if args.output:
            analyzer.export_graph(args.output, results)
            print(f"Graph exported to {args.output}")

        # Exit with appropriate code
        metrics = results.get("metrics", {})
        if metrics.get("isolation_score", 0) < 0.7:
            return 1  # Poor isolation
        if metrics.get("max_call_chain_depth", 0) > 10:
            return 1  # Too complex

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
