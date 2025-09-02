#!/usr/bin/env python3
"""
title: Learning Reporter Module
purpose: Generate reports and insights from learning system
inputs: [{"name": "patterns", "type": "list"}, {"name": "recommendations", "type": "list"}, {"name": "metrics", "type": "dict"}]
outputs: [{"name": "report", "type": "dict"}, {"name": "insights", "type": "list[str]"}]
effects: ["report_generation", "insight_extraction"]
deps: ["json", "dataclasses"]
owners: ["drapala"]
stability: experimental
since_version: "0.5.0"
"""

import json
from typing import Any


class LearningReporter:
    """Generate reports and insights from the learning system."""

    def __init__(self):
        self.report_history: list[dict[str, Any]] = []

    def generate_report(
        self,
        patterns: list[Any],
        recommendations: list[Any],
        metrics: dict[str, Any],
        predictions: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive learning system report."""
        report = {
            "summary": self._generate_summary(patterns, recommendations, predictions),
            "patterns": self._format_patterns(patterns),
            "recommendations": self._format_recommendations(recommendations),
            "metrics": metrics,
            "predictions": predictions,
            "insights": self._generate_insights(patterns, recommendations, metrics),
        }

        self.report_history.append(report)
        return report

    def _generate_summary(
        self, patterns: list[Any], recommendations: list[Any], predictions: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate executive summary."""
        if not patterns:
            return {
                "status": "insufficient_data",
                "patterns_learned": 0,
                "recommendations_generated": 0,
                "confidence": 0.0,
                "message": "Insufficient telemetry data for pattern learning",
            }

        high_success = len([p for p in patterns if p.success_rate > 0.7])
        high_priority = len([r for r in recommendations if r.expected_impact == "high"])

        return {
            "status": "success",
            "patterns_learned": len(patterns),
            "high_success_patterns": high_success,
            "recommendations_generated": len(recommendations),
            "high_priority_recommendations": high_priority,
            "confidence": predictions.get("confidence", 0.0),
            "trend": predictions.get("trend", "unknown"),
        }

    def _format_patterns(self, patterns: list[Any]) -> list[dict[str, Any]]:
        """Format patterns for reporting."""
        if not patterns:
            return []

        formatted = []
        for pattern in patterns[:5]:
            formatted.append(
                {
                    "id": pattern.pattern_id,
                    "description": pattern.description,
                    "success_rate": f"{pattern.success_rate:.1%}",
                    "confidence": f"{pattern.confidence_score:.1%}",
                    "sample_size": pattern.sample_size,
                    "key_traits": pattern.architectural_traits,
                }
            )

        return formatted

    def _format_recommendations(self, recommendations: list[Any]) -> list[dict[str, Any]]:
        """Format recommendations for reporting."""
        if not recommendations:
            return []

        formatted = []
        for rec in recommendations[:10]:
            formatted.append(
                {
                    "id": rec.suggestion_id,
                    "title": rec.title,
                    "description": rec.description,
                    "impact": rec.expected_impact,
                    "effort": rec.effort_estimate,
                    "success_probability": f"{rec.success_probability:.1%}",
                    "steps": rec.implementation_steps,
                }
            )

        return formatted

    def _generate_insights(
        self, patterns: list[Any], recommendations: list[Any], metrics: dict[str, Any]
    ) -> list[str]:
        """Generate actionable insights."""
        insights = []

        if patterns:
            avg_success = sum(p.success_rate for p in patterns) / len(patterns)
            if avg_success > 0.7:
                insights.append("✅ Architecture patterns show high success rate overall")
            elif avg_success < 0.4:
                insights.append("⚠️ Current patterns indicate architectural challenges")

            high_hop_patterns = [
                p for p in patterns if "high_hops" in p.context_features and p.success_rate < 0.5
            ]
            if high_hop_patterns:
                insights.append(
                    f"🔍 {len(high_hop_patterns)} patterns with high cognitive complexity "
                    "show reduced success rates"
                )

        if recommendations:
            high_impact = [r for r in recommendations if r.expected_impact == "high"]
            if high_impact:
                insights.append(f"🎯 {len(high_impact)} high-impact improvements identified")

            easy_wins = [
                r
                for r in recommendations
                if r.effort_estimate == "easy" and r.success_probability > 0.7
            ]
            if easy_wins:
                insights.append(
                    f"💡 {len(easy_wins)} quick wins available with high success probability"
                )

        hotspots = metrics.get("hotspot_files", [])
        if len(hotspots) > 5:
            insights.append(
                f"⚡ {len(hotspots)} dependency hotspots detected - consider refactoring"
            )

        return insights

    def export_report(self, report: dict[str, Any], format: str = "json") -> str:
        """Export report in specified format."""
        if format == "json":
            return json.dumps(report, indent=2)
        elif format == "markdown":
            return self._format_markdown(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _format_markdown(self, report: dict[str, Any]) -> str:
        """Format report as markdown."""
        lines = ["# Learning System Report", ""]

        summary = report["summary"]
        lines.append("## Summary")
        lines.append(f"- Status: {summary['status']}")
        lines.append(f"- Patterns Learned: {summary['patterns_learned']}")
        lines.append(f"- Recommendations: {summary['recommendations_generated']}")
        lines.append(f"- Confidence: {summary['confidence']:.1%}")
        lines.append(f"- Trend: {summary['trend']}")
        lines.append("")

        if report["insights"]:
            lines.append("## Key Insights")
            for insight in report["insights"]:
                lines.append(f"- {insight}")
            lines.append("")

        if report["recommendations"]:
            lines.append("## Top Recommendations")
            for rec in report["recommendations"][:3]:
                lines.append(f"### {rec['title']}")
                lines.append(f"- Impact: {rec['impact']}")
                lines.append(f"- Effort: {rec['effort']}")
                lines.append(f"- Success Probability: {rec['success_probability']}")
                lines.append("")

        return "\n".join(lines)
