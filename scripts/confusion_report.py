#!/usr/bin/env python3
"""
title: Confusion Report - Cognitive Complexity Analyzer
purpose: Identify cognitive complexity hotspots and guide LLM-friendly refactoring
inputs: [{"name": "repo_root", "type": "path"}, {"name": "threshold_config", "type": "yaml"}]
outputs: [
  {"name": "confusion_report", "type": "json"},
  {"name": "recommendations", "type": "markdown"}
]
effects: ["analysis", "reporting", "recommendations"]
deps: ["ast", "pathlib", "json", "sys"]
owners: ["drapala"]
stability: stable
since_version: "0.3.0"
"""

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CodeComplexity:
    """Represents complexity metrics for a code unit."""

    file_path: str
    function_name: str | None
    line_range: str
    cyclomatic_complexity: int
    indirection_depth: int
    context_switches: int
    import_dependencies: int
    confusion_score: float


@dataclass
class RefactoringRecommendation:
    """Represents a specific refactoring recommendation."""

    type: str
    description: str
    affected_files: list[str]
    recommendation: str
    effort_estimate: str
    complexity_reduction: str


class CognitiveComplexityAnalyzer:
    """Advanced AST-based cognitive complexity analyzer for LLM-first development."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.complexity_threshold = 5.0
        self.hotspots: list[CodeComplexity] = []

    def analyze_file(self, file_path: Path) -> list[CodeComplexity]:
        """Analyze cognitive complexity of a Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            complexities = []

            # Analyze module-level complexity
            module_complexity = self._analyze_module(file_path, tree, content)
            complexities.append(module_complexity)

            # Analyze individual functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_complexity = self._analyze_function(file_path, node, content)
                    complexities.append(func_complexity)

            return complexities

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
            return []

    def _analyze_module(self, file_path: Path, tree: ast.AST, content: str) -> CodeComplexity:
        """Analyze module-level complexity metrics."""
        imports = len([n for n in ast.walk(tree) if isinstance(n, ast.Import | ast.ImportFrom)])
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])

        # Calculate context switches (class changes, function calls across modules)
        context_switches = self._count_context_switches(tree)

        # Calculate confusion score
        confusion_score = self._calculate_confusion_score(
            cyclomatic=classes + functions,
            indirection=imports,
            context_switches=context_switches,
            imports=imports,
        )

        return CodeComplexity(
            file_path=str(file_path.relative_to(self.repo_root)),
            function_name=None,
            line_range=f"1-{len(content.splitlines())}",
            cyclomatic_complexity=classes + functions,
            indirection_depth=imports,
            context_switches=context_switches,
            import_dependencies=imports,
            confusion_score=confusion_score,
        )

    def _analyze_function(
        self, file_path: Path, node: ast.FunctionDef, content: str
    ) -> CodeComplexity:
        """Analyze function-level complexity metrics."""
        # Calculate cyclomatic complexity (simplified)
        cyclomatic = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.Try | ast.With):
                cyclomatic += 1
            elif isinstance(child, ast.BoolOp):
                cyclomatic += len(child.values) - 1

        # Count nested levels
        indirection_depth = self._calculate_nesting_depth(node)

        # Count external calls (potential context switches)
        context_switches = len([n for n in ast.walk(node) if isinstance(n, ast.Call)])

        confusion_score = self._calculate_confusion_score(
            cyclomatic=cyclomatic,
            indirection=indirection_depth,
            context_switches=context_switches,
            imports=0,  # Function-level doesn't have imports
        )

        return CodeComplexity(
            file_path=str(file_path.relative_to(self.repo_root)),
            function_name=node.name,
            line_range=f"{node.lineno}-{node.end_lineno or node.lineno}",
            cyclomatic_complexity=cyclomatic,
            indirection_depth=indirection_depth,
            context_switches=context_switches,
            import_dependencies=0,
            confusion_score=confusion_score,
        )

    def _count_context_switches(self, tree: ast.AST) -> int:
        """Count potential context switches in the code."""
        switches = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # External function calls
                switches += 1
            elif isinstance(node, ast.Attribute):
                # Method calls or attribute access
                switches += 1
        return switches

    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a node."""
        max_depth = 0

        def _depth_visitor(n: ast.AST, current_depth: int = 0) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            for child in ast.iter_child_nodes(n):
                if isinstance(
                    child, ast.If | ast.While | ast.For | ast.Try | ast.With | ast.FunctionDef
                ):
                    _depth_visitor(child, current_depth + 1)
                else:
                    _depth_visitor(child, current_depth)

        _depth_visitor(node)
        return max_depth

    def _calculate_confusion_score(
        self, cyclomatic: int, indirection: int, context_switches: int, imports: int
    ) -> float:
        """Calculate overall confusion score for LLM agents."""
        # Weighted scoring based on LLM-first principles
        score = (
            cyclomatic * 0.3  # Branching complexity
            + indirection * 0.4  # Import/nesting depth
            + context_switches * 0.2  # Context switching cost
            + imports * 0.1  # Dependency complexity
        )
        return round(score, 2)


class HotspotDetector:
    """Identifies and ranks cognitive complexity hotspots."""

    def __init__(self, analyzer: CognitiveComplexityAnalyzer):
        self.analyzer = analyzer

    def detect_hotspots(self, threshold: float = 5.0) -> list[CodeComplexity]:
        """Find all complexity hotspots above threshold."""
        hotspots = []

        # Scan all Python files
        for py_file in self.analyzer.repo_root.rglob("*.py"):
            if self._should_analyze_file(py_file):
                complexities = self.analyzer.analyze_file(py_file)
                for complexity in complexities:
                    if complexity.confusion_score >= threshold:
                        hotspots.append(complexity)

        # Sort by confusion score (highest first)
        return sorted(hotspots, key=lambda x: x.confusion_score, reverse=True)

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if a file should be analyzed."""
        # Skip test files, cache directories, and other non-source files
        skip_patterns = ["test_", "_test.py", "__pycache__", ".pyc", "venv", ".git"]
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in skip_patterns)


