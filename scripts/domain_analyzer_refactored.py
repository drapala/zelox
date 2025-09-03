#!/usr/bin/env python3
"""
---
title: Domain Analyzer CLI
purpose: Orchestrate domain analysis using modular components
inputs:
  - name: repo_root
    type: str
    default: "."
outputs:
  - name: domain_report
    type: dict
  - name: vsa_recommendations
    type: list
effects: ["reads_filesystem", "writes_report"]
deps: ["domain_analysis", "argparse", "json"]
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

from domain_analysis.domain_mapper import DomainMapper
from domain_analysis.domain_reporter import DomainReporter
from domain_analysis.domain_rules import BoundaryAnalyzer


class DomainAnalyzerCLI:
    """CLI orchestrator for domain analysis."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.mapper = DomainMapper(repo_root)
        self.analyzer = BoundaryAnalyzer()
        self.reporter = DomainReporter()

    def run_analysis(self) -> dict[str, Any]:
        """Execute complete domain analysis pipeline."""
        # Step 1: Map domain structure
        mapping = self.mapper.map_domain()

        # Step 2: Analyze boundaries
        violations = self.analyzer.analyze_boundaries(mapping)

        # Step 3: Generate recommendations
        recommendations = self.analyzer.generate_recommendations(mapping, violations)

        return {
            "mapping": mapping,
            "violations": violations,
            "recommendations": recommendations,
            "summary": self._generate_summary(mapping, violations),
        }

    def _generate_summary(
        self, mapping: dict[str, Any], violations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate analysis summary."""
        return {
            "files_analyzed": len(mapping.get("files", [])),
            "features_detected": len(mapping.get("features", [])),
            "boundary_violations": len(violations),
            "domain_coherence_score": self._calculate_score(mapping),
        }

    def _calculate_score(self, mapping: dict[str, Any]) -> float:
        """Calculate domain coherence score."""
        if not mapping.get("features"):
            return 0.0

        total_features = len(mapping["features"])
        coherent_features = sum(1 for f in mapping["features"] if f.get("coherence", 0) > 0.7)

        return coherent_features / total_features if total_features > 0 else 0.0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Domain Pattern Detection and Analysis")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    parser.add_argument("--output", help="Output file path (optional)")

    args = parser.parse_args()

    try:
        analyzer = DomainAnalyzerCLI(args.repo_root)
        results = analyzer.run_analysis()

        if args.report:
            reporter = DomainReporter()
            report = reporter.generate_report(results)

            if args.output:
                Path(args.output).write_text(report)
                print(f"Report written to {args.output}")
            else:
                print(report)

        elif args.json:
            output = json.dumps(results, indent=2, default=str)

            if args.output:
                Path(args.output).write_text(output)
                print(f"JSON written to {args.output}")
            else:
                print(output)

        else:
            summary = results["summary"]
            print(f"Domain coherence: {summary['domain_coherence_score']:.2f}")
            print(f"Violations: {summary['boundary_violations']}")
            print(f"Recommendations: {len(results['recommendations'])}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
