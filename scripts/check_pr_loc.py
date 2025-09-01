#!/usr/bin/env python3
"""
PR LOC Gate Script - Enforces categorized size limits on PRs.
Implements differentiated limits for application code, tests, and configuration.
Per ADR-003 and ADR-006: Incentivizes comprehensive testing while maintaining focus.
"""

import re
import subprocess
import sys
from enum import Enum


class FileCategory(Enum):
    """File categories with different LOC limits."""

    APPLICATION = "application"  # Core business logic
    TEST = "test"  # Test files
    CONFIG = "config"  # Configuration and schemas
    DOCUMENTATION = "documentation"  # Pure documentation (excluded)


# Category patterns for classification
CATEGORY_PATTERNS = {
    FileCategory.TEST: [
        r"(^|/)test_[^/]*\.py$",  # test_*.py files
        r"^scripts/test_[^/]*\.py$",  # test files in scripts
        r"(^|/)[^/]*_test\.py$",  # *_test.py files
        r"\.test\.[tj]sx?$",  # *.test.js/ts/jsx/tsx
        r"\.spec\.[tj]sx?$",  # *.spec.js/ts/jsx/tsx
        r"^tests?/",  # files in test(s) directories
    ],
    FileCategory.CONFIG: [
        r"^\.github/.*\.(yml|yaml)$",  # GitHub workflows
        r"^schemas/.*\.json$",  # JSON schemas
        r"^\..*rc(\..*)?$",  # Dotfiles like .eslintrc
        r"(Makefile|makefile)$",  # Makefiles
        r"Dockerfile$",  # Dockerfiles
        r"docker-compose.*\.(yml|yaml)$",  # Docker compose files
    ],
    FileCategory.DOCUMENTATION: [
        r"\.md$",
        r"\.mdx$",
        r"\.rst$",
        r"\.adoc$",
        r"\.txt$",
        r"(^|/)(LICENSE|NOTICE|AUTHORS|CONTRIBUTORS|CHANGELOG|CHANGES|HISTORY|NEWS|README|TODO)(\.[a-z]+)?$",
    ],
}

# Compile regex patterns for efficiency
CATEGORY_REGEX = {
    category: re.compile("|".join(patterns), re.IGNORECASE)
    for category, patterns in CATEGORY_PATTERNS.items()
}

# Differentiated limits per category
CATEGORY_LIMITS = {
    FileCategory.APPLICATION: {
        "loc": 500,  # Strict limit for application code changes
        "files": 10,  # Max application files in one PR
    },
    FileCategory.TEST: {
        "loc": 1000,  # More generous for comprehensive tests
        "files": 20,  # Allow more test files
    },
    FileCategory.CONFIG: {
        "loc": 250,  # Config changes should be small and focused
        "files": 5,  # Few config files at once
    },
    FileCategory.DOCUMENTATION: {
        "loc": None,  # No limit for docs - encourage documentation
        "files": None,  # No limit for doc files
    },
}

# Total files limit across all categories (safety net)
TOTAL_FILES_LIMIT = 25


def categorize_file(filepath: str) -> FileCategory:
    """Categorize a file based on its path and extension."""
    # Check categories in order: TEST > CONFIG > DOCUMENTATION > APPLICATION
    for category in [FileCategory.TEST, FileCategory.CONFIG, FileCategory.DOCUMENTATION]:
        if CATEGORY_REGEX[category].search(filepath):
            return category

    # Default to APPLICATION for any code file not matching other patterns
    return FileCategory.APPLICATION


def run_git_command(*args) -> str:
    """Execute git command and return output."""
    try:
        result = subprocess.check_output(["git"] + list(args), text=True, stderr=subprocess.DEVNULL)
        return result.strip()
    except subprocess.CalledProcessError:
        print(f"Error running git command: {' '.join(args)}")
        return ""


