#!/usr/bin/env python3
"""
title: Adaptation Engine Module
purpose: Generate and prioritize architectural improvements based on patterns
inputs: [{"name": "patterns", "type": "list[ArchitecturalPattern]"}, {"name": "current_metrics", "type": "dict"}]
outputs: [{"name": "recommendations", "type": "list[ImprovementSuggestion]"}]
effects: ["recommendation_generation", "priority_calculation"]
deps: ["dataclasses", "typing"]
owners: ["drapala"]
stability: experimental
since_version: "0.5.0"
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ImprovementSuggestion:
    """Represents a suggested architectural improvement."""

    suggestion_id: str
    title: str
    description: str
    expected_impact: str
    effort_estimate: str
    success_probability: float
    affected_files: list[str]
    implementation_steps: list[str]
    evidence: dict[str, Any]


class AdaptationStrategy:
    """Base class for adaptation strategies."""

    def generate_suggestions(
        self, patterns: list[Any], metrics: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """Generate improvement suggestions."""
        raise NotImplementedError


class PatternAdoptionStrategy(AdaptationStrategy):
    """Strategy for adopting successful patterns."""

    def generate_suggestions(
        self, patterns: list[Any], metrics: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """Generate suggestions to adopt successful patterns."""
        suggestions = []
        high_success_patterns = [p for p in patterns if p.success_rate > 0.7]

        for pattern in high_success_patterns:
            if pattern.confidence_score > 0.6:
                suggestion = self._create_adoption_suggestion(pattern, metrics)
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def _create_adoption_suggestion(
        self, pattern: Any, metrics: dict[str, Any]
    ) -> ImprovementSuggestion | None:
        """Create a suggestion to adopt a successful pattern."""
        traits = pattern.architectural_traits
        current_hops = metrics.get("max_call_chain_depth", 0)
        pattern_hops = traits.get("avg_cognitive_hops", 0)

        if current_hops > pattern_hops * 1.5:
            return ImprovementSuggestion(
                suggestion_id=f"adopt_{pattern.pattern_id}",
                title="Reduce Cognitive Complexity",
                description=(
                    f"Adopt pattern: {pattern.description}. "
                    f"Current avg cognitive hops ({current_hops:.1f}) exceeds "
                    f"successful pattern ({pattern_hops:.1f})"
                ),
                expected_impact="high",
                effort_estimate="medium",
                success_probability=pattern.success_rate,
                affected_files=[],
                implementation_steps=[
                    "Identify files with high cognitive hop counts",
                    "Refactor to reduce call chain depth",
                    "Co-locate related functionality",
                    "Extract common patterns to reduce indirection",
                ],
                evidence={
                    "pattern_success_rate": pattern.success_rate,
                    "sample_size": pattern.sample_size,
                    "target_hops": pattern_hops,
                },
            )
        return None


class AntiPatternAvoidanceStrategy(AdaptationStrategy):
    """Strategy for avoiding unsuccessful patterns."""

    def generate_suggestions(
        self, patterns: list[Any], metrics: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """Generate suggestions to avoid unsuccessful patterns."""
        suggestions = []
        low_success_patterns = [p for p in patterns if p.success_rate < 0.4]

        for pattern in low_success_patterns:
            if pattern.confidence_score > 0.5:
                suggestion = self._create_avoidance_suggestion(pattern, metrics)
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def _create_avoidance_suggestion(
        self, pattern: Any, metrics: dict[str, Any]
    ) -> ImprovementSuggestion | None:
        """Create a suggestion to avoid an unsuccessful pattern."""
        if "low_coherence" in pattern.context_features:
            isolation_score = metrics.get("isolation_score", 1.0)
            if isolation_score < 0.6:
                return ImprovementSuggestion(
                    suggestion_id=f"avoid_{pattern.pattern_id}",
                    title="Improve Domain Isolation",
                    description=(
                        f"Current domain isolation ({isolation_score:.2f}) "
                        f"matches low-success pattern with {pattern.success_rate:.1%} success rate"
                    ),
                    expected_impact="high",
                    effort_estimate="hard",
                    success_probability=1.0 - pattern.success_rate,
                    affected_files=[],
                    implementation_steps=[
                        "Audit cross-feature dependencies",
                        "Extract shared concerns to dedicated modules",
                        "Strengthen bounded context boundaries",
                        "Implement domain-driven design patterns",
                    ],
                    evidence={
                        "anti_pattern_success_rate": pattern.success_rate,
                        "current_isolation": isolation_score,
                    },
                )
        return None


class HotspotReductionStrategy(AdaptationStrategy):
    """Strategy for reducing dependency hotspots."""

    def generate_suggestions(
        self, patterns: list[Any], metrics: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """Generate suggestions to reduce hotspots."""
        suggestions = []
        hotspots = metrics.get("hotspot_files", [])

        if len(hotspots) > 3:
            suggestions.append(
                ImprovementSuggestion(
                    suggestion_id="reduce_hotspots",
                    title="Reduce Dependency Hotspots",
                    description=(
                        f"Found {len(hotspots)} hotspot files that are heavily depended upon"
                    ),
                    expected_impact="medium",
                    effort_estimate="medium",
                    success_probability=0.75,
                    affected_files=[h.get("module", "") for h in hotspots],
                    implementation_steps=[
                        "Extract interfaces for hotspot dependencies",
                        "Apply dependency inversion principle",
                        "Create facade patterns for complex hotspots",
                        "Split large utility modules",
                    ],
                    evidence={"hotspot_count": len(hotspots), "hotspot_details": hotspots},
                )
            )

        return suggestions


class AdaptationEngine:
    """Main adaptation engine using multiple strategies."""

    def __init__(self):
        self.strategies = [
            PatternAdoptionStrategy(),
            AntiPatternAvoidanceStrategy(),
            HotspotReductionStrategy(),
        ]

    def generate_recommendations(
        self, patterns: list[Any], current_metrics: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """Generate recommendations using all strategies."""
        all_suggestions = []

        for strategy in self.strategies:
            suggestions = strategy.generate_suggestions(patterns, current_metrics)
            all_suggestions.extend(suggestions)

        return sorted(all_suggestions, key=lambda r: r.success_probability, reverse=True)
