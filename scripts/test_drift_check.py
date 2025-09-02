#!/usr/bin/env python3
"""
title: Test Suite for Drift Check Monitor
purpose: Comprehensive tests for controlled duplication drift detection
inputs: [{"name": "test_cases", "type": "scenarios"}]
outputs: [{"name": "test_results", "type": "pass/fail"}]
effects: ["validation", "quality_assurance"]
deps: ["unittest", "tempfile", "pathlib"]
owners: ["drapala"]
stability: stable
since_version: "0.4.0"
"""

import tempfile
import unittest
from pathlib import Path

from drift_detection import BlockFinder, DriftCalculator, DriftReporter


class TestDriftDetection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        self.finder = BlockFinder(self.repo_root)
        self.calculator = DriftCalculator()
        self.reporter = DriftReporter()

    def test_exact_duplication_valid(self):
        """Test that identical blocks pass exact tolerance."""
        content = """# DUPLICATED_BLOCK: test_block
def test_function():
    return True
# END_DUPLICATED_BLOCK: test_block"""

        # Create two identical files
        (self.repo_root / "file1.py").write_text(content)
        (self.repo_root / "file2.py").write_text(content)

        blocks = self.finder.find_all()
        results = self.calculator.calculate_all(blocks)
        stats = self.calculator.get_summary_stats(results)

        self.assertEqual(stats["drifted_count"], 0)
        self.assertEqual(stats["healthy_count"], 1)

    def test_whitespace_drift_acceptable(self):
        """Test that whitespace differences are acceptable with whitespace tolerance."""
        content1 = """# DUPLICATED_BLOCK: whitespace_test
def test_function():
    return True
# END_DUPLICATED_BLOCK: whitespace_test"""

        content2 = """# DUPLICATED_BLOCK: whitespace_test
def test_function():
        return True
# END_DUPLICATED_BLOCK: whitespace_test"""

        (self.repo_root / "file1.py").write_text(content1)
        (self.repo_root / "file2.py").write_text(content2)

        blocks = self.finder.find_all()
        results = self.calculator.calculate_all(blocks)
        stats = self.calculator.get_summary_stats(results)

        # Should be healthy due to whitespace tolerance
        self.assertEqual(stats["healthy_count"], 1)

    def test_content_drift_exceeds_tolerance(self):
        """Test that significant content changes are detected as drift."""
        content1 = """# DUPLICATED_BLOCK: drift_test
def test_function():
    return True
# END_DUPLICATED_BLOCK: drift_test"""

        content2 = """# DUPLICATED_BLOCK: drift_test
def completely_different_function():
    return False
# END_DUPLICATED_BLOCK: drift_test"""

        (self.repo_root / "file1.py").write_text(content1)
        (self.repo_root / "file2.py").write_text(content2)

        blocks = self.finder.find_all()
        results = self.calculator.calculate_all(blocks)
        stats = self.calculator.get_summary_stats(results)

        self.assertEqual(stats["drifted_count"], 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].block_id, "drift_test")

    def test_orphaned_block_detection(self):
        """Test detection of blocks without matching END markers."""
        content = """# DUPLICATED_BLOCK: orphaned_block
def test_function():
    return True
# Missing END marker"""

        (self.repo_root / "file1.py").write_text(content)

        blocks = self.finder.find_all()

        # Should not create any blocks due to missing END marker
        self.assertEqual(len(blocks), 0)

    def test_multiple_language_support(self):
        """Test scanning across multiple file types."""
        py_content = """# DUPLICATED_BLOCK: multi_lang
config = {"key": "value"}
# END_DUPLICATED_BLOCK: multi_lang"""

        js_content = """// DUPLICATED_BLOCK: js_block
const config = {key: "value"};
// END_DUPLICATED_BLOCK: js_block"""

        (self.repo_root / "config.py").write_text(py_content)
        (self.repo_root / "config.js").write_text(js_content)

        blocks = self.finder.find_all()

        # Should find blocks from both file types
        self.assertGreater(len(blocks), 0)

    def test_json_report_generation(self):
        """Test JSON report generation."""
        content = """# DUPLICATED_BLOCK: report_test
test_value = 42
# END_DUPLICATED_BLOCK: report_test"""

        (self.repo_root / "file1.py").write_text(content)
        (self.repo_root / "file2.py").write_text(content)

        blocks = self.finder.find_all()
        results = self.calculator.calculate_all(blocks)
        stats = self.calculator.get_summary_stats(results)
        report = self.reporter.report_json(results, stats)

        self.assertIn("summary", report)
        self.assertEqual(report["summary"]["drifted_count"], 0)

    def test_performance_with_cache(self):
        """Test that similarity calculation uses caching."""
        content1 = """# DUPLICATED_BLOCK: cache_test
def function():
    return True
# END_DUPLICATED_BLOCK: cache_test"""

        content2 = """# DUPLICATED_BLOCK: cache_test
def function():
    return True  # slightly different
# END_DUPLICATED_BLOCK: cache_test"""

        # Create files with slightly different content to trigger cache use
        (self.repo_root / "file1.py").write_text(content1)
        (self.repo_root / "file2.py").write_text(content2)
        (self.repo_root / "file3.py").write_text(content1)

        blocks = self.finder.find_all()

        # First calculation
        results1 = self.calculator.calculate_all(blocks)

        # Second calculation should use cache
        results2 = self.calculator.calculate_all(blocks)

        self.assertEqual(len(results1), len(results2))
        # Cache should have entries for non-identical comparisons
        self.assertGreaterEqual(len(self.calculator._cache), 1)


if __name__ == "__main__":
    unittest.main()
