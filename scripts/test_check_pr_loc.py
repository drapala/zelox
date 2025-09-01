#!/usr/bin/env python3
"""
Unit tests for check_pr_loc.py

title: PR LOC Check Tests
purpose: Validate PR size checking logic
inputs: [{"name": "test_scenarios", "type": "functions"}]
outputs: [{"name": "test_results", "type": "pass_fail"}]
effects: ["validation"]
deps: ["pytest", "unittest.mock"]
owners: ["drapala"]
stability: stable
since_version: "0.2.0"
"""

import sys
from pathlib import Path
from unittest.mock import ANY, patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from check_pr_loc import (
    TOTAL_FILES_LIMIT,
    FileCategory,
    analyze_pr,
    categorize_file,
    check_limits,
    get_changed_files,
    get_file_diff_stats,
    run_git_command,
)


class TestFileCategorization:
    """Test file categorization logic."""

    def test_markdown_files_are_documentation(self):
        """Markdown files should be detected as documentation."""
        assert categorize_file("README.md") == FileCategory.DOCUMENTATION
        assert categorize_file("docs/guide.md") == FileCategory.DOCUMENTATION
        assert categorize_file("CHANGELOG.MD") == FileCategory.DOCUMENTATION  # Case insensitive

    def test_license_files_are_documentation(self):
        """License and notice files should be documentation."""
        assert categorize_file("LICENSE") == FileCategory.DOCUMENTATION
        assert categorize_file("NOTICE") == FileCategory.DOCUMENTATION
        assert categorize_file("AUTHORS") == FileCategory.DOCUMENTATION
        assert categorize_file("CONTRIBUTORS.txt") == FileCategory.DOCUMENTATION

    def test_code_files_are_application(self):
        """Code files should be detected as application code."""
        assert categorize_file("main.py") == FileCategory.APPLICATION
        assert categorize_file("script.js") == FileCategory.APPLICATION
        assert categorize_file("style.css") == FileCategory.APPLICATION
        assert categorize_file("component.jsx") == FileCategory.APPLICATION

    def test_test_files_are_tests(self):
        """Test files should be detected as tests."""
        assert categorize_file("test_main.py") == FileCategory.TEST
        assert categorize_file("main_test.py") == FileCategory.TEST
        assert categorize_file("app.test.js") == FileCategory.TEST
        assert categorize_file("component.spec.tsx") == FileCategory.TEST

    def test_config_files_are_config(self):
        """Config files should be detected as config."""
        assert categorize_file(".github/workflows/ci.yml") == FileCategory.CONFIG
        assert categorize_file("schemas/foo.json") == FileCategory.CONFIG
        assert categorize_file("Makefile") == FileCategory.CONFIG
        assert categorize_file("Dockerfile") == FileCategory.CONFIG


class TestGitCommands:
    """Test git command execution."""

    @patch("check_pr_loc.subprocess.check_output")
    def test_run_git_command_success(self, mock_subprocess):
        """Test successful git command execution."""
        mock_subprocess.return_value = "file1.py\nfile2.js\n"

        result = run_git_command("diff", "--name-only", "HEAD")

        assert result == "file1.py\nfile2.js"
        mock_subprocess.assert_called_once_with(
            ["git", "diff", "--name-only", "HEAD"], text=True, stderr=ANY
        )

    @patch("check_pr_loc.subprocess.check_output")
    def test_run_git_command_failure(self, mock_subprocess):
        """Test git command failure handling."""
        from subprocess import CalledProcessError

        mock_subprocess.side_effect = CalledProcessError(1, "git")

        result = run_git_command("invalid", "command")

        assert result == ""

    @patch("check_pr_loc.run_git_command")
    def test_get_changed_files(self, mock_run):
        """Test parsing changed files from git diff."""
        mock_run.return_value = "file1.py\nfile2.md\n\nfile3.js\n"

        files = get_changed_files("main...HEAD")

        assert files == ["file1.py", "file2.md", "file3.js"]
        mock_run.assert_called_once_with("diff", "--name-only", "main...HEAD")


