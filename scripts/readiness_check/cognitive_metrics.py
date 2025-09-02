"""
Cognitive Complexity Metrics
Analyze cognitive load and complexity for LLM editability.
"""

import ast
from pathlib import Path

from .readiness_metrics import MetricPlugin, MetricResult, ReadinessMetric


class CognitiveComplexityMetric(MetricPlugin):
    """Metric for cognitive complexity analysis."""

    @property
    def metric_definition(self) -> ReadinessMetric:
        return ReadinessMetric(
            name="Cognitive Complexity",
            weight=25.0,
            target_threshold=5.0,
            description="Average cognitive complexity across codebase",
            category="complexity",
        )

    def calculate(self) -> MetricResult:
        """Calculate average cognitive complexity."""
        metrics = self._analyze_codebase()

        if metrics["file_count"] == 0:
            return MetricResult(
                score=15,
                max_score=25,
                status="⚠️",
                message="No Python files found to analyze",
            )

        avg_complexity = metrics["total_complexity"] / metrics["file_count"]
        avg_indirection = metrics["total_indirection"] / metrics["file_count"]
        avg_switches = metrics["total_switches"] / metrics["file_count"]

        # Score based on thresholds
        score = self._calculate_score(avg_complexity, avg_indirection, avg_switches)
        status = self._get_complexity_status(avg_complexity, avg_indirection, avg_switches)

        return MetricResult(
            score=score,
            max_score=self.metric_definition.weight,
            status=status,
            message=(
                f"Complexity: {avg_complexity:.1f}, "
                f"Indirection: {avg_indirection:.1f}, "
                f"Context switches: {avg_switches:.1f}"
            ),
            details={
                "avg_complexity": avg_complexity,
                "avg_indirection": avg_indirection,
                "avg_context_switches": avg_switches,
                "file_count": metrics["file_count"],
            },
        )

    def _analyze_codebase(self) -> dict:
        """Analyze all Python files in codebase."""
        metrics = {
            "total_complexity": 0,
            "total_indirection": 0,
            "total_switches": 0,
            "file_count": 0,
        }

        for py_file in self.repo_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            file_metrics = self._analyze_file(py_file)
            metrics["total_complexity"] += file_metrics["cyclomatic"]
            metrics["total_indirection"] += file_metrics["indirection"]
            metrics["total_switches"] += file_metrics["context_switches"]
            metrics["file_count"] += 1

        return metrics

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ["test_", "_test.py", "__pycache__", ".venv", "venv", "migrations"]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path) -> dict:
        """Analyze a single Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            return {
                "cyclomatic": self._calculate_cyclomatic(tree),
                "indirection": self._calculate_indirection(tree),
                "context_switches": self._count_context_switches(tree),
            }
        except Exception:
            return {"cyclomatic": 0, "indirection": 0, "context_switches": 0}

    def _calculate_cyclomatic(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        decision_nodes = (
            ast.If,
            ast.While,
            ast.For,
            ast.AsyncFor,
            ast.ExceptHandler,
            ast.BoolOp,
        )

        for node in ast.walk(tree):
            if isinstance(node, decision_nodes):
                complexity += 1

        return complexity

    def _calculate_indirection(self, tree: ast.AST) -> int:
        """Calculate maximum call chain depth."""

        class CallDepthVisitor(ast.NodeVisitor):
            def __init__(self):
                self.depth = 0
                self.max_depth = 0

            def visit_Call(self, node):
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
                self.generic_visit(node)
                self.depth -= 1

        visitor = CallDepthVisitor()
        visitor.visit(tree)
        return visitor.max_depth

    def _count_context_switches(self, tree: ast.AST) -> int:
        """Count potential context switches."""
        switches = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                switches += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                switches += len(getattr(node, "names", [1]))
        return switches

    def _calculate_score(
        self, avg_complexity: float, avg_indirection: float, avg_switches: float
    ) -> float:
        """Calculate score based on complexity metrics."""
        if avg_complexity <= 5 and avg_indirection <= 3 and avg_switches <= 10:
            return 25
        elif avg_complexity <= 8 and avg_indirection <= 5 and avg_switches <= 15:
            return 18
        elif avg_complexity <= 12 and avg_indirection <= 7 and avg_switches <= 20:
            return 10
        return 5

    def _get_complexity_status(
        self, avg_complexity: float, avg_indirection: float, avg_switches: float
    ) -> str:
        """Get status emoji based on complexity."""
        if avg_complexity <= 5 and avg_indirection <= 3 and avg_switches <= 10:
            return "✅"
        elif avg_complexity <= 8 and avg_indirection <= 5 and avg_switches <= 15:
            return "⚠️"
        return "❌"
