#!/usr/bin/env python3
"""
title: Adaptive Learning System for LLM Architecture
purpose: Learn from telemetry patterns to suggest architectural improvements
inputs: [{"name": "telemetry_data", "type": "jsonl"}, {"name": "codebase_metrics", "type": "dict"}]
outputs: [
  {"name": "improvement_suggestions", "type": "list"},
  {"name": "predictive_score", "type": "float"}
]
effects: ["pattern_learning", "recommendation_generation"]
deps: ["json", "datetime", "statistics", "dataclasses"]
owners: ["drapala"]
stability: experimental
since_version: "0.4.0"
"""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class ArchitecturalPattern:
    """Represents a learned architectural pattern."""

    pattern_id: str
    description: str
    success_rate: float
    context_features: list[str]
    architectural_traits: dict[str, float]
    sample_size: int
    confidence_score: float


@dataclass
class ImprovementSuggestion:
    """Represents a suggested architectural improvement."""

    suggestion_id: str
    title: str
    description: str
    expected_impact: str  # high, medium, low
    effort_estimate: str  # easy, medium, hard
    success_probability: float
    affected_files: list[str]
    implementation_steps: list[str]
    evidence: dict[str, Any]


class PatternLearner:
    """Learn successful patterns from telemetry data."""

    def __init__(self, telemetry_log_path: str):
        self.telemetry_log = Path(telemetry_log_path)
        self.patterns: dict[str, Any] = {}
        self.failure_patterns: dict[str, Any] = {}

    def learn_patterns(self, days_back: int = 30) -> list[ArchitecturalPattern]:
        """Learn patterns from recent telemetry data."""
        events = self._load_events(days_back)
        if not events:
            return []

        # Group events by context features
        context_groups = self._group_by_context(events)

        patterns = []
        for context_signature, group_events in context_groups.items():
            if len(group_events) < 3:  # Need minimum sample size
                continue

            pattern = self._analyze_pattern(context_signature, group_events)
            if pattern and pattern.confidence_score > 0.3:
                patterns.append(pattern)

        return sorted(patterns, key=lambda p: p.success_rate, reverse=True)

    def _load_events(self, days_back: int) -> list[dict[str, Any]]:
        """Load telemetry events from specified time period."""
        if not self.telemetry_log.exists():
            return []

        cutoff_date = datetime.now() - timedelta(days=days_back)
        events = []

        try:
            with open(self.telemetry_log, encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event.get("timestamp", ""))
                        if event_time >= cutoff_date:
                            events.append(event)
                    except Exception:
                        continue
        except Exception:
            return []

        return events

    def _group_by_context(self, events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group events by similar context features."""
        groups = defaultdict(list)

        for event in events:
            if "files_modified" not in event:
                continue

            # Create context signature
            features = []

            # File count bucket
            file_count = len(event.get("files_modified", []))
            if file_count == 1:
                features.append("single_file")
            elif file_count <= 3:
                features.append("few_files")
            else:
                features.append("many_files")

            # Cognitive complexity bucket
            hops = event.get("cognitive_hops", 0)
            if hops == 0:
                features.append("no_hops")
            elif hops <= 2:
                features.append("low_hops")
            else:
                features.append("high_hops")

            # Domain coherence bucket
            coherence = event.get("domain_coherence", 0.5)
            if coherence > 0.8:
                features.append("high_coherence")
            elif coherence > 0.4:
                features.append("medium_coherence")
            else:
                features.append("low_coherence")

            # Edit type
            edit_type = event.get("edit_type", "update")
            features.append(f"edit_{edit_type}")

            context_signature = ",".join(sorted(features))
            groups[context_signature].append(event)

        return groups

    def _analyze_pattern(
        self, context_signature: str, events: list[dict[str, Any]]
    ) -> ArchitecturalPattern | None:
        """Analyze a group of events to extract pattern."""
        if not events:
            return None

        # Calculate success rate
        successful_events = [e for e in events if e.get("success", False)]
        success_rate = len(successful_events) / len(events)

        # Extract architectural traits from successful events
        architectural_traits = {}
        if successful_events:
            # Average traits of successful edits
            total_hops = sum(e.get("cognitive_hops", 0) for e in successful_events)
            total_coherence = sum(e.get("domain_coherence", 0.5) for e in successful_events)
            total_context_size = sum(len(e.get("files_modified", [])) for e in successful_events)

            architectural_traits = {
                "avg_cognitive_hops": total_hops / len(successful_events),
                "avg_domain_coherence": total_coherence / len(successful_events),
                "avg_context_size": total_context_size / len(successful_events),
            }

        # Calculate confidence based on sample size and variance
        confidence = min(1.0, len(events) / 10) * (0.5 + success_rate * 0.5)

        pattern_id = f"pattern_{abs(hash(context_signature)) % 10000}"

        return ArchitecturalPattern(
            pattern_id=pattern_id,
            description=self._generate_pattern_description(context_signature, architectural_traits),
            success_rate=success_rate,
            context_features=context_signature.split(","),
            architectural_traits=architectural_traits,
            sample_size=len(events),
            confidence_score=confidence,
        )

    def _generate_pattern_description(self, context: str, traits: dict[str, float]) -> str:
        """Generate human-readable pattern description."""
        features = context.split(",")

        desc_parts = []
        if "single_file" in features:
            desc_parts.append("Single-file edits")
        elif "few_files" in features:
            desc_parts.append("Small-scope edits")
        else:
            desc_parts.append("Large-scope edits")

        if "high_coherence" in features:
            desc_parts.append("with high domain coherence")
        elif "low_coherence" in features:
            desc_parts.append("with low domain coherence")

        if "low_hops" in features:
            desc_parts.append("and minimal cognitive hops")
        elif "high_hops" in features:
            desc_parts.append("with complex dependency chains")

        return " ".join(desc_parts)


class ImprovementRecommender:
    """Generate architectural improvement recommendations."""

    def __init__(self, patterns: list[ArchitecturalPattern]):
        self.patterns = patterns
        self.high_success_patterns = [p for p in patterns if p.success_rate > 0.7]
        self.low_success_patterns = [p for p in patterns if p.success_rate < 0.4]

    def generate_recommendations(
        self, current_metrics: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """Generate improvement recommendations based on learned patterns."""
        recommendations = []

        # Recommend adopting high-success patterns
        for pattern in self.high_success_patterns:
            if pattern.confidence_score > 0.6:
                suggestion = self._create_adoption_recommendation(pattern, current_metrics)
                if suggestion:
                    recommendations.append(suggestion)

        # Recommend avoiding low-success patterns
        for pattern in self.low_success_patterns:
            if pattern.confidence_score > 0.5:
                suggestion = self._create_avoidance_recommendation(pattern, current_metrics)
                if suggestion:
                    recommendations.append(suggestion)

        # Generate specific architectural recommendations
        specific_recs = self._generate_specific_recommendations(current_metrics)
        recommendations.extend(specific_recs)

        return sorted(recommendations, key=lambda r: r.success_probability, reverse=True)

    def _create_adoption_recommendation(
        self, pattern: ArchitecturalPattern, current_metrics: dict[str, Any]
    ) -> ImprovementSuggestion | None:
        """Create recommendation to adopt successful pattern."""
        traits = pattern.architectural_traits

        # Check if current architecture aligns with this pattern
        current_hops = current_metrics.get("max_call_chain_depth", 0)
        pattern_hops = traits.get("avg_cognitive_hops", 0)

        if current_hops > pattern_hops * 1.5:  # Current is significantly worse
            return ImprovementSuggestion(
                suggestion_id=f"adopt_{pattern.pattern_id}",
                title="Reduce Cognitive Complexity",
                description=f"Adopt pattern: {pattern.description}. "
                f"Current avg cognitive hops ({current_hops:.1f}) exceeds "
                f"successful pattern ({pattern_hops:.1f})",
                expected_impact="high",
                effort_estimate="medium",
                success_probability=pattern.success_rate,
                affected_files=[],  # Would need more context to determine
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

    def _create_avoidance_recommendation(
        self, pattern: ArchitecturalPattern, current_metrics: dict[str, Any]
    ) -> ImprovementSuggestion | None:
        """Create recommendation to avoid unsuccessful pattern."""
        if "low_coherence" in pattern.context_features:
            isolation_score = current_metrics.get("isolation_score", 1.0)
            if isolation_score < 0.6:  # Already showing signs of this anti-pattern
                return ImprovementSuggestion(
                    suggestion_id=f"avoid_{pattern.pattern_id}",
                    title="Improve Domain Isolation",
                    description=f"Current domain isolation ({isolation_score:.2f}) "
                    f"matches low-success pattern with {pattern.success_rate:.1%} success rate",
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

    def _generate_specific_recommendations(
        self, current_metrics: dict[str, Any]
    ) -> list[ImprovementSuggestion]:
        """Generate specific recommendations based on metrics."""
        recommendations = []

        # Hotspot reduction
        hotspots = current_metrics.get("hotspot_files", [])
        if len(hotspots) > 3:
            recommendations.append(
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

        # Cyclic dependency resolution
        cycles = current_metrics.get("cyclic_dependencies", [])
        if cycles:
            recommendations.append(
                ImprovementSuggestion(
                    suggestion_id="resolve_cycles",
                    title="Resolve Cyclic Dependencies",
                    description=f"Found {len(cycles)} cyclic dependency chains",
                    expected_impact="high",
                    effort_estimate="hard",
                    success_probability=0.8,
                    affected_files=[],
                    implementation_steps=[
                        "Map dependency cycles using tools",
                        "Introduce dependency inversion",
                        "Extract shared interfaces",
                        "Apply mediator pattern where appropriate",
                    ],
                    evidence={"cycle_count": len(cycles), "cycles": cycles},
                )
            )

        return recommendations


class AdaptiveLearningSystem:
    """Main system combining pattern learning and recommendation generation."""

    def __init__(self, repo_root: str = ".", telemetry_log: str = ".reports/llm_telemetry.jsonl"):
        self.repo_root = Path(repo_root)
        self.telemetry_log = telemetry_log
        self.pattern_learner = PatternLearner(telemetry_log)

    def analyze_and_recommend(
        self, current_metrics: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Perform full analysis and generate recommendations."""
        print("Learning patterns from telemetry data...")

        # Learn patterns from telemetry
        patterns = self.pattern_learner.learn_patterns()

        if not patterns:
            return {
                "patterns_learned": 0,
                "recommendations": [],
                "message": "Insufficient telemetry data for pattern learning",
            }

        # Generate recommendations
        recommender = ImprovementRecommender(patterns)
        recommendations = recommender.generate_recommendations(current_metrics or {})

        return {
            "patterns_learned": len(patterns),
            "high_success_patterns": len([p for p in patterns if p.success_rate > 0.7]),
            "patterns": [asdict(p) for p in patterns[:5]],  # Top 5 patterns
            "recommendations": [asdict(r) for r in recommendations],
            "overall_prediction": self._calculate_overall_prediction(
                patterns, current_metrics or {}
            ),
        }

    def _calculate_overall_prediction(
        self, patterns: list[ArchitecturalPattern], current_metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate overall architectural health predictions."""
        if not patterns:
            return {"predicted_success_rate": 0.5, "confidence": 0.0}

        # Weight patterns by confidence and relevance
        weighted_success = 0.0
        total_weight = 0.0

        for pattern in patterns:
            weight = pattern.confidence_score * pattern.sample_size
            weighted_success += pattern.success_rate * weight
            total_weight += weight

        predicted_success = weighted_success / total_weight if total_weight > 0 else 0.5
        confidence = min(1.0, total_weight / 100)  # Confidence based on total evidence

        return {
            "predicted_success_rate": predicted_success,
            "confidence": confidence,
            "trend": "improving" if predicted_success > 0.6 else "needs_attention",
        }


def main():
    """CLI interface for adaptive learning system."""
    import argparse

    parser = argparse.ArgumentParser(description="Adaptive Learning System")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument(
        "--telemetry", default=".reports/llm_telemetry.jsonl", help="Telemetry log file"
    )
    parser.add_argument("--analyze", action="store_true", help="Analyze and recommend")
    parser.add_argument("--metrics-file", help="JSON file with current metrics")

    args = parser.parse_args()

    system = AdaptiveLearningSystem(args.repo_root, args.telemetry)

    if args.analyze:
        # Load current metrics if provided
        current_metrics = {}
        if args.metrics_file and Path(args.metrics_file).exists():
            with open(args.metrics_file) as f:
                current_metrics = json.load(f)

        results = system.analyze_and_recommend(current_metrics)
        print(json.dumps(results, indent=2))
    else:
        print("Use --analyze to run the adaptive learning analysis")


if __name__ == "__main__":
    main()
