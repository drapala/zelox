#!/usr/bin/env python3
"""
title: Repository Map Builder
purpose: Fluent interface for building repository maps with composable operations
stability: stable
since_version: "0.4.0"
"""

from pathlib import Path
from typing import Any

from .file_scanner import FileScanner
from .map_builder import MapBuilder
from .map_formatter import MapFormatter
from .map_writer import MapWriter


class RepoMapBuilder:
    """Fluent interface for building repository maps."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize builder with repository root."""
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.file_scanner = FileScanner(self.repo_root)
        self.map_builder = MapBuilder(self.repo_root)
        self.patterns: set[str] = {"*.py", "*.md", "*.yaml", "*.yml"}
        self.directories: list[Path] = []
        self.incremental = False
        self.since = None
        self._scanned_files = []

    def scan(self, path: Path | None = None) -> "RepoMapBuilder":
        """Scan a directory or entire repository."""
        scan_path = path or self.repo_root
        self.directories.append(scan_path)
        return self

    def filter(self, patterns: set[str]) -> "RepoMapBuilder":
        """Set file patterns to include in scan."""
        self.patterns = patterns
        return self

    def exclude(self, patterns: set[str]) -> "RepoMapBuilder":
        """Add patterns to exclude from scan."""
        self.file_scanner.exclude_patterns.update(patterns)
        return self

    def incremental_since(self, since) -> "RepoMapBuilder":
        """Enable incremental update mode."""
        self.incremental = True
        self.since = since
        return self

    def build(self) -> "RepoMapBuilder":
        """Execute scan and build repository structure."""
        # Default to repo root if no directories specified
        if not self.directories:
            self.directories = [self.repo_root]

        # Scan all specified directories
        for directory in self.directories:
            if self.incremental and self.since:
                # Get only changed files
                changed_files = self.file_scanner.get_changed_files(self.since)
                for file_path in changed_files:
                    if self._matches_patterns(file_path):
                        file_info = self.file_scanner._get_file_info(file_path)
                        if file_info:
                            self._scanned_files.append(file_info)
                            self.map_builder.add_file(file_info)
            else:
                # Full scan
                scanned = self.file_scanner.scan_directory(directory, self.patterns)
                self._scanned_files.extend(scanned)
                for file_info in scanned:
                    self.map_builder.add_file(file_info)

        return self

    def _matches_patterns(self, file_path: Path) -> bool:
        """Check if file matches any of the configured patterns."""
        for pattern in self.patterns:
            if pattern.startswith("*."):
                if file_path.suffix == pattern[1:]:
                    return True
            elif file_path.match(pattern):
                return True
        return False

    def format(self, style: str = "markdown") -> str:
        """Format the built map in specified style."""
        structure = self.map_builder.build()
        formatter = MapFormatter(structure)

        if style == "markdown":
            return formatter.format_markdown()
        elif style == "json":
            import json

            return json.dumps(formatter.format_json(), indent=2)
        elif style == "yaml":
            return formatter.format_yaml()
        else:
            raise ValueError(f"Unknown format style: {style}")

    def write(self, output: Path | None = None, style: str = "markdown") -> Path:
        """Write the formatted map to file."""
        output_dir = output or self.repo_root / "docs" / "repo"
        if output_dir.is_file():
            output_dir = output_dir.parent

        writer = MapWriter(output_dir)
        content = self.format(style)

        # Determine filename based on style
        filenames = {
            "markdown": "REPO_MAP.md",
            "json": "repo_map.json",
            "yaml": "repo_map.yaml",
        }
        filename = filenames.get(style, "repo_map.txt")

        # Write based on format
        if style == "markdown":
            return writer.write(content, filename)
        elif style == "json":
            structure = self.map_builder.build()
            formatter = MapFormatter(structure)
            return writer.write_json(formatter.format_json(), filename)
        elif style == "yaml":
            return writer.write_yaml(content, filename)
        else:
            return writer.write(content, filename)

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the scanned repository."""
        stats = self.map_builder.get_statistics()
        stats["files_scanned"] = len(self._scanned_files)
        stats["incremental"] = self.incremental
        return stats

    def reset(self) -> "RepoMapBuilder":
        """Reset builder to initial state."""
        self.map_builder = MapBuilder(self.repo_root)
        self.directories = []
        self._scanned_files = []
        return self
