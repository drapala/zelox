#!/usr/bin/env python3
"""
---
title: Schema Validation Rules
purpose: Specific validation rules for different file types
inputs:
  - name: file_path
    type: Path
  - name: content
    type: str
outputs:
  - name: validation_result
    type: ValidationResult
effects:
  - extracts and validates frontmatter
  - checks file coverage
deps:
  - re
  - yaml
  - pathlib
  - typing
owners: [llm-first-team]
stability: stable
since_version: 1.0.0
complexity: low
---
"""

import re
from pathlib import Path
from typing import Any

import yaml

from .schema_loader import SchemaLoader
from .schema_validator import SchemaValidator, ValidationResult


class FrontmatterExtractor:
    """Extracts frontmatter from various file formats."""

    @staticmethod
    def extract_yaml_block(content: str) -> tuple[dict[str, Any] | None, bool]:
        """Extract YAML frontmatter from markdown files."""
        lines = content.strip().split("\n")

        yaml_start = None
        yaml_end = None

        for i, line in enumerate(lines):
            if line.strip() == "```yaml":
                # Check for metadata context
                if i > 0 and any(
                    marker in lines[i - 1].lower()
                    for marker in ["machine-readable metadata", "front-matter"]
                ):
                    yaml_start = i + 1
            elif yaml_start is not None and line.strip() == "```":
                yaml_end = i
                break

        if yaml_start is None or yaml_end is None:
            return None, False

        yaml_content = "\n".join(lines[yaml_start:yaml_end])

        try:
            # Remove comment lines
            clean_lines = [
                line for line in yaml_content.split("\n") if not line.strip().startswith("#")
            ]
            data = yaml.safe_load("\n".join(clean_lines))
            return data, True
        except yaml.YAMLError:
            return None, False

    @staticmethod
    def extract_python_docstring(content: str) -> tuple[dict[str, Any] | None, bool]:
        """Extract structured metadata from Python docstrings."""
        # Look for triple-quoted docstring at the beginning
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if not match:
            return None, False

        docstring = match.group(1)

        # Check if it contains structured metadata
        if not any(
            marker in docstring.lower() for marker in ["title:", "purpose:", "inputs:", "outputs:"]
        ):
            return None, False

        # Extract YAML between --- markers if present
        yaml_match = re.search(r"---\n(.*?)\n---", docstring, re.DOTALL)
        if yaml_match:
            try:
                data = yaml.safe_load(yaml_match.group(1))
                return data, True
            except yaml.YAMLError:
                pass

        return None, False


class ValidationRules:
    """Specific validation rules for different file types."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.loader = SchemaLoader(repo_root)
        self.validator = SchemaValidator()
        self.extractor = FrontmatterExtractor()

    def validate_index_yaml(self) -> ValidationResult:
        """Validate INDEX.yaml file."""
        result = ValidationResult(is_valid=True)
        index_path = self.repo_root / "docs" / "repo" / "INDEX.yaml"

        if not index_path.exists():
            result.add_error("INDEX.yaml not found at docs/repo/INDEX.yaml")
            return result

        try:
            with open(index_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            schema = self.loader.load("index")
            schema = self.loader.resolve_refs(schema)

            validation = self.validator.validate_with_context(data, schema, "docs/repo/INDEX.yaml")
            result.merge(validation)

        except yaml.YAMLError as e:
            result.add_error(f"YAML syntax error: {e}")
        except Exception as e:
            result.add_error(f"Validation failed: {e}")

        return result

    def validate_adr_files(self) -> ValidationResult:
        """Validate all ADR files."""
        result = ValidationResult(is_valid=True)
        adr_dir = self.repo_root / "docs" / "adr"

        if not adr_dir.exists():
            result.add_warning("No docs/adr directory found")
            return result

        schema = self.loader.load("adr-frontmatter")
        adr_files = [f for f in adr_dir.glob("*.md") if "template" not in f.name]

        if not adr_files:
            result.add_warning("No ADR files found")
            return result

        valid_count = 0
        for adr_file in adr_files:
            with open(adr_file, encoding="utf-8") as f:
                content = f.read()

            frontmatter, found = self.extractor.extract_yaml_block(content)

            if not found:
                result.add_warning(f"No YAML frontmatter in {adr_file.name}")
                continue

            validation = self.validator.validate_with_context(
                frontmatter, schema, f"docs/adr/{adr_file.name}"
            )

            if validation.is_valid:
                valid_count += 1
            else:
                result.merge(validation)

        result.warnings.append(f"{valid_count}/{len(adr_files)} ADRs have valid frontmatter")
        return result

    def validate_obs_plans(self) -> ValidationResult:
        """Validate OBS_PLAN.md files."""
        result = ValidationResult(is_valid=True)
        features_dir = self.repo_root / "features"

        if not features_dir.exists():
            result.add_warning("No features directory found")
            return result

        obs_plans = list(features_dir.rglob("OBS_PLAN.md"))
        if not obs_plans:
            result.add_warning("No OBS_PLAN.md files found")
            return result

        schema = self.loader.load("obs-plan")
        valid_count = 0

        for obs_plan in obs_plans:
            with open(obs_plan, encoding="utf-8") as f:
                content = f.read()

            # Extract YAML blocks
            yaml_blocks = re.findall(r"```yaml\n(.*?)\n```", content, re.DOTALL)

            if not yaml_blocks:
                rel_path = obs_plan.relative_to(self.repo_root)
                result.add_warning(f"No YAML block in {rel_path}")
                continue

            try:
                data = yaml.safe_load(yaml_blocks[0])
                validation = self.validator.validate_with_context(
                    data, schema, str(obs_plan.relative_to(self.repo_root))
                )

                if validation.is_valid:
                    valid_count += 1
                else:
                    result.merge(validation)

            except yaml.YAMLError as e:
                rel_path = obs_plan.relative_to(self.repo_root)
                result.add_error(f"{rel_path} YAML error: {e}")

        result.warnings.append(f"{valid_count}/{len(obs_plans)} OBS_PLANs have valid structure")
        return result

    def check_source_frontmatter_coverage(self) -> ValidationResult:
        """Check Python source files for frontmatter coverage."""
        result = ValidationResult(is_valid=True)
        features_dir = self.repo_root / "features"

        if not features_dir.exists():
            result.add_warning("No features directory found")
            return result

        python_files = []
        missing_frontmatter = []

        for py_file in features_dir.rglob("*.py"):
            # Skip test files and __init__
            if any(skip in py_file.name for skip in ["test", "__init__", "template"]):
                continue

            python_files.append(py_file)

            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            _, found = self.extractor.extract_python_docstring(content)
            if not found:
                rel_path = py_file.relative_to(self.repo_root)
                missing_frontmatter.append(str(rel_path))

        if not python_files:
            result.add_warning("No Python source files found to check")
            return result

        coverage = (len(python_files) - len(missing_frontmatter)) / len(python_files)

        if coverage < 0.9:  # 90% threshold
            result.add_error(f"Frontmatter coverage {coverage:.1%} is below 90% threshold")
            for file_path in missing_frontmatter[:5]:
                result.add_error(f"Missing frontmatter: {file_path}")
            if len(missing_frontmatter) > 5:
                result.add_error(f"... and {len(missing_frontmatter) - 5} more files")
        else:
            result.warnings.append(f"Frontmatter coverage: {coverage:.1%}")

        return result
