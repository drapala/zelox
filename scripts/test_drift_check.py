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
since_version: "0.3.0"
"""

import tempfile
import unittest
from pathlib import Path

from drift_check import DriftChecker


class TestDriftChecker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        self.checker = DriftChecker(self.repo_root)

    def test_exact_duplication_valid(self):
        """Test that identical blocks pass exact tolerance."""
        content = """# DUPLICATED_BLOCK: test_block
def test_function():
    return True
# END_DUPLICATED_BLOCK: test_block"""

        # Create two identical files
        (self.repo_root / "file1.py").write_text(content)
        (self.repo_root / "file2.py").write_text(content)

        self.checker.scan_files()
        report = self.checker.check_drift()

        self.assertEqual(report["summary"]["drifted_blocks"], 0)
        self.assertEqual(report["summary"]["healthy_blocks"], 1)

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

        self.checker.scan_files()
        report = self.checker.check_drift()

        # Should be healthy due to whitespace tolerance
        self.assertEqual(report["summary"]["healthy_blocks"], 1)

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

        self.checker.scan_files()
        report = self.checker.check_drift()

        self.assertEqual(report["summary"]["drifted_blocks"], 1)
        self.assertEqual(len(report["drifted_blocks"]), 1)
        self.assertEqual(report["drifted_blocks"][0]["id"], "drift_test")

    def test_orphaned_block_detection(self):
        """Test detection of blocks without matching END markers."""
        content = """# DUPLICATED_BLOCK: orphaned_block
def test_function():
    return True
# Missing END marker"""

        (self.repo_root / "file1.py").write_text(content)

        self.checker.scan_files()

        # Should not create any blocks due to missing END marker
        self.assertEqual(len(self.checker.blocks), 0)

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

        self.checker.scan_files()

        # Should find blocks from both file types
        self.assertGreater(len(self.checker.blocks), 0)

    def test_exit_codes(self):
        """Test proper exit code behavior."""
        # Test healthy state
        content = """# DUPLICATED_BLOCK: exit_test
test_value = 42
# END_DUPLICATED_BLOCK: exit_test"""

        (self.repo_root / "file1.py").write_text(content)
        (self.repo_root / "file2.py").write_text(content)

        exit_code = self.checker.run()
        self.assertEqual(exit_code, 0)

    # tearDown no longer needed - cleanup handled automatically


if __name__ == "__main__":
    unittest.main()
