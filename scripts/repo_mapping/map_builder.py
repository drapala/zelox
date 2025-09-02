#!/usr/bin/env python3
"""
title: Map Builder Component
purpose: Build structured repository map from scanned files
stability: stable
since_version: "0.4.0"
"""

from pathlib import Path
from typing import Any


class MapBuilder:
    """Build hierarchical repository structure map."""

    def __init__(self, repo_root: Path):
        """Initialize builder with repository root."""
        self.repo_root = repo_root.resolve()
        self.structure = {
            "features": [],
            "scripts": [],
            "docs": {"adrs": [], "repo": []},
            "shared": [],
            "tests": [],
        }

    def add_file(self, file_info: dict[str, Any]) -> "MapBuilder":
        """Add a file to the repository map."""
        path = Path(file_info["path"])
        parts = path.parts

        if not parts:
            return self

        # Categorize by top-level directory
        top_dir = parts[0]

        if top_dir == "features" and len(parts) >= 2:
            self._add_feature_file(parts[1], file_info)
        elif top_dir == "scripts":
            self._add_script_file(file_info)
        elif top_dir == "docs":
            self._add_doc_file(parts, file_info)
        elif top_dir == "shared":
            self._add_shared_file(file_info)
        elif "test" in file_info["name"].lower():
            self._add_test_file(file_info)

        return self

    def _add_feature_file(self, feature_name: str, file_info: dict[str, Any]):
        """Add file to a feature slice."""
        # Find or create feature entry
        feature = next((f for f in self.structure["features"] if f["name"] == feature_name), None)

        if not feature:
            feature = {
                "name": feature_name,
                "files": [],
                "capabilities": set(),
                "metrics": {"loc": 0, "tests": 0, "apis": 0},
            }
            self.structure["features"].append(feature)

        # Add file to feature
        feature["files"].append(
            {
                "name": file_info["name"],
                "purpose": file_info.get("frontmatter", {}).get("purpose", ""),
                "lines": file_info.get("lines", 0),
            }
        )

        # Update capabilities
        if file_info["name"] == "tests.py":
            feature["capabilities"].add("tests")
            feature["metrics"]["tests"] += 1
        elif file_info["name"] == "api.py":
            feature["capabilities"].add("api")
            feature["metrics"]["apis"] += 1
        elif file_info["name"] == "service.py":
            feature["capabilities"].add("business_logic")

        # Update metrics
        feature["metrics"]["loc"] += file_info.get("lines", 0)

    def _add_script_file(self, file_info: dict[str, Any]):
        """Add file to scripts section."""
        if not file_info["name"].startswith("test_"):
            self.structure["scripts"].append(
                {
                    "name": file_info["name"],
                    "purpose": file_info.get("frontmatter", {}).get("purpose", "Utility script"),
                    "lines": file_info.get("lines", 0),
                }
            )

    def _add_doc_file(self, parts: tuple[str, ...], file_info: dict[str, Any]):
        """Add file to documentation section."""
        if len(parts) < 2:
            return

        sub_dir = parts[1]
        if sub_dir == "adr":
            self._add_adr_file(file_info)
        elif sub_dir == "repo":
            self.structure["docs"]["repo"].append(
                {
                    "name": file_info["name"],
                    "path": file_info["path"],
                }
            )

    def _add_adr_file(self, file_info: dict[str, Any]):
        """Add Architecture Decision Record."""
        import re

        # Extract ADR number from filename
        match = re.search(r"(\d+)", Path(file_info["name"]).stem)
        number = match.group(1) if match else ""

        # Clean title from filename
        stem = Path(file_info["name"]).stem
        if match:
            title_part = stem[match.end() :].lstrip("-_")
        else:
            title_part = stem

        title = title_part.replace("-", " ").replace("_", " ").strip().title()

        self.structure["docs"]["adrs"].append(
            {
                "number": number,
                "title": title,
                "path": file_info["path"],
                "status": "accepted",  # Could be parsed from content
            }
        )

    def _add_shared_file(self, file_info: dict[str, Any]):
        """Add file to shared utilities."""
        self.structure["shared"].append(
            {
                "name": file_info["name"],
                "purpose": file_info.get("frontmatter", {}).get("purpose", "Shared utility"),
                "lines": file_info.get("lines", 0),
            }
        )

    def _add_test_file(self, file_info: dict[str, Any]):
        """Add test file to tests section."""
        self.structure["tests"].append(
            {
                "name": file_info["name"],
                "path": file_info["path"],
                "lines": file_info.get("lines", 0),
            }
        )

    def build(self) -> dict[str, Any]:
        """Build and return the complete repository map."""
        # Convert sets to lists for JSON serialization
        for feature in self.structure["features"]:
            feature["capabilities"] = list(feature["capabilities"])

        # Sort sections for consistency
        self.structure["features"].sort(key=lambda x: x["name"])
        self.structure["scripts"].sort(key=lambda x: x["name"])
        self.structure["docs"]["adrs"].sort(key=lambda x: x.get("number", ""))

        return self.structure

    def get_statistics(self) -> dict[str, Any]:
        """Calculate repository statistics."""
        stats = {
            "total_features": len(self.structure["features"]),
            "total_scripts": len(self.structure["scripts"]),
            "total_adrs": len(self.structure["docs"]["adrs"]),
            "total_loc": 0,
            "features_with_tests": 0,
            "features_with_apis": 0,
        }

        for feature in self.structure["features"]:
            stats["total_loc"] += feature["metrics"]["loc"]
            if "tests" in feature.get("capabilities", []):
                stats["features_with_tests"] += 1
            if "api" in feature.get("capabilities", []):
                stats["features_with_apis"] += 1

        return stats
