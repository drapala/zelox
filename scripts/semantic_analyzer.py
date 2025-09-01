#!/usr/bin/env python3
"""
title: Semantic Dependency Analyzer
purpose: Trace actual call chains and semantic dependencies beyond simple imports
inputs: [{"name": "codebase_path", "type": "path"}]
outputs: [
  {"name": "dependency_graph", "type": "json"}, 
  {"name": "complexity_report", "type": "dict"}
]
effects: ["ast_analysis", "graph_generation"]
deps: ["ast", "json", "networkx", "pathlib"]
owners: ["drapala"]
stability: experimental
since_version: "0.4.0"
"""

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


class CallChainAnalyzer(ast.NodeVisitor):
    """Analyze call chains and method dependencies within a file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.function_calls = defaultdict(set)  # function -> set of called functions
        self.method_calls = defaultdict(set)  # method -> set of called methods
        self.class_methods = defaultdict(set)  # class -> set of methods
        self.current_function = None
        self.current_class = None
        self.external_calls = set()  # Calls to external modules

    def visit_FunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name

        if self.current_class:
            self.class_methods[self.current_class].add(node.name)

        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        if self.current_function:
            call_name = self._extract_call_name(node)
            if call_name:
                if "." in call_name:
                    # External or method call
                    self.external_calls.add(call_name)
                else:
                    # Local function call
                    self.function_calls[self.current_function].add(call_name)

        self.generic_visit(node)

    def _extract_call_name(self, node: ast.Call) -> str | None:
        """Extract the name of the called function/method."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            else:
                return node.func.attr
        return None