class RefactoringAnalyzer:
    """Generates specific refactoring recommendations."""

    def __init__(self, hotspots: list[CodeComplexity]):
        self.hotspots = hotspots

    def generate_recommendations(self) -> list[RefactoringRecommendation]:
        """Generate actionable refactoring recommendations."""
        recommendations = []

        # Group hotspots by file for vertical slice opportunities
        file_groups = {}
        for hotspot in self.hotspots:
            file_path = hotspot.file_path
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(hotspot)

        # Generate recommendations based on patterns
        for file_path, hotspots in file_groups.items():
            if len(hotspots) > 2:
                recommendations.append(
                    RefactoringRecommendation(
                        type="vertical_slice_opportunity",
                        description=f"Multiple complexity hotspots in {file_path}",
                        affected_files=[file_path],
                        recommendation=f"Consider splitting {file_path} into focused modules",
                        effort_estimate="4-8 hours",
                        complexity_reduction="40-60%",
                    )
                )

        # Add specific function-level recommendations
        for hotspot in self.hotspots[:5]:  # Top 5 hotspots
            if hotspot.function_name and hotspot.confusion_score > 8:
                recommendations.append(
                    RefactoringRecommendation(
                        type="function_complexity",
                        description=f"High complexity in {hotspot.function_name}",
                        affected_files=[hotspot.file_path],
                        recommendation="Extract helper functions, reduce nesting",
                        effort_estimate="2-4 hours",
                        complexity_reduction="30-50%",
                    )
                )

        return recommendations


