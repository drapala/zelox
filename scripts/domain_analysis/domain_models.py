#!/usr/bin/env python3
"""
---
title: Domain Models Extractor
purpose: Extract domain entities and concepts from code
inputs:
  - name: file_path
    type: Path
outputs:
  - name: domain_terms
    type: set[str]
  - name: class_names
    type: set[str]
  - name: method_names
    type: set[str]
effects: []
deps: ["ast", "re", "pathlib"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
---
"""

import ast
import re
from pathlib import Path
from typing import Any


class DomainLanguageExtractor(ast.NodeVisitor):
    """Extract domain concepts from code using AST analysis."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.domain_terms: set[str] = set()
        self.class_names: set[str] = set()
        self.method_names: set[str] = set()
        self.variable_names: set[str] = set()
        self.string_literals: set[str] = set()
        self.comments: set[str] = set()

    def visit_ClassDef(self, node):
        """Extract class names as domain concepts."""
        self.class_names.add(node.name)
        self.domain_terms.add(node.name)

        docstring = ast.get_docstring(node)
        if docstring:
            self._extract_from_docstring(docstring)

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Extract function names and analyze parameters."""
        self.method_names.add(node.name)
        self._extract_domain_terms_from_name(node.name)

        for arg in node.args.args:
            self.variable_names.add(arg.arg)
            self._extract_domain_terms_from_name(arg.arg)

        docstring = ast.get_docstring(node)
        if docstring:
            self._extract_from_docstring(docstring)

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Extract variable names from assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variable_names.add(target.id)
                self._extract_domain_terms_from_name(target.id)

        self.generic_visit(node)

    def visit_Str(self, node):
        """Extract meaningful string literals."""
        value = node.value if hasattr(node, "value") else node.s
        if 3 < len(value) < 50 and not self._is_technical_string(value):
            self.string_literals.add(value)

    def visit_Constant(self, node):
        """Handle string constants in newer Python versions."""
        if isinstance(node.value, str):
            self.visit_Str(node)

    def _extract_domain_terms_from_name(self, name: str) -> None:
        """Extract domain terms from camelCase or snake_case names."""
        camel_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", name)
        for part in camel_parts:
            if len(part) > 2:
                self.domain_terms.add(part.lower())

        snake_parts = name.split("_")
        for part in snake_parts:
            if len(part) > 2:
                self.domain_terms.add(part.lower())

    def _extract_from_docstring(self, docstring: str) -> None:
        """Extract domain terms from docstrings."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", docstring)
        for word in words:
            word_lower = word.lower()
            if not self._is_technical_word(word_lower):
                self.domain_terms.add(word_lower)

    def _is_technical_string(self, s: str) -> bool:
        """Check if string is likely technical/non-domain."""
        patterns = [
            r"^https?://",
            r"\.(py|js|html|css|json)$",
            r"^[A-Z_]+$",
            r"^\d+$",
        ]
        return any(re.match(p, s) for p in patterns)

    def _is_technical_word(self, word: str) -> bool:
        """Check if word is likely technical/non-domain."""
        technical = {
            "def",
            "class",
            "import",
            "from",
            "return",
            "self",
            "true",
            "false",
            "none",
            "str",
            "int",
            "list",
            "dict",
            "set",
            "tuple",
            "bool",
            "async",
            "await",
            "try",
            "except",
            "finally",
            "with",
            "lambda",
            "function",
            "method",
            "parameter",
            "argument",
            "variable",
            "string",
            "number",
            "boolean",
            "object",
            "array",
            "collection",
            "init",
            "main",
            "args",
            "kwargs",
            "config",
            "logger",
        }
        return word in technical or len(word) < 3


def extract_domain_language(file_path: Path) -> dict[str, Any]:
    """Extract domain language from a Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        extractor = DomainLanguageExtractor(file_path)
        extractor.visit(tree)

        return {
            "domain_terms": extractor.domain_terms,
            "classes": extractor.class_names,
            "methods": extractor.method_names,
            "variables": extractor.variable_names,
            "string_literals": extractor.string_literals,
        }
    except Exception as e:
        raise RuntimeError(f"Failed to extract from {file_path}: {e}")


def extract_feature_name(file_path: str) -> str | None:
    """Extract feature name from file path."""
    parts = file_path.split("/")
    if "features" in parts:
        idx = parts.index("features")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None
