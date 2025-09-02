#!/usr/bin/env python3
"""
title: Semantic Pattern Extractor
purpose: Extract semantic patterns and dependencies from parsed data
inputs: [{name: "parsed_files", type: "list[ParsedFile]"}]
outputs: [{name: "patterns", type: "SemanticPatterns"}]
effects: ["pattern_extraction", "dependency_analysis"]
deps: ["dataclasses", "collections", "pathlib"]
owners: ["drapala"]
stability: stable
since_version: "0.5.0"
complexity: medium
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from semantic_parser import ParsedFile


@dataclass
class DependencyGraph:
    """Dependency relationships between modules."""

    import_graph: dict[str, set[str]] = field(default_factory=dict)
    call_graph: dict[str, set[str]] = field(default_factory=dict)
    reverse_dependencies: dict[str, set[str]] = field(default_factory=dict)


@dataclass
class CallChain:
    """Call chain information."""

    function: str
    depth: int
    chain: list[str] = field(default_factory=list)


@dataclass
class CyclicDependency:
    """Cyclic dependency information."""

    cycle: list[str]
    type: str  # "import" or "call"


@dataclass
class SemanticPatterns:
    """Extracted semantic patterns from codebase."""

    dependency_graph: DependencyGraph
    call_chains: list[CallChain]
    cyclic_deps: list[CyclicDependency]
    hotspots: list[dict[str, Any]]
    feature_isolation: dict[str, float]


class SemanticExtractor:
    """Extract semantic patterns from parsed files."""

    def __init__(self):
        self.parsed_files: dict[str, ParsedFile] = {}
        self.patterns = SemanticPatterns(
            dependency_graph=DependencyGraph(),
            call_chains=[],
            cyclic_deps=[],
            hotspots=[],
            feature_isolation={},
        )

    def extract(self, parsed_files: list[ParsedFile]) -> SemanticPatterns:
        """Extract patterns from parsed files."""
        # Store parsed files
        for parsed in parsed_files:
            rel_path = str(parsed.file_path)
            self.parsed_files[rel_path] = parsed

        # Extract various patterns
        self._build_dependency_graph()
        self._extract_call_chains()
        self._detect_cycles()
        self._identify_hotspots()
        self._analyze_feature_isolation()

        return self.patterns

    def _build_dependency_graph(self) -> None:
        """Build import and call dependency graphs."""
        for file_path, parsed in self.parsed_files.items():
            # Build import graph
            imports = set()
            for import_info in parsed.imports:
                imports.add(import_info.module)
            if imports:
                self.patterns.dependency_graph.import_graph[file_path] = imports

                # Build reverse dependencies
                for module in imports:
                    if module not in self.patterns.dependency_graph.reverse_dependencies:
                        self.patterns.dependency_graph.reverse_dependencies[module] = set()
                    self.patterns.dependency_graph.reverse_dependencies[module].add(file_path)

            # Build call graph
            for func in parsed.functions:
                func_name = f"{file_path}::{func.name}"
                calls = set()

                for call in parsed.calls:
                    if call.caller == func.name:
                        if "::" in call.callee:
                            # External call
                            calls.add(call.callee)
                        else:
                            # Local call
                            calls.add(f"{file_path}::{call.callee}")

                if calls:
                    self.patterns.dependency_graph.call_graph[func_name] = calls

    def _extract_call_chains(self) -> None:
        """Extract call chain patterns."""
        visited = set()

        def trace_chain(func: str, chain: list[str], depth: int) -> int:
            """Trace call chain depth."""
            if func in visited or depth > 10:  # Limit depth to prevent infinite loops
                return depth

            visited.add(func)
            chain.append(func)
            max_depth = depth

            for called in self.patterns.dependency_graph.call_graph.get(func, []):
                new_chain = chain.copy()
                child_depth = trace_chain(called, new_chain, depth + 1)
                if child_depth > max_depth:
                    max_depth = child_depth
                    if child_depth > 3:  # Only track chains deeper than 3
                        self.patterns.call_chains.append(
                            CallChain(function=func, depth=child_depth, chain=new_chain)
                        )

            visited.remove(func)
            return max_depth

        # Start tracing from all functions
        for func in self.patterns.dependency_graph.call_graph:
            trace_chain(func, [], 0)

    def _detect_cycles(self) -> None:
        """Detect cyclic dependencies."""
        # Detect import cycles
        self._detect_import_cycles()

        # Detect call cycles
        self._detect_call_cycles()

    def _detect_import_cycles(self) -> None:
        """Detect cycles in import graph."""
        visited = set()
        rec_stack = set()

        def find_cycle(node: str, path: list[str]) -> bool:
            """Find cycles using DFS."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.patterns.dependency_graph.import_graph.get(node, []):
                if neighbor not in visited:
                    if find_cycle(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycle = path[cycle_start:] + [neighbor]
                    self.patterns.cyclic_deps.append(CyclicDependency(cycle=cycle, type="import"))
                    return True

            rec_stack.remove(node)
            return False

        for node in self.patterns.dependency_graph.import_graph:
            if node not in visited:
                find_cycle(node, [])

    def _detect_call_cycles(self) -> None:
        """Detect cycles in call graph."""
        visited = set()
        rec_stack = set()

        def find_cycle(func: str, path: list[str]) -> bool:
            """Find call cycles using DFS."""
            if func in rec_stack:
                # Found a cycle
                cycle_start = path.index(func) if func in path else 0
                cycle = path[cycle_start:] + [func]
                self.patterns.cyclic_deps.append(CyclicDependency(cycle=cycle, type="call"))
                return True

            if func in visited:
                return False

            visited.add(func)
            rec_stack.add(func)
            path.append(func)

            for called in self.patterns.dependency_graph.call_graph.get(func, []):
                if find_cycle(called, path.copy()):
                    return True

            rec_stack.remove(func)
            return False

        for func in self.patterns.dependency_graph.call_graph:
            if func not in visited:
                find_cycle(func, [])

    def _identify_hotspots(self) -> None:
        """Identify dependency hotspots."""
        dependency_counts = defaultdict(int)

        # Count incoming dependencies
        for module, deps in self.patterns.dependency_graph.reverse_dependencies.items():
            dependency_counts[module] = len(deps)

        # Sort by dependency count
        sorted_deps = sorted(dependency_counts.items(), key=lambda x: x[1], reverse=True)

        # Take top 20% as hotspots
        if sorted_deps:
            hotspot_count = max(1, len(sorted_deps) // 5)
            for module, count in sorted_deps[:hotspot_count]:
                if count > 2:  # Only consider modules with more than 2 dependencies
                    self.patterns.hotspots.append(
                        {
                            "module": module,
                            "dependency_count": count,
                            "risk_level": (
                                "high" if count > 10 else "medium" if count > 5 else "low"
                            ),
                        }
                    )

    def _analyze_feature_isolation(self) -> None:
        """Analyze feature isolation for VSA compliance."""
        feature_deps = defaultdict(lambda: {"internal": 0, "external": 0})

        for file_path, parsed in self.parsed_files.items():
            if "features/" in file_path:
                parts = file_path.split("/")
                if "features" in parts:
                    feature_idx = parts.index("features")
                    if feature_idx + 1 < len(parts):
                        feature_name = parts[feature_idx + 1]

                        # Count dependencies
                        for import_info in parsed.imports:
                            if import_info.module.startswith("features."):
                                if import_info.module.startswith(f"features.{feature_name}"):
                                    feature_deps[feature_name]["internal"] += 1
                                else:
                                    feature_deps[feature_name]["external"] += 1
                            else:
                                feature_deps[feature_name]["internal"] += 1

        # Calculate isolation scores
        for feature, deps in feature_deps.items():
            total = deps["internal"] + deps["external"]
            if total > 0:
                self.patterns.feature_isolation[feature] = deps["internal"] / total
            else:
                self.patterns.feature_isolation[feature] = 1.0


def extract_patterns(parsed_files: list[ParsedFile]) -> SemanticPatterns:
    """Extract semantic patterns from parsed files."""
    extractor = SemanticExtractor()
    return extractor.extract(parsed_files)