class ConfusionReporter:
    """Main confusion report generator."""

    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path.cwd()
        self.analyzer = CognitiveComplexityAnalyzer(self.repo_root)

    def generate_report(self, threshold: float = 5.0, verbose: bool = False) -> dict[str, Any]:
        """Generate comprehensive confusion analysis report."""
        detector = HotspotDetector(self.analyzer)
        hotspots = detector.detect_hotspots(threshold)

        refactoring_analyzer = RefactoringAnalyzer(hotspots)
        recommendations = refactoring_analyzer.generate_recommendations()

        # Calculate summary metrics
        total_files = sum(1 for _ in self.repo_root.rglob("*.py"))
        high_confusion_files = len({h.file_path for h in hotspots})
        avg_confusion = sum(h.confusion_score for h in hotspots) / len(hotspots) if hotspots else 0

        report = {
            "summary": {
                "total_files_analyzed": total_files,
                "high_confusion_files": high_confusion_files,
                "hotspot_functions": len([h for h in hotspots if h.function_name]),
                "overall_confusion_score": round(avg_confusion, 2),
                "refactoring_priority": (
                    "high" if avg_confusion > 7 else "medium" if avg_confusion > 4 else "low"
                ),
            },
            "hotspots": [asdict(h) for h in hotspots[:10]],  # Top 10 hotspots
            "architecture_recommendations": [asdict(r) for r in recommendations],
        }

        if verbose:
            from datetime import datetime

            report["detailed_analysis"] = {
                "threshold_used": threshold,
                "analysis_timestamp": datetime.now().isoformat(),
                "all_hotspots": [asdict(h) for h in hotspots],
            }

        return report

    def run_analysis(
        self,
        threshold: float = 5.0,
        verbose: bool = False,
        output_file: str | None = None,
        generate_plan: bool = False,
    ) -> int:
        """Run complete confusion analysis and output results."""
        report = self.generate_report(threshold, verbose)

        if generate_plan:
            self._generate_refactoring_plan(report, output_file or "refactoring_plan.md")
        else:
            output = json.dumps(report, indent=2)
            if output_file:
                with open(output_file, "w") as f:
                    f.write(output)
            else:
                print(output)

        # Return exit code based on confusion level
        avg_confusion = report["summary"]["overall_confusion_score"]
        if avg_confusion > 7:
            return 2  # High confusion
        elif avg_confusion > 4:
            return 1  # Medium confusion
        else:
            return 0  # Low confusion

    def _generate_refactoring_plan(self, report: dict[str, Any], output_file: str) -> None:
        """Generate markdown refactoring plan."""
        with open(output_file, "w") as f:
            f.write("# Refactoring Plan - LLM-First Architecture\n\n")
            f.write(
                f"**Overall Confusion Score:** {report['summary']['overall_confusion_score']}\n"
            )
            f.write(f"**Priority:** {report['summary']['refactoring_priority']}\n\n")

            f.write("## Top Complexity Hotspots\n\n")
            for hotspot in report["hotspots"][:5]:
                f.write(f"### {hotspot['file_path']}")
                if hotspot["function_name"]:
                    f.write(f" - {hotspot['function_name']}")
                f.write("\n")
                f.write(f"- **Confusion Score:** {hotspot['confusion_score']}\n")
                f.write(f"- **Lines:** {hotspot['line_range']}\n")
                f.write(f"- **Cyclomatic Complexity:** {hotspot['cyclomatic_complexity']}\n")
                f.write(f"- **Context Switches:** {hotspot['context_switches']}\n\n")

            f.write("## Architecture Recommendations\n\n")
            for rec in report["architecture_recommendations"]:
                f.write(f"### {rec['type'].replace('_', ' ').title()}\n")
                f.write(f"**Description:** {rec['description']}\n")
                f.write(f"**Recommendation:** {rec['recommendation']}\n")
                f.write(f"**Effort:** {rec['effort_estimate']}\n")
                f.write(f"**Complexity Reduction:** {rec['complexity_reduction']}\n\n")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Generate cognitive complexity confusion report")
    parser.add_argument(
        "--threshold", type=float, default=5.0, help="Confusion score threshold for hotspots"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Include detailed analysis in output"
    )
    parser.add_argument("--focus", type=str, help="Focus analysis on specific directory")
    parser.add_argument(
        "--plan", action="store_true", help="Generate refactoring plan instead of JSON"
    )
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--ci", action="store_true", help="CI mode with exit codes")
    parser.add_argument(
        "--max-confusion", type=float, default=7.0, help="Maximum acceptable confusion score for CI"
    )

    args = parser.parse_args()

    repo_root = Path(args.focus) if args.focus else Path.cwd()
    reporter = ConfusionReporter(repo_root)

    exit_code = reporter.run_analysis(
        threshold=args.threshold,
        verbose=args.verbose,
        output_file=args.output,
        generate_plan=args.plan,
    )

    if args.ci and exit_code > 0:
        print(f"❌ Confusion analysis failed with exit code {exit_code}", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
