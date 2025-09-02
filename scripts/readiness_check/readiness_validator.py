"""
Readiness Validator
Validate readiness scores against thresholds.
"""

from dataclasses import dataclass

from .readiness_calculator import ReadinessScore
from .readiness_metrics import MetricResult


@dataclass
class ValidationResult:
    """Result of threshold validation."""

    passed: bool
    score: float
    threshold: float
    failures: list[str]
    warnings: list[str]


@dataclass
class ThresholdConfig:
    """Configuration for validation thresholds."""

    min_overall_score: float = 80.0
    min_category_scores: dict[str, float] = None
    required_metrics: list[str] = None
    warning_threshold: float = 70.0

    def __post_init__(self):
        if self.min_category_scores is None:
            self.min_category_scores = {
                "co-location": 60.0,
                "complexity": 50.0,
                "documentation": 70.0,
            }
        if self.required_metrics is None:
            self.required_metrics = ["Co-location Index", "Cognitive Complexity"]


class ReadinessValidator:
    """Validate readiness scores against configurable thresholds."""

    def __init__(self, config: ThresholdConfig | None = None):
        self.config = config or ThresholdConfig()

    def validate(self, score: ReadinessScore) -> ValidationResult:
        """Validate a readiness score against thresholds."""
        failures = []
        warnings = []

        # Check overall score
        if score.percentage < self.config.min_overall_score:
            failures.append(
                f"Overall score {score.percentage:.1f}% "
                f"below threshold {self.config.min_overall_score}%"
            )
        elif score.percentage < self.config.warning_threshold:
            warnings.append(
                f"Overall score {score.percentage:.1f}% "
                f"approaching threshold {self.config.min_overall_score}%"
            )

        # Check required metrics
        for required in self.config.required_metrics:
            if required not in score.metric_results:
                failures.append(f"Required metric '{required}' not calculated")
            else:
                self._validate_metric(score.metric_results[required], required, failures, warnings)

        # Check category minimums
        self._validate_categories(score.metric_results, failures, warnings)

        return ValidationResult(
            passed=len(failures) == 0,
            score=score.percentage,
            threshold=self.config.min_overall_score,
            failures=failures,
            warnings=warnings,
        )

    def _validate_metric(
        self, result: MetricResult, metric_name: str, failures: list[str], warnings: list[str]
    ):
        """Validate individual metric result."""
        percentage = (result.score / result.max_score * 100) if result.max_score > 0 else 0

        if result.status == "❌":
            failures.append(f"Metric '{metric_name}' failed with {percentage:.1f}%")
        elif result.status == "⚠️":
            warnings.append(f"Metric '{metric_name}' needs improvement: {percentage:.1f}%")

    def _validate_categories(
        self, metric_results: dict[str, MetricResult], failures: list[str], warnings: list[str]
    ):
        """Validate category-level scores."""
        category_scores = self._calculate_category_scores(metric_results)

        for category, min_score in self.config.min_category_scores.items():
            if category in category_scores:
                score = category_scores[category]
                if score < min_score:
                    failures.append(
                        f"Category '{category}' score {score:.1f}% " f"below minimum {min_score}%"
                    )
                elif score < min_score + 10:
                    warnings.append(
                        f"Category '{category}' score {score:.1f}% "
                        f"approaching minimum {min_score}%"
                    )

    def _calculate_category_scores(
        self, metric_results: dict[str, MetricResult]
    ) -> dict[str, float]:
        """Calculate aggregate scores by category."""
        category_map = {
            "Co-location Index": "co-location",
            "Cognitive Complexity": "complexity",
            "Front-matter Coverage": "documentation",
            "Documentation Structure": "documentation",
            "ADR Structure": "documentation",
        }

        category_totals = {}
        category_max = {}

        for metric_name, result in metric_results.items():
            category = category_map.get(metric_name, "other")
            if category not in category_totals:
                category_totals[category] = 0
                category_max[category] = 0
            category_totals[category] += result.score
            category_max[category] += result.max_score

        return {
            cat: (total / category_max[cat] * 100 if category_max[cat] > 0 else 0)
            for cat, total in category_totals.items()
        }

    def get_exit_code(self, validation: ValidationResult) -> int:
        """Get appropriate exit code for CI/CD."""
        if not validation.passed:
            return 1
        if validation.warnings:
            return 0  # Pass with warnings
        return 0