class TestDiffStats:
    """Test diff statistics calculation."""

    @patch("check_pr_loc.run_git_command")
    def test_get_file_diff_stats_with_changes(self, mock_run):
        """Test counting added and deleted lines."""
        mock_run.return_value = """
diff --git a/file.py b/file.py
@@ -1,5 +1,6 @@
 def hello():
-    print("old")
+    print("new")
+    print("added line")
 def world():
"""

        added, deleted = get_file_diff_stats("file.py", "main...HEAD")

        assert added == 2  # Two lines with +
        assert deleted == 1  # One line with -

    @patch("check_pr_loc.run_git_command")
    def test_get_file_diff_stats_no_changes(self, mock_run):
        """Test file with no changes."""
        mock_run.return_value = ""

        added, deleted = get_file_diff_stats("unchanged.py", "main...HEAD")

        assert added == 0
        assert deleted == 0

    @patch("check_pr_loc.run_git_command")
    def test_get_file_diff_stats_ignores_diff_headers(self, mock_run):
        """Test that diff headers are not counted."""
        mock_run.return_value = """
--- a/file.py
+++ b/file.py
@@ -1,2 +1,3 @@
+actual content
-removed content
"""

        added, deleted = get_file_diff_stats("file.py", "main...HEAD")

        assert added == 1  # Only actual content line
        assert deleted == 1  # Only actual content line


class TestPRAnalysis:
    """Test complete PR analysis."""

    @patch("check_pr_loc.get_changed_files")
    @patch("check_pr_loc.get_file_diff_stats")
    def test_analyze_pr_categorizes_files(self, mock_diff, mock_files):
        """Test PR analysis categorizes files correctly."""
        mock_files.return_value = [
            "main.py",
            "README.md",
            "test_main.py",
            ".github/workflows/ci.yml",
            "LICENSE",
        ]
        mock_diff.return_value = (10, 5)  # 10 added, 5 deleted for each

        stats = analyze_pr("main...HEAD")

        assert stats["total_files"] == 5
        assert len(stats["categorized_files"][FileCategory.APPLICATION]) == 1  # main.py only
        assert len(stats["categorized_files"][FileCategory.TEST]) == 1  # test_main.py
        assert len(stats["categorized_files"][FileCategory.CONFIG]) == 1  # ci.yml
        assert len(stats["categorized_files"][FileCategory.DOCUMENTATION]) == 2  # README, LICENSE

        # Check LOC calculations (documentation doesn't count)
        assert stats["categorized_stats"][FileCategory.APPLICATION]["loc"] == 15
        assert stats["categorized_stats"][FileCategory.TEST]["loc"] == 15
        assert stats["categorized_stats"][FileCategory.CONFIG]["loc"] == 15
        assert stats["categorized_stats"][FileCategory.DOCUMENTATION]["loc"] == 0

    @patch("check_pr_loc.get_changed_files")
    def test_analyze_pr_empty(self, mock_files):
        """Test analyzing empty PR."""
        mock_files.return_value = []

        stats = analyze_pr("main...HEAD")

        assert stats["total_files"] == 0
        for category in FileCategory:
            assert len(stats["categorized_files"][category]) == 0
            assert stats["categorized_stats"][category]["loc"] == 0


