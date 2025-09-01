#!/usr/bin/env python3
"""
LLM Readiness Score Calculator
Measures how well the repository is optimized for LLM agent effectiveness.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re
import subprocess


class LLMReadinessChecker:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.score = 0
        self.max_score = 100
        self.checks = []

    def check_co_location(self) -> Tuple[int, str]:
        """Check if tests are co-located with code (target: ≥80%)"""
        features_dir = self.repo_root / "features"
        if not features_dir.exists():
            return 0, "❌ No features/ directory found"

        feature_dirs = [d for d in features_dir.iterdir() if d.is_dir()]
        if not feature_dirs:
            return 20, "⚠️  Features directory exists but is empty"

        co_located_count = 0
        total_count = len(feature_dirs)

        for feature_dir in feature_dirs:
            has_code = any(
                (feature_dir / f).exists() for f in ["service.py", "models.py", "api.py"]
            )
            has_tests = (feature_dir / "tests.py").exists()

            if has_code and has_tests:
                co_located_count += 1

        if total_count == 0:
            return 20, "⚠️  No feature directories to check"

        co_location_ratio = co_located_count / total_count
        score = int(co_location_ratio * 25)  # 25 points max

        status = "✅" if co_location_ratio >= 0.8 else "❌"
        return (
            score,
            f"{status} Co-location: {co_located_count}/{total_count} features ({co_location_ratio:.1%})",
        )

    def check_average_hops(self) -> Tuple[int, str]:
        """Check average cognitive hops via import analysis (target: ≤3)"""
        try:
            # Simple heuristic: count imports in Python files
            total_imports = 0
            file_count = 0

            for py_file in self.repo_root.rglob("*.py"):
                if "test" in str(py_file) or "__pycache__" in str(py_file):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Count import statements
                        imports = len(re.findall(r"^(?:import|from)\s+\w+", content, re.MULTILINE))
                        total_imports += imports
                        file_count += 1
                except Exception:
                    continue

            if file_count == 0:
                return 15, "⚠️  No Python files found to analyze"

            avg_imports = total_imports / file_count
            # Score based on imports (lower is better)
            if avg_imports <= 3:
                score = 20
                status = "✅"
            elif avg_imports <= 5:
                score = 15
                status = "⚠️ "
            else:
                score = 5
                status = "❌"

            return score, f"{status} Average imports per file: {avg_imports:.1f} (target: ≤3)"

        except Exception as e:
            return 10, f"⚠️  Could not analyze imports: {str(e)}"

    def check_front_matter_coverage(self) -> Tuple[int, str]:
        """Check front-matter coverage in feature files (target: ≥90%)"""
        features_dir = self.repo_root / "features"
        if not features_dir.exists():
            return 0, "❌ No features/ directory found"

        python_files = list(features_dir.rglob("*.py"))
        if not python_files:
            return 15, "⚠️  No Python files in features/ to check"

        files_with_frontmatter = 0

        for py_file in python_files:
            if "test" in py_file.name or "__init__" in py_file.name:
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Check for YAML front-matter or structured docstrings
                    if (
                        '"""' in content
                        and any(
                            keyword in content.lower()
                            for keyword in ["title:", "purpose:", "inputs:", "outputs:"]
                        )
                    ) or content.startswith("---"):
                        files_with_frontmatter += 1
            except Exception:
                continue

        total_files = len(
            [f for f in python_files if "test" not in f.name and "__init__" not in f.name]
        )
        if total_files == 0:
            return 15, "⚠️  No feature files to check for front-matter"

        coverage = files_with_frontmatter / total_files
        score = int(coverage * 20)  # 20 points max

        status = "✅" if coverage >= 0.9 else "❌"
        return (
            score,
            f"{status} Front-matter coverage: {files_with_frontmatter}/{total_files} files ({coverage:.1%})",
        )

    def check_documentation_structure(self) -> Tuple[int, str]:
        """Check for required documentation files"""
        required_files = [
            ("CLAUDE.md", 5),
            ("docs/repo/REPO_MAP.md", 5),
            ("docs/repo/INDEX.yaml", 5),
            ("docs/repo/FACTS.md", 5),
        ]

        score = 0
        missing = []

        for file_path, points in required_files:
            if (self.repo_root / file_path).exists():
                score += points
            else:
                missing.append(file_path)

        if missing:
            status = "❌" if len(missing) > 2 else "⚠️ "
            return score, f"{status} Missing docs: {', '.join(missing)}"
        else:
            return score, "✅ All required documentation files present"

    def check_adr_structure(self) -> Tuple[int, str]:
        """Check ADR structure and completeness"""
        adr_dir = self.repo_root / "docs" / "adr"
        if not adr_dir.exists():
            return 0, "❌ No docs/adr/ directory found"

        adr_files = list(adr_dir.glob("*.md"))
        if len(adr_files) < 2:  # At least template + one real ADR
            return 3, "⚠️  Need at least 2 ADR files (template + decisions)"

        # Check if ADRs have proper front-matter
        valid_adrs = 0
        for adr_file in adr_files:
            try:
                with open(adr_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "adr_number:" in content and "status:" in content:
                        valid_adrs += 1
            except Exception:
                continue

        if valid_adrs >= len(adr_files) * 0.8:  # 80% have proper structure
            return 10, f"✅ ADR structure: {valid_adrs}/{len(adr_files)} properly formatted"
        else:
            return 5, f"⚠️  ADR structure: {valid_adrs}/{len(adr_files)} properly formatted"

    def run_all_checks(self) -> Dict:
        """Run all readiness checks and return results"""
        results = {"score": 0, "max_score": self.max_score, "checks": [], "recommendations": []}

        # Run individual checks
        checks_to_run = [
            ("Co-location Index", self.check_co_location),
            ("Average Hops", self.check_average_hops),
            ("Front-matter Coverage", self.check_front_matter_coverage),
            ("Documentation Structure", self.check_documentation_structure),
            ("ADR Structure", self.check_adr_structure),
        ]

        total_score = 0

        for check_name, check_func in checks_to_run:
            try:
                score, message = check_func()
                total_score += score
                results["checks"].append(
                    {
                        "name": check_name,
                        "score": score,
                        "message": message,
                        "passed": not message.startswith("❌"),
                    }
                )
            except Exception as e:
                results["checks"].append(
                    {
                        "name": check_name,
                        "score": 0,
                        "message": f"❌ Check failed: {str(e)}",
                        "passed": False,
                    }
                )

        results["score"] = total_score

        # Add recommendations based on score
        if total_score < 60:
            results["recommendations"].extend(
                [
                    "Create basic repository structure with features/ directory",
                    "Add essential documentation (REPO_MAP.md, INDEX.yaml, FACTS.md)",
                    "Co-locate tests with feature code",
                ]
            )
        elif total_score < 80:
            results["recommendations"].extend(
                [
                    "Improve co-location of tests with features",
                    "Add front-matter to Python files",
                    "Review and reduce import complexity",
                ]
            )
        else:
            results["recommendations"].append("Repository meets LLM-first standards! 🎉")

        return results


def print_results(results: Dict):
    """Print formatted results"""
    score = results["score"]
    max_score = results["max_score"]

    print("=" * 60)
    print("LLM READINESS ASSESSMENT")
    print("=" * 60)

    # Overall score
    if score >= 80:
        status = "✅ PASS"
        color = ""
    elif score >= 60:
        status = "⚠️  NEEDS IMPROVEMENT"
        color = ""
    else:
        status = "❌ FAIL"
        color = ""

    print(f"Overall Score: {score}/{max_score} ({score/max_score:.1%}) - {status}")
    print()

    # Individual checks
    print("Detailed Results:")
    print("-" * 40)

    for check in results["checks"]:
        print(f"{check['message']}")

    print()
    print("Recommendations:")
    print("-" * 20)

    for i, rec in enumerate(results["recommendations"], 1):
        print(f"{i}. {rec}")

    print()
    print("=" * 60)


def main():
    """Main entry point"""
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."

    checker = LLMReadinessChecker(repo_root)
    results = checker.run_all_checks()

    print_results(results)

    # Exit with error code if score is below threshold
    threshold = 80
    if results["score"] < threshold:
        print(f"❌ Score {results['score']} is below threshold {threshold}")
        sys.exit(1)
    else:
        print(f"✅ Score {results['score']} meets threshold {threshold}")
        sys.exit(0)


if __name__ == "__main__":
    main()
