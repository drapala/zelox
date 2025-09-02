#!/usr/bin/env python3
"""
title: Repository Mapping Module Tests
purpose: Test suite for modular repo mapping components
stability: stable
since_version: "0.4.0"
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from repo_mapping import (
    FileScanner,
    MapBuilder,
    MapFormatter,
    MapWriter,
    RepoMapBuilder,
)


class TestFileScanner(unittest.TestCase):
    """Test FileScanner component."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.scanner = FileScanner(self.repo_root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scan_empty_directory(self):
        """Test scanning empty directory returns empty list."""
        results = self.scanner.scan_directory(self.repo_root)
        self.assertEqual(results, [])

    def test_scan_python_files(self):
        """Test scanning finds Python files."""
        # Create test file
        test_file = self.repo_root / "test.py"
        test_file.write_text('"""title: Test\npurpose: Testing"""\nprint("hello")')

        results = self.scanner.scan_directory(self.repo_root, {"*.py"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "test.py")

    def test_exclude_patterns(self):
        """Test exclude patterns work correctly."""
        # Create files
        (self.repo_root / "__pycache__").mkdir()
        cache_file = self.repo_root / "__pycache__" / "test.pyc"
        cache_file.write_text("compiled")

        normal_file = self.repo_root / "normal.py"
        normal_file.write_text("code")

        results = self.scanner.scan_directory(self.repo_root, {"*.py", "*.pyc"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "normal.py")

    def test_incremental_changes(self):
        """Test detecting changed files."""
        # Create file
        test_file = self.repo_root / "test.py"
        test_file.write_text("original")

        # Get changed files in last hour
        since = datetime.now() - timedelta(hours=1)
        changed = self.scanner.get_changed_files(since)
        # Compare resolved paths to handle symlinks
        self.assertIn(test_file.resolve(), changed)

        # No changes before file creation
        future = datetime.now() + timedelta(hours=1)
        changed = self.scanner.get_changed_files(future)
        self.assertEqual(changed, [])


class TestMapBuilder(unittest.TestCase):
    """Test MapBuilder component."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.builder = MapBuilder(self.repo_root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_feature_file(self):
        """Test adding files to features."""
        file_info = {
            "path": "features/auth/service.py",
            "name": "service.py",
            "lines": 100,
            "frontmatter": {"purpose": "Authentication logic"},
        }

        self.builder.add_file(file_info)
        structure = self.builder.build()

        self.assertEqual(len(structure["features"]), 1)
        self.assertEqual(structure["features"][0]["name"], "auth")
        self.assertEqual(len(structure["features"][0]["files"]), 1)

    def test_add_script_file(self):
        """Test adding script files."""
        file_info = {
            "path": "scripts/analyze.py",
            "name": "analyze.py",
            "lines": 50,
            "frontmatter": {"purpose": "Code analysis"},
        }

        self.builder.add_file(file_info)
        structure = self.builder.build()

        self.assertEqual(len(structure["scripts"]), 1)
        self.assertEqual(structure["scripts"][0]["name"], "analyze.py")

    def test_statistics(self):
        """Test statistics calculation."""
        # Add feature with tests
        self.builder.add_file(
            {
                "path": "features/auth/tests.py",
                "name": "tests.py",
                "lines": 200,
            }
        )

        stats = self.builder.get_statistics()
        self.assertEqual(stats["total_features"], 1)
        self.assertEqual(stats["features_with_tests"], 1)


class TestMapFormatter(unittest.TestCase):
    """Test MapFormatter component."""

    def test_format_markdown(self):
        """Test Markdown formatting."""
        structure = {
            "features": [
                {
                    "name": "auth",
                    "files": [{"name": "service.py", "purpose": "Auth logic"}],
                    "capabilities": ["tests"],
                    "metrics": {"loc": 100},
                }
            ],
            "scripts": [],
            "docs": {"adrs": [], "repo": []},
        }

        formatter = MapFormatter(structure)
        markdown = formatter.format_markdown()

        self.assertIn("# REPO_MAP.md", markdown)
        self.assertIn("Auth", markdown)
        self.assertIn("features/auth/", markdown)

    def test_format_json(self):
        """Test JSON formatting."""
        structure = {"features": [], "scripts": []}
        formatter = MapFormatter(structure)
        json_data = formatter.format_json()

        self.assertIn("generated", json_data)
        self.assertIn("structure", json_data)
        self.assertEqual(json_data["structure"], structure)


class TestMapWriter(unittest.TestCase):
    """Test MapWriter component."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.writer = MapWriter(self.output_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_markdown(self):
        """Test writing Markdown content."""
        content = "# Test Map\nContent here"
        output_path = self.writer.write(content, "test.md")

        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_text(), content)

    def test_backup_creation(self):
        """Test backup is created when overwriting."""
        # Write initial content
        self.writer.write("original", "test.md")

        # Overwrite with backup
        self.writer.write("updated", "test.md", backup=True)

        # Check backup exists
        backup_dir = self.output_dir / ".backups"
        self.assertTrue(backup_dir.exists())
        backups = list(backup_dir.glob("test_*.md"))
        self.assertEqual(len(backups), 1)

    def test_versioning(self):
        """Test version tracking."""
        self.writer.write("v1", "test.md")
        self.writer.write("v2", "test.md")

        versions = self.writer.get_versions("test.md")
        self.assertEqual(len(versions), 2)


class TestRepoMapBuilder(unittest.TestCase):
    """Test RepoMapBuilder fluent interface."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

        # Create test structure
        (self.repo_root / "features" / "auth").mkdir(parents=True)
        (self.repo_root / "scripts").mkdir()

        auth_service = self.repo_root / "features" / "auth" / "service.py"
        auth_service.write_text('"""purpose: Auth logic"""\nclass AuthService: pass')

        script = self.repo_root / "scripts" / "tool.py"
        script.write_text('"""purpose: Utility"""\nprint("tool")')

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fluent_interface(self):
        """Test fluent builder interface."""
        builder = RepoMapBuilder(self.repo_root)
        result = builder.scan().filter({"*.py"}).build()

        self.assertIsInstance(result, RepoMapBuilder)
        stats = builder.get_statistics()
        self.assertGreater(stats["files_scanned"], 0)

    def test_incremental_mode(self):
        """Test incremental scanning."""
        builder = RepoMapBuilder(self.repo_root)

        # Full scan
        builder.scan().build()
        initial_count = builder.get_statistics()["files_scanned"]

        # Incremental scan (no changes)
        builder.reset()
        since = datetime.now() + timedelta(hours=1)  # Future
        builder.incremental_since(since).scan().build()
        incremental_count = builder.get_statistics()["files_scanned"]

        self.assertEqual(incremental_count, 0)
        self.assertGreater(initial_count, 0)

    def test_format_output(self):
        """Test formatting in different styles."""
        builder = RepoMapBuilder(self.repo_root)
        builder.scan().build()

        # Test Markdown
        markdown = builder.format("markdown")
        self.assertIn("# REPO_MAP.md", markdown)

        # Test JSON
        json_str = builder.format("json")
        json_data = json.loads(json_str)
        self.assertIn("structure", json_data)


if __name__ == "__main__":
    unittest.main()