def get_changed_files(base_ref: str = "origin/main...HEAD") -> list[str]:
    """Get list of changed files in PR."""
    output = run_git_command("diff", "--name-only", base_ref)
    return [f for f in output.splitlines() if f.strip()]


def get_file_diff_stats(filepath: str, base_ref: str = "origin/main...HEAD") -> tuple[int, int]:
    """Get added and deleted line counts for a file."""
    try:
        # Get unified diff with no context lines
        diff_output = run_git_command("diff", "--unified=0", base_ref, "--", filepath)

        if not diff_output:
            return 0, 0

        lines = diff_output.splitlines()
        added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        deleted = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))

        return added, deleted
    except Exception:
        return 0, 0


def analyze_pr(base_ref: str = "origin/main...HEAD") -> dict:
    """Analyze PR and return categorized statistics."""
    all_files = get_changed_files(base_ref)

    # Categorize files
    categorized_files: dict[FileCategory, list[str]] = {category: [] for category in FileCategory}
    categorized_stats = {
        category: {"added": 0, "deleted": 0, "loc": 0} for category in FileCategory
    }

    for filepath in all_files:
        category = categorize_file(filepath)
        categorized_files[category].append(filepath)

        # Get LOC stats for non-documentation files
        if category != FileCategory.DOCUMENTATION:
            added, deleted = get_file_diff_stats(filepath, base_ref)
            categorized_stats[category]["added"] += added
            categorized_stats[category]["deleted"] += deleted
            categorized_stats[category]["loc"] += added + deleted

    return {
        "total_files": len(all_files),
        "categorized_files": categorized_files,
        "categorized_stats": categorized_stats,
    }


def print_analysis(stats: dict) -> None:
    """Print categorized analysis results."""
    print("=" * 60)
    print("PR LOC ANALYSIS (Categorized)")
    print("=" * 60)

    print(f"\nTotal files changed: {stats['total_files']}")
    print("\nBreakdown by category:")

    for category in FileCategory:
        files = stats["categorized_files"][category]
        cat_stats = stats["categorized_stats"][category]

        if not files:
            continue

        print(f"\n{category.value.upper()}:")
        print(f"  Files: {len(files)}")

        if category != FileCategory.DOCUMENTATION:
            print(f"  Lines added: +{cat_stats['added']}")
            print(f"  Lines deleted: -{cat_stats['deleted']}")
            print(f"  Effective LOC: {cat_stats['loc']}")

            # Show limits for this category
            limits = CATEGORY_LIMITS[category]
            if isinstance(limits, dict):
                loc_limit = limits.get("loc")
                files_limit = limits.get("files")
                if loc_limit:
                    loc_msg = f"  Limits: {cat_stats['loc']}/{loc_limit} LOC, "
                    loc_msg += f"{len(files)}/{files_limit} files"
                print(loc_msg)
        else:
            print("  (Documentation excluded from LOC limits)")

        # Show first few files
        for f in files[:3]:
            print(f"    - {f}")
        if len(files) > 3:
            print(f"    ... and {len(files) - 3} more")


def generate_claude_pr_prompt(stats: dict, violations: list[str]) -> None:
    """Generate a copy-paste prompt for Claude CLI to split the PR."""
    print("\n" + "=" * 60)
    print("🤖 CLAUDE CLI FIX PROMPT")
    print("=" * 60)
    print("\nCopy and paste this into Claude CLI:\n")
    print("-" * 40)

    prompt = "My PR exceeds the categorized size limits. Please help me split it.\n\n"
    prompt += "VIOLATIONS:\n"
    for violation in violations:
        prompt += f"• {violation}\n"

    prompt += "\nCURRENT PR BREAKDOWN:\n"
    for category in FileCategory:
        files = stats["categorized_files"][category]
        if files:
            cat_stats = stats["categorized_stats"][category]
            prompt += f"\n{category.value.upper()}: {len(files)} files, {cat_stats['loc']} LOC\n"
            for f in files[:3]:
                prompt += f"  - {f}\n"
            if len(files) > 3:
                prompt += f"  ... and {len(files) - 3} more\n"

    prompt += "\nPlease:\n"
    prompt += "1. Analyze which files belong together\n"
    prompt += "2. Create a plan to split into multiple PRs\n"
    prompt += "3. Ensure each PR respects category limits:\n"
    prompt += "   - Application: ≤500 LOC, ≤10 files\n"
    prompt += "   - Test: ≤1000 LOC, ≤20 files\n"
    prompt += "   - Config: ≤250 LOC, ≤5 files\n"
    prompt += "4. Generate git commands for the first PR\n"

    print(prompt)
    print("-" * 40)
    print("\n💡 TIP: Claude will create focused PRs respecting category limits")


