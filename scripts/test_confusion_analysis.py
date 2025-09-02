#!/usr/bin/env python3
"""
Tests for confusion analysis modules.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from confusion_analysis.complexity_analyzer import ComplexityAnalyzer, ComplexityMetrics
from confusion_analysis.confusion_reporter import ConfusionReporter
from confusion_analysis.confusion_scorer import ConfusionScorer, ScoredFile
from confusion_analysis.hotspot_detector import Hotspot, HotspotDetector


class TestComplexityAnalyzer(unittest.TestCase):
    """Test complexity analysis."""

    def test_simple_function(self):
        """Test analysis of simple function."""
        code = """
def hello():
    return "world"
"""
        metrics = ComplexityAnalyzer.analyze(code)
        self.assertEqual(metrics.cyclomatic_complexity, 1)
        self.assertEqual(metrics.indirection_depth, 1)
        self.assertEqual(metrics.lines_of_code, 3)

    def test_complex_function(self):
        """Test analysis of complex function."""
        code = """
def complex_func(x):
    if x > 0:
        if x > 10:
            return "big"
        else:
            return "small"
    elif x < 0:
        return "negative"
    else:
        return "zero"
"""
        metrics = ComplexityAnalyzer.analyze(code)
        self.assertGreater(metrics.cyclomatic_complexity, 3)
        self.assertEqual(metrics.indirection_depth, 1)  # Single function = depth 1

    def test_class_depth(self):
        """Test indirection depth calculation."""
        code = """
class Outer:
    class Inner:
        def method(self):
            pass
"""
        metrics = ComplexityAnalyzer.analyze(code)
        self.assertEqual(metrics.indirection_depth, 3)

    def test_context_switches(self):
        """Test context switch counting."""
        code = """
import os
from pathlib import Path

def process():
    p = Path("test")
    result = p.exists()
    os.path.join("a", "b")
    return result
