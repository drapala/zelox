#!/usr/bin/env python3
"""
---
title: LOC Counter
purpose: Count lines of code in PR changes
inputs:
  - name: filepath
    type: str
  - name: base_ref
    type: str
outputs:
  - name: line_counts
    type: tuple[int, int]
effects: []
deps: [subprocess]
owners: []
stability: stable
since_version: 1.0.0
---

Line counting utility for PR validation.
Provides simple, focused line counting functionality.
"""

import subprocess


def run_git_command(*args: str) -> str:
    """Execute git command and return output."""
    try:
        result = subprocess.check_output(["git"] + list(args), text=True, stderr=subprocess.DEVNULL)
        return result.strip()
    except subprocess.CalledProcessError:
        return ""


def get_changed_files(base_ref: str = "origin/main...HEAD") -> list[str]:
    """Get list of changed files in PR."""
    output = run_git_command("diff", "--name-only", base_ref)
    return [f for f in output.splitlines() if f.strip()]


def count_file_changes(filepath: str, base_ref: str = "origin/main...HEAD") -> tuple[int, int]:
    """
    Count added and deleted lines for a file.

    Returns:
        Tuple of (added_lines, deleted_lines)
    """
    try:
        # Get unified diff with no context
        diff = run_git_command("diff", "--unified=0", base_ref, "--", filepath)

        if not diff:
            return 0, 0

        lines = diff.splitlines()
        added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        deleted = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))

        return added, deleted
    except Exception:
        return 0, 0


def get_effective_loc(added: int, deleted: int) -> int:
    """Calculate effective LOC (added + deleted)."""
    return added + deleted
