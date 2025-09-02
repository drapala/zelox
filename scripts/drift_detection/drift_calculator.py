"""
title: Drift Calculator
purpose: Calculate drift between duplicate blocks
inputs: [{"name": "blocks", "type": "dict[str, list[Block]]"}]
outputs: [{"name": "drift_results", "type": "list[DriftResult]"}]
effects: ["computation"]
deps: ["difflib", "hashlib"]
owners: ["drapala"]
stability: stable
since_version: "0.4.0"
"""

from dataclasses import dataclass
from difflib import SequenceMatcher

from .block_finder import Block


@dataclass(frozen=True)
class DriftResult:
    """Result of drift calculation between blocks."""

    block_id: str
    base_location: str
    compared_location: str
    similarity: float
    threshold: float
    is_drifted: bool
    recommendation: str


class DriftCalculator:
    """Calculate drift between duplicate blocks."""

    # Tolerance thresholds
    TOLERANCE_THRESHOLDS = {
        "exact": 1.0,
        "whitespace": 0.95,
        "comments": 0.85,
        "minor": 0.75,
        "flexible": 0.50,
    }

    def __init__(self):
        self._cache: dict[tuple[int, int], float] = {}

    def calculate_all(self, blocks: dict[str, list[Block]]) -> list[DriftResult]:
        """Calculate drift for all block groups."""
        results = []
        for block_id, block_list in blocks.items():
            if len(block_list) >= 2:
                results.extend(self._calculate_group(block_id, block_list))
        return results

    def _calculate_group(self, block_id: str, blocks: list[Block]) -> list[DriftResult]:
        """Calculate drift within a group of blocks."""
        results = []
        base_block = blocks[0]

        for other_block in blocks[1:]:
            similarity = self._calculate_similarity(base_block, other_block)
            threshold = self.TOLERANCE_THRESHOLDS.get(base_block.tolerance, 0.95)
            is_drifted = similarity < threshold

            result = DriftResult(
                block_id=block_id,
                base_location=f"{base_block.file_path}:{base_block.start_line}",
                compared_location=f"{other_block.file_path}:{other_block.start_line}",
                similarity=similarity,
                threshold=threshold,
                is_drifted=is_drifted,
                recommendation=self._get_recommendation(similarity),
            )
            results.append(result)

        return results

    def _calculate_similarity(self, block1: Block, block2: Block) -> float:
        """Calculate similarity between two blocks with caching."""
        # Quick hash check for exact matches
        if block1.content_hash == block2.content_hash:
            return 1.0

        # Check cache
        cache_key = (block1.content_hash, block2.content_hash)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Normalize and calculate
        norm1 = self._normalize_content(block1.content, block1.tolerance)
        norm2 = self._normalize_content(block2.content, block2.tolerance)

        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        self._cache[cache_key] = similarity

        return similarity

    def _normalize_content(self, content: str, tolerance: str) -> str:
        """Normalize content based on tolerance level."""
        if tolerance == "exact":
            return content

        lines = content.strip().splitlines()
        normalized = []

        for line in lines:
            if tolerance in ("whitespace", "comments", "minor", "flexible"):
                # Normalize whitespace
                line = " ".join(line.split())

            if tolerance in ("comments", "minor", "flexible"):
                # Remove common comment markers
                line = self._strip_comments(line)

            normalized.append(line)

        return "\n".join(normalized)

    def _strip_comments(self, line: str) -> str:
        """Remove comment markers while preserving content."""
        # Remove common single-line comment markers
        for marker in ["#", "//", "--"]:
            if marker in line:
                idx = line.find(marker)
                # Only remove if it's likely a comment (not in string)
                if idx > 0 and line[:idx].count('"') % 2 == 0:
                    line = line[:idx].strip()
        return line

    def _get_recommendation(self, similarity: float) -> str:
        """Get recommendation based on similarity score."""
        if similarity >= 0.95:
            return "healthy"
        elif similarity >= 0.75:
            return "minor_sync_needed"
        elif similarity >= 0.50:
            return "significant_drift"
        else:
            return "consolidate_or_diverge"

    def get_summary_stats(self, results: list[DriftResult]) -> dict:
        """Calculate summary statistics."""
        if not results:
            return {
                "total_comparisons": 0,
                "drifted_count": 0,
                "healthy_count": 0,
                "avg_similarity": 0.0,
            }

        drifted = sum(1 for r in results if r.is_drifted)
        healthy = len(results) - drifted
        avg_sim = sum(r.similarity for r in results) / len(results)

        return {
            "total_comparisons": len(results),
            "drifted_count": drifted,
            "healthy_count": healthy,
            "avg_similarity": round(avg_sim, 3),
        }
