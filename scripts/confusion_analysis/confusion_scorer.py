"""
---
title: Confusion Scorer
purpose: Calculate confusion scores from metrics
inputs:
  - name: metrics
    type: ComplexityMetrics
outputs:
  - name: score
    type: float
effects: []
deps: ['dataclasses']
owners: ['llm-architect']
stability: stable
since_version: 1.0.0
---

Calculates confusion scores using weighted metrics.
"""

from dataclasses import dataclass

from .complexity_analyzer import (
    MAX_COMPLEXITY,
    MAX_CONTEXT_SWITCHES,
    MAX_INDIRECTION,
    MAX_LINES,
    ComplexityMetrics,
)

# Scoring weights
WEIGHTS = {"complexity": 0.35, "indirection": 0.25, "context": 0.25, "loc": 0.15}

# Score thresholds
CRITICAL_SCORE = 70
HIGH_SCORE = 50
MODERATE_SCORE = 30


@dataclass
class ScoredFile:
    """File with confusion score and issues."""

    file_path: str
    metrics: ComplexityMetrics
    score: float
    issues: list[str]
    severity: str


class ConfusionScorer:
    """Calculates confusion scores from complexity metrics."""

    @staticmethod
    def calculate_score(metrics: ComplexityMetrics) -> float:
        """Calculate confusion score from metrics."""
        scores = ConfusionScorer._normalize_metrics(metrics)
        return ConfusionScorer._weighted_average(scores)

    @staticmethod
    def _normalize_metrics(metrics: ComplexityMetrics) -> dict[str, float]:
        """Normalize metrics to 0-100 scale."""
        return {
            "complexity": min(metrics.cyclomatic_complexity / MAX_COMPLEXITY * 100, 100),
            "indirection": min(metrics.indirection_depth / MAX_INDIRECTION * 100, 100),
            "context": min(metrics.context_switches / MAX_CONTEXT_SWITCHES * 100, 100),
            "loc": (
                min(metrics.lines_of_code / MAX_LINES * 100, 100)
                if metrics.lines_of_code > 200
                else 0
            ),
        }

    @staticmethod
    def _weighted_average(scores: dict[str, float]) -> float:
        """Calculate weighted average of scores."""
        total = sum(scores[key] * WEIGHTS[key] for key in WEIGHTS)
        return round(total, 1)

    @staticmethod
    def identify_issues(metrics: ComplexityMetrics) -> list[str]:
        """Identify specific issues from metrics."""
        issues = []

        if metrics.cyclomatic_complexity > MAX_COMPLEXITY:
            issues.append(
                f"High cyclomatic complexity: {metrics.cyclomatic_complexity} (target: <{MAX_COMPLEXITY})"
            )

        if metrics.indirection_depth > MAX_INDIRECTION:
            issues.append(
                f"Deep indirection: {metrics.indirection_depth} levels (target: <{MAX_INDIRECTION})"
            )

        if metrics.context_switches > MAX_CONTEXT_SWITCHES:
            issues.append(
                f"Many context switches: {metrics.context_switches} (target: <{MAX_CONTEXT_SWITCHES})"
            )

        if metrics.lines_of_code > MAX_LINES:
            issues.append(f"Large file: {metrics.lines_of_code} lines (target: <{MAX_LINES})")

        return issues

    @staticmethod
    def get_severity(score: float) -> str:
        """Determine severity level from score."""
        if score >= CRITICAL_SCORE:
            return "critical"
        elif score >= HIGH_SCORE:
            return "high"
        elif score >= MODERATE_SCORE:
            return "moderate"
        else:
            return "low"

    @staticmethod
    def score_file(file_path: str, metrics: ComplexityMetrics) -> ScoredFile:
        """Score a single file."""
        score = ConfusionScorer.calculate_score(metrics)
        issues = ConfusionScorer.identify_issues(metrics)
        severity = ConfusionScorer.get_severity(score)

        return ScoredFile(
            file_path=file_path, metrics=metrics, score=score, issues=issues, severity=severity
        )