"""
        metrics = ComplexityAnalyzer.analyze(code)
        self.assertGreater(metrics.context_switches, 10)

    def test_invalid_syntax(self):
        """Test handling of invalid syntax."""
        code = "def broken("
        metrics = ComplexityAnalyzer.analyze(code)
        self.assertEqual(metrics.cyclomatic_complexity, 0)


class TestConfusionScorer(unittest.TestCase):
    """Test confusion scoring."""

    def test_low_complexity_score(self):
        """Test scoring of low complexity code."""
        metrics = ComplexityMetrics(
            cyclomatic_complexity=3, indirection_depth=1, context_switches=20, lines_of_code=50
        )
        score = ConfusionScorer.calculate_score(metrics)
        self.assertLess(score, 30)

    def test_high_complexity_score(self):
        """Test scoring of high complexity code."""
        metrics = ComplexityMetrics(
            cyclomatic_complexity=25, indirection_depth=8, context_switches=300, lines_of_code=500
        )
        score = ConfusionScorer.calculate_score(metrics)
        self.assertGreater(score, 70)

    def test_identify_issues(self):
        """Test issue identification."""
        metrics = ComplexityMetrics(
            cyclomatic_complexity=15, indirection_depth=5, context_switches=150, lines_of_code=300
        )
        issues = ConfusionScorer.identify_issues(metrics)
        self.assertGreater(len(issues), 2)
        self.assertTrue(any("complexity" in i.lower() for i in issues))

    def test_severity_levels(self):
        """Test severity determination."""
        self.assertEqual(ConfusionScorer.get_severity(85), "critical")
        self.assertEqual(ConfusionScorer.get_severity(60), "high")
        self.assertEqual(ConfusionScorer.get_severity(40), "moderate")
        self.assertEqual(ConfusionScorer.get_severity(20), "low")

    def test_score_file(self):
        """Test complete file scoring."""
        metrics = ComplexityMetrics(
            cyclomatic_complexity=12, indirection_depth=4, context_switches=120, lines_of_code=250
        )
        scored = ConfusionScorer.score_file("test.py", metrics)
        self.assertEqual(scored.file_path, "test.py")
        self.assertIsInstance(scored.score, float)
        self.assertIsInstance(scored.issues, list)
        self.assertIn(scored.severity, ["low", "moderate", "high", "critical"])


class TestHotspotDetector(unittest.TestCase):
    """Test hotspot detection."""

    def setUp(self):
        """Create test data."""
        self.scored_files = [
            ScoredFile(
                file_path=f"file{i}.py",
                metrics=ComplexityMetrics(),
                score=float(i * 10),
                issues=[],
                severity="low" if i < 5 else "high",
            )
            for i in range(10)
        ]

    def test_find_hotspots(self):
        """Test hotspot detection."""
        hotspots = HotspotDetector.find_hotspots(self.scored_files, threshold=50)
        self.assertEqual(len(hotspots), 5)  # Files with score >= 50
        self.assertEqual(hotspots[0].score, 90)  # Highest score first

    def test_categorize_hotspots(self):
        """Test hotspot categorization."""
        hotspots = HotspotDetector.find_hotspots(self.scored_files)
        categories = HotspotDetector.categorize_hotspots(hotspots)
        self.assertIn("high", categories)
        self.assertGreater(len(categories["high"]), 0)

    def test_top_hotspots(self):
        """Test getting top N hotspots."""
        hotspots = HotspotDetector.find_hotspots(self.scored_files, threshold=0)
        top_3 = HotspotDetector.get_top_hotspots(hotspots, 3)
        self.assertEqual(len(top_3), 3)
        self.assertEqual(top_3[0].rank, 1)

    def test_calculate_impact(self):
        """Test impact calculation."""
        hotspots = HotspotDetector.find_hotspots(self.scored_files)
        impact = HotspotDetector.calculate_impact(hotspots)
        self.assertIn("total_hotspots", impact)
        self.assertIn("average_score", impact)
        self.assertIsInstance(impact["average_score"], float)

    def test_common_issues(self):
        """Test finding common issues."""
        hotspots = [
            Hotspot(
                "file1.py", 80, "high", ["High cyclomatic complexity: 20", "Large file: 400"], 1
            ),
            Hotspot(
                "file2.py", 75, "high", ["High cyclomatic complexity: 18", "Deep indirection: 5"], 2
            ),
        ]
        common = HotspotDetector.get_common_issues(hotspots)
        self.assertEqual(common[0][0], "High cyclomatic complexity")
        self.assertEqual(common[0][1], 2)


class TestConfusionReporter(unittest.TestCase):
    """Test report generation."""

    def setUp(self):
        """Create test data."""
        self.scored_files = [
            ScoredFile(
                file_path="test.py",
                metrics=ComplexityMetrics(
                    cyclomatic_complexity=15,
                    indirection_depth=4,
                    context_switches=150,
                    lines_of_code=300,
                ),
                score=65.0,
                issues=["High complexity"],
                severity="high",
            )
        ]
        self.hotspots = HotspotDetector.find_hotspots(self.scored_files)

    def test_generate_report(self):
        """Test report generation."""
        report = ConfusionReporter.generate_report(self.scored_files, self.hotspots, 1.5)
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["total_files"], 1)
        self.assertIn("summary", report)
        self.assertIn("hotspots", report)

    def test_empty_report(self):
        """Test empty report generation."""
        report = ConfusionReporter.generate_report([], [], 0)
        self.assertEqual(report["status"], "no_files_analyzed")
        self.assertEqual(report["total_files"], 0)

    def test_summary_calculation(self):
        """Test summary statistics."""
        report = ConfusionReporter.generate_report(self.scored_files, self.hotspots, 1.0)
        summary = report["summary"]
        self.assertIn("average_complexity", summary)
        self.assertIn("average_confusion_score", summary)
        self.assertEqual(summary["high_confusion_count"], 1)

    def test_save_json(self):
        """Test JSON output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            report = ConfusionReporter.generate_report(self.scored_files, self.hotspots, 1.0)
            ConfusionReporter.save_json(report, Path(f.name))

            # Verify file was written
            content = Path(f.name).read_text()
            self.assertIn('"status": "success"', content)
            Path(f.name).unlink()

    def test_save_markdown(self):
        """Test Markdown output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            report = ConfusionReporter.generate_report(self.scored_files, self.hotspots, 1.0)
            ConfusionReporter.save_markdown(report, Path(f.name))

            # Verify file was written
            content = Path(f.name).read_text()
            self.assertIn("# Confusion Analysis Report", content)
            Path(f.name).unlink()


class TestIntegration(unittest.TestCase):
    """Integration tests for complete pipeline."""

    def test_full_pipeline(self):
        """Test complete analysis pipeline."""
        # Sample code to analyze
        code = """
import os
import sys
from pathlib import Path

class ComplexClass:
    def __init__(self):
        self.value = 0
    
    def complex_method(self, x, y):
        if x > 0:
            if y > 0:
                return x + y
            else:
                return x - y
        elif x < 0:
            if y > 0:
                return y - x
            else:
                return -(x + y)
        else:
            return y

def another_function(items):
    result = []
    for item in items:
        if item > 10:
            result.append(item * 2)
        elif item > 5:
            result.append(item + 5)
        else:
            result.append(item)
    return result
"""

        # Run analysis
        metrics = ComplexityAnalyzer.analyze(code)
        scored = ConfusionScorer.score_file("test.py", metrics)
        hotspots = HotspotDetector.find_hotspots([scored])
        report = ConfusionReporter.generate_report([scored], hotspots, 0.1)

        # Verify results
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["total_files"], 1)
        self.assertGreater(metrics.cyclomatic_complexity, 5)
        self.assertIsInstance(scored.score, float)


if __name__ == "__main__":
    unittest.main()
