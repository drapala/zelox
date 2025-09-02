#!/usr/bin/env python3
"""
title: Learning System Wiring Module
purpose: Wire together learning system components
inputs: [{"name": "repo_root", "type": "str"}, {"name": "telemetry_log", "type": "str"}]
outputs: [{"name": "system", "type": "AdaptiveLearningSystem"}]
effects: ["component_initialization", "dependency_injection"]
deps: ["pathlib", "json"]
owners: ["drapala"]
stability: experimental
since_version: "0.5.0"
"""

import json
from pathlib import Path
from typing import Any

from adaptation_engine import AdaptationEngine
from learning_reporter import LearningReporter
from metric_tracker import MetricTracker
from pattern_learner import PatternLearner


class AdaptiveLearningSystem:
    """Main system wiring learning components together."""

    def __init__(self, repo_root: str = ".", telemetry_log: str = ".reports/llm_telemetry.jsonl"):
        self.repo_root = Path(repo_root)
        self.telemetry_log = telemetry_log

        self.pattern_learner = PatternLearner(telemetry_log)
        self.metric_tracker = MetricTracker()
        self.adaptation_engine = AdaptationEngine()
        self.reporter = LearningReporter()

    def analyze_and_recommend(
        self, current_metrics: dict[str, Any] | None = None, days_back: int = 30
    ) -> dict[str, Any]:
        """Perform full analysis and generate recommendations."""
        print("Learning patterns from telemetry data...")

        patterns = self.pattern_learner.learn_patterns(days_back)

        if not patterns:
            return self.reporter.generate_report(
                patterns=[],
                recommendations=[],
                metrics={},
                predictions={"predicted_success_rate": 0.5, "confidence": 0.0, "trend": "unknown"},
            )

        pattern_metrics = self.metric_tracker.track_patterns(patterns)

        predictions = self.metric_tracker.calculate_predictions(patterns, current_metrics or {})

        recommendations = self.adaptation_engine.generate_recommendations(
            patterns, current_metrics or {}
        )

        report = self.reporter.generate_report(
            patterns=patterns,
            recommendations=recommendations,
            metrics={**pattern_metrics, **(current_metrics or {})},
            predictions=predictions,
        )

        return report

    def export_report(self, report: dict[str, Any], output_path: str) -> None:
        """Export report to file."""
        output_file = Path(output_path)

        if output_file.suffix == ".json":
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
        elif output_file.suffix == ".md":
            markdown = self.reporter.export_report(report, format="markdown")
            with open(output_file, "w") as f:
                f.write(markdown)
        else:
            raise ValueError(f"Unsupported output format: {output_file.suffix}")

        print(f"Report exported to {output_file}")


def build_learning_system(
    repo_root: str = ".", telemetry_log: str = ".reports/llm_telemetry.jsonl"
) -> AdaptiveLearningSystem:
    """Factory function to build the learning system."""
    return AdaptiveLearningSystem(repo_root, telemetry_log)


def main():
    """CLI interface for adaptive learning system."""
    import argparse

    parser = argparse.ArgumentParser(description="Adaptive Learning System")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument(
        "--telemetry", default=".reports/llm_telemetry.jsonl", help="Telemetry log file"
    )
    parser.add_argument("--analyze", action="store_true", help="Analyze and recommend")
    parser.add_argument("--metrics-file", help="JSON file with current metrics")
    parser.add_argument("--days-back", type=int, default=30, help="Days of telemetry to analyze")
    parser.add_argument("--output", help="Output file path (.json or .md)")

    args = parser.parse_args()

    system = build_learning_system(args.repo_root, args.telemetry)

    if args.analyze:
        current_metrics = {}
        if args.metrics_file and Path(args.metrics_file).exists():
            with open(args.metrics_file) as f:
                current_metrics = json.load(f)

        report = system.analyze_and_recommend(current_metrics, args.days_back)

        if args.output:
            system.export_report(report, args.output)
        else:
            print(json.dumps(report, indent=2))
    else:
        print("Use --analyze to run the adaptive learning analysis")


if __name__ == "__main__":
    main()
