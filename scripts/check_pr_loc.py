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

import sys
from pathlib import Path

import yaml

# Import validation modules
from pr_validation import (
    FileCategory,
    categorize_files,
    count_file_changes,
    generate_failure_report,
    generate_success_report,
    get_changed_files,
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


def analyze_pr(base_ref: str, config: dict) -> dict:
    """Analyze PR and return categorized statistics."""
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
            added, deleted = count_file_changes(filepath, base_ref)
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


def main():
    """Main entry point."""
    # Load configuration
    config = load_config()

    # Get base ref
    base_ref = get_base_ref(sys.argv)
    print(f"Checking PR against: {base_ref}")

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
