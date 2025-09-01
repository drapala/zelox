#!/usr/bin/env python3
"""
title: Test Suite for Confusion Report Analyzer
purpose: Comprehensive tests for cognitive complexity analysis and hotspot detection
inputs: [{"name": "test_scenarios", "type": "code_samples"}]
outputs: [{"name": "test_results", "type": "pass/fail"}]
effects: ["validation", "quality_assurance"]
deps: ["unittest", "tempfile", "pathlib", "ast"]
owners: ["drapala"]
stability: stable
since_version: "0.3.0"
"""

import tempfile
import unittest
from pathlib import Path

from confusion_report import (
    CodeComplexity,
    CognitiveComplexityAnalyzer,
    ConfusionReporter,
    HotspotDetector,
    RefactoringAnalyzer,
)


class TestCognitiveComplexityAnalyzer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        self.analyzer = CognitiveComplexityAnalyzer(self.repo_root)

    def test_simple_function_analysis(self):
        """Test analysis of a simple function with low complexity."""
        simple_code = '''
def simple_function(x):
    """Simple function with minimal complexity."""
    return x * 2
'''
        test_file = self.repo_root / "simple.py"
        test_file.write_text(simple_code)

        complexities = self.analyzer.analyze_file(test_file)

        # Should have module and function complexity
        self.assertEqual(len(complexities), 2)

        # Function should have low complexity
        func_complexity = [c for c in complexities if c.function_name == "simple_function"][0]
        self.assertLessEqual(func_complexity.confusion_score, 3.0)
        self.assertEqual(func_complexity.cyclomatic_complexity, 1)

    def test_complex_function_analysis(self):
        """Test analysis of a complex function with high complexity."""
        complex_code = '''
import os
import sys
from pathlib import Path
from typing import Dict, List

def complex_function(data: Dict, options: List) -> bool:
    """Complex function with high cognitive load."""
    if not data:
        return False
    
    for item in data.get('items', []):
        if item.get('type') == 'special':
            try:
                for i in range(len(item.get('values', []))):
                    if i % 2 == 0:
                        result = process_item(item['values'][i])
                        if result and result.get('status') == 'valid':
                            item['processed'] = True
                        else:
                            item['error'] = 'Processing failed'
                    else:
                        skip_item(item['values'][i])
            except Exception as e:
                log_error(f"Error processing item: {e}")
                return False
        elif item.get('type') == 'normal':
            simple_process(item)
    
    return True

def process_item(value):
    pass

def skip_item(value):
    pass

def simple_process(item):
    pass

def log_error(msg):
    pass
'''
        test_file = self.repo_root / "complex.py"
        test_file.write_text(complex_code)

        complexities = self.analyzer.analyze_file(test_file)

        # Find the complex function
        func_complexity = [c for c in complexities if c.function_name == "complex_function"][0]

        # Should have high complexity
        self.assertGreaterEqual(func_complexity.confusion_score, 5.0)
        self.assertGreaterEqual(func_complexity.cyclomatic_complexity, 5)
        self.assertGreaterEqual(func_complexity.indirection_depth, 3)

    def test_module_level_analysis(self):
        """Test module-level complexity analysis."""
        module_code = """
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

class DataProcessor:
    def __init__(self):
        pass

class ResultHandler:
    def handle(self, result):
        pass

def global_function():
    pass

def another_function():
    pass
"""
        test_file = self.repo_root / "module.py"
        test_file.write_text(module_code)

        complexities = self.analyzer.analyze_file(test_file)

        # Find module-level complexity
        module_complexity = [c for c in complexities if c.function_name is None][0]

        # Should reflect module complexity
        self.assertGreaterEqual(module_complexity.import_dependencies, 5)
        # 2 classes + 2 functions
        self.assertGreaterEqual(module_complexity.cyclomatic_complexity, 4)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestHotspotDetector(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        self.analyzer = CognitiveComplexityAnalyzer(self.repo_root)
        self.detector = HotspotDetector(self.analyzer)

    def test_hotspot_detection_with_threshold(self):
        """Test hotspot detection with different thresholds."""
        # Create a file with known high complexity
        complex_code = '''
import os
import sys
from pathlib import Path

def very_complex_function(data, options, config, state):
    """Function designed to exceed complexity threshold."""
    if not data:
        return None
    
    results = []
    for item in data:
        if item.get('enabled'):
            try:
                if config.get('mode') == 'advanced':
                    for i, value in enumerate(item.get('values', [])):
                        if i % 2 == 0:
                            processed = complex_calculation(value, options, config)
                            if processed and validate_result(processed, state):
                                results.append(processed)
                            else:
                                handle_error(value, "Validation failed")
                        else:
                            alternate_process(value, config)
                else:
                    simple_process(item, results)
            except Exception as e:
                error_handler(e, item)
        else:
            skip_item(item)
    
    return results

def complex_calculation(value, options, config):
    pass

def validate_result(result, state):
    pass

def handle_error(value, message):
    pass

def alternate_process(value, config):
    pass

def simple_process(item, results):
    pass

def error_handler(error, item):
    pass

def skip_item(item):
    pass
'''
        test_file = self.repo_root / "hotspot.py"
        test_file.write_text(complex_code)

        # Test different thresholds
        low_threshold_hotspots = self.detector.detect_hotspots(threshold=3.0)
        high_threshold_hotspots = self.detector.detect_hotspots(threshold=8.0)

        # Should detect more hotspots with lower threshold
        self.assertGreaterEqual(len(low_threshold_hotspots), len(high_threshold_hotspots))

        # Should have at least one hotspot from the complex function
        complex_hotspots = [
            h for h in low_threshold_hotspots if h.function_name == "very_complex_function"
        ]
        self.assertGreater(len(complex_hotspots), 0)

    def test_file_filtering(self):
        """Test that test files and cache directories are filtered out."""
        # Create test file (should be filtered)
        test_code = """
def test_something():
    assert True
"""
        test_file = self.repo_root / "test_module.py"
        test_file.write_text(test_code)

        # Create cache directory (should be filtered)
        cache_dir = self.repo_root / "__pycache__"
        cache_dir.mkdir()
        cache_file = cache_dir / "cached.py"
        cache_file.write_text("# cached file")

        # Create normal file (should be analyzed)
        normal_file = self.repo_root / "normal.py"
        normal_file.write_text("def normal_func(): pass")

        # Test file filtering
        self.assertFalse(self.detector._should_analyze_file(test_file))
        self.assertFalse(self.detector._should_analyze_file(cache_file))
        self.assertTrue(self.detector._should_analyze_file(normal_file))

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestRefactoringAnalyzer(unittest.TestCase):

    def test_vertical_slice_recommendations(self):
        """Test generation of vertical slice refactoring recommendations."""
        # Create mock hotspots indicating scattered complexity
        hotspots = [
            CodeComplexity(
                file_path="features/user/service.py",
                function_name="process_user",
                line_range="10-30",
                cyclomatic_complexity=8,
                indirection_depth=4,
                context_switches=15,
                import_dependencies=6,
                confusion_score=7.5,
            ),
            CodeComplexity(
                file_path="features/user/service.py",
                function_name="validate_user",
                line_range="35-55",
                cyclomatic_complexity=6,
                indirection_depth=3,
                context_switches=12,
                import_dependencies=4,
                confusion_score=6.2,
            ),
            CodeComplexity(
                file_path="features/user/service.py",
                function_name="save_user",
                line_range="60-80",
                cyclomatic_complexity=5,
                indirection_depth=2,
                context_switches=8,
                import_dependencies=3,
                confusion_score=5.8,
            ),
        ]

        analyzer = RefactoringAnalyzer(hotspots)
        recommendations = analyzer.generate_recommendations()

        # Should generate vertical slice recommendation
        vertical_slice_recs = [r for r in recommendations if r.type == "vertical_slice_opportunity"]
        self.assertGreater(len(vertical_slice_recs), 0)

        # Should suggest file splitting
        rec = vertical_slice_recs[0]
        self.assertIn("splitting", rec.recommendation)
        self.assertIn("features/user/service.py", rec.affected_files)

    def test_function_complexity_recommendations(self):
        """Test generation of function-level complexity recommendations."""
        hotspots = [
            CodeComplexity(
                file_path="module.py",
                function_name="extremely_complex_function",
                line_range="10-100",
                cyclomatic_complexity=15,
                indirection_depth=6,
                context_switches=25,
                import_dependencies=0,
                confusion_score=9.5,
            )
        ]

        analyzer = RefactoringAnalyzer(hotspots)
        recommendations = analyzer.generate_recommendations()

        # Should generate function complexity recommendation
        func_recs = [r for r in recommendations if r.type == "function_complexity"]
        self.assertGreater(len(func_recs), 0)

        # Should suggest extraction and nesting reduction
        rec = func_recs[0]
        self.assertIn("Extract", rec.recommendation)
        self.assertIn("nesting", rec.recommendation)


class TestConfusionReporter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        self.reporter = ConfusionReporter(self.repo_root)

    def test_report_generation(self):
        """Test generation of complete confusion analysis report."""
        # Create a sample Python file
        sample_code = '''
import os
from pathlib import Path

def sample_function(data):
    """Sample function for testing."""
    if not data:
        return None
    
    results = []
    for item in data:
        if item.get('valid'):
            try:
                processed = process_item(item)
                results.append(processed)
            except Exception:
                continue
    
    return results

def process_item(item):
    return item.get('value', 0) * 2
'''
        sample_file = self.repo_root / "sample.py"
        sample_file.write_text(sample_code)

        report = self.reporter.generate_report(threshold=3.0)

        # Validate report structure
        self.assertIn("summary", report)
        self.assertIn("hotspots", report)
        self.assertIn("architecture_recommendations", report)

        # Validate summary metrics
        summary = report["summary"]
        self.assertIn("total_files_analyzed", summary)
        self.assertIn("high_confusion_files", summary)
        self.assertIn("overall_confusion_score", summary)
        self.assertIn("refactoring_priority", summary)

        # Should analyze at least one file
        self.assertGreaterEqual(summary["total_files_analyzed"], 1)

    def test_report_with_verbose_mode(self):
        """Test report generation with verbose mode enabled."""
        simple_file = self.repo_root / "simple.py"
        simple_file.write_text("def simple(): pass")

        verbose_report = self.reporter.generate_report(threshold=1.0, verbose=True)

        # Should include detailed analysis section
        self.assertIn("detailed_analysis", verbose_report)
        detailed = verbose_report["detailed_analysis"]
        self.assertIn("threshold_used", detailed)
        self.assertIn("analysis_timestamp", detailed)
        self.assertIn("all_hotspots", detailed)

    def test_refactoring_plan_generation(self):
        """Test markdown refactoring plan generation."""
        # Create file with complexity
        complex_file = self.repo_root / "complex.py"
        complex_file.write_text(
            """
def complex_function(a, b, c):
    if a:
        if b:
            if c:
                for i in range(10):
                    if i % 2 == 0:
                        process(i)
                    else:
                        skip(i)
    return True

def process(x): pass
def skip(x): pass
"""
        )

        plan_file = self.repo_root / "test_plan.md"
        report = self.reporter.generate_report(threshold=2.0)
        self.reporter._generate_refactoring_plan(report, str(plan_file))

        # Plan file should be created
        self.assertTrue(plan_file.exists())

        # Should contain expected sections
        content = plan_file.read_text()
        self.assertIn("# Refactoring Plan", content)
        self.assertIn("## Top Complexity Hotspots", content)
        self.assertIn("## Architecture Recommendations", content)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestIntegrationScenarios(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)

    def test_empty_repository_analysis(self):
        """Test analysis of empty repository."""
        reporter = ConfusionReporter(self.repo_root)
        report = reporter.generate_report()

        # Should handle empty repository gracefully
        self.assertEqual(report["summary"]["total_files_analyzed"], 0)
        self.assertEqual(report["summary"]["high_confusion_files"], 0)
        self.assertEqual(len(report["hotspots"]), 0)

    def test_repository_with_mixed_complexity(self):
        """Test analysis of repository with files of varying complexity."""
        # Simple file
        simple_file = self.repo_root / "simple.py"
        simple_file.write_text("def simple(): return 42")

        # Medium complexity file
        medium_file = self.repo_root / "medium.py"
        medium_file.write_text(
            """
import os
def medium_function(data):
    if data:
        for item in data:
            if item.get('valid'):
                return process(item)
    return None

def process(item): 
    return item * 2
"""
        )

        # Complex file
        complex_file = self.repo_root / "complex.py"
        complex_file.write_text(
            """
import os
import sys
from pathlib import Path
from typing import Dict, List

class ComplexProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.state = {}
    
    def process_all(self, items: List[Dict]) -> List:
        results = []
        for item in items:
            try:
                if self.validate_item(item):
                    if item.get('type') == 'special':
                        result = self.special_process(item)
                    elif item.get('type') == 'normal':
                        result = self.normal_process(item)
                    else:
                        result = self.default_process(item)
                    
                    if result:
                        results.append(result)
                else:
                    self.handle_invalid(item)
            except Exception as e:
                self.handle_error(e, item)
        return results
    
    def validate_item(self, item): pass
    def special_process(self, item): pass
    def normal_process(self, item): pass
    def default_process(self, item): pass
    def handle_invalid(self, item): pass
    def handle_error(self, error, item): pass
"""
        )

        reporter = ConfusionReporter(self.repo_root)
        report = reporter.generate_report(threshold=4.0)

        # Should analyze all files
        self.assertEqual(report["summary"]["total_files_analyzed"], 3)

        # Should identify high complexity files
        self.assertGreaterEqual(report["summary"]["high_confusion_files"], 1)

        # Should have hotspots from complex file
        complex_hotspots = [h for h in report["hotspots"] if "complex.py" in h["file_path"]]
        self.assertGreater(len(complex_hotspots), 0)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
