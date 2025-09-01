#!/usr/bin/env python3
"""
PR LOC Gate Script - Enforces size limits on PRs for LLM-friendly reviews.
Excludes pure documentation files from LOC count while maintaining strict limits on code changes.
"""
import subprocess
import sys
import re
import pathlib
from typing import Tuple, List

# Extensions/names EXCLUDED from LOC count (pure documentation)
EXCLUDE_PATTERNS = (
    r"\.md$",
    r"\.mdx$", 
    r"\.rst$",
    r"\.adoc$",
    r"\.txt$",
    r"(^|/)(LICENSE|NOTICE|AUTHORS|CONTRIBUTORS|CHANGELOG|CHANGES|HISTORY|NEWS|README|TODO)(\.[a-z]+)?$"
)

EXCLUDE_RE = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)

# Configuration
HARD_FILES_LIMIT = 10
HARD_LOC_LIMIT = 500


def run_git_command(*args) -> str:
    """Execute git command and return output."""
    try:
        result = subprocess.check_output(["git"] + list(args), text=True, stderr=subprocess.DEVNULL)
        return result.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {' '.join(args)}")
        return ""


def get_changed_files(base_ref: str = "origin/main...HEAD") -> List[str]:
    """Get list of changed files in PR."""
    output = run_git_command("diff", "--name-only", base_ref)
    return [f for f in output.splitlines() if f.strip()]


def is_documentation_only(filepath: str) -> bool:
    """Check if file is pure documentation that should be excluded from LOC count."""
    return bool(EXCLUDE_RE.search(filepath))


def get_file_diff_stats(filepath: str, base_ref: str = "origin/main...HEAD") -> Tuple[int, int]:
    """Get added and deleted line counts for a file."""
    try:
        # Get unified diff with no context lines
        diff_output = run_git_command("diff", "--unified=0", base_ref, "--", filepath)
        
        if not diff_output:
            return 0, 0
        
        lines = diff_output.splitlines()
        added = sum(1 for line in lines 
                   if line.startswith("+") and not line.startswith("+++"))
        deleted = sum(1 for line in lines 
                     if line.startswith("-") and not line.startswith("---"))
        
        return added, deleted
    except Exception:
        return 0, 0


def analyze_pr(base_ref: str = "origin/main...HEAD") -> dict:
    """Analyze PR and return statistics."""
    all_files = get_changed_files(base_ref)
    
    # Separate code files from documentation
    code_files = []
    doc_files = []
    
    for f in all_files:
        if is_documentation_only(f):
            doc_files.append(f)
        else:
            code_files.append(f)
    
    # Calculate LOC for code files only
    total_added = 0
    total_deleted = 0
    
    for filepath in code_files:
        added, deleted = get_file_diff_stats(filepath, base_ref)
        total_added += added
        total_deleted += deleted
    
    effective_loc = total_added + total_deleted
    
    return {
        "total_files": len(all_files),
        "code_files": code_files,
        "doc_files": doc_files,
        "code_files_count": len(code_files),
        "doc_files_count": len(doc_files),
        "lines_added": total_added,
        "lines_deleted": total_deleted,
        "effective_loc": effective_loc
    }


def print_analysis(stats: dict) -> None:
    """Print analysis results."""
    print("=" * 60)
    print("PR LOC ANALYSIS")
    print("=" * 60)
    
    print(f"Total files changed: {stats['total_files']}")
    print(f"  Code files: {stats['code_files_count']}")
    print(f"  Documentation files: {stats['doc_files_count']} (excluded from LOC)")
    
    print(f"\nCode changes:")
    print(f"  Lines added: +{stats['lines_added']}")
    print(f"  Lines deleted: -{stats['lines_deleted']}")
    print(f"  Effective LOC: {stats['effective_loc']}")
    
    print(f"\nLimits:")
    print(f"  Max code files: {HARD_FILES_LIMIT}")
    print(f"  Max effective LOC: {HARD_LOC_LIMIT}")
    
    if stats['doc_files']:
        print(f"\nExcluded documentation files:")
        for f in stats['doc_files'][:5]:  # Show first 5
            print(f"  - {f}")
        if len(stats['doc_files']) > 5:
            print(f"  ... and {len(stats['doc_files']) - 5} more")


def check_limits(stats: dict) -> bool:
    """Check if PR exceeds limits."""
    files_ok = stats['code_files_count'] <= HARD_FILES_LIMIT
    loc_ok = stats['effective_loc'] <= HARD_LOC_LIMIT
    
    if not files_ok or not not loc_ok:
        print("\n" + "=" * 60)
        print("❌ PR EXCEEDS LIMITS")
        print("=" * 60)
        
        if not files_ok:
            print(f"✗ Too many code files: {stats['code_files_count']} > {HARD_FILES_LIMIT}")
            print("  Consider splitting this PR into smaller, focused changes")
        
        if not loc_ok:
            print(f"✗ Too many lines changed: {stats['effective_loc']} > {HARD_LOC_LIMIT}")
            print("  Break this into multiple PRs for better reviewability")
        
        print("\nNote: Documentation files (*.md, etc.) don't count toward limits")
        return False
    
    print("\n" + "=" * 60)
    print("✅ PR WITHIN LIMITS")
    print("=" * 60)
    return True


def main():
    """Main entry point."""
    # Get base ref from command line or use default
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main...HEAD"
    
    # Special case for CI environments
    if base_ref == "auto":
        # Try to detect the base branch
        if subprocess.call(["git", "rev-parse", "origin/main"], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL) == 0:
            base_ref = "origin/main...HEAD"
        else:
            base_ref = "HEAD~1...HEAD"
    
    print(f"Checking PR against: {base_ref}\n")
    
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