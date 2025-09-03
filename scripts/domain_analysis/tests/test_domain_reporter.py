#!/usr/bin/env python3
"""
---
title: Test Domain Reporter
purpose: Golden tests for report generation
inputs: []
outputs: []
effects: []
deps: ["pytest", "tempfile", "pathlib", "json"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
---
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain_analysis.domain_reporter import DomainPatternDetector


def test_domain_pattern_detector_init():
    """Test DomainPatternDetector initialization."""
    detector = DomainPatternDetector()
    assert detector.repo_root == "."

    detector = DomainPatternDetector("/custom/path")
    assert detector.repo_root == "/custom/path"


def test_analyze_empty_repo():
    """Test analysis on empty repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        detector = DomainPatternDetector(tmpdir)
        results = detector.analyze()

        assert results["files_analyzed"] == 0
        assert results["feature_domains"] == {}
        assert results["boundary_violations"] == 0
        assert results["domain_coherence_score"] == 0.0
        assert results["recommendations"] == []


def test_generate_report():
    """Test report generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        feature_dir = tmpdir_path / "features" / "billing"
        feature_dir.mkdir(parents=True)

        payment_file = feature_dir / "payment.py"
        payment_file.write_text(
            """
class PaymentProcessor:
    '''Process customer payments.'''
    
    def process_payment(self, amount: float, customer_id: str):
        '''Process a payment transaction.'''
        pass
    
    def validate_payment(self, payment_data: dict):
        '''Validate payment information.'''
        pass
        """
        )

        detector = DomainPatternDetector(tmpdir)
        report = detector.generate_report()

        assert "Domain Pattern Analysis Report" in report
        assert "Files analyzed:" in report
        assert "Domain coherence score:" in report


def test_json_output():
    """Test JSON output format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        test_file = tmpdir_path / "test.py"
        test_file.write_text(
            """
class TestClass:
    def test_method(self):
        pass
        """
        )

        detector = DomainPatternDetector(tmpdir)
        results = detector.analyze()

        for feature_data in results.get("feature_domains", {}).values():
            if "domain_terms" in feature_data:
                feature_data["domain_terms"] = dict(feature_data["domain_terms"])

        json_str = json.dumps(results, indent=2, default=str)
        parsed = json.loads(json_str)

        assert "files_analyzed" in parsed
        assert "feature_domains" in parsed
        assert "boundary_violations" in parsed
        assert "domain_coherence_score" in parsed
        assert "recommendations" in parsed
