#!/usr/bin/env python3
"""
LLM Readiness Score Calculator
Measures how well the repository is optimized for LLM agent effectiveness.
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path


class CognitiveComplexityAnalyzer:
    """Analyze cognitive complexity for LLM editability."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.call_graph = defaultdict(set)
        self.import_graph = defaultdict(set)

    def analyze_file(self, file_path: Path) -> dict[str, int]:
        """Analyze cognitive complexity metrics for a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            return {
                "cyclomatic": self._calculate_cyclomatic_complexity(tree),
                "indirection_depth": self._calculate_indirection_depth(tree),
                "context_switches": self._count_context_switches(tree),
                "mutation_surface": self._estimate_mutation_surface(tree),
            }
        except Exception:
            return {
                "cyclomatic": 0,
                "indirection_depth": 0,
                "context_switches": 0,
                "mutation_surface": 0,
            }

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.If
                | ast.While
                | ast.For
                | ast.AsyncFor
                | ast.ExceptHandler
                | ast.BoolOp
                | ast.Compare,
            ):
                complexity += 1

        return complexity

    def _calculate_indirection_depth(self, tree: ast.AST) -> int:
        """Calculate maximum call chain depth."""

        class CallDepthVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                self.max_depth = 0

            def visit_Call(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1

        visitor = CallDepthVisitor()
        visitor.visit(tree)
        return visitor.max_depth

    def _count_context_switches(self, tree: ast.AST) -> int:
        """Count cross-module references that require context switching."""
        context_switches = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Attribute access might indicate cross-module dependency
                context_switches += 1
            elif isinstance(node, ast.Import | ast.ImportFrom):
                # Each import represents a potential context switch
                context_switches += len(node.names) if hasattr(node, "names") else 1

        return context_switches

    def _estimate_mutation_surface(self, tree: ast.AST) -> int:
        """Estimate how many places could be affected by a change."""
        mutation_points = 0

        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.FunctionDef
                | ast.AsyncFunctionDef
                | ast.ClassDef
                | ast.Assign
                | ast.AugAssign
                | ast.AnnAssign,
            ):
                mutation_points += 1

        return mutation_points


class LLMReadinessChecker:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.score = 0
        self.max_score = 100
        self.checks = []
        self.cognitive_analyzer = CognitiveComplexityAnalyzer(self.repo_root)

    def check_co_location(self) -> tuple[int, str]:
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
        msg = f"{status} Co-location: {co_located_count}/{total_count} features "
        msg += f"({co_location_ratio:.1%})"
        return score, msg

    def check_cognitive_complexity(self) -> tuple[int, str]:
        """Check cognitive complexity across codebase (target: ≤5 avg complexity)"""
        try:
            total_complexity = 0
            total_indirection = 0
            total_context_switches = 0
            file_count = 0

            for py_file in self.repo_root.rglob("*.py"):
                # Skip test files and cache directories
                file_name = py_file.name
                if (
                    file_name.startswith("test_")
                    or file_name.endswith("_test.py")
                    or "__pycache__" in str(py_file)
                ):
                    continue

                metrics = self.cognitive_analyzer.analyze_file(py_file)
                total_complexity += metrics["cyclomatic"]
                total_indirection += metrics["indirection_depth"]
                total_context_switches += metrics["context_switches"]
                file_count += 1

            if file_count == 0:
                return 15, "⚠️  No Python files found to analyze"

            avg_complexity = total_complexity / file_count
            avg_indirection = total_indirection / file_count
            avg_context_switches = total_context_switches / file_count

            # Scoring based on cognitive load (lower is better for LLM)
            if avg_complexity <= 5 and avg_indirection <= 3 and avg_context_switches <= 10:
                score = 25
                status = "✅"
            elif avg_complexity <= 8 and avg_indirection <= 5 and avg_context_switches <= 15:
                score = 18
                status = "⚠️ "
            else:
                score = 8
                status = "❌"

            return score, (
                f"{status} Cognitive metrics - Complexity: {avg_complexity:.1f}, "
                f"Indirection: {avg_indirection:.1f}, Context switches: {avg_context_switches:.1f}"
            )

        except Exception as e:
            return 10, f"⚠️  Could not analyze cognitive complexity: {str(e)}"

    def check_front_matter_coverage(self) -> tuple[int, str]:
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
                with open(py_file, encoding="utf-8") as f:
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
        msg = f"{status} Front-matter coverage: {files_with_frontmatter}/{total_files} files "
        msg += f"({coverage:.1%})"
        return score, msg

    def check_documentation_structure(self) -> tuple[int, str]:
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

    def check_adr_structure(self) -> tuple[int, str]:
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
                with open(adr_file, encoding="utf-8") as f:
                    content = f.read()
                    if "adr_number:" in content and "status:" in content:
                        valid_adrs += 1
            except Exception:
                continue

        if valid_adrs >= len(adr_files) * 0.8:  # 80% have proper structure
            return 10, f"✅ ADR structure: {valid_adrs}/{len(adr_files)} properly formatted"
        else:
            return 5, f"⚠️  ADR structure: {valid_adrs}/{len(adr_files)} properly formatted"

    def run_all_checks(self) -> dict:
        """Run all readiness checks and return results"""
        results = {"score": 0, "max_score": self.max_score, "checks": [], "recommendations": []}

        # Run individual checks
        checks_to_run = [
            ("Co-location Index", self.check_co_location),
            ("Cognitive Complexity", self.check_cognitive_complexity),
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


def print_results(results: dict):
    """Print formatted results"""
    score = results["score"]
    max_score = results["max_score"]

    print("=" * 60)
    print("LLM READINESS ASSESSMENT")
    print("=" * 60)

    # Overall score
    if score >= 80:
        status = "✅ PASS"
    elif score >= 60:
        status = "⚠️  NEEDS IMPROVEMENT"
    else:
        status = "❌ FAIL"

    print(f"Overall Score: {score}/{max_score} ({score / max_score:.1%}) - {status}")
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
