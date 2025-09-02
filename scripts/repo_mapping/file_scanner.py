#!/usr/bin/env python3
"""
title: File Scanner Component
purpose: Scan repository files with configurable filters and metadata extraction
stability: stable
since_version: "0.4.0"
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class FileScanner:
    """Efficiently scan repository files with caching and incremental updates."""

    DEFAULT_EXCLUDE_PATTERNS = {
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".venv",
        "venv",
        "node_modules",
        "*.pyc",
        "*.pyo",
        ".DS_Store",
    }

    def __init__(self, repo_root: Path, cache_dir: Path | None = None):
        """Initialize scanner with repository root and optional cache directory."""
        self.repo_root = repo_root.resolve()
        self.cache_dir = cache_dir or (repo_root / ".repo_cache")
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        self._file_cache = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        """Load file metadata cache for incremental updates."""
        cache_file = self.cache_dir / "file_scanner.json"
        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                return {}
        return {}

    def _save_cache(self):
        """Save file metadata cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / "file_scanner.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(self._file_cache, f, indent=2, default=str)

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded based on patterns."""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True
        return False

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def scan_directory(
        self, directory: Path, patterns: set[str] | None = None
    ) -> list[dict[str, Any]]:
        """Scan directory for files matching patterns."""
        if not directory.exists():
            return []

        results = []
        patterns = patterns or {"*.py", "*.md", "*.yaml", "*.yml"}

        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                if self._should_exclude(file_path):
                    continue

                file_info = self._get_file_info(file_path)
                if file_info:
                    results.append(file_info)

        self._save_cache()
        return results

    def _get_file_info(self, file_path: Path) -> dict[str, Any] | None:
        """Extract metadata from a single file with caching."""
        try:
            # Resolve both paths to handle symlinks and /private prefix on macOS
            file_path = file_path.resolve()
            stats = file_path.stat()
            path_str = str(file_path.relative_to(self.repo_root))

            # Check cache validity
            cached = self._file_cache.get(path_str, {})
            if cached.get("mtime") == stats.st_mtime:
                return cached["info"]

            # Extract fresh metadata
            info = {
                "path": path_str,
                "name": file_path.name,
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "extension": file_path.suffix,
                "hash": self._get_file_hash(file_path),
            }

            # Extract additional metadata based on file type
            if file_path.suffix == ".py":
                info.update(self._extract_python_metadata(file_path))

            # Update cache
            self._file_cache[path_str] = {
                "mtime": stats.st_mtime,
                "info": info,
            }

            return info

        except OSError:
            return None

    def _extract_python_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract Python-specific metadata."""
        metadata = {}
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Extract module docstring with frontmatter
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith('"""'):
                    docstring = self._extract_docstring(lines, i)
                    if docstring:
                        metadata["frontmatter"] = self._parse_frontmatter(docstring)
                    break

            # Count key metrics
            metadata["lines"] = len(lines)
            metadata["imports"] = len(re.findall(r"^\s*(import|from)\s+", content, re.MULTILINE))
            metadata["functions"] = len(re.findall(r"^\s*def\s+", content, re.MULTILINE))
            metadata["classes"] = len(re.findall(r"^\s*class\s+", content, re.MULTILINE))

        except (OSError, UnicodeDecodeError):
            pass

        return metadata

    def _extract_docstring(self, lines: list[str], start_idx: int) -> str:
        """Extract docstring from lines starting at index."""
        if '"""' in lines[start_idx] and lines[start_idx].count('"""') == 2:
            return lines[start_idx].strip()[3:-3]

        docstring_lines = []
        for i in range(start_idx + 1, len(lines)):
            if '"""' in lines[i]:
                return "\n".join(docstring_lines).strip()
            docstring_lines.append(lines[i])

        return ""

    def _parse_frontmatter(self, docstring: str) -> dict[str, Any]:
        """Parse YAML-like frontmatter from docstring."""
        frontmatter = {}
        for line in docstring.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key in ["title", "purpose", "stability", "since_version"]:
                    frontmatter[key] = value
        return frontmatter

    def get_changed_files(self, since: datetime | None = None) -> list[Path]:
        """Get files changed since a given timestamp."""
        changed = []
        since_timestamp = since.timestamp() if since else 0

        for file_path in self.repo_root.rglob("*"):
            if file_path.is_file() and not self._should_exclude(file_path):
                if file_path.stat().st_mtime > since_timestamp:
                    # Resolve path to handle symlinks consistently
                    changed.append(file_path.resolve())

        return changed
