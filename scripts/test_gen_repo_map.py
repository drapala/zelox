#!/usr/bin/env python3
"""
title: Repository Map Generator Tests
purpose: Comprehensive test suite for gen_repo_map.py
inputs: [{"name": "test_fixtures", "type": "directory"}]
outputs: [{"name": "test_results", "type": "boolean"}]
effects: ["test_execution"]
deps: ["unittest", "tempfile", "pathlib"]
owners: ["drapala"]
stability: stable
since_version: "0.3.0"
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gen_repo_map import (
    FileAnalyzer,
    MarkdownGenerator,
    StructureMapper,
)


class TestFileAnalyzer(unittest.TestCase):
    """Test FileAnalyzer class functionality."""

    def test_extract_python_frontmatter_valid(self):
        """Test extraction of valid Python frontmatter."""
        content = '''#!/usr/bin/env python3
"""
title: Test Module
purpose: Testing frontmatter extraction
deps: ["pathlib", "yaml"]
owners: ["test_user"]
stability: stable
"""

def test_function():
    pass
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()

            result = FileAnalyzer.extract_python_frontmatter(Path(f.name))

            self.assertEqual(result["title"], "Test Module")
            self.assertEqual(result["purpose"], "Testing frontmatter extraction")
            self.assertEqual(result["stability"], "stable")
            self.assertIn("pathlib", result.get("deps", []))
            self.assertIn("test_user", result.get("owners", []))

        os.unlink(f.name)

    def test_extract_python_frontmatter_empty(self):
        """Test handling of files without frontmatter."""
        content = """def simple_function():
    return "no frontmatter here"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()

            result = FileAnalyzer.extract_python_frontmatter(Path(f.name))

            self.assertEqual(result, {})

        os.unlink(f.name)

    def test_get_file_purpose_known_files(self):
        """Test purpose detection for known file types."""
        test_cases = [
            ("service.py", "Business logic orchestration"),
            ("models.py", "Domain entities and value objects"),
            ("api.py", "HTTP endpoints and request handling"),
            ("tests.py", "Test suite"),
            ("wiring.py", "Dependency injection setup"),
            ("repository.py", "Data access layer"),
        ]

        for filename, expected_purpose in test_cases:
            with self.subTest(filename=filename):
                result = FileAnalyzer.get_file_purpose(Path(filename))
                self.assertEqual(result, expected_purpose)

    def test_get_file_purpose_with_frontmatter(self):
        """Test purpose extraction from frontmatter."""
        content = '''"""
title: Custom Module
purpose: Custom purpose from frontmatter
"""

def custom_function():
    pass
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()

            result = FileAnalyzer.get_file_purpose(Path(f.name))

            self.assertEqual(result, "Custom purpose from frontmatter")

        os.unlink(f.name)


class TestStructureMapper(unittest.TestCase):
    """Test StructureMapper class functionality."""

    def setUp(self):
        """Set up temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.test_dir)
        self.mapper = StructureMapper(self.repo_root)

        # Create basic directory structure
        (self.repo_root / "features").mkdir()
        (self.repo_root / "scripts").mkdir()
        (self.repo_root / "docs").mkdir()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.test_dir)

    def test_scan_features_empty(self):
        """Test scanning empty features directory."""
        result = self.mapper.scan_features()
        self.assertEqual(result, [])

    def test_scan_features_with_content(self):
        """Test scanning features with actual content."""
        # Create a test feature
        feature_dir = self.repo_root / "features" / "test_feature"
        feature_dir.mkdir()

        # Add some files
        (feature_dir / "service.py").write_text("# Service file")
        (feature_dir / "tests.py").write_text("# Test file")
        (feature_dir / "api.py").write_text("# API file")

        result = self.mapper.scan_features()

        self.assertEqual(len(result), 1)
        feature = result[0]
        self.assertEqual(feature["name"], "test_feature")
        self.assertIn("Tests", feature["capabilities"])
        self.assertIn("HTTP API", feature["capabilities"])
        self.assertIn("Business Logic", feature["capabilities"])
        self.assertEqual(len(feature["files"]), 3)

    def test_scan_scripts(self):
        """Test scanning scripts directory."""
        # Create test scripts
        (self.repo_root / "scripts" / "gen_repo_map.py").write_text(
            '''"""
title: Repo Map Generator
purpose: Generate repository map
"""
'''
        )
        (self.repo_root / "scripts" / "test_gen_repo_map.py").write_text("# Test file")

        result = self.mapper.scan_scripts()

        # Should only include non-test files
        self.assertEqual(len(result), 1)
        script = result[0]
        self.assertEqual(script["name"], "gen_repo_map.py")
        self.assertEqual(script["purpose"], "Generate repository map")

    def test_scan_adrs(self):
        """Test scanning ADR directory."""
        # Create test ADR directory and files
        adr_dir = self.repo_root / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "001-test-decision.md").write_text("# Test ADR")
        (adr_dir / "002_another_decision.md").write_text("# Another ADR")
        (adr_dir / "003use-microservices.md").write_text("# No separator")
        (adr_dir / "my-adr-004-title.md").write_text("# Edge case")

        result = self.mapper.scan_adrs()

        # Should find all ADRs
        self.assertEqual(len(result), 4)

        # Test normal dash separator
        first_adr = result[0]
        self.assertEqual(first_adr["number"], "001")
        self.assertEqual(first_adr["title"], "Test Decision")
        self.assertEqual(first_adr["path"], "../adr/001-test-decision.md")

        # Test underscore separator
        second_adr = result[1]
        self.assertEqual(second_adr["number"], "002")
        self.assertEqual(second_adr["title"], "Another Decision")

        # Test no separator
        third_adr = result[2]
        self.assertEqual(third_adr["number"], "003")
        self.assertEqual(third_adr["title"], "Use Microservices")

        # Test edge case - should extract first number, not 'my'
        fourth_adr = result[3]
        self.assertEqual(fourth_adr["number"], "004")
        self.assertEqual(fourth_adr["title"], "Title")

    def test_scan_adrs_empty(self):
        """Test scanning empty ADR directory."""
        result = self.mapper.scan_adrs()
        self.assertEqual(len(result), 0)


class TestMarkdownGenerator(unittest.TestCase):
    """Test MarkdownGenerator class functionality."""

    def setUp(self):
        """Set up temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.test_dir)
        self.generator = MarkdownGenerator(self.repo_root)

        # Create minimal structure
        (self.repo_root / "features").mkdir()
        (self.repo_root / "scripts").mkdir()
        (self.repo_root / "docs").mkdir()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.test_dir)

    def test_generate_header(self):
        """Test header generation."""
        header = self.generator.generate_header()

        self.assertIn("# REPO_MAP.md - Repository Navigation Guide", header)
        self.assertIn("**Generated:**", header)
        self.assertIn("**Purpose:** LLM-first navigation", header)

    def test_generate_structure_overview(self):
        """Test structure overview generation."""
        overview = self.generator.generate_structure_overview()

        self.assertIn("## Repository Structure", overview)
        self.assertIn("zelox/", overview)
        self.assertIn("features/", overview)
        self.assertIn("scripts/", overview)

    def test_generate_features_section_empty(self):
        """Test features section with no features."""
        section = self.generator.generate_features_section()

        self.assertIn("## Current Features", section)
        self.assertIn("*None yet - this is a new repository*", section)

    def test_generate_features_section_with_content(self):
        """Test features section with actual features."""
        # Create a test feature
        feature_dir = self.repo_root / "features" / "user_management"
        feature_dir.mkdir()
        (feature_dir / "service.py").write_text("# Service")
        (feature_dir / "tests.py").write_text("# Tests")

        section = self.generator.generate_features_section()

        self.assertIn("## Current Features", section)
        self.assertIn("### User Management", section)
        self.assertIn("Business Logic", section)
        self.assertIn("Tests", section)

    def test_generate_full_map(self):
        """Test full map generation."""
        full_map = self.generator.generate_full_map()

        # Check for all major sections
        expected_sections = [
            "# REPO_MAP.md - Repository Navigation Guide",
            "## Repository Structure",
            "## Quick Navigation",
            "## Current Features",
            "## Architecture Decisions",
            "## Common Tasks",
            "## Last Updated",
        ]

        for section in expected_sections:
            with self.subTest(section=section):
                self.assertIn(section, full_map)


class TestIntegration(unittest.TestCase):
    """Integration tests using real repository structure."""

    def setUp(self):
        """Set up using actual repository root."""
        # Use the real repository for integration tests
        self.repo_root = Path(__file__).parent.parent
        self.generator = MarkdownGenerator(self.repo_root)

    def test_real_repository_scan(self):
        """Test scanning the actual repository."""
        # This should not crash and should find real content
        full_map = self.generator.generate_full_map()

        self.assertIn("# REPO_MAP.md", full_map)
        self.assertIn("## Repository Structure", full_map)
        self.assertIn("scripts/gen_repo_map.py", full_map)  # Should find our script

    def test_real_scripts_detection(self):
        """Test detection of actual scripts."""
        mapper = StructureMapper(self.repo_root)
        scripts = mapper.scan_scripts()

        script_names = [s["name"] for s in scripts]
        self.assertIn("gen_repo_map.py", script_names)

        # Find our script and check its purpose
        gen_script = next(s for s in scripts if s["name"] == "gen_repo_map.py")
        self.assertEqual(
            gen_script["purpose"], "Auto-generate REPO_MAP.md from current codebase state"
        )


def run_smoke_tests():
    """Run smoke tests for critical functionality."""
    print("🧪 Running smoke tests...")

    # Test 1: Can import all classes
    try:
        import gen_repo_map  # noqa: F401

        print("✅ Import test passed")
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

    # Test 2: Can create temporary structure and scan
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "features").mkdir()

            mapper = StructureMapper(repo_root)
            mapper.scan_features()

            generator = MarkdownGenerator(repo_root)
            content = generator.generate_full_map()

            assert len(content) > 100, "Generated content too short"
            assert "REPO_MAP" in content, "Missing title"

        print("✅ Basic functionality test passed")
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

    print("🎉 All smoke tests passed!")
    return True


if __name__ == "__main__":
    # Run smoke tests first
    if not run_smoke_tests():
        sys.exit(1)

    # Run full test suite
    unittest.main(verbosity=2)
