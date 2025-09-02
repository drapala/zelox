#!/usr/bin/env python3
"""
title: Semantic Parser
purpose: Parse Python files and extract semantic elements
inputs: [{name: "file_path", type: "Path"}]
outputs: [{name: "parsed_data", type: "ParsedFile"}]
effects: ["ast_parsing"]
deps: ["ast", "pathlib", "dataclasses"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: low
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FunctionInfo:
    """Information about a function."""

    name: str
    line_number: int
    is_async: bool = False
    parent_class: str | None = None


@dataclass
class ImportInfo:
    """Information about an import."""

    module: str
    line_number: int
    alias: str | None = None


@dataclass
class CallInfo:
    """Information about a function call."""

    caller: str
    callee: str
    line_number: int


@dataclass
class ParsedFile:
    """Parsed semantic elements from a file."""

    file_path: Path
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: dict[str, list[str]] = field(default_factory=dict)
    imports: list[ImportInfo] = field(default_factory=list)
    calls: list[CallInfo] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)


class SemanticParser(ast.NodeVisitor):
    """Parse semantic elements from Python AST."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.parsed = ParsedFile(file_path=file_path)
        self.current_function: str | None = None
        self.current_class: str | None = None

    def parse(self) -> ParsedFile:
        """Parse the file and return semantic elements."""
        try:
            content = self.file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(self.file_path))
            self.visit(tree)
        except SyntaxError as e:
            self.parsed.parse_errors.append(f"Syntax error: {e}")
        except Exception as e:
            self.parsed.parse_errors.append(f"Parse error: {e}")

        return self.parsed

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._handle_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._handle_function(node, is_async=True)

    def _handle_function(self, node, is_async: bool) -> None:
        """Handle function definition."""
        func_info = FunctionInfo(
            name=node.name,
            line_number=node.lineno,
            is_async=is_async,
            parent_class=self.current_class,
        )
        self.parsed.functions.append(func_info)

        # Update class methods tracking
        if self.current_class:
            if self.current_class not in self.parsed.classes:
                self.parsed.classes[self.current_class] = []
            self.parsed.classes[self.current_class].append(node.name)

        # Track current function for call analysis
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name

        if node.name not in self.parsed.classes:
            self.parsed.classes[node.name] = []

        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call."""
        if not self.current_function:
            self.generic_visit(node)
            return

        callee = self._extract_call_name(node)
        if callee:
            call_info = CallInfo(
                caller=self.current_function, callee=callee, line_number=node.lineno
            )
            self.parsed.calls.append(call_info)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            import_info = ImportInfo(module=alias.name, line_number=node.lineno, alias=alias.asname)
            self.parsed.imports.append(import_info)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statement."""
        if node.module:
            import_info = ImportInfo(module=node.module, line_number=node.lineno, alias=None)
            self.parsed.imports.append(import_info)
        self.generic_visit(node)

    def _extract_call_name(self, node: ast.Call) -> str | None:
        """Extract the name of called function."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return None


def parse_file(file_path: Path) -> ParsedFile:
    """Parse a Python file and extract semantic elements."""
    parser = SemanticParser(file_path)
    return parser.parse()
