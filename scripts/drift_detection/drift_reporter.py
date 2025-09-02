"""
title: Drift Reporter
purpose: Generate clear drift reports in various formats
inputs: [{"name": "drift_results", "type": "list[DriftResult]"}]
outputs: [{"name": "report", "type": "str|dict"}]
effects: ["reporting"]
deps: ["json", "sys"]
owners: ["drapala"]
stability: stable
since_version: "0.4.0"
"""

import sys
from typing import TextIO

from .drift_calculator import DriftResult


class DriftReporter:
    """Generate drift reports in various formats."""

    def __init__(self, output: TextIO = sys.stdout):
        self.output = output

    def report_json(self, results: list[DriftResult], stats: dict) -> dict:
        """Generate JSON report."""
        report = {"summary": stats, "drifted_blocks": [], "healthy_blocks": []}

        for result in results:
            entry = {
                "id": result.block_id,
                "locations": [result.base_location, result.compared_location],
                "similarity": round(result.similarity, 3),
                "threshold": result.threshold,
                "recommendation": result.recommendation,
            }

            if result.is_drifted:
                report["drifted_blocks"].append(entry)
            else:
                report["healthy_blocks"].append(entry)

        return report

    def report_text(self, results: list[DriftResult], stats: dict) -> str:
        """Generate human-readable text report."""
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("DRIFT CHECK REPORT")
        lines.append("=" * 60)

        # Summary
        lines.append("\nSUMMARY:")
        lines.append(f"  Total comparisons: {stats['total_comparisons']}")
        lines.append(f"  Drifted blocks: {stats['drifted_count']}")
        lines.append(f"  Healthy blocks: {stats['healthy_count']}")
        lines.append(f"  Average similarity: {stats['avg_similarity']:.1%}")

        # Drifted blocks
        drifted = [r for r in results if r.is_drifted]
        if drifted:
            lines.append("\nDRIFTED BLOCKS:")
            for result in drifted:
                lines.append(f"\n  Block ID: {result.block_id}")
                lines.append(f"    Base: {result.base_location}")
                lines.append(f"    Compared: {result.compared_location}")
                lines.append(f"    Similarity: {result.similarity:.1%} < {result.threshold:.1%}")
                lines.append(f"    Action: {result.recommendation}")

        # Footer
        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def report_ci(self, results: list[DriftResult], stats: dict) -> int:
        """Generate CI-friendly report with exit code."""
        drifted = stats["drifted_count"]
        total = stats["total_comparisons"]

        if drifted == 0:
            if total > 0:
                print(f"✅ All {total} duplicate blocks are synchronized", file=self.output)
            else:
                print("✅ No duplicate blocks found", file=self.output)
            return 0
        else:
            print(f"❌ Found {drifted}/{total} drifted blocks", file=self.output)

            for result in results:
                if result.is_drifted:
                    print(
                        f"  - {result.block_id}: {result.similarity:.1%} < {result.threshold:.1%}",
                        file=self.output,
                    )
                    print(
                        f"    {result.base_location} ↔ {result.compared_location}", file=self.output
                    )

            return 1

    def report_markdown(self, results: list[DriftResult], stats: dict) -> str:
        """Generate Markdown report for documentation."""
        lines = []

        lines.append("# Drift Check Report")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Comparisons:** {stats['total_comparisons']}")
        lines.append(f"- **Drifted Blocks:** {stats['drifted_count']}")
        lines.append(f"- **Healthy Blocks:** {stats['healthy_count']}")
        lines.append(f"- **Average Similarity:** {stats['avg_similarity']:.1%}")
        lines.append("")

        drifted = [r for r in results if r.is_drifted]
        if drifted:
            lines.append("## Drifted Blocks")
            lines.append("")
            lines.append("| Block ID | Locations | Similarity | Action |")
            lines.append("|----------|-----------|------------|--------|")

            for result in drifted:
                locations = f"{result.base_location}<br>{result.compared_location}"
                similarity = f"{result.similarity:.1%}"
                lines.append(
                    f"| {result.block_id} | {locations} | {similarity} | {result.recommendation} |"
                )

        return "\n".join(lines)
