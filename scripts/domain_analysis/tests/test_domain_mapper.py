#!/usr/bin/env python3
"""
---
title: Test Domain Mapper
purpose: Golden tests for domain mapping and aggregation
inputs: []
outputs: []
effects: []
deps: ["pytest", "tempfile", "pathlib"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
---
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain_analysis.domain_mapper import BoundedContextAnalyzer, map_domain_boundaries


def test_bounded_context_analyzer_init():
    """Test BoundedContextAnalyzer initialization."""
    analyzer = BoundedContextAnalyzer()

    assert analyzer.repo_root == Path(".")
    assert analyzer.file_domains == {}
    assert analyzer.feature_domains == {}


def test_should_skip_file():
    """Test file skip logic."""
    analyzer = BoundedContextAnalyzer()

    assert analyzer._should_skip_file(Path("test_something.py")) is True
    assert analyzer._should_skip_file(Path("something_test.py")) is True
    assert analyzer._should_skip_file(Path(".hidden.py")) is True
    assert analyzer._should_skip_file(Path("__pycache__/file.py")) is True
    assert analyzer._should_skip_file(Path("regular_file.py")) is False


def test_aggregate_feature_domains():
    """Test feature domain aggregation."""
    analyzer = BoundedContextAnalyzer()

    analyzer.file_domains = {
        "features/billing/payment.py": {
            "domain_terms": {"payment", "transaction"},
            "classes": {"PaymentProcessor"},
            "methods": {"process_payment"},
            "feature": "billing",
        },
        "features/billing/invoice.py": {
            "domain_terms": {"invoice", "payment"},
            "classes": {"InvoiceGenerator"},
            "methods": {"generate_invoice"},
            "feature": "billing",
        },
        "utils/helpers.py": {
            "domain_terms": {"helper"},
            "classes": set(),
            "methods": {"format_date"},
            "feature": None,
        },
    }

    analyzer.aggregate_feature_domains()

    assert "billing" in analyzer.feature_domains
    assert analyzer.feature_domains["billing"]["domain_terms"]["payment"] == 2
    assert "PaymentProcessor" in analyzer.feature_domains["billing"]["classes"]
    assert "InvoiceGenerator" in analyzer.feature_domains["billing"]["classes"]
    assert len(analyzer.feature_domains["billing"]["files"]) == 2


def test_map_domain_boundaries():
    """Test complete domain boundary mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        feature_dir = tmpdir_path / "features" / "orders"
        feature_dir.mkdir(parents=True)

        order_file = feature_dir / "order.py"
        order_file.write_text(
            """
class Order:
    '''Represents a customer order in the system.'''
    
    def process_order(self, customer_id: str):
        pass
        """
        )

        result = map_domain_boundaries(tmpdir)

        assert result["files_analyzed"] == 1
        assert len(result["file_domains"]) == 1

        file_key = "features/orders/order.py"
        assert file_key in result["file_domains"]

        domain_data = result["file_domains"][file_key]
        assert "order" in domain_data["domain_terms"]
        assert "Order" in domain_data["classes"]
