#!/usr/bin/env python3
"""
title: LLM Telemetry Collector
purpose: Track LLM agent interactions and edit success patterns
inputs: [{"name": "edit_events", "type": "list"}, {"name": "context_data", "type": "dict"}]
outputs: [{"name": "telemetry_log", "type": "jsonl_file"}]
effects: ["file_append", "metrics_tracking"]
deps: ["json", "datetime", "pathlib", "dataclasses"]
owners: ["drapala"]
stability: experimental
since_version: "0.4.0"
"""

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EditEvent:
    """Represents a single LLM edit attempt."""

    timestamp: str
    session_id: str
    files_modified: list[str]
    success: bool
    error_type: str | None = None
    context_size: int = 0
    cognitive_hops: int = 0
    edit_type: str = "unknown"  # create, update, delete, refactor
    domain_coherence: float = 0.0  # 0-1 score of how well edit fits domain


@dataclass
class ContextEvent:
    """Represents context usage patterns."""

    timestamp: str
    session_id: str
    files_accessed: list[str]
    search_patterns: list[str]
    confusion_indicators: list[str]  # Error messages, retry attempts
    resolution_time_seconds: float


class LLMTelemetryCollector:
    """Collects and analyzes LLM interaction patterns."""

    def __init__(self, repo_root: str = ".", log_file: str = ".reports/llm_telemetry.jsonl"):
        self.repo_root = Path(repo_root)
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def track_edit_attempt(
        self,
        session_id: str,
        files_modified: list[str],
        success: bool,
        error_type: str | None = None,
        edit_type: str = "update",
    ) -> None:
        """Track an LLM edit attempt."""

        event = EditEvent(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            files_modified=files_modified,
            success=success,
            error_type=error_type,
            context_size=len(files_modified),
            cognitive_hops=self._calculate_cognitive_hops(files_modified),
            edit_type=edit_type,
            domain_coherence=self._estimate_domain_coherence(files_modified),
        )

        self._append_event(event)

    def track_context_usage(
        self,
        session_id: str,
        files_accessed: list[str],
        search_patterns: list[str],
        confusion_indicators: list[str] | None = None,
        resolution_time: float = 0.0,
    ) -> None:
        """Track context navigation patterns."""

        event = ContextEvent(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            files_accessed=files_accessed,
            search_patterns=search_patterns,
            confusion_indicators=confusion_indicators or [],
            resolution_time_seconds=resolution_time,
        )

        self._append_event(event)

    def _calculate_cognitive_hops(self, files: list[str]) -> int:
        """Calculate cognitive hops between files."""
        if len(files) <= 1:
            return 0

        # Simple heuristic: files in different directories = context switch
        directories = {Path(f).parent for f in files}
        return len(directories) - 1

    def _estimate_domain_coherence(self, files: list[str]) -> float:
        """Estimate how well files belong to same domain context."""
        if len(files) <= 1:
            return 1.0

        # Check if files are in same feature slice
        feature_dirs = set()
        for file_path in files:
            parts = Path(file_path).parts
            if "features" in parts:
                feature_idx = parts.index("features")
                if feature_idx + 1 < len(parts):
                    feature_dirs.add(parts[feature_idx + 1])

        # High coherence if all files in same feature
        return 1.0 if len(feature_dirs) <= 1 else 0.5 / len(feature_dirs)

    def _append_event(self, event: Any) -> None:
        """Append event to telemetry log."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                json.dump(asdict(event), f)
                f.write("\n")
        except Exception as e:
            print(f"Warning: Could not write telemetry: {e}", file=sys.stderr)

    def analyze_success_patterns(self, days: int = 7) -> dict[str, Any]:
        """Analyze recent success patterns."""
        if not self.log_file.exists():
            return {"error": "No telemetry data found"}

        try:
            events = self._load_recent_events(days)
            edit_events = [e for e in events if "files_modified" in e]

            if not edit_events:
                return {"error": "No edit events found"}

            total_edits = len(edit_events)
            successful_edits = sum(1 for e in edit_events if e.get("success", False))

            success_rate = successful_edits / total_edits if total_edits > 0 else 0

            # Analyze failure patterns
            failed_events = [e for e in edit_events if not e.get("success", False)]
            error_types: dict[str, int] = {}
            for event in failed_events:
                error_type = event.get("error_type", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1

            # Analyze cognitive complexity impact
            low_complexity = [e for e in edit_events if e.get("cognitive_hops", 0) <= 2]
            low_complexity_success = sum(1 for e in low_complexity if e.get("success", False))
            low_complexity_rate = (
                low_complexity_success / len(low_complexity) if low_complexity else 0
            )

            return {
                "total_edits": total_edits,
                "success_rate": success_rate,
                "error_patterns": error_types,
                "low_complexity_success_rate": low_complexity_rate,
                "recommendations": self._generate_recommendations(success_rate, error_types),
            }

        except Exception as e:
            return {"error": f"Analysis failed: {e}"}

    def _load_recent_events(self, days: int) -> list[dict[str, Any]]:
        """Load events from recent days."""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        events = []

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_time = datetime.fromisoformat(event["timestamp"]).timestamp()
                    if event_time >= cutoff_date:
                        events.append(event)
                except Exception:
                    continue

        return events

    def _generate_recommendations(
        self, success_rate: float, error_types: dict[str, int]
    ) -> list[str]:
        """Generate actionable recommendations based on telemetry."""
        recommendations = []

        if success_rate < 0.7:
            recommendations.append(
                "Consider reducing cognitive complexity - success rate below 70%"
            )

        if "ImportError" in error_types:
            recommendations.append("Review dependency wiring - import errors detected")

        if "SyntaxError" in error_types:
            recommendations.append(
                "Check template quality - syntax errors suggest templating issues"
            )

        most_common_error = max(error_types.items(), key=lambda x: x[1]) if error_types else None
        if most_common_error and most_common_error[1] > 2:
            recommendations.append(f"Address recurring {most_common_error[0]} errors")

        return recommendations


def main():
    """CLI interface for telemetry analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Telemetry Analysis")
    parser.add_argument("--analyze", action="store_true", help="Analyze recent patterns")
    parser.add_argument("--days", type=int, default=7, help="Days to analyze")
    parser.add_argument("--repo-root", default=".", help="Repository root")

    args = parser.parse_args()

    collector = LLMTelemetryCollector(args.repo_root)

    if args.analyze:
        results = collector.analyze_success_patterns(args.days)
        print(json.dumps(results, indent=2))
    else:
        print("Use --analyze to analyze recent telemetry patterns")


if __name__ == "__main__":
    main()
