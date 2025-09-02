#!/usr/bin/env python3
"""
---
title: Domain Mapper
purpose: Map and aggregate domain information across repository
inputs:
  - name: repo_root
    type: Path
outputs:
  - name: file_domains
    type: dict[str, dict]
  - name: feature_domains
    type: dict[str, dict]
effects: ["file_system_read"]
deps: ["pathlib", "collections", "sys"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
---
"""

import sys
from collections import Counter
from pathlib import Path
from typing import Any

from domain_models import extract_domain_language, extract_feature_name


class BoundedContextAnalyzer:
    """Analyze bounded contexts and suggest VSA improvements."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.file_domains: dict[str, dict[str, Any]] = {}
        self.feature_domains: dict[str, dict[str, Any]] = {}

    def extract_all_domain_language(self) -> None:
        """Extract domain language from all Python files."""
        python_files = list(self.repo_root.rglob("*.py"))

        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                domain_data = extract_domain_language(py_file)
                rel_path = str(py_file.relative_to(self.repo_root))

                self.file_domains[rel_path] = {
                    "domain_terms": domain_data["domain_terms"],
                    "classes": domain_data["classes"],
                    "methods": domain_data["methods"],
                    "feature": extract_feature_name(rel_path),
                }

            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}", file=sys.stderr)

    def aggregate_feature_domains(self) -> None:
        """Aggregate domain terms by feature."""
        for file_path, domain_data in self.file_domains.items():
            feature = domain_data["feature"]
            if not feature:
                continue

            if feature not in self.feature_domains:
                self.feature_domains[feature] = {
                    "domain_terms": Counter(),
                    "classes": set(),
                    "files": [],
                }

            self.feature_domains[feature]["domain_terms"].update(domain_data["domain_terms"])
            self.feature_domains[feature]["classes"].update(domain_data["classes"])
            self.feature_domains[feature]["files"].append(file_path)

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        name = file_path.name
        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or "__pycache__" in str(file_path)
            or name.startswith(".")
        )

    def get_file_domains(self) -> dict[str, dict[str, Any]]:
        """Get file-level domain information."""
        return self.file_domains

    def get_feature_domains(self) -> dict[str, dict[str, Any]]:
        """Get feature-level domain information."""
        return self.feature_domains


def map_domain_boundaries(repo_root: str = ".") -> dict[str, Any]:
    """Map domain boundaries across the repository."""
    analyzer = BoundedContextAnalyzer(repo_root)

    analyzer.extract_all_domain_language()
    analyzer.aggregate_feature_domains()

    return {
        "file_domains": analyzer.get_file_domains(),
        "feature_domains": analyzer.get_feature_domains(),
        "files_analyzed": len(analyzer.get_file_domains()),
    }
