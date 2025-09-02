#!/usr/bin/env python3
"""
---
title: Test Domain Models
purpose: Golden tests for domain entity extraction
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

from domain_analysis.domain_models import extract_domain_language


def test_extract_class_names():
    """Test extraction of class names as domain concepts."""
    code = """
class Customer:
    pass

class OrderService:
    pass
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = extract_domain_language(Path(f.name))

        assert "Customer" in result["classes"]
        assert "OrderService" in result["classes"]
        assert "customer" in result["domain_terms"]
        assert "order" in result["domain_terms"]
        assert "service" in result["domain_terms"]


def test_extract_method_names():
    """Test extraction of method names and parameters."""
    code = """
def process_payment(customer_id, amount):
    pass

def validate_order(order_items):
    pass
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = extract_domain_language(Path(f.name))

        assert "process_payment" in result["methods"]
        assert "validate_order" in result["methods"]
        assert "payment" in result["domain_terms"]
        assert "customer" in result["domain_terms"]
        assert "order" in result["domain_terms"]


def test_extract_from_docstrings():
    """Test extraction of domain terms from docstrings."""
    code = '''
def calculate_discount():
    """Calculate discount for premium customers based on purchase history."""
    pass
    '''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = extract_domain_language(Path(f.name))

        assert "discount" in result["domain_terms"]
        assert "customers" in result["domain_terms"]
        assert "purchase" in result["domain_terms"]


def test_skip_technical_words():
    """Test that technical words are filtered out."""
    code = """
class DataProcessor:
    def __init__(self):
        self.config = {}
        self.logger = None
    
    def process(self, data: dict) -> list:
        return []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = extract_domain_language(Path(f.name))

        assert "dict" not in result["domain_terms"]
        assert "list" not in result["domain_terms"]
        assert "self" not in result["domain_terms"]
        assert "return" not in result["domain_terms"]
