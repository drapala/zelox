"""
---
title: Hotspot Detector
purpose: Find confusion hotspots in codebase
inputs:
  - name: scored_files
    type: List[ScoredFile]
outputs:
  - name: hotspots
    type: List[Hotspot]
effects: []
deps: ['dataclasses', 'typing']
owners: ['llm-architect']
stability: stable
since_version: 1.0.0
---

Detects and ranks confusion hotspots.
"""

from dataclasses import dataclass

from .confusion_scorer import HIGH_SCORE, ScoredFile


@dataclass
class Hotspot:
    """Represents a confusion hotspot."""

    file_path: str
    score: float
    severity: str
    issues: list[str]
    rank: int


class HotspotDetector:
    """Detects and analyzes confusion hotspots."""

    @staticmethod
    def find_hotspots(
        scored_files: list[ScoredFile], threshold: float = HIGH_SCORE
    ) -> list[Hotspot]:
        """Find files exceeding confusion threshold."""
        hotspots = []

        # Filter files above threshold
        high_confusion = [f for f in scored_files if f.score >= threshold]

        # Sort by score descending
        high_confusion.sort(key=lambda x: x.score, reverse=True)

        # Create hotspot entries
        for rank, file in enumerate(high_confusion, 1):
            hotspot = Hotspot(
                file_path=file.file_path,
                score=file.score,
                severity=file.severity,
                issues=file.issues,
                rank=rank,
            )
            hotspots.append(hotspot)

        return hotspots

    @staticmethod
    def categorize_hotspots(hotspots: list[Hotspot]) -> dict[str, list[Hotspot]]:
        """Categorize hotspots by severity."""
        categories = {"critical": [], "high": [], "moderate": []}

        for hotspot in hotspots:
            if hotspot.severity in categories:
                categories[hotspot.severity].append(hotspot)

        return categories

    @staticmethod
    def get_top_hotspots(hotspots: list[Hotspot], limit: int = 10) -> list[Hotspot]:
        """Get top N hotspots."""
        return hotspots[:limit]

    @staticmethod
    def calculate_impact(hotspots: list[Hotspot]) -> dict[str, int]:
        """Calculate impact statistics."""
        return {
            "total_hotspots": len(hotspots),
            "critical_count": sum(1 for h in hotspots if h.severity == "critical"),
            "high_count": sum(1 for h in hotspots if h.severity == "high"),
            "moderate_count": sum(1 for h in hotspots if h.severity == "moderate"),
            "average_score": (
                round(sum(h.score for h in hotspots) / len(hotspots), 1) if hotspots else 0
            ),
        }

    @staticmethod
    def get_common_issues(hotspots: list[Hotspot]) -> list[tuple[str, int]]:
        """Find most common issues across hotspots."""
        issue_counts = {}

        for hotspot in hotspots:
            for issue in hotspot.issues:
                # Extract issue type from message
                issue_type = issue.split(":")[0]
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        # Sort by frequency
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return common_issues
