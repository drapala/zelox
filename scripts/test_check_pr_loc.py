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
from unittest.mock import patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from check_pr_loc import (
    HARD_FILES_LIMIT,
    HARD_LOC_LIMIT,
    analyze_pr,
    check_limits,
    get_changed_files,
    get_file_diff_stats,
    is_documentation_only,
    run_git_command,
)


class TestDocumentationDetection:
    """Test documentation file detection logic."""

    def test_markdown_files_are_documentation(self):
        """Markdown files should be detected as documentation."""
        assert is_documentation_only("README.md") is True
        assert is_documentation_only("docs/guide.md") is True
        assert is_documentation_only("CHANGELOG.MD") is True  # Case insensitive

    def test_license_files_are_documentation(self):
        """License and notice files should be documentation."""
        assert is_documentation_only("LICENSE") is True
        assert is_documentation_only("NOTICE") is True
        assert is_documentation_only("AUTHORS") is True
        assert is_documentation_only("CONTRIBUTORS.txt") is True

    def test_code_files_are_not_documentation(self):
        """Code files should NOT be detected as documentation."""
        assert is_documentation_only("main.py") is False
        assert is_documentation_only("script.js") is False
        assert is_documentation_only("style.css") is False
        assert is_documentation_only("config.yaml") is False
        assert is_documentation_only("package.json") is False

    def test_path_with_directories(self):
        """Should work with full paths."""
        assert is_documentation_only("docs/adr/001-decision.md") is True
        assert is_documentation_only("src/components/README.md") is True
        assert is_documentation_only("src/main.py") is False


class TestGitCommands:
    """Test git command execution."""

    @patch("check_pr_loc.subprocess.check_output")
    def test_run_git_command_success(self, mock_subprocess):
        """Test successful git command execution."""
        mock_subprocess.return_value = "file1.py\nfile2.js\n"

        result = run_git_command("diff", "--name-only", "HEAD")

        assert result == "file1.py\nfile2.js"
        mock_subprocess.assert_called_once_with(
            ["git", "diff", "--name-only", "HEAD"], text=True, stderr=pytest.ANY
        )

    @patch("check_pr_loc.subprocess.check_output")
    def test_run_git_command_failure(self, mock_subprocess):
        """Test git command failure handling."""
        mock_subprocess.side_effect = Exception("Git error")

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
    def test_analyze_pr_separates_code_and_docs(self, mock_diff, mock_files):
        """Test PR analysis separates code from documentation."""
        mock_files.return_value = [
            "main.py",
            "README.md",
            "src/utils.js",
            "docs/guide.md",
            "LICENSE",
        ]
        mock_diff.return_value = (10, 5)  # 10 added, 5 deleted for each

        stats = analyze_pr("main...HEAD")

        assert stats["total_files"] == 5
        assert stats["code_files_count"] == 2  # main.py, src/utils.js
        assert stats["doc_files_count"] == 3  # README.md, docs/guide.md, LICENSE
        assert stats["lines_added"] == 20  # 2 code files * 10 lines
        assert stats["lines_deleted"] == 10  # 2 code files * 5 lines
        assert stats["effective_loc"] == 30  # 20 + 10
        assert "main.py" in stats["code_files"]
        assert "README.md" in stats["doc_files"]

    @patch("check_pr_loc.get_changed_files")
    def test_analyze_pr_empty(self, mock_files):
        """Test analyzing empty PR."""
        mock_files.return_value = []

        stats = analyze_pr("main...HEAD")

        assert stats["total_files"] == 0
        assert stats["code_files_count"] == 0
        assert stats["doc_files_count"] == 0
        assert stats["effective_loc"] == 0


class TestLimitChecking:
    """Test PR size limit checking."""

    def test_check_limits_within_bounds(self):
        """Test PR within limits passes."""
        stats = {"code_files_count": 5, "effective_loc": 300}

        result = check_limits(stats)

        assert result is True

    def test_check_limits_too_many_files(self):
        """Test PR with too many files fails."""
        stats = {
            "code_files_count": 15,  # Over limit of 10
            "effective_loc": 100,
        }

        result = check_limits(stats)

        assert result is False

    def test_check_limits_too_many_lines(self):
        """Test PR with too many lines fails."""
        stats = {
            "code_files_count": 5,
            "effective_loc": 600,  # Over limit of 500
        }

        result = check_limits(stats)

        assert result is False

    def test_check_limits_both_exceeded(self):
        """Test PR exceeding both limits fails."""
        stats = {"code_files_count": 20, "effective_loc": 1000}

        result = check_limits(stats)

        assert result is False

    def test_check_limits_at_maximum(self):
        """Test PR exactly at limits passes."""
        stats = {"code_files_count": HARD_FILES_LIMIT, "effective_loc": HARD_LOC_LIMIT}

        result = check_limits(stats)

        assert result is True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_binary_files_handled(self):
        """Binary files should be treated as code (not docs)."""
        assert is_documentation_only("image.png") is False
        assert is_documentation_only("data.db") is False
        assert is_documentation_only("archive.zip") is False

    @patch("check_pr_loc.get_changed_files")
    @patch("check_pr_loc.get_file_diff_stats")
    def test_large_pr_with_only_docs(self, mock_diff, mock_files):
        """Large PR with only docs should pass."""
        # 50 markdown files (way over file limit)
        mock_files.return_value = [f"doc{i}.md" for i in range(50)]
        mock_diff.return_value = (100, 50)  # Many changes per file

        stats = analyze_pr("main...HEAD")

        assert stats["code_files_count"] == 0  # No code files
        assert stats["doc_files_count"] == 50
        assert stats["effective_loc"] == 0  # Docs don't count

        # Should pass because no code files
        assert check_limits(stats) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
