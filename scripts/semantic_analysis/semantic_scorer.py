#!/usr/bin/env python3
"""
title: Semantic Quality Scorer
purpose: Score semantic quality and complexity metrics
inputs: [{name: "patterns", type: "SemanticPatterns"}]
outputs: [{name: "scores", type: "QualityScores"}]
effects: ["scoring", "metric_calculation"]
deps: ["dataclasses", "statistics"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: low
"""

from dataclasses import dataclass, field
from statistics import mean

from semantic_extractor import SemanticPatterns


@dataclass
class ComplexityMetrics:
    """Complexity metrics for the codebase."""

    avg_imports_per_file: float = 0.0
    max_call_chain_depth: int = 0
    cyclic_dependency_count: int = 0
    hotspot_count: int = 0
    isolation_score: float = 0.0


@dataclass
class QualityScores:
    """Quality scores for semantic analysis."""

    complexity_metrics: ComplexityMetrics
    llm_readiness_score: float = 0.0
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class SemanticScorer:
    """Score semantic quality of codebase."""

    def __init__(self):
        self.scores = QualityScores(complexity_metrics=ComplexityMetrics())

    def score(self, patterns: SemanticPatterns) -> QualityScores:
        """Calculate quality scores from patterns."""
        # Calculate complexity metrics
        self._calculate_complexity_metrics(patterns)

        # Calculate LLM readiness score
        self._calculate_llm_readiness(patterns)

        # Generate insights
        self._generate_insights(patterns)

        # Generate recommendations
        self._generate_recommendations(patterns)

        return self.scores

    def _calculate_complexity_metrics(self, patterns: SemanticPatterns) -> None:
        """Calculate complexity metrics."""
        metrics = self.scores.complexity_metrics

        # Average imports per file
        if patterns.dependency_graph.import_graph:
            total_imports = sum(
                len(imports) for imports in patterns.dependency_graph.import_graph.values()
            )
            metrics.avg_imports_per_file = total_imports / len(
                patterns.dependency_graph.import_graph
            )

        # Max call chain depth
        if patterns.call_chains:
            metrics.max_call_chain_depth = max(chain.depth for chain in patterns.call_chains)

        # Cyclic dependencies
        metrics.cyclic_dependency_count = len(patterns.cyclic_deps)

        # Hotspot count
        metrics.hotspot_count = len(patterns.hotspots)

        # Isolation score
        if patterns.feature_isolation:
            metrics.isolation_score = mean(patterns.feature_isolation.values())

    def _calculate_llm_readiness(self, patterns: SemanticPatterns) -> None:
        """Calculate LLM readiness score (0-100)."""
        score = 100.0
        metrics = self.scores.complexity_metrics

        # Deduct points for complexity issues

        # Import complexity (max -20 points)
        if metrics.avg_imports_per_file > 8:
            score -= min(20, (metrics.avg_imports_per_file - 8) * 2)

        # Call chain depth (max -20 points)
        if metrics.max_call_chain_depth > 6:
            score -= min(20, (metrics.max_call_chain_depth - 6) * 5)

        # Cyclic dependencies (max -30 points)
        if metrics.cyclic_dependency_count > 0:
            score -= min(30, metrics.cyclic_dependency_count * 10)

        # Hotspots (max -15 points)
        high_risk_hotspots = sum(1 for h in patterns.hotspots if h.get("risk_level") == "high")
        if high_risk_hotspots > 0:
            score -= min(15, high_risk_hotspots * 5)

        # Feature isolation (max -15 points)
        if metrics.isolation_score < 0.8:
            score -= min(15, (0.8 - metrics.isolation_score) * 75)

        self.scores.llm_readiness_score = max(0, score)

    def _generate_insights(self, patterns: SemanticPatterns) -> None:
        """Generate insights based on analysis."""
        metrics = self.scores.complexity_metrics
        insights = []

        # Import coupling
        if metrics.avg_imports_per_file > 8:
            insights.append(
                f"High import coupling detected ({metrics.avg_imports_per_file:.1f} avg imports)"
            )
        elif metrics.avg_imports_per_file < 3:
            insights.append("Good import isolation - low coupling")

        # Call chains
        if metrics.max_call_chain_depth > 6:
            insights.append(
                f"Deep call chains detected (max depth: {metrics.max_call_chain_depth})"
            )
        elif metrics.max_call_chain_depth <= 3:
            insights.append("Shallow call chains - good for LLM comprehension")

        # Cyclic dependencies
        if metrics.cyclic_dependency_count > 0:
            insights.append(f"Found {metrics.cyclic_dependency_count} cyclic dependencies")
        else:
            insights.append("No cyclic dependencies - clean architecture")

        # Hotspots
        if metrics.hotspot_count > 0:
            high_risk = sum(1 for h in patterns.hotspots if h.get("risk_level") == "high")
            if high_risk > 0:
                insights.append(f"High-risk dependency hotspots: {high_risk} modules")

        # Feature isolation
        if metrics.isolation_score >= 0.9:
            insights.append("Excellent feature isolation (VSA compliant)")
        elif metrics.isolation_score >= 0.8:
            insights.append("Good feature isolation")
        elif metrics.isolation_score < 0.6:
            insights.append("Poor feature isolation - consider VSA refactoring")

        self.scores.insights = insights

    def _generate_recommendations(self, patterns: SemanticPatterns) -> None:
        """Generate actionable recommendations."""
        metrics = self.scores.complexity_metrics
        recommendations = []

        # Based on LLM readiness score
        if self.scores.llm_readiness_score < 80:
            recommendations.append("URGENT: LLM readiness below threshold (80)")

        # Import recommendations
        if metrics.avg_imports_per_file > 8:
            recommendations.append("Reduce import coupling - consider splitting large modules")

        # Call chain recommendations
        if metrics.max_call_chain_depth > 6:
            recommendations.append("Flatten call chains - extract intermediate functions")

        # Cyclic dependency recommendations
        if metrics.cyclic_dependency_count > 0:
            recommendations.append("Break cyclic dependencies - use dependency injection")

        # Hotspot recommendations
        high_risk = [h for h in patterns.hotspots if h.get("risk_level") == "high"]
        if high_risk:
            modules = ", ".join(h["module"] for h in high_risk[:3])
            recommendations.append(f"Refactor high-risk hotspots: {modules}")

        # Feature isolation recommendations
        if metrics.isolation_score < 0.8:
            recommendations.append("Improve feature isolation - move to VSA structure")

        # Positive recommendations
        if self.scores.llm_readiness_score >= 90:
            recommendations.append("Excellent LLM readiness - maintain current standards")

        self.scores.recommendations = recommendations


def calculate_scores(patterns: SemanticPatterns) -> QualityScores:
    """Calculate quality scores from semantic patterns."""
    scorer = SemanticScorer()
    return scorer.score(patterns)
