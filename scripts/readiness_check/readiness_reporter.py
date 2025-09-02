"""
Readiness Reporter
Generate reports from readiness assessment results.
"""

import json
from enum import Enum
from pathlib import Path

from .readiness_calculator import ReadinessScore
from .readiness_validator import ValidationResult


class ReportFormat(Enum):
    """Available report formats."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class ReadinessReporter:
    """Generate reports in various formats."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path(".")

    def generate(
        self,
        score: ReadinessScore,
        validation: ValidationResult | None = None,
        format: ReportFormat = ReportFormat.TEXT,
    ) -> str:
        """Generate report in specified format."""
        if format == ReportFormat.TEXT:
            return self._generate_text(score, validation)
        elif format == ReportFormat.JSON:
            return self._generate_json(score, validation)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown(score, validation)
        elif format == ReportFormat.HTML:
            return self._generate_html(score, validation)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_text(self, score: ReadinessScore, validation: ValidationResult | None) -> str:
        """Generate plain text report."""
        lines = []
        lines.append("=" * 60)
        lines.append("LLM READINESS ASSESSMENT")
        lines.append("=" * 60)
        lines.append("")

        # Overall score
        lines.append(f"Overall Score: {score.total_score:.1f}/{score.max_score} ")
        lines.append(f"({score.percentage:.1f}%) - {score.status}")
        lines.append("")

        # Validation result
        if validation:
            if validation.passed:
                lines.append("✅ Validation: PASSED")
            else:
                lines.append("❌ Validation: FAILED")
                for failure in validation.failures:
                    lines.append(f"  - {failure}")
            lines.append("")

        # Detailed results
        lines.append("Detailed Results:")
        lines.append("-" * 40)
        for metric_name, result in score.metric_results.items():
            lines.append(f"{result.status} {metric_name}: {result.message}")

        # Recommendations
        if score.recommendations:
            lines.append("")
            lines.append("Recommendations:")
            lines.append("-" * 20)
            for i, rec in enumerate(score.recommendations, 1):
                lines.append(f"{i}. {rec}")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _generate_json(self, score: ReadinessScore, validation: ValidationResult | None) -> str:
        """Generate JSON report."""
        report = {
            "score": {
                "total": score.total_score,
                "max": score.max_score,
                "percentage": score.percentage,
                "status": score.status,
                "passed": score.passed,
            },
            "metrics": {},
            "recommendations": score.recommendations,
        }

        # Add metric details
        for metric_name, result in score.metric_results.items():
            report["metrics"][metric_name] = {
                "score": result.score,
                "max_score": result.max_score,
                "status": result.status,
                "message": result.message,
                "details": result.details,
            }

        # Add validation if present
        if validation:
            report["validation"] = {
                "passed": validation.passed,
                "threshold": validation.threshold,
                "failures": validation.failures,
                "warnings": validation.warnings,
            }

        return json.dumps(report, indent=2)

    def _generate_markdown(self, score: ReadinessScore, validation: ValidationResult | None) -> str:
        """Generate Markdown report."""
        lines = []
        lines.append("# LLM Readiness Assessment Report")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append(f"**Score:** {score.total_score:.1f}/{score.max_score} ")
        lines.append(f"({score.percentage:.1f}%)")
        lines.append(f"**Status:** {score.status}")
        lines.append("")

        # Validation
        if validation:
            lines.append("## Validation")
            if validation.passed:
                lines.append("✅ **PASSED**")
            else:
                lines.append("❌ **FAILED**")
                lines.append("")
                lines.append("### Failures")
                for failure in validation.failures:
                    lines.append(f"- {failure}")
            if validation.warnings:
                lines.append("")
                lines.append("### Warnings")
                for warning in validation.warnings:
                    lines.append(f"- {warning}")
            lines.append("")

        # Metrics
        lines.append("## Metric Results")
        lines.append("")
        lines.append("| Metric | Score | Status | Message |")
        lines.append("|--------|-------|--------|---------|")
        for metric_name, result in score.metric_results.items():
            score_str = f"{result.score:.1f}/{result.max_score:.0f}"
            lines.append(f"| {metric_name} | {score_str} | {result.status} | {result.message} |")
        lines.append("")

        # Recommendations
        if score.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for rec in score.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)

    def _generate_html(self, score: ReadinessScore, validation: ValidationResult | None) -> str:
        """Generate HTML report."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("  <title>LLM Readiness Report</title>")
        html.append("  <style>")
        html.append("    body { font-family: sans-serif; margin: 20px; }")
        html.append("    .pass { color: green; }")
        html.append("    .fail { color: red; }")
        html.append("    .warn { color: orange; }")
        html.append("    table { border-collapse: collapse; width: 100%; }")
        html.append("    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("    th { background-color: #f2f2f2; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("  <h1>LLM Readiness Assessment</h1>")

        # Score
        status_class = "pass" if score.passed else "fail"
        html.append(
            f'  <h2 class="{status_class}">Score: {score.percentage:.1f}% - {score.status}</h2>'
        )

        # Metrics table
        html.append("  <h3>Metrics</h3>")
        html.append("  <table>")
        html.append("    <tr><th>Metric</th><th>Score</th><th>Status</th></tr>")
        for metric_name, result in score.metric_results.items():
            html.append(
                f"    <tr><td>{metric_name}</td><td>{result.score:.1f}/{result.max_score}</td>"
                f"<td>{result.status} {result.message}</td></tr>"
            )
        html.append("  </table>")

        # Recommendations
        if score.recommendations:
            html.append("  <h3>Recommendations</h3>")
            html.append("  <ul>")
            for rec in score.recommendations:
                html.append(f"    <li>{rec}</li>")
            html.append("  </ul>")

        html.append("</body>")
        html.append("</html>")
        return "\n".join(html)

    def save(self, report: str, format: ReportFormat, filename: str | None = None) -> Path:
        """Save report to file."""
        if filename is None:
            extension = format.value if format != ReportFormat.TEXT else "txt"
            filename = f"readiness_report.{extension}"

        output_path = self.output_dir / filename
        output_path.write_text(report)
        return output_path
