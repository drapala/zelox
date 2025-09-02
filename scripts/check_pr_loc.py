#!/usr/bin/env python3
"""
---
title: PR LOC Gate Script
purpose: Enforce categorized size limits on PRs
inputs:
  - name: base_ref
    type: str
outputs:
  - name: exit_code
    type: int
effects: [stdout, exit_code]
deps: [pr_validation, yaml, sys]
owners: []
stability: stable
since_version: 2.0.0
---

Simplified PR LOC validation using modular components.
Per ADR-003 and ADR-006: Incentivizes comprehensive testing.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

# Import validation modules
from pr_validation import (
    FileCategory,
    categorize_files,
    compile_patterns,
    generate_failure_report,
    generate_success_report,
    get_effective_loc,
    print_analysis,
    validate_pr,
)


def load_config() -> dict:
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent / "pr_validation" / "config.yaml"

    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)

    # Fallback to default config
    return {
        "total_files_limit": 25,
        "override_labels": [
            "override: pr-loc-exempt",
            "override: size-exempt",
            "override/size-exempt",
        ],
        "category_limits": {
            FileCategory.APPLICATION: {"loc": 500, "files": 10},
            FileCategory.TEST: {"loc": 1000, "files": 20},
            FileCategory.CONFIG: {"loc": 250, "files": 5},
            FileCategory.DOCUMENTATION: {"loc": None, "files": None},
        },
        "category_patterns": {
            "test": [
                r"(^|/)test_[^/]*\.py$",
                r"^scripts/test_[^/]*\.py$",
                r"(^|/)[^/]*_test\.py$",
                r"\.test\.[tj]sx?$",
                r"\.spec\.[tj]sx?$",
                r"^tests?/",
            ],
            "config": [
                r"^\.github/.*\.(yml|yaml)$",
                r"^schemas/.*\.json$",
                r"^\..*rc(\..*)?$",
                r"(Makefile|makefile)$",
                r"Dockerfile$",
                r"docker-compose.*\.(yml|yaml)$",
            ],
            "documentation": [
                r"\.md$",
                r"\.mdx$",
                r"\.rst$",
                r"\.adoc$",
                r"\.txt$",
                r"(^|/)(LICENSE|NOTICE|AUTHORS|CONTRIBUTORS|CHANGELOG|CHANGES|HISTORY|NEWS|README|TODO)(\.[a-z]+)?$",
            ],
        },
    }


# Backward-compatibility constants and helpers for existing tests
# Expose TOTAL_FILES_LIMIT expected by tests without changing modular design
TOTAL_FILES_LIMIT = load_config().get("total_files_limit", 25)


def get_file_diff_stats(filepath: str, base_ref: str) -> tuple[int, int]:
    """Return added, deleted lines for a file (patchable via local git runner)."""
    try:
        diff = run_git_command("diff", "--unified=0", base_ref, "--", filepath)
        if not diff:
            return 0, 0
        lines = diff.splitlines()
        added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        deleted = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
        return added, deleted
    except Exception:
        return 0, 0


def check_limits(stats: dict) -> bool:
    """Compatibility wrapper: validate stats against config limits.

    Returns True when within limits, False otherwise.
    """
    config = load_config()
    is_valid, _ = validate_pr(stats, config)
    return is_valid


# Expose run_git_command to satisfy existing tests' patch targets
def run_git_command(*args: str) -> str:
    """Execute git command and return output (patchable in tests)."""
    try:
        result = subprocess.check_output(["git"] + list(args), text=True, stderr=subprocess.DEVNULL)
        return result.strip()
    except subprocess.CalledProcessError:
        return ""


def get_changed_files(base_ref: str = "origin/main...HEAD") -> list[str]:
    """Get list of changed files using local git runner (patchable)."""
    output = run_git_command("diff", "--name-only", base_ref)
    return [f for f in output.splitlines() if f.strip()]


def categorize_file(filepath: str) -> FileCategory:
    """Categorize a file using configured patterns (single-arg wrapper)."""
    patterns = load_config().get("category_patterns", {})
    compiled = compile_patterns(patterns)
    from pr_validation.file_categorizer import categorize_file as _categorize_file

    return _categorize_file(filepath, compiled)


def analyze_pr(base_ref: str, config: dict | None = None) -> dict:
    """Analyze PR and return categorized statistics."""
    if config is None:
        config = load_config()
    # Get changed files
    all_files = get_changed_files(base_ref)

    # Categorize files
    patterns = config.get("category_patterns", {})
    categorized_files = categorize_files(all_files, patterns)

    # Calculate stats
    categorized_stats = {
        category: {"added": 0, "deleted": 0, "loc": 0} for category in FileCategory
    }

    for category, files in categorized_files.items():
        if category == FileCategory.DOCUMENTATION:
            continue  # Skip docs

        for filepath in files:
            added, deleted = get_file_diff_stats(filepath, base_ref)
            categorized_stats[category]["added"] += added
            categorized_stats[category]["deleted"] += deleted
            categorized_stats[category]["loc"] += get_effective_loc(added, deleted)

    return {
        "total_files": len(all_files),
        "categorized_files": categorized_files,
        "categorized_stats": categorized_stats,
    }


def get_base_ref(args: list) -> str:
    """Determine base ref from arguments."""
    if len(args) > 1:
        base_ref = args[1]
        if base_ref == "auto":
            # Auto-detect base branch
            import subprocess

            try:
                subprocess.check_call(
                    ["git", "rev-parse", "origin/main"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return "origin/main...HEAD"
            except subprocess.CalledProcessError:
                return "HEAD~1...HEAD"
        return base_ref
    return "origin/main...HEAD"


def get_pr_labels_from_event() -> list[str]:
    """Extract PR labels from GitHub Actions event payload, if available."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return []
    try:
        with open(event_path, encoding="utf-8") as f:
            payload = json.load(f)
        pr = payload.get("pull_request") or {}
        labels = pr.get("labels") or []
        return [lbl.get("name", "") for lbl in labels if isinstance(lbl, dict)]
    except Exception:
        return []


def main():
    """Main entry point."""
    # Load configuration
    config = load_config()

    # Get base ref
    base_ref = get_base_ref(sys.argv)
    print(f"Checking PR against: {base_ref}")

    # Respect override labels if present in the PR (GitHub Actions)
    labels = set(get_pr_labels_from_event())
    override_labels = set(config.get("override_labels", []))
    if labels & override_labels:
        print("PR LOC check: override label present; skipping size enforcement.")
        sys.exit(0)

    # Analyze PR
    stats = analyze_pr(base_ref, config)

    # Print analysis
    print_analysis(stats)

    # Validate PR
    is_valid, violations = validate_pr(stats, config)

    # Generate report
    if is_valid:
        print(generate_success_report(stats, config))
        sys.exit(0)
    else:
        print(generate_failure_report(stats, violations, config))
        sys.exit(1)


if __name__ == "__main__":
    main()
