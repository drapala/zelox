"""
---
title: Confusion Reporter
purpose: Generate confusion analysis reports
inputs:
  - name: hotspots
    type: List[Hotspot]
  - name: scored_files
    type: List[ScoredFile]
outputs:
  - name: report
    type: Dict
effects:
  - Writes to stdout or file
deps: ['json', 'typing']
owners: ['llm-architect']
stability: stable
since_version: 1.0.0
---

Generates formatted confusion reports.
"""

import json
from pathlib import Path
from typing import Any

from .confusion_scorer import ScoredFile
from .hotspot_detector import Hotspot, HotspotDetector


class ConfusionReporter:
    """Generates confusion analysis reports."""

    @staticmethod
    def generate_report(
        scored_files: list[ScoredFile], hotspots: list[Hotspot], analysis_time: float
    ) -> dict[str, Any]:
        """Generate comprehensive confusion report."""
        if not scored_files:
            return ConfusionReporter._empty_report()

        summary = ConfusionReporter._calculate_summary(scored_files)
        impact = HotspotDetector.calculate_impact(hotspots)
        common_issues = HotspotDetector.get_common_issues(hotspots)

        return {
            "status": "success",
            "total_files": len(scored_files),
            "analysis_time": round(analysis_time, 2),
            "summary": summary,
            "impact": impact,
            "common_issues": [{"type": issue[0], "count": issue[1]} for issue in common_issues[:5]],
            "hotspots": ConfusionReporter._format_hotspots(hotspots[:10]),
            "thresholds": {
                "complexity": 10,
                "indirection": 3,
                "context_switches": 100,
                "lines_of_code": 200,
                "confusion_score": 50,
            },
        }

    @staticmethod
    def _empty_report() -> dict[str, Any]:
        """Generate empty report when no files analyzed."""
        return {"status": "no_files_analyzed", "total_files": 0, "hotspots": [], "summary": {}}

    @staticmethod
    def _calculate_summary(scored_files: list[ScoredFile]) -> dict[str, float]:
        """Calculate summary statistics."""
        count = len(scored_files)

        return {
            "average_complexity": round(
                sum(f.metrics.cyclomatic_complexity for f in scored_files) / count, 1
            ),
            "average_indirection": round(
                sum(f.metrics.indirection_depth for f in scored_files) / count, 1
            ),
            "average_context_switches": round(
                sum(f.metrics.context_switches for f in scored_files) / count, 1
            ),
            "average_confusion_score": round(sum(f.score for f in scored_files) / count, 1),
            "high_confusion_count": sum(1 for f in scored_files if f.score > 50),
            "critical_count": sum(1 for f in scored_files if f.score > 70),
        }

    @staticmethod
    def _format_hotspots(hotspots: list[Hotspot]) -> list[dict[str, Any]]:
        """Format hotspots for report."""
        return [
            {
                "rank": h.rank,
                "file": h.file_path,
                "score": h.score,
                "severity": h.severity,
                "issues": h.issues,
            }
            for h in hotspots
        ]

    @staticmethod
    def print_report(report: dict[str, Any]):
        """Print human-readable report to stdout."""
        print("\n" + "=" * 60)
        print("CONFUSION REPORT")
        print("=" * 60)

        if report["status"] == "no_files_analyzed":
            print("No Python files were analyzed.")
            return

        print(f"\nAnalyzed {report['total_files']} files in {report['analysis_time']} seconds")

        print("\n📊 SUMMARY STATISTICS:")
        summary = report["summary"]
        for key, value in summary.items():
            label = key.replace("_", " ").title()
            print(f"  • {label}: {value}")

        if report.get("common_issues"):
            print("\n⚠️  COMMON ISSUES:")
            for issue in report["common_issues"]:
                print(f"  • {issue['type']}: {issue['count']} occurrences")

        if report.get("hotspots"):
            print("\n🔥 TOP CONFUSION HOTSPOTS:")
            for hotspot in report["hotspots"][:5]:
                print(f"\n  {hotspot['rank']}. {hotspot['file']} (Score: {hotspot['score']})")
                for issue in hotspot["issues"][:2]:
                    print(f"     - {issue}")

        print("\n" + "=" * 60 + "\n")

    @staticmethod
    def save_json(report: dict[str, Any], output_path: Path):
        """Save report as JSON."""
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

    @staticmethod
    def save_markdown(report: dict[str, Any], output_path: Path):
        """Save report as Markdown."""
        content = ["# Confusion Analysis Report\n"]

        if report["status"] == "no_files_analyzed":
            content.append("No Python files were analyzed.")
        else:
            content.append(f"**Analyzed:** {report['total_files']} files")
            content.append(f"**Time:** {report['analysis_time']} seconds\n")

            content.append("## Summary Statistics\n")
            for key, value in report["summary"].items():
                label = key.replace("_", " ").title()
                content.append(f"- {label}: {value}")

            if report.get("hotspots"):
                content.append("\n## Top Hotspots\n")
                for h in report["hotspots"][:10]:
                    content.append(f"\n### {h['rank']}. {h['file']}")
                    content.append(f"- Score: {h['score']}")
                    content.append(f"- Severity: {h['severity']}")
                    if h["issues"]:
                        content.append("- Issues:")
                        for issue in h["issues"]:
                            content.append(f"  - {issue}")

        with open(output_path, "w") as f:
            f.write("\n".join(content))
