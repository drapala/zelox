#!/usr/bin/env python3
"""
title: Semantic Analysis Reporter
purpose: Generate reports from semantic analysis scores
inputs: [{name: "scores", type: "QualityScores"}, {name: "patterns", type: "SemanticPatterns"}]
outputs: [{name: "report", type: "AnalysisReport"}]
effects: ["report_generation", "json_export"]
deps: ["json", "dataclasses", "pathlib"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: low
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from semantic_extractor import SemanticPatterns
from semantic_scorer import QualityScores


@dataclass
class AnalysisReport:
    """Complete semantic analysis report."""

    summary: dict[str, Any]
    metrics: dict[str, Any]
    insights: list[str]
    recommendations: list[str]
    details: dict[str, Any] = field(default_factory=dict)


class SemanticReporter:
    """Generate reports from semantic analysis."""

    def __init__(self):
        self.report = AnalysisReport(summary={}, metrics={}, insights=[], recommendations=[])

    def generate_report(
        self, scores: QualityScores, patterns: SemanticPatterns, file_count: int = 0
    ) -> AnalysisReport:
        """Generate comprehensive analysis report."""
        # Build summary
        self._build_summary(scores, patterns, file_count)

        # Add metrics
        self._add_metrics(scores)

        # Add insights and recommendations
        self.report.insights = scores.insights
        self.report.recommendations = scores.recommendations

        # Add detailed patterns
        self._add_details(patterns)

        return self.report

    def _build_summary(
        self, scores: QualityScores, patterns: SemanticPatterns, file_count: int
    ) -> None:
        """Build report summary."""
        self.report.summary = {
            "files_analyzed": file_count,
            "llm_readiness_score": round(scores.llm_readiness_score, 1),
            "status": self._get_status(scores.llm_readiness_score),
            "total_functions": len(patterns.dependency_graph.call_graph),
            "cyclic_dependencies": len(patterns.cyclic_deps),
            "hotspots": len(patterns.hotspots),
        }

    def _get_status(self, score: float) -> str:
        """Get status based on LLM readiness score."""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 60:
            return "needs_improvement"
        else:
            return "poor"

    def _add_metrics(self, scores: QualityScores) -> None:
        """Add complexity metrics to report."""
        metrics = scores.complexity_metrics
        self.report.metrics = {
            "average_imports_per_file": round(metrics.avg_imports_per_file, 1),
            "max_call_chain_depth": metrics.max_call_chain_depth,
            "cyclic_dependency_count": metrics.cyclic_dependency_count,
            "hotspot_count": metrics.hotspot_count,
            "isolation_score": round(metrics.isolation_score, 2),
        }

    def _add_details(self, patterns: SemanticPatterns) -> None:
        """Add detailed pattern information."""
        # Add hotspot details
        if patterns.hotspots:
            self.report.details["hotspots"] = patterns.hotspots[:10]  # Top 10

        # Add cyclic dependency details
        if patterns.cyclic_deps:
            self.report.details["cyclic_dependencies"] = [
                {"type": dep.type, "cycle": dep.cycle[:5]}  # Limit cycle display
                for dep in patterns.cyclic_deps[:5]  # Top 5 cycles
            ]

        # Add deep call chains
        deep_chains = [c for c in patterns.call_chains if c.depth > 5]
        if deep_chains:
            self.report.details["deep_call_chains"] = [
                {
                    "function": chain.function.split("::")[-1],
                    "depth": chain.depth,
                    "sample_chain": chain.chain[:5],  # Sample of chain
                }
                for chain in sorted(deep_chains, key=lambda x: x.depth, reverse=True)[:5]
            ]

        # Add feature isolation details
        if patterns.feature_isolation:
            self.report.details["feature_isolation"] = {
                feature: round(score, 2) for feature, score in patterns.feature_isolation.items()
            }

    def export_json(self, report: AnalysisReport, output_path: Path) -> None:
        """Export report to JSON file."""
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2)

    def export_markdown(self, report: AnalysisReport, output_path: Path) -> None:
        """Export report to Markdown file."""
        md_content = self._generate_markdown(report)
        output_path.write_text(md_content, encoding="utf-8")

    def _generate_markdown(self, report: AnalysisReport) -> str:
        """Generate Markdown formatted report."""
        lines = []

        # Header
        lines.append("# Semantic Analysis Report")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append(f"- **Files Analyzed:** {report.summary['files_analyzed']}")
        lines.append(f"- **LLM Readiness Score:** {report.summary['llm_readiness_score']}/100")
        lines.append(f"- **Status:** {report.summary['status'].replace('_', ' ').title()}")
        lines.append(f"- **Total Functions:** {report.summary['total_functions']}")
        lines.append("")

        # Metrics
        lines.append("## Complexity Metrics")
        for key, value in report.metrics.items():
            formatted_key = key.replace("_", " ").title()
            lines.append(f"- **{formatted_key}:** {value}")
        lines.append("")

        # Insights
        if report.insights:
            lines.append("## Insights")
            for insight in report.insights:
                lines.append(f"- {insight}")
            lines.append("")

        # Recommendations
        if report.recommendations:
            lines.append("## Recommendations")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        # Details
        if report.details:
            lines.append("## Details")

            if "hotspots" in report.details:
                lines.append("### Dependency Hotspots")
                for hotspot in report.details["hotspots"][:5]:
                    lines.append(
                        f"- **{hotspot['module']}**: {hotspot['dependency_count']} dependencies ({hotspot['risk_level']} risk)"
                    )
                lines.append("")

            if "cyclic_dependencies" in report.details:
                lines.append("### Cyclic Dependencies")
                for cycle in report.details["cyclic_dependencies"]:
                    cycle_str = " → ".join(cycle["cycle"][:3])
                    if len(cycle["cycle"]) > 3:
                        cycle_str += " → ..."
                    lines.append(f"- {cycle['type'].title()}: {cycle_str}")
                lines.append("")

        return "\n".join(lines)

    def print_report(self, report: AnalysisReport) -> None:
        """Print report to console."""
        print("=== Semantic Analysis Report ===")
        print(f"Files analyzed: {report.summary['files_analyzed']}")
        print(f"LLM Readiness Score: {report.summary['llm_readiness_score']}/100")
        print(f"Status: {report.summary['status'].replace('_', ' ').title()}")
        print()

        print("Complexity Metrics:")
        for key, value in report.metrics.items():
            formatted_key = key.replace("_", " ").title()
            print(f"  {formatted_key}: {value}")
        print()

        if report.insights:
            print("Insights:")
            for insight in report.insights:
                print(f"  - {insight}")
            print()

        if report.recommendations:
            print("Recommendations:")
            for rec in report.recommendations:
                print(f"  - {rec}")


def generate_report(
    scores: QualityScores, patterns: SemanticPatterns, file_count: int = 0
) -> AnalysisReport:
    """Generate analysis report from scores and patterns."""
    reporter = SemanticReporter()
    return reporter.generate_report(scores, patterns, file_count)
