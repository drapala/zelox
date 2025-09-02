#!/usr/bin/env python3
"""
title: Repository Map Generator (Refactored)
purpose: CLI entry point for repository map generation using modular components
inputs: [{"name": "repo_root", "type": "path"}, {"name": "output_path", "type": "path"}]
outputs: [{"name": "repo_map", "type": "markdown_file"}]
effects: ["file_generation", "documentation_update"]
deps: ["pathlib", "argparse", "datetime", "repo_mapping"]
owners: ["drapala"]
stability: stable
since_version: "0.4.0"
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from repo_mapping import RepoMapBuilder


def main():
    """Main entry point for repository map generation."""
    parser = argparse.ArgumentParser(
        description="Auto-generate REPO_MAP.md using modular components"
    )
    parser.add_argument(
        "--repo-root", default=".", help="Repository root path (default: current directory)"
    )
    parser.add_argument("--output", help="Output path (default: docs/repo/REPO_MAP.md)")
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--incremental", action="store_true", help="Only update changed files since last run"
    )
    parser.add_argument(
        "--since-hours", type=int, help="For incremental mode, scan files changed in last N hours"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="Additional patterns to exclude (can be specified multiple times)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show output without writing files")
    parser.add_argument(
        "--stats", action="store_true", help="Show repository statistics after generation"
    )

    args = parser.parse_args()

    # Resolve paths
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"Error: Repository root '{repo_root}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
        if output_path.is_file():
            output_dir = output_path.parent
        else:
            output_dir = output_path
    else:
        output_dir = repo_root / "docs" / "repo"

    # Build repository map using fluent interface
    builder = RepoMapBuilder(repo_root)

    # Apply exclude patterns if provided
    if args.exclude:
        builder.exclude(set(args.exclude))

    # Configure incremental mode if requested
    if args.incremental:
        if args.since_hours:
            since = datetime.now() - timedelta(hours=args.since_hours)
            builder.incremental_since(since)
        else:
            # Default to last 24 hours for incremental
            since = datetime.now() - timedelta(hours=24)
            builder.incremental_since(since)

    # Build and format the map
    builder.scan().build()

    if args.dry_run:
        # Display output without writing
        content = builder.format(args.format)
        print(f"Generated {args.format.upper()} content:")
        print("=" * 50)
        print(content)
        print("=" * 50)
    else:
        # Write to file
        output_file = builder.write(output_dir, args.format)
        print(f"✅ Generated repository map at {output_file}")

        # Show statistics if requested
        if args.stats:
            stats = builder.get_statistics()
            print("\n📊 Repository Statistics:")
            print(f"   Features: {stats['total_features']}")
            print(f"   Scripts: {stats['total_scripts']}")
            print(f"   ADRs: {stats['total_adrs']}")
            print(f"   Total LOC: {stats['total_loc']:,}")
            print(f"   Files scanned: {stats['files_scanned']}")
            if stats["total_features"] > 0:
                test_coverage = stats["features_with_tests"] / stats["total_features"] * 100
                print(f"   Features with tests: {test_coverage:.1f}%")

        # Show file metrics
        with open(output_file, encoding="utf-8") as f:
            content = f.read()
            words = len(content.split())
            lines = content.count("\n") + 1
            print("\n📄 Output Metrics:")
            print(f"   Words: {words:,}")
            print(f"   Lines: {lines:,}")
            print(f"   Size: {len(content):,} bytes")


if __name__ == "__main__":
    main()
