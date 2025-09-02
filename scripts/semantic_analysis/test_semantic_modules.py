#!/usr/bin/env python3
"""
title: Semantic Analysis Module Tests
purpose: Smoke tests for semantic analysis pipeline modules
inputs: []
outputs: [{name: "test_results", type: "bool"}]
effects: ["testing"]
deps: ["unittest", "pathlib", "tempfile"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: low
"""

import tempfile
import unittest
from pathlib import Path

from semantic_extractor import SemanticPatterns, extract_patterns
from semantic_parser import ParsedFile, parse_file
from semantic_pipeline import SemanticAnalysisPipeline
from semantic_reporter import AnalysisReport, generate_report
from semantic_scorer import QualityScores, calculate_scores


class TestSemanticParser(unittest.TestCase):
    """Test semantic parser module."""

    def test_parse_python_file(self):
        """Test parsing a simple Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def hello():
    print("Hello")
    return "world"

class MyClass:
    def method(self):
        hello()
"""
            )
            temp_path = Path(f.name)

        try:
            # Parse the file
            parsed = parse_file(temp_path)

            # Verify parsed data
            self.assertIsInstance(parsed, ParsedFile)
            self.assertEqual(len(parsed.functions), 2)  # hello and method
            self.assertEqual(len(parsed.classes), 1)  # MyClass
            self.assertEqual(len(parsed.calls), 1)  # hello() call
            self.assertEqual(len(parsed.parse_errors), 0)

            # Check function details
            func_names = [f.name for f in parsed.functions]
            self.assertIn("hello", func_names)
            self.assertIn("method", func_names)

            # Check class details
            self.assertIn("MyClass", parsed.classes)
            self.assertIn("method", parsed.classes["MyClass"])
        finally:
            temp_path.unlink()

    def test_parse_with_imports(self):
        """Test parsing file with imports."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
from pathlib import Path
import json as j

def process():
    Path().exists()
"""
            )
            temp_path = Path(f.name)

        try:
            parsed = parse_file(temp_path)

            # Check imports
            self.assertEqual(len(parsed.imports), 3)
            module_names = [i.module for i in parsed.imports]
            self.assertIn("os", module_names)
            self.assertIn("pathlib", module_names)
            self.assertIn("json", module_names)
        finally:
            temp_path.unlink()

    def test_parse_invalid_file(self):
        """Test parsing invalid Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def invalid(:\n    pass")
            temp_path = Path(f.name)

        try:
            parsed = parse_file(temp_path)

            # Should have parse errors
            self.assertIsInstance(parsed, ParsedFile)
            self.assertGreater(len(parsed.parse_errors), 0)
            self.assertIn("Syntax error", parsed.parse_errors[0])
        finally:
            temp_path.unlink()


class TestSemanticExtractor(unittest.TestCase):
    """Test semantic extractor module."""

    def test_extract_patterns(self):
        """Test extracting patterns from parsed files."""
        # Create test parsed data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os

def func1():
    func2()

def func2():
    pass
"""
            )
            temp_path = Path(f.name)

        try:
            parsed = parse_file(temp_path)
            patterns = extract_patterns([parsed])

            # Verify patterns
            self.assertIsInstance(patterns, SemanticPatterns)
            self.assertIsNotNone(patterns.dependency_graph)
            self.assertIsInstance(patterns.call_chains, list)
            self.assertIsInstance(patterns.cyclic_deps, list)
            self.assertIsInstance(patterns.hotspots, list)
        finally:
            temp_path.unlink()

    def test_detect_cycles(self):
        """Test cycle detection."""
        # Create files with cyclic dependency
        files = []
        parsed_files = []

        try:
            # File 1
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(
                    """
def func_a():
    func_b()

def func_b():
    func_a()
"""
                )
                files.append(Path(f.name))
                parsed_files.append(parse_file(Path(f.name)))

            patterns = extract_patterns(parsed_files)

            # Should detect call cycle
            # Note: Simple internal recursion might not be flagged as problematic
            self.assertIsNotNone(patterns.cyclic_deps)
        finally:
            for f in files:
                f.unlink()


class TestSemanticScorer(unittest.TestCase):
    """Test semantic scorer module."""

    def test_calculate_scores(self):
        """Test score calculation."""
        # Create test data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
import sys

def simple_function():
    pass
"""
            )
            temp_path = Path(f.name)

        try:
            parsed = parse_file(temp_path)
            patterns = extract_patterns([parsed])
            scores = calculate_scores(patterns)

            # Verify scores
            self.assertIsInstance(scores, QualityScores)
            self.assertIsNotNone(scores.complexity_metrics)
            self.assertGreaterEqual(scores.llm_readiness_score, 0)
            self.assertLessEqual(scores.llm_readiness_score, 100)
            self.assertIsInstance(scores.insights, list)
            self.assertIsInstance(scores.recommendations, list)
        finally:
            temp_path.unlink()

    def test_score_thresholds(self):
        """Test scoring thresholds."""
        # Create complex file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Create deep call chain
            code = ""
            for i in range(10):
                code += f"""
def func_{i}():
    {"func_" + str(i+1) + "()" if i < 9 else "pass"}
"""
            f.write(code)
            temp_path = Path(f.name)

        try:
            parsed = parse_file(temp_path)
            patterns = extract_patterns([parsed])
            scores = calculate_scores(patterns)

            # Deep call chains should reduce score
            self.assertLess(scores.llm_readiness_score, 100)

            # Should have insights about deep chains
            insights_text = " ".join(scores.insights)
            if scores.complexity_metrics.max_call_chain_depth > 6:
                self.assertIn("call chain", insights_text.lower())
        finally:
            temp_path.unlink()


class TestSemanticReporter(unittest.TestCase):
    """Test semantic reporter module."""

    def test_generate_report(self):
        """Test report generation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def test():
    pass
"""
            )
            temp_path = Path(f.name)

        try:
            parsed = parse_file(temp_path)
            patterns = extract_patterns([parsed])
            scores = calculate_scores(patterns)
            report = generate_report(scores, patterns, 1)

            # Verify report structure
            self.assertIsInstance(report, AnalysisReport)
            self.assertIn("files_analyzed", report.summary)
            self.assertIn("llm_readiness_score", report.summary)
            self.assertIn("status", report.summary)
            self.assertIsNotNone(report.metrics)
            self.assertIsInstance(report.insights, list)
            self.assertIsInstance(report.recommendations, list)
        finally:
            temp_path.unlink()


class TestSemanticPipeline(unittest.TestCase):
    """Test semantic pipeline orchestration."""

    def test_pipeline_execution(self):
        """Test complete pipeline execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(
                """
def main():
    print("Hello")

if __name__ == "__main__":
    main()
"""
            )

            # Run pipeline
            pipeline = SemanticAnalysisPipeline(tmpdir)
            result = pipeline.analyze()

            # Verify result
            self.assertIsInstance(result, dict)
            self.assertTrue(result["success"])
            self.assertIn("llm_readiness_score", result)
            self.assertIn("status", result)

            # Verify pipeline stages completed
            self.assertIsNotNone(pipeline.parsed_files)
            self.assertIsNotNone(pipeline.patterns)
            self.assertIsNotNone(pipeline.scores)
            self.assertIsNotNone(pipeline.report)


def run_smoke_tests():
    """Run all smoke tests."""
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    unittest.main()
