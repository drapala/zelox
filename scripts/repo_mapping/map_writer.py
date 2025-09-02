#!/usr/bin/env python3
"""
title: Map Writer Component
purpose: Write repository maps to various outputs with versioning
stability: stable
since_version: "0.4.0"
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class MapWriter:
    """Write repository maps with versioning and backup support."""

    def __init__(self, output_dir: Path, enable_versioning: bool = True):
        """Initialize writer with output directory."""
        self.output_dir = output_dir.resolve()
        self.enable_versioning = enable_versioning
        self.versions_dir = output_dir / ".versions"

    def write(self, content: str, filename: str = "REPO_MAP.md", backup: bool = True) -> Path:
        """Write content to file with optional backup."""
        output_path = self.output_dir / filename

        # Create backup if file exists
        if backup and output_path.exists():
            self._create_backup(output_path)

        # Ensure directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write new content
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Version the file if enabled
        if self.enable_versioning:
            self._version_file(output_path, content)

        return output_path

    def write_json(
        self, data: dict[str, Any], filename: str = "repo_map.json", backup: bool = True
    ) -> Path:
        """Write JSON data to file."""
        output_path = self.output_dir / filename

        if backup and output_path.exists():
            self._create_backup(output_path)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        if self.enable_versioning:
            self._version_file(output_path, json.dumps(data, indent=2, default=str))

        return output_path

    def write_yaml(
        self, content: str, filename: str = "repo_map.yaml", backup: bool = True
    ) -> Path:
        """Write YAML content to file."""
        output_path = self.output_dir / filename

        if backup and output_path.exists():
            self._create_backup(output_path)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        if self.enable_versioning:
            self._version_file(output_path, content)

        return output_path

    def _create_backup(self, file_path: Path):
        """Create backup of existing file."""
        backup_dir = self.output_dir / ".backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name

        shutil.copy2(file_path, backup_path)

    def _version_file(self, file_path: Path, content: str):
        """Create versioned copy of file."""
        if not self.enable_versioning:
            return

        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # Create version metadata
        version_data = {
            "timestamp": datetime.now().isoformat(),
            "file": file_path.name,
            "size": len(content),
            "lines": content.count("\n") + 1,
        }

        # Save versioned content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_name = f"{file_path.stem}_v{timestamp}{file_path.suffix}"
        version_path = self.versions_dir / version_name

        with open(version_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Update version manifest
        manifest_path = self.versions_dir / "manifest.json"
        manifest = self._load_manifest()
        manifest["versions"].append(
            {
                **version_data,
                "path": str(version_path.relative_to(self.versions_dir)),
            }
        )
        self._save_manifest(manifest)

    def _load_manifest(self) -> dict[str, Any]:
        """Load version manifest."""
        manifest_path = self.versions_dir / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
        return {"versions": []}

    def _save_manifest(self, manifest: dict[str, Any]):
        """Save version manifest."""
        manifest_path = self.versions_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)

    def get_versions(self, filename: str) -> list[dict[str, Any]]:
        """Get version history for a file."""
        manifest = self._load_manifest()
        return [v for v in manifest.get("versions", []) if v.get("file") == filename]

    def restore_version(self, version_path: str, target_filename: str) -> Path:
        """Restore a specific version of a file."""
        version_file = self.versions_dir / version_path
        if not version_file.exists():
            raise FileNotFoundError(f"Version not found: {version_path}")

        target_path = self.output_dir / target_filename

        # Backup current version
        if target_path.exists():
            self._create_backup(target_path)

        # Restore version
        shutil.copy2(version_file, target_path)
        return target_path
