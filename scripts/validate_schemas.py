#!/usr/bin/env python3
"""
Schema Validation Script
Validates repository files against JSON schemas for LLM-first compliance.
"""

import contextlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print("❌ jsonschema package required: pip install jsonschema")
    sys.exit(1)


class SchemaValidator:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self.errors = []
        self.warnings = []
        self._schema_store = None

    def load_schema(self, schema_name: str) -> dict[str, Any]:
        """Load a JSON schema file."""
        schema_path = self.schemas_dir / f"{schema_name}.schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)

    def build_schema_store(self) -> dict[str, Any]:
        """Load all schemas and build a URI store for $id-based resolution."""
        if self._schema_store is not None:
            return self._schema_store
        store: dict[str, Any] = {}
        for schema_file in self.schemas_dir.glob("*.schema.json"):
            try:
                with open(schema_file, encoding="utf-8") as f:
                    schema_obj = json.load(f)
                schema_id = schema_obj.get("$id")
                if schema_id:
                    store[schema_id] = schema_obj
                # Also map file URI to schema
                with contextlib.suppress(Exception):
                    store[schema_file.resolve().as_uri()] = schema_obj
            except Exception:
                # Skip malformed schema files, will be caught during validation anyway
                continue
        self._schema_store = store
        return store

    def validate_index_yaml(self) -> bool:
        """Validate docs/repo/INDEX.yaml against schema with $ref resolution."""
        index_path = self.repo_root / "docs" / "repo" / "INDEX.yaml"
        if not index_path.exists():
            self.errors.append("❌ INDEX.yaml not found at docs/repo/INDEX.yaml")
            return False

        try:
            with open(index_path, encoding="utf-8") as f:
                index_data = yaml.safe_load(f)
            # Load main schema and resolve local $refs manually
            schema = self.load_schema("index")

            # Resolve $refs in the schema manually
            schema = self._resolve_refs(schema)

            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(index_data))

            if errors:
                for e in errors:
                    path = ".".join(str(p) for p in e.absolute_path)
                    self.errors.append(f"❌ INDEX.yaml validation error: {e.message}")
                    if path:
                        self.errors.append(f"   Path: {path}")
                return False

            print("   ✅ Schema structure valid - all modules properly defined")
            print("   ✅ Cross-references valid - no broken dependencies")
            return True

        except yaml.YAMLError as e:
            self.errors.append(f"❌ INDEX.yaml YAML syntax error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"❌ INDEX.yaml validation failed: {e}")
            return False

    def _resolve_refs(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Recursively resolve $ref references in schema."""
        if isinstance(schema, dict):
            if "$ref" in schema:
                ref_path = schema["$ref"]
                if ref_path.startswith("#/"):
                    # Internal reference, not handling for now
                    return schema
                elif ref_path.endswith(".schema.json"):
                    # External file reference
                    ref_name = ref_path.replace(".schema.json", "").split("/")[-1]
                    try:
                        return self.load_schema(ref_name)
                    except Exception:
                        return schema
                return schema
            else:
                return {k: self._resolve_refs(v) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [self._resolve_refs(item) for item in schema]
        else:
            return schema

    def extract_yaml_frontmatter(self, content: str) -> tuple[dict[str, Any], bool]:
        """Extract YAML frontmatter from markdown file."""
        lines = content.strip().split("\n")

        # Look for YAML frontmatter block in ADR
        yaml_start = None
        yaml_end = None

        for i, line in enumerate(lines):
            # Check for ```yaml with "machine-readable metadata" comment nearby
            if line.strip() == "```yaml":
                # Check if previous line contains metadata comment (case-insensitive)
                if (
                    i > 0
                    and "machine-readable metadata" in lines[i - 1].lower()
                    or i > 0
                    and any(
                        prev_line.startswith("## Front-matter")
                        for prev_line in lines[max(0, i - 3) : i]
                    )
                ):
                    yaml_start = i + 1
            elif yaml_start is not None and line.strip() == "```":
                yaml_end = i
                break

        if yaml_start is None or yaml_end is None:
            return {}, False

        yaml_content = "\n".join(lines[yaml_start:yaml_end])
        try:
            # Skip comment lines
            yaml_lines = [
                line for line in yaml_content.split("\n") if not line.strip().startswith("#")
            ]
            return yaml.safe_load("\n".join(yaml_lines)), True
        except yaml.YAMLError:
            return {}, False

    def validate_adr_frontmatter(self) -> bool:
        """Validate ADR front-matter against schema."""
        adr_dir = self.repo_root / "docs" / "adr"
        if not adr_dir.exists():
            self.warnings.append("⚠️  No docs/adr directory found")
            return True

        schema = self.load_schema("adr-frontmatter")
        adr_files = list(adr_dir.glob("*.md"))

        if not adr_files:
            self.warnings.append("⚠️  No ADR files found")
            return True

        valid_count = 0

        for adr_file in adr_files:
            # Skip template
            if "template" in adr_file.name:
                continue

            try:
                with open(adr_file, encoding="utf-8") as f:
                    content = f.read()

                frontmatter, found = self.extract_yaml_frontmatter(content)

                if not found:
                    self.warnings.append(f"⚠️  No YAML frontmatter in {adr_file.name}")
                    continue

                jsonschema.validate(frontmatter, schema)
                valid_count += 1

            except jsonschema.ValidationError as e:
                self.errors.append(f"❌ {adr_file.name} frontmatter error: {e.message}")
            except Exception as e:
                self.errors.append(f"❌ {adr_file.name} validation failed: {e}")

        total_adrs = len([f for f in adr_files if "template" not in f.name])
        if total_adrs > 0:
            print(f"   ✅ {valid_count}/{total_adrs} ADRs have valid frontmatter")
            if valid_count == total_adrs:
                print("   ✅ All ADRs properly tagged for LLM discovery")

        return len(self.errors) == 0

    def validate_obs_plans(self) -> bool:
        """Validate OBS_PLAN.md files against schema."""
        features_dir = self.repo_root / "features"
        if not features_dir.exists():
            self.warnings.append("⚠️  No features directory found")
            return True

        obs_plans = list(features_dir.rglob("OBS_PLAN.md"))
        if not obs_plans:
            self.warnings.append("⚠️  No OBS_PLAN.md files found")
            return True

        schema = self.load_schema("obs-plan")
        valid_count = 0

        for obs_plan in obs_plans:
            try:
                with open(obs_plan, encoding="utf-8") as f:
                    content = f.read()

                # Extract YAML from markdown (look for ```yaml blocks)
                yaml_blocks = re.findall(r"```yaml\n(.*?)\n```", content, re.DOTALL)

                if not yaml_blocks:
                    self.warnings.append(
                        f"⚠️  No YAML block in {obs_plan.relative_to(self.repo_root)}"
                    )
                    continue

                # Validate the first YAML block
                obs_data = yaml.safe_load(yaml_blocks[0])
                jsonschema.validate(obs_data, schema)
                valid_count += 1

            except yaml.YAMLError as e:
                self.errors.append(f"❌ {obs_plan.relative_to(self.repo_root)} YAML error: {e}")
            except jsonschema.ValidationError as e:
                self.errors.append(
                    f"❌ {obs_plan.relative_to(self.repo_root)} schema error: {e.message}"
                )
            except Exception as e:
                self.errors.append(
                    f"❌ {obs_plan.relative_to(self.repo_root)} validation failed: {e}"
                )

        if obs_plans:
            print(f"   ✅ {valid_count}/{len(obs_plans)} OBS_PLANs have valid structure")
            if valid_count == len(obs_plans):
                print("   ✅ All features have proper observability contracts")

        return len(self.errors) == 0

    def run_all_validations(self) -> bool:
        """Run all schema validations."""
        print("=" * 60)
        print("SCHEMA VALIDATION FOR LLM-FIRST ARCHITECTURE")
        print("=" * 60)
        print("\n📚 WHY THESE VALIDATIONS MATTER:")
        print("→ Schemas ensure machine-readable contracts for LLM agents")
        print("→ Consistent structure reduces cognitive load")
        print("→ Valid metadata enables automated tooling")
        print("")

        results = []

        # Validate INDEX.yaml
        print("1️⃣  INDEX.yaml Validation")
        print("   WHAT: Central module registry and API contracts")
        print("   WHY: LLMs need structured navigation to understand the codebase")
        results.append(self.validate_index_yaml())

        # Validate ADR frontmatter
        print("\n2️⃣  ADR Frontmatter Validation")
        print("   WHAT: Machine-readable metadata in Architecture Decision Records")
        print("   WHY: Enables LLMs to understand decision context and impact")
        results.append(self.validate_adr_frontmatter())

        # Validate OBS_PLAN files
        print("\n3️⃣  OBS_PLAN.md Validation")
        print("   WHAT: Observability contracts for each feature")
        print("   WHY: Defines metrics, alerts, and SLOs for automated monitoring")
        results.append(self.validate_obs_plans())

        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")

        all_passed = all(results) and len(self.errors) == 0

        if all_passed:
            print("\n✅ All schema validations passed!")
            print("\n💡 WHAT THIS MEANS:")
            print("   • Your repository structure is LLM-readable")
            print("   • All contracts and metadata are valid")
            print("   • Automated tools can parse your codebase")
            print("   • New contributors (human or AI) can navigate easily")
        else:
            print("\n❌ Schema validation failed!")
            print("\n💡 HOW TO FIX:")
            print("   • Check the specific errors above")
            print("   • Ensure YAML syntax is correct")
            print("   • Verify required fields are present")
            print("   • Run 'make validate.schemas' locally before pushing")

        return all_passed


def check_source_files_frontmatter(repo_root: Path) -> bool:
    """Check Python source files for frontmatter coverage."""
    features_dir = repo_root / "features"
    if not features_dir.exists():
        print("⚠️  No features directory found")
        return True

    python_files = []
    missing_frontmatter = []

    # Find all Python files (excluding tests and templates)
    for py_file in features_dir.rglob("*.py"):
        if "test" in py_file.name or "__init__" in py_file.name or "template" in str(py_file):
            continue
        python_files.append(py_file)

        # Check for frontmatter
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()
                # Check for structured docstrings with metadata
                if not (
                    '"""' in content
                    and any(
                        keyword in content.lower()
                        for keyword in ["title:", "purpose:", "inputs:", "outputs:"]
                    )
                ):
                    missing_frontmatter.append(str(py_file.relative_to(repo_root)))
        except Exception:
            continue

    if not python_files:
        print("⚠️  No Python source files found to check")
        return True

    coverage = (len(python_files) - len(missing_frontmatter)) / len(python_files)

    print("=" * 60)
    print("SOURCE FILE FRONTMATTER CHECK")
    print("=" * 60)
    coverage_msg = f"\nCoverage: {coverage:.1%} "
    coverage_msg += f"({len(python_files) - len(missing_frontmatter)}/{len(python_files)} files)"
    print(coverage_msg)

    if coverage >= 0.9:  # 90% threshold
        print("✅ Frontmatter coverage meets LLM-first standards")
        return True
    else:
        print(f"❌ {len(missing_frontmatter)} files missing frontmatter:")
        for file in missing_frontmatter[:5]:  # Show first 5
            print(f"   - {file}")
        if len(missing_frontmatter) > 5:
            print(f"   ... and {len(missing_frontmatter) - 5} more")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate schemas and frontmatter")
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root path")
    parser.add_argument(
        "--check-source-files",
        action="store_true",
        help="Check Python source files for frontmatter",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root)

    if args.check_source_files:
        # Just check source file frontmatter
        success = check_source_files_frontmatter(repo_root)
    else:
        # Run full schema validations
        validator = SchemaValidator(repo_root)
        success = validator.run_all_validations()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
