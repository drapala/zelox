#!/usr/bin/env python3
"""
title: Semantic Analysis Pipeline
purpose: Orchestrate semantic analysis pipeline stages
inputs: [{name: "repo_root", type: "str"}, {name: "output_path", type: "str"}]
outputs: [{name: "report", type: "AnalysisReport"}]
effects: ["file_analysis", "report_generation"]
deps: ["pathlib", "argparse", "sys"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: low
"""

import argparse
import sys
from pathlib import Path

from semantic_extractor import extract_patterns
from semantic_parser import parse_file
from semantic_reporter import SemanticReporter, generate_report
from semantic_scorer import calculate_scores


class SemanticAnalysisPipeline:
    """Orchestrate the semantic analysis pipeline."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.parsed_files = []
        self.patterns = None
        self.scores = None
        self.report = None

    def analyze(self) -> dict:
        """Run the complete analysis pipeline."""
        print("Starting semantic analysis pipeline...")

        # Stage 1: Parse files
        self._parse_stage()

        # Stage 2: Extract patterns
        self._extract_stage()

        # Stage 3: Score quality
        self._score_stage()

        # Stage 4: Generate report
        self._report_stage()

        return {
            "success": True,
            "llm_readiness_score": self.scores.llm_readiness_score,
            "status": self._get_status(),
        }

    def _parse_stage(self) -> None:
        """Stage 1: Parse all Python files."""
        print("Stage 1: Parsing files...")

        python_files = list(self.repo_root.rglob("*.py"))
        filtered_files = [f for f in python_files if not self._should_skip_file(f)]

        for file_path in filtered_files:
            try:
                parsed = parse_file(file_path)
                if not parsed.parse_errors:
                    self.parsed_files.append(parsed)
                else:
                    print(f"  Warning: Parse errors in {file_path}: {parsed.parse_errors[0]}")
            except Exception as e:
                print(f"  Error parsing {file_path}: {e}", file=sys.stderr)

        print(f"  Parsed {len(self.parsed_files)} files successfully")

    def _extract_stage(self) -> None:
        """Stage 2: Extract semantic patterns."""
        print("Stage 2: Extracting patterns...")

        if not self.parsed_files:
            print("  No files to analyze")
            return

        self.patterns = extract_patterns(self.parsed_files)

        print(f"  Extracted {len(self.patterns.dependency_graph.import_graph)} import dependencies")
        print(f"  Extracted {len(self.patterns.dependency_graph.call_graph)} call dependencies")
        print(f"  Found {len(self.patterns.cyclic_deps)} cyclic dependencies")
        print(f"  Identified {len(self.patterns.hotspots)} hotspots")

    def _score_stage(self) -> None:
        """Stage 3: Calculate quality scores."""
        print("Stage 3: Calculating scores...")

        if not self.patterns:
            print("  No patterns to score")
            return

        self.scores = calculate_scores(self.patterns)

        print(f"  LLM Readiness Score: {self.scores.llm_readiness_score:.1f}/100")
        print("  Complexity metrics calculated")
        print(f"  Generated {len(self.scores.insights)} insights")
        print(f"  Generated {len(self.scores.recommendations)} recommendations")

    def _report_stage(self) -> None:
        """Stage 4: Generate report."""
        print("Stage 4: Generating report...")

        if not self.scores or not self.patterns:
            print("  No data for report")
            return

        self.report = generate_report(self.scores, self.patterns, len(self.parsed_files))

        print(f"  Report generated with status: {self.report.summary['status']}")

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        name = file_path.name
        path_str = str(file_path)

        # Skip test files
        if name.startswith("test_") or name.endswith("_test.py"):
            return True

        # Skip cache and hidden files
        if "__pycache__" in path_str or "/." in path_str:
            return True

        # Skip virtual environments
        if "venv/" in path_str or "env/" in path_str:
            return True

        # Skip node_modules
        if "node_modules/" in path_str:
            return True

        return False

    def _get_status(self) -> str:
        """Get pipeline status."""
        if not self.scores:
            return "incomplete"

        score = self.scores.llm_readiness_score
        if score >= 80:
            return "success"
        elif score >= 60:
            return "warning"
        else:
            return "failure"

    def save_report(self, output_path: str | None = None) -> None:
        """Save report to file."""
        if not self.report:
            print("No report to save")
            return

        reporter = SemanticReporter()

        if output_path:
            output = Path(output_path)
            if output.suffix == ".json":
                reporter.export_json(self.report, output)
                print(f"Report saved to {output}")
            elif output.suffix == ".md":
                reporter.export_markdown(self.report, output)
                print(f"Report saved to {output}")
            else:
                # Default to JSON
                output = output.with_suffix(".json")
                reporter.export_json(self.report, output)
                print(f"Report saved to {output}")

    def print_report(self) -> None:
        """Print report to console."""
        if not self.report:
            print("No report to print")
            return

        reporter = SemanticReporter()
        reporter.print_report(self.report)


def analyze_codebase(repo_root: str = ".", output_path: str | None = None) -> dict:
    """Run semantic analysis on codebase."""
    pipeline = SemanticAnalysisPipeline(repo_root)
    result = pipeline.analyze()

    if output_path:
        pipeline.save_report(output_path)

    return result


def main():
    """CLI interface for semantic analysis pipeline."""
    parser = argparse.ArgumentParser(
        description="Semantic Analysis Pipeline - LLM-First Architecture"
    )
    parser.add_argument(
        "--repo-root", default=".", help="Repository root path (default: current directory)"
    )
    parser.add_argument("--output", help="Output file path (.json or .md)")
    parser.add_argument("--report", action="store_true", help="Print analysis report to console")
    parser.add_argument(
        "--threshold", type=float, default=80.0, help="LLM readiness threshold (default: 80.0)"
    )

    args = parser.parse_args()

    # Run pipeline
    pipeline = SemanticAnalysisPipeline(args.repo_root)
    result = pipeline.analyze()

    # Print report if requested
    if args.report:
        pipeline.print_report()

    # Save report if output specified
    if args.output:
        pipeline.save_report(args.output)

    # Check threshold and exit accordingly
    score = pipeline.scores.llm_readiness_score if pipeline.scores else 0
    if score < args.threshold:
        print(f"\n❌ LLM readiness score ({score:.1f}) below threshold ({args.threshold})")
        sys.exit(1)
    else:
        print(f"\n✅ LLM readiness score ({score:.1f}) meets threshold ({args.threshold})")
        sys.exit(0)


if __name__ == "__main__":
    main()
