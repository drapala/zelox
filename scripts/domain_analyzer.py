#!/usr/bin/env python3
"""
title: Domain Pattern Detector
purpose: Extract ubiquitous language and detect bounded context violations
inputs: [{"name": "codebase_path", "type": "path"}]
outputs: [
  {"name": "domain_report", "type": "dict"}, 
  {"name": "vsa_recommendations", "type": "list"}
]
effects: ["nlp_analysis", "domain_modeling"]
deps: ["ast", "re", "collections", "pathlib"]
owners: ["drapala"]
stability: experimental
since_version: "0.4.0"
"""

import ast
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


class DomainLanguageExtractor(ast.NodeVisitor):
    """Extract domain concepts from code using AST analysis."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.domain_terms = set()
        self.class_names = set()
        self.method_names = set()
        self.variable_names = set()
        self.string_literals = set()
        self.comments = set()

    def visit_ClassDef(self, node):
        """Extract class names as domain concepts."""
        self.class_names.add(node.name)
        self.domain_terms.add(node.name)

        # Extract from docstring
        if ast.get_docstring(node):
            self._extract_from_docstring(ast.get_docstring(node))

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Extract function names and analyze parameters."""
        self.method_names.add(node.name)
        self._extract_domain_terms_from_name(node.name)

        # Extract parameter names
        for arg in node.args.args:
            self.variable_names.add(arg.arg)
            self._extract_domain_terms_from_name(arg.arg)

        # Extract from docstring
        if ast.get_docstring(node):
            self._extract_from_docstring(ast.get_docstring(node))

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
        if len(node.s) > 3 and len(node.s) < 50 and not self._is_technical_string(node.s):
            self.string_literals.add(node.s)

    def visit_Constant(self, node):
        """Handle string constants in newer Python versions."""
        if isinstance(node.value, str):
            self.visit_Str(node)

    def _extract_domain_terms_from_name(self, name: str) -> None:
        """Extract domain terms from camelCase or snake_case names."""
        # Split camelCase
        camel_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\\d|\\W|$)|\\d+", name)
        for part in camel_parts:
            if len(part) > 2:  # Filter out short words
                self.domain_terms.add(part.lower())

        # Split snake_case
        snake_parts = name.split("_")
        for part in snake_parts:
            if len(part) > 2:
                self.domain_terms.add(part.lower())

    def _extract_from_docstring(self, docstring: str) -> None:
        """Extract domain terms from docstrings."""
        # Remove common technical words and extract meaningful terms
        words = re.findall(r"\\b[a-zA-Z]{3,}\\b", docstring)
        for word in words:
            word_lower = word.lower()
            if not self._is_technical_word(word_lower):
                self.domain_terms.add(word_lower)

    def _is_technical_string(self, s: str) -> bool:
        """Check if string is likely technical/non-domain."""
        technical_patterns = [
            r"^https?://",
            r"\\.(py|js|html|css|json)$",
            r"^[A-Z_]+$",  # Constants
            r"^\\d+$",  # Numbers
        ]
        return any(re.match(pattern, s) for pattern in technical_patterns)

    def _is_technical_word(self, word: str) -> bool:
        """Check if word is likely technical/non-domain."""
        technical_words = {
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
        }
        return word in technical_words or len(word) < 3


