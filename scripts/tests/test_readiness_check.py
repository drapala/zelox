#!/usr/bin/env python3
"""
Tests for LLM Readiness Check Module
Test the refactored modular readiness assessment system.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from readiness_check import (
    ReadinessCalculator,
    ReadinessReporter,
    ReadinessValidator,
)
from readiness_check.cognitive_metrics import CognitiveComplexityMetric
from readiness_check.readiness_calculator import ReadinessScore
from readiness_check.readiness_metrics import (
    CoLocationMetric,
    MetricResult,
)
from readiness_check.readiness_reporter import ReportFormat


class TestMetricPlugins(unittest.TestCase):
    """Test individual metric plugins."""

    def setUp(self):
        """Create temporary test directory."""
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir)

    def test_co_location_metric_no_features(self):
        """Test co-location metric with no features directory."""
        metric = CoLocationMetric(self.repo_path)
        result = metric.calculate()

        self.assertEqual(result.score, 0)
        self.assertEqual(result.status, "❌")
        self.assertIn("No features/ directory", result.message)

    def test_co_location_metric_with_features(self):
        """Test co-location metric with features directory."""
        # Create features directory with test structure
        features_dir = self.repo_path / "features"
        features_dir.mkdir()

        feature1 = features_dir / "feature1"
        feature1.mkdir()
        (feature1 / "service.py").touch()
        (feature1 / "tests.py").touch()

        feature2 = features_dir / "feature2"
        feature2.mkdir()
        (feature2 / "models.py").touch()
        # No tests for feature2

        metric = CoLocationMetric(self.repo_path)
        result = metric.calculate()

        self.assertEqual(result.max_score, 25)
        self.assertIn("1/2", result.message)  # 1 of 2 features has tests
        self.assertEqual(result.details["co_located"], 1)
        self.assertEqual(result.details["total"], 2)

    def test_cognitive_complexity_metric(self):
        """Test cognitive complexity metric."""
        # Create a Python file with known complexity
        (self.repo_path / "test.py").write_text(
            """
def simple_function():
    if True:
        for i in range(10):
            pass
    return True
"""
        )

        metric = CognitiveComplexityMetric(self.repo_path)
        result = metric.calculate()

        self.assertEqual(result.max_score, 25)
        self.assertIsNotNone(result.details)
        self.assertIn("avg_complexity", result.details)


class TestReadinessCalculator(unittest.TestCase):
    """Test the readiness calculator."""

    def setUp(self):
        """Create temporary test directory."""
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir)

    def test_calculate_with_default_plugins(self):
        """Test calculation with default plugins."""
        calculator = ReadinessCalculator(self.repo_path)
        score = calculator.calculate()

        self.assertIsInstance(score, ReadinessScore)
        self.assertGreaterEqual(score.max_score, 100)
        self.assertIsNotNone(score.metric_results)
        self.assertIsNotNone(score.recommendations)

    def test_calculate_with_custom_plugins(self):
        """Test calculation with custom plugins."""
        mock_plugin = MagicMock()
        mock_plugin.metric_definition.name = "Test Metric"
        mock_plugin.metric_definition.weight = 10
        mock_plugin.calculate.return_value = MetricResult(
            score=8, max_score=10, status="✅", message="Test passed"
        )

        calculator = ReadinessCalculator(self.repo_path, [mock_plugin])
        score = calculator.calculate()

        self.assertEqual(score.total_score, 8)
        self.assertEqual(score.max_score, 10)
        self.assertEqual(score.percentage, 80)
        self.assertTrue(score.passed)


class TestReadinessValidator(unittest.TestCase):
    """Test the readiness validator."""

    def test_validate_passing_score(self):
        """Test validation with passing score."""
        # Create mock metrics to satisfy validator requirements
        metric_results = {
            "Co-location Index": MetricResult(
                score=20, max_score=25, status="✅", message="Test passed"
            ),
            "Cognitive Complexity": MetricResult(
                score=20, max_score=25, status="✅", message="Test passed"
            ),
        }

        score = ReadinessScore(
            total_score=85,
            max_score=100,
            percentage=85,
            status="✅ PASS",
            passed=True,
            metric_results=metric_results,
        )

        validator = ReadinessValidator()
        result = validator.validate(score)

        self.assertTrue(result.passed)
        self.assertEqual(len(result.failures), 0)

    def test_validate_failing_score(self):
        """Test validation with failing score."""
        score = ReadinessScore(
            total_score=50,
            max_score=100,
            percentage=50,
            status="❌ FAIL",
            passed=False,
            metric_results={},  # Add empty metric_results
        )

        validator = ReadinessValidator()
        result = validator.validate(score)

        self.assertFalse(result.passed)
        self.assertGreater(len(result.failures), 0)


class TestReadinessReporter(unittest.TestCase):
    """Test the readiness reporter."""

    def setUp(self):
        """Create test score and validation."""
        self.score = ReadinessScore(
            total_score=75,
            max_score=100,
            percentage=75,
            status="⚠️ NEEDS IMPROVEMENT",
            metric_results={
                "Test Metric": MetricResult(
                    score=75, max_score=100, status="⚠️", message="Test metric result"
                )
            },
            recommendations=["Test recommendation"],
            passed=False,
        )

    def test_text_report_generation(self):
        """Test text report generation."""
        reporter = ReadinessReporter()
        report = reporter.generate(self.score, None, ReportFormat.TEXT)

        self.assertIn("LLM READINESS ASSESSMENT", report)
        self.assertIn("75.0%", report)
        self.assertIn("Test metric result", report)
        self.assertIn("Test recommendation", report)

    def test_json_report_generation(self):
        """Test JSON report generation."""
        reporter = ReadinessReporter()
        report = reporter.generate(self.score, None, ReportFormat.JSON)

        data = json.loads(report)
        self.assertEqual(data["score"]["percentage"], 75)
        self.assertIn("Test Metric", data["metrics"])
        self.assertEqual(data["recommendations"][0], "Test recommendation")


if __name__ == "__main__":
    unittest.main()
