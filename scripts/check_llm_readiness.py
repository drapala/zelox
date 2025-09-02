#!/usr/bin/env python3
"""
LLM Readiness Score Calculator - Orchestrator
Main entry point for the modular readiness assessment system.
"""

import argparse
import sys
from pathlib import Path

from readiness_check import (
    ReadinessCalculator,
    ReadinessReporter,
    ReadinessValidator,
)
from readiness_check.readiness_reporter import ReportFormat
from readiness_check.readiness_validator import ThresholdConfig


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Assess repository LLM-friendliness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Repository path to analyze (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Minimum passing score (default: 80)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if validation fails",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed metric information",
    )
    return parser.parse_args()


def main():
    """Main orchestration logic."""
    args = parse_args()
    repo_path = Path(args.repo_path).resolve()

    if not repo_path.exists():
        print(f"❌ Repository path does not exist: {repo_path}")
        sys.exit(1)

    # Initialize components
    calculator = ReadinessCalculator(repo_path)
    validator = ReadinessValidator(ThresholdConfig(min_overall_score=args.threshold))
    reporter = ReadinessReporter()

    # Calculate readiness score
    try:
        score = calculator.calculate()
    except Exception as e:
        print(f"❌ Failed to calculate readiness score: {e}")
        sys.exit(1)

    # Validate against thresholds
    validation = validator.validate(score)

    # Generate report
    format_enum = ReportFormat[args.format.upper()]
    report = reporter.generate(score, validation, format_enum)

    # Output report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"✅ Report saved to: {output_path}")
    else:
        print(report)

    # Exit with appropriate code
    if args.strict:
        exit_code = validator.get_exit_code(validation)
        if exit_code != 0:
            print(f"\n❌ Validation failed - Score: {score.percentage:.1f}%")
        else:
            print(f"\n✅ Validation passed - Score: {score.percentage:.1f}%")
        sys.exit(exit_code)
    else:
        # Non-strict mode: only fail if score is very low
        if score.percentage < 60:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
