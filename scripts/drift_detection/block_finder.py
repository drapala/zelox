"""
title: Block Finder
purpose: Find and extract DUPLICATED_BLOCK markers from files
inputs: [{"name": "file_paths", "type": "list[Path]"}]
outputs: [{"name": "blocks", "type": "dict[str, list[Block]]"}]
effects: ["file_scanning"]
deps: ["pathlib", "re"]
owners: ["drapala"]
stability: stable
since_version: "0.4.0"
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Block:
    """A duplicated block with metadata."""

    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    tolerance: str = "whitespace"

    @property
    def content_hash(self) -> int:
        """Quick hash for initial comparison."""
        return hash(self.content)


class BlockFinder:
    """Find duplicate blocks in source files."""

    # Language-agnostic patterns
    START_PATTERN = re.compile(r"(?:#|//|<!--)\s*DUPLICATED_BLOCK:\s*(\w+)")
    END_PATTERN = re.compile(r"(?:#|//|<!--)\s*END_DUPLICATED_BLOCK:\s*(\w+)")
    TOLERANCE_PATTERN = re.compile(r"(?:#|//|<!--)\s*DRIFT_TOLERANCE:\s*(\w+)")

    SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml"}
    EXCLUDE_DIRS = {"node_modules", "__pycache__", ".git", "dist", "build"}

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.blocks: dict[str, list[Block]] = {}

    def find_all(self) -> dict[str, list[Block]]:
        """Find all duplicate blocks in repository."""
        for file_path in self._get_source_files():
            self._scan_file(file_path)
        return self.blocks

    def _get_source_files(self) -> list[Path]:
        """Get all source files to scan."""
        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            pattern = f"**/*{ext}"
            for path in self.repo_root.glob(pattern):
                if not any(ex in str(path) for ex in self.EXCLUDE_DIRS):
                    files.append(path)
        return files

    def _scan_file(self, file_path: Path) -> None:
        """Scan single file for blocks."""
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            self._extract_blocks(lines, file_path)
        except (OSError, UnicodeDecodeError):
            pass  # Skip unreadable files

    def _extract_blocks(self, lines: list[str], file_path: Path) -> None:
        """Extract blocks from lines."""
        i = 0
        while i < len(lines):
            match = self.START_PATTERN.search(lines[i])
            if match:
                block = self._extract_single_block(lines, i, match.group(1), file_path)
                if block:
                    self.blocks.setdefault(block.id, []).append(block)
                    i = block.end_line  # Skip to end of block
                else:
                    i += 1
            else:
                i += 1

    def _extract_single_block(
        self, lines: list[str], start_idx: int, block_id: str, file_path: Path
    ) -> Block | None:
        """Extract a single block starting at the given index."""
        content_lines = []
        tolerance = "whitespace"

        # Check for tolerance in nearby lines
        for j in range(max(0, start_idx - 2), min(len(lines), start_idx + 3)):
            tol_match = self.TOLERANCE_PATTERN.search(lines[j])
            if tol_match:
                tolerance = tol_match.group(1)
                break

        # Find end marker
        for end_idx in range(start_idx + 1, len(lines)):
            end_match = self.END_PATTERN.search(lines[end_idx])
            if end_match and end_match.group(1) == block_id:
                content = "\n".join(content_lines)
                return Block(
                    id=block_id,
                    content=content,
                    file_path=str(file_path.relative_to(self.repo_root)),
                    start_line=start_idx + 1,
                    end_line=end_idx + 1,
                    tolerance=tolerance,
                )
            content_lines.append(lines[end_idx])

        return None  # No matching end marker
