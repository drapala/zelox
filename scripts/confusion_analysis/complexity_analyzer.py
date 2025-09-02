"""
---
title: Complexity Analyzer
purpose: Measure code complexity metrics
inputs:
  - name: ast_tree
    type: ast.AST
outputs:
  - name: metrics
    type: ComplexityMetrics
effects: []
deps: ['ast']
owners: ['llm-architect']
stability: stable
since_version: 1.0.0
---

Analyzes AST to calculate complexity metrics.
"""

import ast
from dataclasses import dataclass
from functools import lru_cache

# Constants for thresholds
MAX_COMPLEXITY = 10
MAX_INDIRECTION = 3
MAX_CONTEXT_SWITCHES = 100
MAX_LINES = 200


@dataclass
class ComplexityMetrics:
    """Stores complexity metrics for analysis."""

    cyclomatic_complexity: int = 0
    indirection_depth: int = 0
    context_switches: int = 0
    lines_of_code: int = 0
    cognitive_complexity: int = 0


class ComplexityAnalyzer:
    """Analyzes code complexity using AST."""

    @staticmethod
    @lru_cache(maxsize=128)
    def analyze(content: str) -> ComplexityMetrics:
        """Analyze content and return complexity metrics."""
        try:
            tree = ast.parse(content)
            return ComplexityAnalyzer._calculate_metrics(tree, content)
        except SyntaxError:
            return ComplexityMetrics()

    @staticmethod
    def _calculate_metrics(tree: ast.AST, content: str) -> ComplexityMetrics:
        """Calculate all complexity metrics."""
        return ComplexityMetrics(
            cyclomatic_complexity=ComplexityAnalyzer._cyclomatic(tree),
            indirection_depth=ComplexityAnalyzer._indirection(tree),
            context_switches=ComplexityAnalyzer._context_switches(tree),
            lines_of_code=len(content.splitlines()),
            cognitive_complexity=ComplexityAnalyzer._cognitive(tree),
        )

    @staticmethod
    def _cyclomatic(tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.Match):
                complexity += len(node.cases)
        return complexity

    @staticmethod
    def _indirection(tree: ast.AST) -> int:
        """Calculate maximum indirection depth."""
        visitor = DepthVisitor()
        visitor.visit(tree)
        return visitor.max_depth

    @staticmethod
    def _context_switches(tree: ast.AST) -> int:
        """Count context switches in code."""
        switches = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                switches += 5
            elif isinstance(node, ast.Call):
                switches += 2
            elif isinstance(node, ast.Attribute):
                switches += 1
        return switches

    @staticmethod
    def _cognitive(tree: ast.AST) -> int:
        """Calculate cognitive complexity."""
        visitor = CognitiveVisitor()
        visitor.visit(tree)
        return visitor.complexity


class DepthVisitor(ast.NodeVisitor):
    """Visitor to calculate indirection depth."""

    def __init__(self):
        self.depth = 0
        self.max_depth = 0

    def _enter(self):
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)

    def _exit(self):
        self.depth -= 1

    def visit_FunctionDef(self, node):
        self._enter()
        self.generic_visit(node)
        self._exit()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self._enter()
        self.generic_visit(node)
        self._exit()


class CognitiveVisitor(ast.NodeVisitor):
    """Visitor to calculate cognitive complexity."""

    def __init__(self):
        self.complexity = 0
        self.nesting = 0

    def visit_If(self, node):
        self.complexity += 1 + self.nesting
        self.nesting += 1
        self.generic_visit(node)
        self.nesting -= 1

    def visit_For(self, node):
        self.complexity += 1 + self.nesting
        self.nesting += 1
        self.generic_visit(node)
        self.nesting -= 1

    def visit_While(self, node):
        self.complexity += 1 + self.nesting
        self.nesting += 1
        self.generic_visit(node)
        self.nesting -= 1