def check_limits(stats: dict) -> bool:
    """Check if PR exceeds any category limits."""
    violations = []

    # Check total files limit
    total_files = stats["total_files"]
    if total_files > TOTAL_FILES_LIMIT:
        violations.append(f"Total files ({total_files}) exceeds limit of {TOTAL_FILES_LIMIT}")

    # Check per-category limits
    for category in FileCategory:
        if category == FileCategory.DOCUMENTATION:
            continue  # Skip documentation

        files = stats["categorized_files"][category]
        cat_stats = stats["categorized_stats"][category]
        limits = CATEGORY_LIMITS[category]

        if not files:
            continue

        # Check file count limit
        if isinstance(limits, dict):
            files_limit = limits.get("files")
            if files_limit and len(files) > files_limit:
                msg = f"{category.value.capitalize()} files ({len(files)}) "
                msg += f"exceed limit of {files_limit}"
                violations.append(msg)

        # Check LOC limit
        if isinstance(limits, dict):
            loc_limit = limits.get("loc")
            if loc_limit and cat_stats["loc"] > loc_limit:
                msg = f"{category.value.capitalize()} LOC ({cat_stats['loc']}) "
                msg += f"exceeds limit of {loc_limit}"
                violations.append(msg)

    if violations:
        print("\n" + "=" * 60)
        print("❌ PR EXCEEDS LIMITS")
        print("=" * 60)
        for violation in violations:
            print(f"✗ {violation}")

        print("\n💡 Suggestions:")
        print("  - Split application logic changes into smaller, focused PRs")
        print("  - Consider if all test changes are necessary in this PR")
        print("  - Configuration changes might warrant a separate PR")
        print("\n📖 Per ADR-006: Different categories have different limits to")
        print("   incentivize testing while maintaining reviewability.")

        # Generate Claude CLI prompt
        generate_claude_pr_prompt(stats, violations)
        return False

    print("\n" + "=" * 60)
    print("✅ PR WITHIN LIMITS")
    print("=" * 60)
    print("\n✓ All category limits respected:")

    for category in [FileCategory.APPLICATION, FileCategory.TEST, FileCategory.CONFIG]:
        files = stats["categorized_files"][category]
        if files:
            cat_stats = stats["categorized_stats"][category]
            limits = CATEGORY_LIMITS[category]
            if isinstance(limits, dict):
                loc_limit = limits.get("loc", 0)
                files_limit = limits.get("files", 0)
                status_msg = f"  {category.value}: {cat_stats['loc']}/{loc_limit} LOC, "
                status_msg += f"{len(files)}/{files_limit} files"
            print(status_msg)

    return True


def main():
    """Main entry point."""
    # Get base ref from command line or use default
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main...HEAD"

    # Special case for CI environments
    if base_ref == "auto":
        # Try to detect the base branch
        if (
            subprocess.call(
                ["git", "rev-parse", "origin/main"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        ):
            base_ref = "origin/main...HEAD"
        else:
            base_ref = "HEAD~1...HEAD"

    print(f"Checking PR against: {base_ref}")

    # Analyze PR
    stats = analyze_pr(base_ref)

    # Print results
    print_analysis(stats)

    # Check limits and exit accordingly
    if not check_limits(stats):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