class SemanticDependencyAnalyzer:
    """Analyze semantic dependencies across the codebase."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.file_dependencies = {}  # file -> CallChainAnalyzer
        self.import_graph = defaultdict(set)  # module -> imported modules
        self.call_graph = defaultdict(set)  # function -> called functions
        self.complexity_metrics = {}

    def analyze_codebase(self) -> dict[str, Any]:
        """Perform full semantic analysis of the codebase."""
        print("Analyzing codebase semantic dependencies...")

        # Step 1: Analyze individual files
        python_files = list(self.repo_root.rglob("*.py"))
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                self._analyze_file(py_file)
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}", file=sys.stderr)

        # Step 2: Build global dependency graph
        self._build_global_graph()

        # Step 3: Calculate complexity metrics
        self._calculate_complexity_metrics()

        return {
            "files_analyzed": len(self.file_dependencies),
            "total_functions": sum(
                len(analyzer.function_calls) for analyzer in self.file_dependencies.values()
            ),
            "complexity_metrics": self.complexity_metrics,
            "architectural_insights": self._generate_insights(),
        }

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = CallChainAnalyzer(file_path)
            analyzer.visit(tree)

            # Store results
            rel_path = str(file_path.relative_to(self.repo_root))
            self.file_dependencies[rel_path] = analyzer

            # Extract imports for dependency graph
            self._extract_imports(tree, rel_path)

        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)

    def _extract_imports(self, tree: ast.AST, file_path: str) -> None:
        """Extract import statements from AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.import_graph[file_path].add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                self.import_graph[file_path].add(node.module)

    def _build_global_graph(self) -> None:
        """Build global call graph across files."""
        for file_path, analyzer in self.file_dependencies.items():
            # Add internal function calls to global graph
            for func, calls in analyzer.function_calls.items():
                full_func_name = f"{file_path}::{func}"
                for called_func in calls:
                    full_called_name = f"{file_path}::{called_func}"
                    self.call_graph[full_func_name].add(full_called_name)

    def _calculate_complexity_metrics(self) -> None:
        """Calculate various complexity metrics."""
        self.complexity_metrics = {
            "average_imports_per_file": self._avg_imports_per_file(),
            "max_call_chain_depth": self._max_call_chain_depth(),
            "cyclic_dependencies": self._detect_cycles(),
            "hotspot_files": self._identify_hotspots(),
            "isolation_score": self._calculate_isolation_score(),
        }

    def _avg_imports_per_file(self) -> float:
        """Calculate average imports per file."""
        if not self.import_graph:
            return 0.0
        return sum(len(imports) for imports in self.import_graph.values()) / len(self.import_graph)

    def _max_call_chain_depth(self) -> int:
        """Find maximum call chain depth using DFS."""
        max_depth = 0
        visited = set()

        def dfs_depth(func_name: str, current_depth: int) -> int:
            if func_name in visited:
                return current_depth

            visited.add(func_name)
            max_local_depth = current_depth

            for called_func in self.call_graph.get(func_name, []):
                depth = dfs_depth(called_func, current_depth + 1)
                max_local_depth = max(max_local_depth, depth)

            visited.remove(func_name)
            return max_local_depth

        for func in self.call_graph:
            depth = dfs_depth(func, 0)
            max_depth = max(max_depth, depth)

        return max_depth

    def _detect_cycles(self) -> list[list[str]]:
        """Detect cyclic dependencies in import graph."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs_cycle(node: str, path: list[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.import_graph.get(node, []):
                if neighbor not in visited:
                    if dfs_cycle(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True

            rec_stack.remove(node)
            return False

        for node in self.import_graph:
            if node not in visited:
                dfs_cycle(node, [])

        return cycles

    def _identify_hotspots(self) -> list[dict[str, Any]]:
        """Identify files that are heavily depended upon."""
        dependency_counts = defaultdict(int)

        # Count incoming dependencies
        for _file_path, imports in self.import_graph.items():
            for imported_module in imports:
                dependency_counts[imported_module] += 1

        # Find hotspots (top 20% most referenced)
        sorted_deps = sorted(dependency_counts.items(), key=lambda x: x[1], reverse=True)
        hotspot_count = max(1, len(sorted_deps) // 5)  # Top 20%

        hotspots = []
        for module, count in sorted_deps[:hotspot_count]:
            hotspots.append(
                {
                    "module": module,
                    "dependency_count": count,
                    "risk_level": "high" if count > 10 else "medium",
                }
            )

        return hotspots

    def _calculate_isolation_score(self) -> float:
        """Calculate how well features are isolated (VSA compliance)."""
        features_dir = self.repo_root / "features"
        if not features_dir.exists():
            return 0.0

        feature_dirs = [d for d in features_dir.iterdir() if d.is_dir()]
        if not feature_dirs:
            return 0.0

        cross_feature_deps = 0
        total_deps = 0

        for file_path, imports in self.import_graph.items():
            if "features/" in file_path:
                # Extract feature name
                parts = file_path.split("/")
                if "features" in parts:
                    feature_idx = parts.index("features")
                    if feature_idx + 1 < len(parts):
                        current_feature = parts[feature_idx + 1]

                        for imported_module in imports:
                            total_deps += 1
                            # Check if import is to different feature
                            if (
                                imported_module.startswith("features.")
                                and imported_module != f"features.{current_feature}"
                            ):
                                cross_feature_deps += 1

        if total_deps == 0:
            return 1.0

        return 1.0 - (cross_feature_deps / total_deps)

    def _generate_insights(self) -> list[str]:
        """Generate architectural insights based on analysis."""
        insights = []

        metrics = self.complexity_metrics

        if metrics["average_imports_per_file"] > 8:
            insights.append("High import coupling detected - consider reducing dependencies")

        if metrics["max_call_chain_depth"] > 6:
            insights.append("Deep call chains detected - may impact LLM comprehension")

        if metrics["cyclic_dependencies"]:
            insights.append(
                f"Cyclic dependencies found: {len(metrics['cyclic_dependencies'])} cycles"
            )

        if metrics["isolation_score"] < 0.8:
            insights.append("Poor feature isolation - consider strengthening VSA boundaries")

        if metrics["hotspot_files"]:
            high_risk_hotspots = [h for h in metrics["hotspot_files"] if h["risk_level"] == "high"]
            if high_risk_hotspots:
                insights.append(
                    f"High-risk dependency hotspots detected: {len(high_risk_hotspots)} files"
                )

        return insights

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        name = file_path.name
        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or "__pycache__" in str(file_path)
            or name.startswith(".")
        )

    def export_graph(self, output_path: str) -> None:
        """Export dependency graph to JSON."""
        graph_data = {
            "import_graph": {k: list(v) for k, v in self.import_graph.items()},
            "call_graph": {k: list(v) for k, v in self.call_graph.items()},
            "complexity_metrics": self.complexity_metrics,
            "file_details": {},
        }

        # Add file-level details
        for file_path, analyzer in self.file_dependencies.items():
            graph_data["file_details"][file_path] = {
                "functions": list(analyzer.function_calls.keys()),
                "external_calls": list(analyzer.external_calls),
                "classes": list(analyzer.class_methods.keys()),
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)


def main():
    """CLI interface for semantic analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Dependency Analysis")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--report", action="store_true", help="Print analysis report")

    args = parser.parse_args()

    analyzer = SemanticDependencyAnalyzer(args.repo_root)
    results = analyzer.analyze_codebase()

    if args.report:
        print("=== Semantic Dependency Analysis Report ===")
        print(f"Files analyzed: {results['files_analyzed']}")
        print(f"Total functions: {results['total_functions']}")
        print()

        metrics = results["complexity_metrics"]
        print("Complexity Metrics:")
        print(f"  Average imports per file: {metrics['average_imports_per_file']:.1f}")
        print(f"  Max call chain depth: {metrics['max_call_chain_depth']}")
        print(f"  Cyclic dependencies: {len(metrics['cyclic_dependencies'])}")
        print(f"  Isolation score: {metrics['isolation_score']:.2f}")
        print(f"  Hotspot files: {len(metrics['hotspot_files'])}")
        print()

        if results["architectural_insights"]:
            print("Architectural Insights:")
            for insight in results["architectural_insights"]:
                print(f"  - {insight}")

    if args.output:
        analyzer.export_graph(args.output)
        print(f"Graph exported to {args.output}")


if __name__ == "__main__":
    main()
