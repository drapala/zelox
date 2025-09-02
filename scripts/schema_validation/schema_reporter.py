#!/usr/bin/env python3
"""
---
title: Schema Validation Reporter
purpose: Format and output validation results
inputs:
  - name: results
    type: List[ValidationResult]
outputs:
  - name: formatted_report
    type: str
  - name: exit_code
    type: int
effects:
  - prints formatted output to console
deps:
  - typing
  - sys
owners: [llm-first-team]
stability: stable
since_version: 1.0.0
complexity: low
---
"""


from .schema_validator import ValidationResult


class ValidationReporter:
    """Formats and reports validation results."""

    def __init__(self):
        self.all_errors: list[str] = []
        self.all_warnings: list[str] = []

    def print_header(self) -> None:
        """Print validation header."""
        print("=" * 60)
        print("SCHEMA VALIDATION FOR LLM-FIRST ARCHITECTURE")
        print("=" * 60)
        print("\n📚 WHY THESE VALIDATIONS MATTER:")
        print("→ Schemas ensure machine-readable contracts for LLM agents")
        print("→ Consistent structure reduces cognitive load")
        print("→ Valid metadata enables automated tooling")
        print("")

    def print_section(self, number: str, title: str, what: str, why: str) -> None:
        """Print a validation section header."""
        print(f"\n{number}  {title}")
        print(f"   WHAT: {what}")
        print(f"   WHY: {why}")

    def report_result(self, result: ValidationResult, success_message: str = "") -> None:
        """Report a single validation result."""
        if result.is_valid and success_message:
            print(f"   ✅ {success_message}")

        # Collect errors and warnings
        self.all_errors.extend(result.errors)
        self.all_warnings.extend(result.warnings)

        # Print warnings inline if any
        for warning in result.warnings:
            if not warning.startswith("⚠️"):
                print(f"   ⚠️  {warning}")

    def print_summary(self) -> bool:
        """Print final summary and return success status."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        if self.all_errors:
            print("\nERRORS:")
            for error in self.all_errors:
                if error.startswith("❌"):
                    print(f"  {error}")
                else:
                    print(f"  ❌ {error}")

        if self.all_warnings:
            print("\nWARNINGS:")
            for warning in self.all_warnings:
                if warning.startswith("⚠️"):
                    print(f"  {warning}")
                else:
                    print(f"  ⚠️  {warning}")

        all_passed = len(self.all_errors) == 0

        if all_passed:
            self._print_success_message()
        else:
            self._print_failure_message()

        return all_passed

    def _print_success_message(self) -> None:
        """Print success message."""
        print("\n✅ All schema validations passed!")
        print("\n💡 WHAT THIS MEANS:")
        print("   • Your repository structure is LLM-readable")
        print("   • All contracts and metadata are valid")
        print("   • Automated tools can parse your codebase")
        print("   • New contributors (human or AI) can navigate easily")

    def _print_failure_message(self) -> None:
        """Print failure message with guidance."""
        print("\n❌ Schema validation failed!")
        print("\n💡 HOW TO FIX:")
        print("   • Check the specific errors above")
        print("   • Ensure YAML syntax is correct")
        print("   • Verify required fields are present")
        print("   • Run 'make validate.schemas' locally before pushing")

    def get_exit_code(self) -> int:
        """Return appropriate exit code."""
        return 0 if len(self.all_errors) == 0 else 1
