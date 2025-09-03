#!/usr/bin/env python3
"""
---
title: Domain Analysis Reporter
purpose: Generate domain analysis reports and CLI interface
inputs:
  - name: analysis_results
    type: dict
outputs:
  - name: report
    type: str
effects: ["console_output"]
deps: ["argparse", "json"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
---
"""

import argparse
import json
from typing import Any

from domain_mapper import map_domain_boundaries
from domain_rules import (
    calculate_coherence_score,
    detect_boundary_violations,
    generate_vsa_recommendations,
)


class DomainPatternDetector:
    """Main class combining domain analysis capabilities."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root

    def analyze(self) -> dict[str, Any]:
        """Perform complete domain analysis."""
        print("Analyzing domain boundaries...")

        mapping = map_domain_boundaries(self.repo_root)

        # file_domains is currently unused; keep feature-level aggregation
        _ = mapping["file_domains"]
        feature_domains = mapping["feature_domains"]

        violations = detect_boundary_violations(feature_domains)
        coherence = calculate_coherence_score(feature_domains)
        recommendations = generate_vsa_recommendations(feature_domains, violations)

        return {
            "files_analyzed": mapping["files_analyzed"],
            "feature_domains": feature_domains,
            "boundary_violations": len(violations),
            "domain_coherence_score": coherence,
            "recommendations": recommendations,
        }

    def generate_report(self) -> str:
        """Generate human-readable domain analysis report."""
        results = self.analyze()

        report = ["=== Domain Pattern Analysis Report ===", ""]
        report.append(f"Files analyzed: {results['files_analyzed']}")
        report.append(f"Features detected: {len(results['feature_domains'])}")
        report.append(f"Boundary violations: {results['boundary_violations']}")
        report.append(f"Domain coherence score: {results['domain_coherence_score']:.2f}")
        report.append("")

        if results["feature_domains"]:
            report.append("Feature Domain Summary:")
            for feature, data in results["feature_domains"].items():
                top_terms = data["domain_terms"].most_common(5)
                terms_str = ", ".join([f"{term}({count})" for term, count in top_terms])
                report.append(f"  {feature}: {terms_str}")
            report.append("")

        if results["recommendations"]:
            report.append("Recommendations:")
            for rec in results["recommendations"]:
                report.append(f"  [{rec['priority'].upper()}] {rec['type']}: {rec['reason']}")
            report.append("")

        return "\n".join(report)


def main():
    """CLI interface for domain analysis."""
    parser = argparse.ArgumentParser(description="Domain Pattern Detection")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--json", action="store_true", help="Output JSON results")

    args = parser.parse_args()

    detector = DomainPatternDetector(args.repo_root)

    if args.report:
        print(detector.generate_report())
    elif args.json:
        results = detector.analyze()
        for feature_data in results.get("feature_domains", {}).values():
            if "domain_terms" in feature_data:
                feature_data["domain_terms"] = dict(feature_data["domain_terms"])
        print(json.dumps(results, indent=2, default=str))
    else:
        results = detector.analyze()
        print(f"Domain coherence: {results['domain_coherence_score']:.2f}")
        print(f"Recommendations: {len(results['recommendations'])}")


if __name__ == "__main__":
    main()
