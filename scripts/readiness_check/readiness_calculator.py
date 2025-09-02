"""
Readiness Score Calculator
Calculate overall LLM readiness scores from metrics.
"""

from dataclasses import dataclass, field
from pathlib import Path

from .cognitive_metrics import CognitiveComplexityMetric
from .documentation_metrics import ADRMetric, DocumentationStructureMetric
from .readiness_metrics import CoLocationMetric, FrontMatterMetric, MetricPlugin, MetricResult


@dataclass
class ReadinessScore:
    """Overall readiness score with breakdown."""

    total_score: float
    max_score: float
    percentage: float
    status: str
    metric_results: dict[str, MetricResult] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    passed: bool = False


class ReadinessCalculator:
    """Calculate LLM readiness scores using pluggable metrics."""

    def __init__(self, repo_root: Path, metric_plugins: list[MetricPlugin] | None = None):
        self.repo_root = repo_root
        self.metric_plugins = metric_plugins or self._get_default_plugins()

    def _get_default_plugins(self) -> list[MetricPlugin]:
        """Get default set of metric plugins."""
        return [
            CoLocationMetric(self.repo_root),
            CognitiveComplexityMetric(self.repo_root),
            FrontMatterMetric(self.repo_root),
            DocumentationStructureMetric(self.repo_root),
            ADRMetric(self.repo_root),
        ]

    def calculate(self) -> ReadinessScore:
        """Calculate overall readiness score."""
        metric_results = {}
        total_score = 0
        max_score = 0

        # Calculate each metric
        for plugin in self.metric_plugins:
            try:
                result = plugin.calculate()
                metric_name = plugin.metric_definition.name
                metric_results[metric_name] = result
                total_score += result.score
                max_score += result.max_score
            except Exception as e:
                # Handle metric calculation failures gracefully
                metric_name = getattr(plugin.metric_definition, "name", plugin.__class__.__name__)
                metric_results[metric_name] = MetricResult(
                    score=0,
                    max_score=plugin.metric_definition.weight,
                    status="❌",
                    message=f"Calculation failed: {str(e)}",
                )
                max_score += plugin.metric_definition.weight

        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        status = self._calculate_status(percentage)
        recommendations = self._generate_recommendations(metric_results, percentage)

        return ReadinessScore(
            total_score=round(total_score, 1),
            max_score=max_score,
            percentage=round(percentage, 1),
            status=status,
            metric_results=metric_results,
            recommendations=recommendations,
            passed=percentage >= 80,
        )

    def _calculate_status(self, percentage: float) -> str:
        """Calculate overall status based on percentage."""
        if percentage >= 80:
            return "✅ PASS"
        elif percentage >= 60:
            return "⚠️ NEEDS IMPROVEMENT"
        return "❌ FAIL"

    def _generate_recommendations(
        self, metric_results: dict[str, MetricResult], percentage: float
    ) -> list[str]:
        """Generate recommendations based on results."""
        recommendations = []

        if percentage >= 80:
            recommendations.append("Repository meets LLM-first standards! 🎉")
            return recommendations

        # Check specific metrics for targeted recommendations
        for metric_name, result in metric_results.items():
            if result.status == "❌":
                recommendations.extend(self._get_metric_recommendations(metric_name, result))

        # General recommendations based on score range
        if percentage < 60:
            recommendations.extend(
                [
                    "Consider adopting vertical slice architecture",
                    "Create comprehensive repository documentation",
                    "Implement consistent metric tracking",
                ]
            )
        elif percentage < 80:
            recommendations.extend(
                ["Review and optimize high-complexity areas", "Improve test coverage patterns"]
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    def _get_metric_recommendations(self, metric_name: str, result: MetricResult) -> list[str]:
        """Get specific recommendations for a failed metric."""
        recommendations_map = {
            "Co-location Index": ["Move tests closer to feature code", "Adopt VSA structure"],
            "Cognitive Complexity": [
                "Break down complex functions",
                "Reduce nesting and indirection",
            ],
            "Front-matter Coverage": [
                "Add structured documentation to files",
                "Use YAML front-matter",
            ],
            "Documentation Structure": [
                "Create missing documentation files",
                "Update REPO_MAP.md",
            ],
            "ADR Structure": ["Document architectural decisions", "Create ADR templates"],
        }
        return recommendations_map.get(metric_name, [])
