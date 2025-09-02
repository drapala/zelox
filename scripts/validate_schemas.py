#!/usr/bin/env python3
"""
---
title: Schema Validation Entry Point
purpose: Orchestrate schema validation using modular components
inputs:
  - name: repo_root
    type: str
  - name: check_source_files
    type: bool
outputs:
  - name: exit_code
    type: int
effects:
  - validates repository schemas
  - prints validation report
deps:
  - argparse
  - sys
  - pathlib
  - schema_validation.schema_rules
  - schema_validation.schema_reporter
owners: [llm-first-team]
stability: stable
since_version: 2.0.0
complexity: low
---

Schema validation orchestrator that uses vertical slice architecture
for improved LLM editability. See schema_validation/README.md for details.
"""

import argparse
import sys
from pathlib import Path

from schema_validation.schema_reporter import ValidationReporter
from schema_validation.schema_rules import ValidationRules


def validate_all_schemas(repo_root: Path) -> bool:
    """Run all schema validations with clear linear flow."""
    rules = ValidationRules(str(repo_root))
    reporter = ValidationReporter()

    # Print header
    reporter.print_header()

    # 1. Validate INDEX.yaml
    reporter.print_section(
        "1️⃣",
        "INDEX.yaml Validation",
        "Central module registry and API contracts",
        "LLMs need structured navigation to understand the codebase",
    )
    index_result = rules.validate_index_yaml()
    reporter.report_result(index_result, "Schema structure valid - all modules properly defined")

    # 2. Validate ADR frontmatter
    reporter.print_section(
        "2️⃣",
        "ADR Frontmatter Validation",
        "Machine-readable metadata in Architecture Decision Records",
        "Enables LLMs to understand decision context and impact",
    )
    adr_result = rules.validate_adr_files()
    reporter.report_result(adr_result, "All ADRs properly tagged for LLM discovery")

    # 3. Validate OBS_PLAN files
    reporter.print_section(
        "3️⃣",
        "OBS_PLAN.md Validation",
        "Observability contracts for each feature",
        "Defines metrics, alerts, and SLOs for automated monitoring",
    )
    obs_result = rules.validate_obs_plans()
    reporter.report_result(obs_result, "All features have proper observability contracts")

    # Print summary
    return reporter.print_summary()


def check_source_frontmatter(repo_root: Path) -> bool:
    """Check Python source files for frontmatter coverage."""
    rules = ValidationRules(str(repo_root))

    print("=" * 60)
    print("SOURCE FILE FRONTMATTER CHECK")
    print("=" * 60)

    result = rules.check_source_frontmatter_coverage()

    if result.is_valid:
        print("✅ Frontmatter coverage meets LLM-first standards")
    else:
        for error in result.errors:
            print(f"❌ {error}")

    for warning in result.warnings:
        print(f"⚠️  {warning}")

    return result.is_valid


def main():
    """Main entry point with clear command dispatch."""
    parser = argparse.ArgumentParser(
        description="Validate schemas and frontmatter for LLM-first architecture"
    )
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root path")
    parser.add_argument(
        "--check-source-files",
        action="store_true",
        help="Check Python source files for frontmatter",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root)

    if args.check_source_files:
        success = check_source_frontmatter(repo_root)
    else:
        success = validate_all_schemas(repo_root)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