class BoundedContextAnalyzer:
    """Analyze bounded contexts and suggest VSA improvements."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.file_domains = {}  # file -> domain terms
        self.feature_domains = {}  # feature -> aggregated domain terms
        self.cross_domain_violations = []

    def analyze_domain_boundaries(self) -> dict[str, Any]:
        """Analyze domain boundaries and VSA compliance."""
        print("Analyzing domain boundaries...")

        # Step 1: Extract domain language from all files
        self._extract_domain_language()

        # Step 2: Aggregate by features
        self._aggregate_feature_domains()

        # Step 3: Detect boundary violations
        self._detect_boundary_violations()

        # Step 4: Generate recommendations
        recommendations = self._generate_vsa_recommendations()

        return {
            "files_analyzed": len(self.file_domains),
            "feature_domains": self.feature_domains,
            "boundary_violations": len(self.cross_domain_violations),
            "domain_coherence_score": self._calculate_coherence_score(),
            "recommendations": recommendations,
        }

    def _extract_domain_language(self) -> None:
        """Extract domain language from all Python files."""
        python_files = list(self.repo_root.rglob("*.py"))

        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                extractor = DomainLanguageExtractor(py_file)
                extractor.visit(tree)

                rel_path = str(py_file.relative_to(self.repo_root))
                self.file_domains[rel_path] = {
                    "domain_terms": extractor.domain_terms,
                    "classes": extractor.class_names,
                    "methods": extractor.method_names,
                    "feature": self._extract_feature_name(rel_path),
                }

            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}", file=sys.stderr)

    def _aggregate_feature_domains(self) -> None:
        """Aggregate domain terms by feature."""
        for file_path, domain_data in self.file_domains.items():
            feature = domain_data["feature"]
            if not feature:
                continue

            if feature not in self.feature_domains:
                self.feature_domains[feature] = {
                    "domain_terms": Counter(),
                    "classes": set(),
                    "files": [],
                }

            self.feature_domains[feature]["domain_terms"].update(domain_data["domain_terms"])
            self.feature_domains[feature]["classes"].update(domain_data["classes"])
            self.feature_domains[feature]["files"].append(file_path)

    def _detect_boundary_violations(self) -> None:
        """Detect potential bounded context violations."""
        # Look for shared domain terms across features
        all_terms_by_feature = {}
        for feature, data in self.feature_domains.items():
            all_terms_by_feature[feature] = set(data["domain_terms"].keys())

        # Find overlapping domain terms
        for feature1, terms1 in all_terms_by_feature.items():
            for feature2, terms2 in all_terms_by_feature.items():
                if feature1 >= feature2:  # Avoid duplicates
                    continue

                overlap = terms1.intersection(terms2)
                if len(overlap) > 3:  # Significant overlap
                    self.cross_domain_violations.append(
                        {
                            "feature1": feature1,
                            "feature2": feature2,
                            "shared_terms": list(overlap),
                            "overlap_score": len(overlap) / min(len(terms1), len(terms2)),
                        }
                    )

    def _calculate_coherence_score(self) -> float:
        """Calculate domain coherence score (0-1)."""
        if not self.feature_domains:
            return 0.0

        total_coherence = 0.0
        feature_count = len(self.feature_domains)

        for _feature, data in self.feature_domains.items():
            # Coherence based on term frequency distribution
            term_counts = list(data["domain_terms"].values())
            if not term_counts:
                continue

            # Higher coherence if terms are used consistently
            max_count = max(term_counts)
            avg_count = sum(term_counts) / len(term_counts)
            coherence = avg_count / max_count if max_count > 0 else 0
            total_coherence += coherence

        return total_coherence / feature_count if feature_count > 0 else 0.0

    def _generate_vsa_recommendations(self) -> list[dict[str, Any]]:
        """Generate VSA improvement recommendations."""
        recommendations = []

        # Recommend splitting features with low coherence
        for feature, data in self.feature_domains.items():
            term_counts = list(data["domain_terms"].values())
            if not term_counts:
                continue

            # Check for multiple distinct domain clusters
            dominant_terms = [term for term, count in data["domain_terms"].most_common(5)]
            if len(dominant_terms) > 3 and len(data["files"]) > 5:
                recommendations.append(
                    {
                        "type": "split_feature",
                        "feature": feature,
                        "reason": "Multiple domain concepts detected",
                        "suggested_splits": self._suggest_feature_splits(feature, data),
                        "priority": "medium",
                    }
                )

        # Recommend merging features with high overlap
        for violation in self.cross_domain_violations:
            if violation["overlap_score"] > 0.7:
                recommendations.append(
                    {
                        "type": "merge_features",
                        "features": [violation["feature1"], violation["feature2"]],
                        "reason": f"High domain overlap ({violation['overlap_score']:.1%})",
                        "shared_concepts": violation["shared_terms"],
                        "priority": "high",
                    }
                )

        # Recommend extracting shared concepts
        shared_terms = self._find_cross_cutting_concerns()
        if shared_terms:
            recommendations.append(
                {
                    "type": "extract_shared",
                    "terms": shared_terms,
                    "reason": "Cross-cutting domain concepts detected",
                    "suggested_location": "shared/domain/",
                    "priority": "low",
                }
            )

        return recommendations

    def _suggest_feature_splits(self, feature: str, data: dict[str, Any]) -> list[str]:
        """Suggest how to split a feature based on domain clustering."""
        # Simple clustering based on term co-occurrence
        # This is a simplified version - real implementation would use more sophisticated clustering

        top_terms = [term for term, count in data["domain_terms"].most_common(10)]

        # Group terms that might belong together
        clusters = []
        remaining_terms = set(top_terms)

        while remaining_terms and len(clusters) < 3:
            seed_term = remaining_terms.pop()
            cluster = {seed_term}

            # Find related terms (simple heuristic)
            for term in list(remaining_terms):
                if any(self._terms_related(seed_term, term) for seed_term in cluster):
                    cluster.add(term)
                    remaining_terms.remove(term)

            if len(cluster) > 1:
                clusters.append(cluster)

        # Generate suggested names
        suggestions = []
        for _i, cluster in enumerate(clusters):
            # Use the most common term as base for name
            cluster_name = f"{feature}_{list(cluster)[0]}"
            suggestions.append(cluster_name)

        return suggestions[:2]  # Limit to 2 splits

    def _terms_related(self, term1: str, term2: str) -> bool:
        """Check if two terms are likely related."""
        # Simple heuristics for term relatedness
        if term1 in term2 or term2 in term1:
            return True

        # Check for common prefixes/suffixes
        return (
            len(term1) > 4
            and len(term2) > 4
            and (term1[:3] == term2[:3] or term1[-3:] == term2[-3:])
        )

    def _find_cross_cutting_concerns(self) -> list[str]:
        """Find domain terms that appear across many features."""
        term_features = defaultdict(set)

        for feature, data in self.feature_domains.items():
            for term in data["domain_terms"]:
                term_features[term].add(feature)

        # Terms that appear in 3+ features might be cross-cutting
        cross_cutting = []
        for term, features in term_features.items():
            if len(features) >= 3:
                cross_cutting.append(term)

        return cross_cutting

    def _extract_feature_name(self, file_path: str) -> str | None:
        """Extract feature name from file path."""
        parts = file_path.split("/")
        if "features" in parts:
            feature_idx = parts.index("features")
            if feature_idx + 1 < len(parts):
                return parts[feature_idx + 1]
        return None

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        name = file_path.name
        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or "__pycache__" in str(file_path)
            or name.startswith(".")
        )


class DomainPatternDetector:
    """Main class combining domain analysis capabilities."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
        self.context_analyzer = BoundedContextAnalyzer(repo_root)

    def analyze(self) -> dict[str, Any]:
        """Perform complete domain analysis."""
        return self.context_analyzer.analyze_domain_boundaries()

    def generate_report(self) -> str:
        """Generate human-readable domain analysis report."""
        results = self.analyze()

        report = ["=== Domain Pattern Analysis Report ===", ""]
        report.append(f"Files analyzed: {results['files_analyzed']}")
        report.append(f"Features detected: {len(results['feature_domains'])}")
        report.append(f"Boundary violations: {results['boundary_violations']}")
        report.append(f"Domain coherence score: {results['domain_coherence_score']:.2f}")
        report.append("")

        if results["feature_domains"]:
            report.append("Feature Domain Summary:")
            for feature, data in results["feature_domains"].items():
                top_terms = data["domain_terms"].most_common(5)
                terms_str = ", ".join([f"{term}({count})" for term, count in top_terms])
                report.append(f"  {feature}: {terms_str}")
            report.append("")

        if results["recommendations"]:
            report.append("Recommendations:")
            for rec in results["recommendations"]:
                report.append(f"  [{rec['priority'].upper()}] {rec['type']}: {rec['reason']}")
            report.append("")

        return "\\n".join(report)


def main():
    """CLI interface for domain analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Domain Pattern Detection")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--json", action="store_true", help="Output JSON results")

    args = parser.parse_args()

    detector = DomainPatternDetector(args.repo_root)

    if args.report:
        print(detector.generate_report())
    elif args.json:
        import json

        results = detector.analyze()
        # Convert Counter objects to dicts for JSON serialization
        for feature_data in results.get("feature_domains", {}).values():
            if "domain_terms" in feature_data:
                feature_data["domain_terms"] = dict(feature_data["domain_terms"])
        print(json.dumps(results, indent=2, default=str))
    else:
        results = detector.analyze()
        print(f"Domain coherence: {results['domain_coherence_score']:.2f}")
        print(f"Recommendations: {len(results['recommendations'])}")


if __name__ == "__main__":
    main()
