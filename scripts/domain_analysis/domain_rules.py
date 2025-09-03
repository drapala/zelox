#!/usr/bin/env python3
"""
---
title: Domain Rules Analyzer
purpose: Analyze business rules and detect bounded context violations
inputs:
  - name: file_domains
    type: dict[str, dict]
outputs:
  - name: boundary_violations
    type: list[dict]
  - name: coherence_score
    type: float
effects: []
deps: ["collections"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
---
"""

from collections import defaultdict
from typing import Any


def detect_boundary_violations(feature_domains: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect potential bounded context violations."""
    violations = []
    all_terms_by_feature = {}

    for feature, data in feature_domains.items():
        all_terms_by_feature[feature] = set(data["domain_terms"].keys())

    for feature1, terms1 in all_terms_by_feature.items():
        for feature2, terms2 in all_terms_by_feature.items():
            if feature1 >= feature2:
                continue

            overlap = terms1.intersection(terms2)
            if len(overlap) >= 2:  # Lower threshold for testing
                violations.append(
                    {
                        "feature1": feature1,
                        "feature2": feature2,
                        "shared_terms": list(overlap),
                        "overlap_score": len(overlap) / min(len(terms1), len(terms2)),
                    }
                )

    return violations


def calculate_coherence_score(feature_domains: dict[str, dict[str, Any]]) -> float:
    """Calculate domain coherence score (0-1)."""
    if not feature_domains:
        return 0.0

    total_coherence = 0.0
    feature_count = len(feature_domains)

    for _feature, data in feature_domains.items():
        term_counts = list(data["domain_terms"].values())
        if not term_counts:
            continue

        max_count = max(term_counts)
        avg_count = sum(term_counts) / len(term_counts)
        coherence = avg_count / max_count if max_count > 0 else 0
        total_coherence += coherence

    return total_coherence / feature_count if feature_count > 0 else 0.0


def find_cross_cutting_concerns(feature_domains: dict[str, dict[str, Any]]) -> list[str]:
    """Find domain terms that appear across many features."""
    term_features = defaultdict(set)

    for feature, data in feature_domains.items():
        for term in data["domain_terms"]:
            term_features[term].add(feature)

    cross_cutting = []
    for term, features in term_features.items():
        if len(features) >= 3:
            cross_cutting.append(term)

    return cross_cutting


def terms_related(term1: str, term2: str) -> bool:
    """Check if two terms are likely related."""
    if term1 in term2 or term2 in term1:
        return True

    return (
        len(term1) > 4 and len(term2) > 4 and (term1[:3] == term2[:3] or term1[-3:] == term2[-3:])
    )


def suggest_feature_splits(feature: str, data: dict[str, Any]) -> list[str]:
    """Suggest how to split a feature based on domain clustering."""
    top_terms = [term for term, count in data["domain_terms"].most_common(10)]

    clusters: list[set[str]] = []
    remaining_terms = set(top_terms)

    while remaining_terms and len(clusters) < 3:
        seed_term = remaining_terms.pop()
        cluster = {seed_term}

        for term in list(remaining_terms):
            if any(terms_related(seed_term, term) for seed_term in cluster):
                cluster.add(term)
                remaining_terms.remove(term)

        if len(cluster) > 1:
            clusters.append(cluster)

    suggestions = []
    for _i, cluster in enumerate(clusters):
        cluster_name = f"{feature}_{list(cluster)[0]}"
        suggestions.append(cluster_name)

    return suggestions[:2]


def generate_vsa_recommendations(
    feature_domains: dict[str, dict[str, Any]], boundary_violations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Generate VSA improvement recommendations."""
    recommendations = []

    for feature, data in feature_domains.items():
        term_counts = list(data["domain_terms"].values())
        if not term_counts:
            continue

        dominant_terms = [term for term, count in data["domain_terms"].most_common(5)]
        if len(dominant_terms) > 3 and len(data["files"]) > 5:
            recommendations.append(
                {
                    "type": "split_feature",
                    "feature": feature,
                    "reason": "Multiple domain concepts detected",
                    "suggested_splits": suggest_feature_splits(feature, data),
                    "priority": "medium",
                }
            )

    for violation in boundary_violations:
        if violation["overlap_score"] > 0.7:
            recommendations.append(
                {
                    "type": "merge_features",
                    "features": [violation["feature1"], violation["feature2"]],
                    "reason": f"High domain overlap ({violation['overlap_score']:.1%})",
                    "shared_concepts": violation["shared_terms"],
                    "priority": "high",
                }
            )

    shared_terms = find_cross_cutting_concerns(feature_domains)
    if shared_terms:
        recommendations.append(
            {
                "type": "extract_shared",
                "terms": shared_terms,
                "reason": "Cross-cutting domain concepts detected",
                "suggested_location": "shared/domain/",
                "priority": "low",
            }
        )

    return recommendations
