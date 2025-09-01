#!/usr/bin/env python3
"""
README Coverage Check
Ensures features are documented with READMEs for LLM discoverability.
"""

import sys
from pathlib import Path


def find_feature_dirs(repo_root: Path) -> list[Path]:
    """Find all feature directories."""
    features_dir = repo_root / "features"
    if not features_dir.exists():
        return []

    # Get all directories under features/
    return [d for d in features_dir.iterdir() if d.is_dir() and d.name != "template"]


def check_readme_coverage(repo_root: Path = Path(".")) -> tuple[bool, list[str]]:
    """Check if all features have README documentation."""
    feature_dirs = find_feature_dirs(repo_root)

    if not feature_dirs:
        print("⚠️  No feature directories found to check")
        return True, []

    missing_readmes = []

    for feature_dir in feature_dirs:
        readme_path = feature_dir / "README.md"
        if not readme_path.exists():
            missing_readmes.append(str(feature_dir.relative_to(repo_root)))

    return len(missing_readmes) == 0, missing_readmes


def main():
    """Main entry point."""
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    print("=" * 60)
    print("README COVERAGE CHECK (LLM-First)")
    print("=" * 60)
    print("\n📚 WHY THIS MATTERS:")
    print("→ READMEs enable LLM agents to understand feature purpose")
    print("→ Documentation at the source reduces cognitive hops")
    print("→ Self-contained features improve maintainability")
    print("")

    passed, missing = check_readme_coverage(repo_root)

    if passed:
        feature_count = len(find_feature_dirs(repo_root))
        print(f"✅ All {feature_count} features have README documentation")
        print("\n💡 WHAT THIS MEANS:")
        print("   • Features are self-documenting")
        print("   • LLM agents can navigate your codebase")
        print("   • New contributors understand feature purpose")
        sys.exit(0)
    else:
        print(f"❌ {len(missing)} features missing README documentation:")
        for feature in missing:
            print(f"   - {feature}/README.md")

        print("\n💡 HOW TO FIX:")
        print("   • Create README.md in each feature directory")
        print("   • Document: purpose, API, dependencies, testing")
        print("   • Use the template in features/template/README.md")

        # Generate Claude CLI prompt
        print("\n" + "=" * 60)
        print("🤖 CLAUDE CLI FIX PROMPT")
        print("=" * 60)
        print("\nCopy and paste this into Claude CLI:\n")
        print("-" * 40)
        prompt = "Please create README.md files for the following features:\n\n"
        for feature in missing:
            prompt += f"• {feature}\n"
        prompt += "\nEach README should include:\n"
        prompt += "1. Feature purpose and business value\n"
        prompt += "2. API surface (if applicable)\n"
        prompt += "3. Dependencies and interactions\n"
        prompt += "4. Testing approach\n"
        prompt += "5. Configuration options\n"
        print(prompt)
        print("-" * 40)

        sys.exit(1)


if __name__ == "__main__":
    main()
