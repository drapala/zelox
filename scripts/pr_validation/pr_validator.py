#!/usr/bin/env python3
"""
---
title: PR Validator
purpose: Validate PR changes against configured limits
inputs:
  - name: stats
    type: dict
  - name: config
    type: dict
outputs:
  - name: validation_result
    type: tuple[bool, list]
effects: []
deps: []
owners: []
stability: stable
since_version: 1.0.0
---

PR validation logic with configurable thresholds.
Returns clear pass/fail status with violation details.
"""

from .file_categorizer import FileCategory


def check_category_limit(
    category: FileCategory, file_count: int, loc_count: int, limits: dict
) -> list[str]:
    """
    Check if category exceeds limits.

    Returns list of violations (empty if valid).
    """
    violations = []
    # Support configs keyed by either Enum or string values
    cat_limits = limits.get(category, limits.get(category.value, {}))

    # Check file count
    if cat_limits.get("files") and file_count > cat_limits["files"]:
        violations.append(
            f"{category.value.capitalize()} files ({file_count}) "
            f"exceed limit of {cat_limits['files']}"
        )

    # Check LOC count
    if cat_limits.get("loc") and loc_count > cat_limits["loc"]:
        violations.append(
            f"{category.value.capitalize()} LOC ({loc_count}) "
            f"exceeds limit of {cat_limits['loc']}"
        )

    return violations


def validate_pr(stats: dict, config: dict) -> tuple[bool, list[str]]:
    """
    Validate PR against configured limits.

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations = []

    # Check total files limit
    total_limit = config.get("total_files_limit")
    if total_limit and stats["total_files"] > total_limit:
        violations.append(
            f"Total files ({stats['total_files']}) " f"exceeds limit of {total_limit}"
        )

    # Check per-category limits
    category_limits = config.get("category_limits", {})
    for category in FileCategory:
        if category == FileCategory.DOCUMENTATION:
            continue  # Skip docs

        files = stats["categorized_files"].get(category, [])
        cat_stats = stats["categorized_stats"].get(category, {})

        if not files:
            continue

        cat_violations = check_category_limit(
            category, len(files), cat_stats.get("loc", 0), category_limits
        )
        violations.extend(cat_violations)

    return len(violations) == 0, violations


def get_category_status(category: FileCategory, stats: dict, limits: dict) -> str:
    """Get formatted status for a category."""
    files = stats["categorized_files"].get(category, [])
    cat_stats = stats["categorized_stats"].get(category, {})
    # Support configs keyed by either Enum or string values
    cat_limits = limits.get(category, limits.get(category.value, {}))

    if not files:
        return ""

    loc = cat_stats.get("loc", 0)
    loc_limit = cat_limits.get("loc", "∞")
    file_limit = cat_limits.get("files", "∞")

    return f"{category.value}: " f"{loc}/{loc_limit} LOC, " f"{len(files)}/{file_limit} files"
