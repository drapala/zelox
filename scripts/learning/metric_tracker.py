#!/usr/bin/env python3
"""
title: Metrics Tracking Module
purpose: Track and aggregate learning system metrics
inputs: [{"name": "patterns", "type": "list[ArchitecturalPattern]"}, {"name": "metrics", "type": "dict"}]
outputs: [{"name": "metrics_summary", "type": "dict"}, {"name": "predictions", "type": "dict"}]
effects: ["metric_aggregation", "prediction_calculation"]
deps: ["dataclasses", "statistics"]
owners: ["drapala"]
stability: experimental
since_version: "0.5.0"
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""

    timestamp: str
    success_rate: float
    confidence: float
    pattern_count: int
    high_success_patterns: int
    low_success_patterns: int
    avg_cognitive_hops: float
    avg_domain_coherence: float


class MetricTracker:
    """Track and aggregate learning system metrics."""

    def __init__(self):
        self.snapshots: list[MetricSnapshot] = []
        self.current_metrics: dict[str, Any] = {}

    def track_patterns(self, patterns: list[Any]) -> dict[str, Any]:
        """Track metrics from learned patterns."""
        if not patterns:
            return {
                "patterns_learned": 0,
                "high_success_patterns": 0,
                "low_success_patterns": 0,
                "avg_success_rate": 0.0,
                "avg_confidence": 0.0,
            }

        high_success = [p for p in patterns if p.success_rate > 0.7]
        low_success = [p for p in patterns if p.success_rate < 0.4]

        metrics = {
            "patterns_learned": len(patterns),
            "high_success_patterns": len(high_success),
            "low_success_patterns": len(low_success),
            "avg_success_rate": sum(p.success_rate for p in patterns) / len(patterns),
            "avg_confidence": sum(p.confidence_score for p in patterns) / len(patterns),
        }

        self.current_metrics.update(metrics)
        return metrics

    def calculate_predictions(
        self, patterns: list[Any], current_metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate predictive metrics based on patterns."""
        if not patterns:
            return {
                "predicted_success_rate": 0.5,
                "confidence": 0.0,
                "trend": "unknown",
            }

        weighted_success = 0.0
        total_weight = 0.0

        for pattern in patterns:
            weight = pattern.confidence_score * pattern.sample_size
            weighted_success += pattern.success_rate * weight
            total_weight += weight

        predicted_success = weighted_success / total_weight if total_weight > 0 else 0.5
        confidence = min(1.0, total_weight / 100)

        trend = self._determine_trend(predicted_success, current_metrics)

        return {
            "predicted_success_rate": predicted_success,
            "confidence": confidence,
            "trend": trend,
            "recommendation_priority": self._calculate_priority(predicted_success, confidence),
        }

    def _determine_trend(self, predicted_success: float, current_metrics: dict[str, Any]) -> str:
        """Determine the trend based on predicted success rate."""
        if predicted_success > 0.7:
            return "improving"
        elif predicted_success > 0.5:
            return "stable"
        else:
            return "needs_attention"

    def _calculate_priority(self, success_rate: float, confidence: float) -> str:
        """Calculate recommendation priority."""
        score = (1.0 - success_rate) * confidence

        if score > 0.6:
            return "high"
        elif score > 0.3:
            return "medium"
        else:
            return "low"

    def get_summary(self) -> dict[str, Any]:
        """Get summary of tracked metrics."""
        return {
            "current_metrics": self.current_metrics,
            "snapshot_count": len(self.snapshots),
        }
