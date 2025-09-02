#!/usr/bin/env python3
"""
---
title: PR Reporter
purpose: Generate clear reports for PR validation results
inputs:
  - name: stats
    type: dict
  - name: violations
    type: list
outputs:
  - name: report
    type: str
effects: [stdout]
deps: []
owners: []
stability: stable
since_version: 1.0.0
---

Report generation for PR validation results.
Provides clear, actionable feedback to users.
"""

from enum import Enum


class FileCategory(Enum):
    """File categories."""

    APPLICATION = "application"
    TEST = "test"
    CONFIG = "config"
    DOCUMENTATION = "documentation"


def format_header(title: str, width: int = 60) -> str:
    """Format section header."""
    border = "=" * width
    return f"\n{border}\n{title}\n{border}"


def format_category_section(
    category: FileCategory, files: list[str], stats: dict, show_files: int = 3
) -> str:
    """Format category section of report."""
    if not files:
        return ""

    lines = [f"\n{category.value.upper()}:"]
    lines.append(f"  Files: {len(files)}")

    if category != FileCategory.DOCUMENTATION:
        lines.append(f"  Lines added: +{stats.get('added', 0)}")
        lines.append(f"  Lines deleted: -{stats.get('deleted', 0)}")
        lines.append(f"  Effective LOC: {stats.get('loc', 0)}")
    else:
        lines.append("  (Documentation excluded from LOC limits)")

    # Show sample files
    for f in files[:show_files]:
        lines.append(f"    - {f}")
    if len(files) > show_files:
        lines.append(f"    ... and {len(files) - show_files} more")

    return "\n".join(lines)


def generate_success_report(stats: dict, config: dict) -> str:
    """Generate success report."""
    lines = [format_header("✅ PR WITHIN LIMITS")]
    lines.append("\n✓ All category limits respected:")

    limits = config.get("category_limits", {})
    for category in [FileCategory.APPLICATION, FileCategory.TEST, FileCategory.CONFIG]:
        files = stats["categorized_files"].get(category, [])
        if files:
            cat_stats = stats["categorized_stats"].get(category, {})
            cat_limits = limits.get(category, {})
            status = (
                f"  {category.value}: "
                f"{cat_stats.get('loc', 0)}/{cat_limits.get('loc', '∞')} LOC, "
                f"{len(files)}/{cat_limits.get('files', '∞')} files"
            )
            lines.append(status)

    return "\n".join(lines)


def generate_failure_report(stats: dict, violations: list[str], config: dict) -> str:
    """Generate failure report with actionable feedback."""
    lines = [format_header("❌ PR EXCEEDS LIMITS")]

    for violation in violations:
        lines.append(f"✗ {violation}")

    lines.append("\n💡 Suggestions:")
    lines.append("  - Split application logic into focused PRs")
    lines.append("  - Consider if all tests are necessary now")
    lines.append("  - Config changes might warrant separate PR")

    lines.append("\n📖 Per ADR-006: Different categories have")
    lines.append("   different limits for reviewability.")

    # Add Claude prompt
    lines.append(generate_claude_prompt(stats, violations, config))

    return "\n".join(lines)


def generate_claude_prompt(stats: dict, violations: list[str], config: dict) -> str:
    """Generate Claude CLI fix prompt."""
    lines = [format_header("🤖 CLAUDE CLI FIX PROMPT")]
    lines.append("\nCopy and paste this into Claude CLI:\n")
    lines.append("-" * 40)

    prompt = ["My PR exceeds size limits. Please help split it.\n"]
    prompt.append("VIOLATIONS:")
    for v in violations:
        prompt.append(f"• {v}")

    prompt.append("\nCURRENT BREAKDOWN:")
    for category in FileCategory:
        files = stats["categorized_files"].get(category, [])
        if files:
            cat_stats = stats["categorized_stats"].get(category, {})
            prompt.append(
                f"\n{category.value.upper()}: " f"{len(files)} files, {cat_stats.get('loc', 0)} LOC"
            )
            for f in files[:3]:
                prompt.append(f"  - {f}")

    prompt.append("\nPlease create focused PRs respecting limits.")

    lines.extend(prompt)
    lines.append("-" * 40)

    return "\n".join(lines)


def print_analysis(stats: dict) -> None:
    """Print categorized analysis."""
    print(format_header("PR LOC ANALYSIS (Categorized)"))
    print(f"\nTotal files changed: {stats['total_files']}")
    print("\nBreakdown by category:")

    for category in FileCategory:
        files = stats["categorized_files"].get(category, [])
        cat_stats = stats["categorized_stats"].get(category, {})
        section = format_category_section(category, files, cat_stats)
        if section:
            print(section)
