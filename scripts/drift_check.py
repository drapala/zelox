#!/usr/bin/env python3
"""
title: Drift Check - Controlled Duplication Monitor
purpose: Monitor controlled duplication with DUPLICATED_BLOCK tags
inputs: [{"name": "repo_root", "type": "path"}, {"name": "config_file", "type": "yaml"}]
outputs: [{"name": "drift_report", "type": "json"}, {"name": "exit_code", "type": "int"}]
effects: ["validation", "reporting"]
deps: ["pathlib", "re", "difflib", "yaml"]
owners: ["drapala"]
stability: stable
since_version: "0.3.0"
"""

import json
import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


@dataclass
class DuplicatedBlock:
    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    tolerance: str = "whitespace"


class DriftChecker:
    # Comment patterns for different languages
    BLOCK_PATTERNS = {
        "start": r"(?:#|//|<!--)\s*DUPLICATED_BLOCK:\s*(\w+)",
        "end": r"(?:#|//|<!--)\s*END_DUPLICATED_BLOCK:\s*(\w+)",
    }

    def __init__(self, repo_root: Path | None = None, config_file: Path | None = None):
        self.repo_root = repo_root or Path.cwd()
        self.blocks: dict[str, list[DuplicatedBlock]] = {}
        self.drift_tolerance = {
            "exact": 0.0,
            "whitespace": 0.95,
            "comments": 0.85,
            "minor": 0.75,
            "flexible": 0.50,
        }
        self._load_config(config_file)

    def scan_files(self) -> None:
        """Scan repository for DUPLICATED_BLOCK tags."""
        patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.yaml", "**/*.yml"]
        exclude = {"node_modules", "__pycache__", ".git"}

        for pattern in patterns:
            for file_path in self.repo_root.glob(pattern):
                if any(ex in str(file_path) for ex in exclude):
                    continue
                self._scan_file(file_path)

    def _scan_file(self, file_path: Path) -> None:
        """Extract DUPLICATED_BLOCK markers from a single file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            block_pattern = self.BLOCK_PATTERNS["start"]
            end_pattern = self.BLOCK_PATTERNS["end"]

            i = 0
            while i < len(lines):
                start_match = re.search(block_pattern, lines[i])
                if start_match:
                    block_id = start_match.group(1)
                    start_line = i + 1
                    block_content: list[str] = []

                    i += 1
                    while i < len(lines):
                        end_match = re.search(end_pattern, lines[i])
                        if end_match and end_match.group(1) == block_id:
                            end_line = i + 1
                            # Extract tolerance from block comments or use default
                            tolerance = self._extract_tolerance(lines, i) or "whitespace"
                            block = DuplicatedBlock(
                                id=block_id,
                                content="\n".join(block_content),
                                file_path=str(file_path.relative_to(self.repo_root)),
                                start_line=start_line,
                                end_line=end_line,
                                tolerance=tolerance,
                            )
                            self.blocks.setdefault(block_id, []).append(block)
                            break
                        block_content.append(lines[i])
                        i += 1
                i += 1

        except Exception as e:
            print(f"Error scanning {file_path}: {e}", file=sys.stderr)

    def check_drift(self) -> dict[str, Any]:
        """Check for drift between duplicated blocks."""
        report = {
            "summary": {
                "total_blocks": sum(len(blocks) for blocks in self.blocks.values()),
                "unique_ids": len(self.blocks),
                "drifted_blocks": 0,
                "healthy_blocks": 0,
            },
            "drifted_blocks": [],
        }

        for block_id, blocks in self.blocks.items():
            if len(blocks) < 2:
                continue

            drift_detected = False
            base_block = blocks[0]

            for other_block in blocks[1:]:
                similarity = self._calculate_similarity(base_block.content, other_block.content)
                threshold = self.drift_tolerance.get(base_block.tolerance, 0.95)

                if similarity < threshold:
                    drift_detected = True
                    report["drifted_blocks"].append(
                        {
                            "id": block_id,
                            "locations": [
                                f"{base_block.file_path}:{base_block.start_line}-{base_block.end_line}",
                                f"{other_block.file_path}:{other_block.start_line}-{other_block.end_line}",
                            ],
                            "similarity": similarity,
                            "threshold": threshold,
                            "recommendation": (
                                "consolidate_or_diverge" if similarity < 0.5 else "minor_sync"
                            ),
                        }
                    )

            if drift_detected:
                report["summary"]["drifted_blocks"] += 1
            else:
                report["summary"]["healthy_blocks"] += 1

        return report

    def _load_config(self, config_file: Path | None) -> None:
        """Load configuration from YAML file if provided."""
        if config_file and config_file.exists():
            try:
                import yaml

                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    if "drift_tolerance" in config:
                        self.drift_tolerance.update(config["drift_tolerance"])
            except Exception as e:
                print(f"Warning: Could not load config {config_file}: {e}", file=sys.stderr)

    def _extract_tolerance(self, lines: list[str], current_line: int) -> str | None:
        """Extract tolerance setting from block comments."""
        # Look for DRIFT_TOLERANCE comment in the block header area
        for i in range(max(0, current_line - 5), min(len(lines), current_line + 3)):
            line = lines[i].lower()
            if "drift_tolerance:" in line or "drift-tolerance:" in line:
                # Extract tolerance value (exact, whitespace, etc.)
                parts = line.split(":")
                if len(parts) > 1:
                    tolerance = parts[1].strip()
                    if tolerance in self.drift_tolerance:
                        return tolerance
        return None

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity ratio between two content blocks."""
        return SequenceMatcher(None, content1.strip(), content2.strip()).ratio()

    def run(self, report_only: bool = False) -> int:
        """Main execution method."""
        self.scan_files()
        report = self.check_drift()

        if report_only:
            print(json.dumps(report, indent=2))
            return 0

        drifted = report["summary"]["drifted_blocks"]
        total = report["summary"]["unique_ids"]

        if drifted == 0:
            print(f"✅ All {total} duplicated blocks maintain healthy synchronization")
            return 0
        else:
            print(f"❌ Found {drifted} drifted blocks out of {total} total")
            for drift in report["drifted_blocks"]:
                similarity = drift["similarity"]
                threshold = drift["threshold"]
                print(f"  - {drift['id']}: similarity {similarity:.2f} < {threshold}")
            return 2


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check for controlled duplication drift")
    parser.add_argument("--report", action="store_true", help="Generate detailed JSON report")
    parser.add_argument("--repo-root", type=Path, help="Repository root path")

    args = parser.parse_args()

    checker = DriftChecker(args.repo_root)
    exit_code = checker.run(report_only=args.report)
    sys.exit(exit_code)
