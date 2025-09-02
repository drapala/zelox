#!/usr/bin/env python3
"""
---
title: File Categorizer
purpose: Categorize files based on patterns
inputs:
  - name: filepath
    type: str
  - name: patterns
    type: dict
outputs:
  - name: category
    type: FileCategory
effects: []
deps: [re]
owners: []
stability: stable
since_version: 1.0.0
---

File categorization utility for PR validation.
"""

import re
from enum import Enum


class FileCategory(Enum):
    """File categories."""

    APPLICATION = "application"
    TEST = "test"
    CONFIG = "config"
    DOCUMENTATION = "documentation"


def compile_patterns(patterns: dict[str, list[str]]) -> dict[FileCategory, re.Pattern]:
    """Compile regex patterns for efficiency."""
    compiled = {}
    for category_name, pattern_list in patterns.items():
        if category_name in [c.value for c in FileCategory]:
            category = FileCategory(category_name)
            if pattern_list:
                pattern = "|".join(pattern_list)
                compiled[category] = re.compile(pattern, re.IGNORECASE)
    return compiled


def categorize_file(
    filepath: str, compiled_patterns: dict[FileCategory, re.Pattern]
) -> FileCategory:
    """
    Categorize a file based on patterns.

    Check order: TEST > CONFIG > DOCUMENTATION > APPLICATION
    """
    for category in [FileCategory.TEST, FileCategory.CONFIG, FileCategory.DOCUMENTATION]:
        if category in compiled_patterns:
            if compiled_patterns[category].search(filepath):
                return category

    # Default to APPLICATION
    return FileCategory.APPLICATION


def categorize_files(
    filepaths: list[str], patterns: dict[str, list[str]]
) -> dict[FileCategory, list[str]]:
    """Categorize multiple files."""
    compiled = compile_patterns(patterns)
    categorized = {category: [] for category in FileCategory}

    for filepath in filepaths:
        category = categorize_file(filepath, compiled)
        categorized[category].append(filepath)

    return categorized
