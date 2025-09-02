#!/usr/bin/env python3
"""
title: Learning System Unit Tests
purpose: Test learning system components
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from adaptation_engine import (
    AdaptationEngine,
    ImprovementSuggestion,
    PatternAdoptionStrategy,
)
from learning_reporter import LearningReporter
from metric_tracker import MetricTracker
from pattern_learner import ArchitecturalPattern, PatternLearner


class TestPatternLearner(unittest.TestCase):
    """Test pattern learning functionality."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.telemetry_file = Path(self.temp_dir) / "telemetry.jsonl"

    def test_learn_patterns_empty_log(self):
        """Test learning with empty telemetry log."""
        learner = PatternLearner(str(self.telemetry_file))
        patterns = learner.learn_patterns()
        self.assertEqual(patterns, [])

    def test_learn_patterns_with_events(self):
        """Test learning with valid telemetry events."""
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "files_modified": ["file1.py"],
                "cognitive_hops": 1,
                "domain_coherence": 0.9,
                "edit_type": "update",
                "success": True,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "files_modified": ["file2.py"],
                "cognitive_hops": 1,
                "domain_coherence": 0.8,
                "edit_type": "update",
                "success": True,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "files_modified": ["file3.py"],
                "cognitive_hops": 1,
                "domain_coherence": 0.85,
                "edit_type": "update",
                "success": False,
            },
        ]

        with open(self.telemetry_file, "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

        learner = PatternLearner(str(self.telemetry_file))
        patterns = learner.learn_patterns()

        self.assertGreater(len(patterns), 0)
        self.assertIsInstance(patterns[0], ArchitecturalPattern)

    def test_extract_context_features(self):
        """Test context feature extraction."""
        learner = PatternLearner(str(self.telemetry_file))

        event = {
            "files_modified": ["file1.py"],
            "cognitive_hops": 1,
            "domain_coherence": 0.9,
            "edit_type": "create",
        }

        features = learner._extract_context_features(event)

        self.assertIn("single_file", features)
        self.assertIn("low_hops", features)
        self.assertIn("high_coherence", features)
        self.assertIn("edit_create", features)


class TestMetricTracker(unittest.TestCase):
    """Test metrics tracking functionality."""

    def test_track_patterns_empty(self):
        """Test tracking with no patterns."""
        tracker = MetricTracker()
        metrics = tracker.track_patterns([])

        self.assertEqual(metrics["patterns_learned"], 0)
        self.assertEqual(metrics["avg_success_rate"], 0.0)

    def test_track_patterns_with_data(self):
        """Test tracking with patterns."""
        patterns = [
            MagicMock(success_rate=0.8, confidence_score=0.7),
            MagicMock(success_rate=0.3, confidence_score=0.5),
            MagicMock(success_rate=0.9, confidence_score=0.9),
        ]

        tracker = MetricTracker()
        metrics = tracker.track_patterns(patterns)

        self.assertEqual(metrics["patterns_learned"], 3)
        self.assertEqual(metrics["high_success_patterns"], 2)
        self.assertEqual(metrics["low_success_patterns"], 1)

    def test_calculate_predictions(self):
        """Test prediction calculations."""
        patterns = [
            MagicMock(success_rate=0.8, confidence_score=0.9, sample_size=10),
        ]

        tracker = MetricTracker()
        predictions = tracker.calculate_predictions(patterns, {})

        self.assertIn("predicted_success_rate", predictions)
        self.assertIn("confidence", predictions)
        self.assertIn("trend", predictions)


class TestAdaptationEngine(unittest.TestCase):
    """Test adaptation engine functionality."""

    def test_generate_recommendations_empty(self):
        """Test recommendations with no patterns."""
        engine = AdaptationEngine()
        recommendations = engine.generate_recommendations([], {})
        self.assertEqual(recommendations, [])

    def test_pattern_adoption_strategy(self):
        """Test pattern adoption strategy."""
        pattern = MagicMock(
            pattern_id="test_pattern",
            description="Test pattern",
            success_rate=0.8,
            confidence_score=0.7,
            sample_size=10,
            architectural_traits={"avg_cognitive_hops": 2.0},
        )

        metrics = {"max_call_chain_depth": 5}

        strategy = PatternAdoptionStrategy()
        suggestions = strategy.generate_suggestions([pattern], metrics)

        self.assertEqual(len(suggestions), 1)
        self.assertIsInstance(suggestions[0], ImprovementSuggestion)
        self.assertIn("Reduce Cognitive Complexity", suggestions[0].title)

    def test_hotspot_reduction(self):
        """Test hotspot reduction recommendations."""
        metrics = {
            "hotspot_files": [
                {"module": "utils.py"},
                {"module": "config.py"},
                {"module": "helpers.py"},
                {"module": "common.py"},
            ]
        }

        engine = AdaptationEngine()
        recommendations = engine.generate_recommendations([], metrics)

        self.assertGreater(len(recommendations), 0)
        hotspot_rec = [r for r in recommendations if "hotspot" in r.suggestion_id]
        self.assertEqual(len(hotspot_rec), 1)


class TestLearningReporter(unittest.TestCase):
    """Test learning reporter functionality."""

    def test_generate_report_empty(self):
        """Test report generation with no data."""
        reporter = LearningReporter()
        report = reporter.generate_report(
            patterns=[],
            recommendations=[],
            metrics={},
            predictions={"predicted_success_rate": 0.5, "confidence": 0.0},
        )

        self.assertIn("summary", report)
        self.assertEqual(report["summary"]["patterns_learned"], 0)

    def test_generate_insights(self):
        """Test insight generation."""
        patterns = [
            MagicMock(success_rate=0.8, context_features=["low_hops", "high_coherence"]),
        ]

        recommendations = [
            MagicMock(expected_impact="high", effort_estimate="easy", success_probability=0.8),
        ]

        metrics = {"hotspot_files": [{"module": f"file{i}.py"} for i in range(6)]}

        reporter = LearningReporter()
        insights = reporter._generate_insights(patterns, recommendations, metrics)

        self.assertGreater(len(insights), 0)
        self.assertTrue(any("hotspot" in i.lower() for i in insights))

    def test_export_markdown(self):
        """Test markdown export."""
        reporter = LearningReporter()
        report = {
            "summary": {
                "status": "success",
                "patterns_learned": 5,
                "recommendations_generated": 3,
                "confidence": 0.75,
                "trend": "improving",
            },
            "insights": ["Test insight 1", "Test insight 2"],
            "recommendations": [
                {
                    "title": "Test Recommendation",
                    "impact": "high",
                    "effort": "medium",
                    "success_probability": "80%",
                }
            ],
        }

        markdown = reporter._format_markdown(report)

        self.assertIn("# Learning System Report", markdown)
        self.assertIn("## Summary", markdown)
        self.assertIn("## Key Insights", markdown)


if __name__ == "__main__":
    unittest.main()