class TestLimitChecking:
    """Test PR size limit checking."""

    def test_check_limits_within_bounds(self):
        """Test PR within limits passes."""
        stats = {
            "total_files": 10,
            "categorized_files": {
                FileCategory.APPLICATION: ["file1.py", "file2.py"],
                FileCategory.TEST: ["test1.py"],
                FileCategory.CONFIG: [],
                FileCategory.DOCUMENTATION: ["README.md"],
            },
            "categorized_stats": {
                FileCategory.APPLICATION: {"loc": 300, "added": 200, "deleted": 100},
                FileCategory.TEST: {"loc": 400, "added": 300, "deleted": 100},
                FileCategory.CONFIG: {"loc": 0, "added": 0, "deleted": 0},
                FileCategory.DOCUMENTATION: {"loc": 0, "added": 0, "deleted": 0},
            },
        }

        result = check_limits(stats)

        assert result is True

    def test_check_limits_too_many_application_files(self):
        """Test PR with too many application files fails."""
        stats = {
            "total_files": 15,
            "categorized_files": {
                FileCategory.APPLICATION: [f"file{i}.py" for i in range(15)],  # Over limit
                FileCategory.TEST: [],
                FileCategory.CONFIG: [],
                FileCategory.DOCUMENTATION: [],
            },
            "categorized_stats": {
                FileCategory.APPLICATION: {"loc": 100, "added": 50, "deleted": 50},
                FileCategory.TEST: {"loc": 0, "added": 0, "deleted": 0},
                FileCategory.CONFIG: {"loc": 0, "added": 0, "deleted": 0},
                FileCategory.DOCUMENTATION: {"loc": 0, "added": 0, "deleted": 0},
            },
        }

        result = check_limits(stats)

        assert result is False

    def test_check_limits_too_many_lines(self):
        """Test PR with too many lines fails."""
        stats = {
            "total_files": 5,
            "categorized_files": {
                FileCategory.APPLICATION: ["file1.py", "file2.py"],
                FileCategory.TEST: [],
                FileCategory.CONFIG: [],
                FileCategory.DOCUMENTATION: [],
            },
            "categorized_stats": {
                # Over limit of 500 LOC
                FileCategory.APPLICATION: {"loc": 600, "added": 400, "deleted": 200},
                FileCategory.TEST: {"loc": 0, "added": 0, "deleted": 0},
                FileCategory.CONFIG: {"loc": 0, "added": 0, "deleted": 0},
                FileCategory.DOCUMENTATION: {"loc": 0, "added": 0, "deleted": 0},
            },
        }

        result = check_limits(stats)

        assert result is False

    def test_check_limits_at_maximum(self):
        """Test PR exactly at limits passes."""
        stats = {
            "total_files": TOTAL_FILES_LIMIT,
            "categorized_files": {
                FileCategory.APPLICATION: [f"file{i}.py" for i in range(10)],  # Max 10 files
                FileCategory.TEST: [f"test{i}.py" for i in range(10)],  # Within test limit
                FileCategory.CONFIG: [],
                FileCategory.DOCUMENTATION: [],
            },
            "categorized_stats": {
                # At max 500 LOC limit
                FileCategory.APPLICATION: {"loc": 500, "added": 300, "deleted": 200},
                FileCategory.TEST: {"loc": 800, "added": 500, "deleted": 300},  # Within test limit
                FileCategory.CONFIG: {"loc": 0, "added": 0, "deleted": 0},
                FileCategory.DOCUMENTATION: {"loc": 0, "added": 0, "deleted": 0},
            },
        }

        result = check_limits(stats)

        assert result is True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_binary_files_handled(self):
        """Binary files should be treated as application code (not docs)."""
        assert categorize_file("image.png") == FileCategory.APPLICATION
        assert categorize_file("data.db") == FileCategory.APPLICATION
        assert categorize_file("archive.zip") == FileCategory.APPLICATION

    @patch("check_pr_loc.get_changed_files")
    @patch("check_pr_loc.get_file_diff_stats")
    def test_large_pr_with_only_docs(self, mock_diff, mock_files):
        """Large PR with only docs should fail due to total file limit."""
        # 50 markdown files (way over total file limit)
        mock_files.return_value = [f"doc{i}.md" for i in range(50)]
        mock_diff.return_value = (100, 50)  # Many changes per file

        stats = analyze_pr("main...HEAD")

        assert len(stats["categorized_files"][FileCategory.DOCUMENTATION]) == 50
        assert len(stats["categorized_files"][FileCategory.APPLICATION]) == 0
        # Docs don't count towards LOC
        assert stats["categorized_stats"][FileCategory.DOCUMENTATION]["loc"] == 0

        # Should FAIL because exceeds total file limit of 25
        assert check_limits(stats) is False

    @patch("check_pr_loc.get_changed_files")
    @patch("check_pr_loc.get_file_diff_stats")
    def test_reasonable_docs_pr_passes(self, mock_diff, mock_files):
        """PR with reasonable number of docs should pass."""
        # 20 markdown files (under total limit)
        mock_files.return_value = [f"doc{i}.md" for i in range(20)]
        mock_diff.return_value = (100, 50)  # Many changes per file

        stats = analyze_pr("main...HEAD")

        assert len(stats["categorized_files"][FileCategory.DOCUMENTATION]) == 20
        # Should pass because under total file limit
        assert check_limits(stats) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
