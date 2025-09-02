#!/usr/bin/env python3
"""
---
title: Test Domain Rules
purpose: Golden tests for business rule analysis
inputs: []
outputs: []
effects: []
deps: ["pytest", "collections"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
---
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain_analysis.domain_rules import (
    calculate_coherence_score,
    detect_boundary_violations,
    find_cross_cutting_concerns,
    generate_vsa_recommendations,
    suggest_feature_splits,
    terms_related,
)


def test_detect_boundary_violations():
    """Test detection of bounded context violations."""
    feature_domains = {
        "feature1": {
            "domain_terms": Counter({"customer": 5, "order": 3, "payment": 2}),
            "files": ["file1.py", "file2.py"],
        },
        "feature2": {
            "domain_terms": Counter({"customer": 4, "order": 6, "shipping": 3}),
            "files": ["file3.py"],
        },
        "feature3": {
            "domain_terms": Counter({"inventory": 5, "stock": 3}),
            "files": ["file4.py"],
        },
    }

    violations = detect_boundary_violations(feature_domains)

    assert len(violations) == 1
    assert violations[0]["feature1"] == "feature1"
    assert violations[0]["feature2"] == "feature2"
    assert "customer" in violations[0]["shared_terms"]
    assert "order" in violations[0]["shared_terms"]


def test_calculate_coherence_score():
    """Test domain coherence score calculation."""
    feature_domains = {
        "coherent_feature": {
            "domain_terms": Counter({"payment": 10, "transaction": 9, "amount": 8}),
        },
        "scattered_feature": {
            "domain_terms": Counter({"user": 1, "product": 1, "order": 1}),
        },
    }

    score = calculate_coherence_score(feature_domains)

    assert 0 <= score <= 1
    assert score > 0.3


def test_find_cross_cutting_concerns():
    """Test identification of cross-cutting domain terms."""
    feature_domains = {
        "feature1": {"domain_terms": Counter({"audit": 2, "customer": 3})},
        "feature2": {"domain_terms": Counter({"audit": 1, "order": 4})},
        "feature3": {"domain_terms": Counter({"audit": 3, "inventory": 2})},
    }

    cross_cutting = find_cross_cutting_concerns(feature_domains)

    assert "audit" in cross_cutting
    assert "customer" not in cross_cutting


def test_terms_related():
    """Test term relationship detection."""
    assert terms_related("payment", "payments") is True
    assert terms_related("order", "ordering") is True
    assert terms_related("customer", "inventory") is False
    assert terms_related("ship", "shipping") is True


def test_suggest_feature_splits():
    """Test feature split suggestions."""
    feature_data = {
        "domain_terms": Counter(
            {
                "payment": 10,
                "transaction": 8,
                "customer": 7,
                "profile": 6,
                "settings": 5,
            }
        ),
        "files": ["f1.py", "f2.py", "f3.py", "f4.py", "f5.py", "f6.py"],
    }

    suggestions = suggest_feature_splits("billing", feature_data)

    assert len(suggestions) <= 2
    assert all("billing" in s for s in suggestions)


def test_generate_vsa_recommendations():
    """Test VSA recommendation generation."""
    feature_domains = {
        "complex_feature": {
            "domain_terms": Counter(
                {
                    "payment": 5,
                    "order": 4,
                    "customer": 3,
                    "inventory": 2,
                    "shipping": 1,
                }
            ),
            "files": ["f1.py", "f2.py", "f3.py", "f4.py", "f5.py", "f6.py"],
        },
        "feature1": {
            "domain_terms": Counter({"order": 10, "item": 8}),
            "files": ["f7.py"],
        },
        "feature2": {
            "domain_terms": Counter({"order": 9, "item": 7, "cart": 3}),
            "files": ["f8.py"],
        },
    }

    violations = detect_boundary_violations(feature_domains)
    recommendations = generate_vsa_recommendations(feature_domains, violations)

    assert len(recommendations) > 0

    rec_types = {r["type"] for r in recommendations}
    assert "split_feature" in rec_types or "merge_features" in rec_types
