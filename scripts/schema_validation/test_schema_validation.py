#!/usr/bin/env python3
"""
---
title: Schema Validation Test Suite
purpose: Comprehensive tests for schema validation modules
inputs:
  - name: test_data
    type: dict
outputs:
  - name: test_results
    type: bool
effects:
  - runs unit tests
  - creates temporary test files
deps:
  - pytest
  - tempfile
  - pathlib
owners: [llm-first-team]
stability: stable
since_version: 1.0.0
complexity: low
---
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import yaml

from schema_validation.schema_loader import SchemaLoader
from schema_validation.schema_reporter import ValidationReporter
from schema_validation.schema_rules import FrontmatterExtractor, ValidationRules
from schema_validation.schema_validator import SchemaValidator, ValidationResult


class TestSchemaLoader:
    """Test schema loading functionality."""

    def test_load_schema(self, tmp_path):
        """Test loading a valid schema."""
        # Create test schema
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        test_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        schema_file = schemas_dir / "test.schema.json"
        schema_file.write_text(json.dumps(test_schema))

        loader = SchemaLoader(tmp_path)
        loaded = loader.load("test")

        assert loaded == test_schema

    def test_cache_schema(self, tmp_path):
        """Test schema caching."""
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        test_schema = {"type": "object"}
        schema_file = schemas_dir / "test.schema.json"
        schema_file.write_text(json.dumps(test_schema))

        loader = SchemaLoader(tmp_path)

        # Load twice
        loaded1 = loader.load("test")
        loaded2 = loader.load("test")

        # Should be the same object (cached)
        assert loaded1 is loaded2

    def test_missing_schema(self, tmp_path):
        """Test loading non-existent schema."""
        loader = SchemaLoader(tmp_path)

        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent")

    def test_resolve_refs(self, tmp_path):
        """Test reference resolution."""
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        # Create referenced schema
        ref_schema = {"type": "string", "minLength": 1}
        ref_file = schemas_dir / "ref.schema.json"
        ref_file.write_text(json.dumps(ref_schema))

        # Create main schema with reference
        main_schema = {"type": "object", "properties": {"field": {"$ref": "ref.schema.json"}}}

        loader = SchemaLoader(tmp_path)
        resolved = loader.resolve_refs(main_schema)

        assert resolved["properties"]["field"] == ref_schema


class TestSchemaValidator:
    """Test schema validation functionality."""

    def test_valid_data(self):
        """Test validating valid data."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        data = {"name": "test"}

        validator = SchemaValidator()
        result = validator.validate(data, schema)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_data(self):
        """Test validating invalid data."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        data = {"other": "field"}

        validator = SchemaValidator()
        result = validator.validate(data, schema)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert "name" in result.errors[0]

    def test_validation_with_context(self):
        """Test validation with context path."""
        schema = {"type": "object"}
        data = []  # Wrong type

        validator = SchemaValidator()
        result = validator.validate_with_context(data, schema, "test/file.yaml")

        assert not result.is_valid
        assert "test/file.yaml" in result.errors[0]


class TestFrontmatterExtractor:
    """Test frontmatter extraction."""

    def test_extract_yaml_from_markdown(self):
        """Test extracting YAML from markdown."""
        content = """
# Document

<!-- Machine-readable metadata -->
```yaml
title: Test
purpose: Testing
```

Content here
"""
        extractor = FrontmatterExtractor()
        data, found = extractor.extract_yaml_block(content)

        assert found
        assert data["title"] == "Test"
        assert data["purpose"] == "Testing"

    def test_extract_python_docstring(self):
        """Test extracting from Python docstring."""
        content = '''"""
---
title: Test Module
purpose: Testing
inputs:
  - name: data
    type: dict
---
"""

def test():
    pass
'''
        extractor = FrontmatterExtractor()
        data, found = extractor.extract_python_docstring(content)

        assert found
        assert data["title"] == "Test Module"
        assert data["purpose"] == "Testing"

    def test_no_frontmatter(self):
        """Test when no frontmatter exists."""
        content = "# Just a regular document\n\nWith content"

        extractor = FrontmatterExtractor()
        data, found = extractor.extract_yaml_block(content)

        assert not found
        assert data is None


class TestValidationRules:
    """Test validation rules."""

    def test_validate_index_yaml(self, tmp_path):
        """Test INDEX.yaml validation."""
        # Setup
        docs_dir = tmp_path / "docs" / "repo"
        docs_dir.mkdir(parents=True)
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        # Create schema
        index_schema = {
            "type": "object",
            "properties": {"modules": {"type": "array"}},
            "required": ["modules"],
        }
        schema_file = schemas_dir / "index.schema.json"
        schema_file.write_text(json.dumps(index_schema))

        # Create valid INDEX.yaml
        index_data = {"modules": ["module1", "module2"]}
        index_file = docs_dir / "INDEX.yaml"
        index_file.write_text(yaml.dump(index_data))

        rules = ValidationRules(tmp_path)
        result = rules.validate_index_yaml()

        assert result.is_valid

    def test_validate_adr_files(self, tmp_path):
        """Test ADR validation."""
        # Setup
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        # Create schema
        adr_schema = {
            "type": "object",
            "properties": {"title": {"type": "string"}, "status": {"type": "string"}},
            "required": ["title", "status"],
        }
        schema_file = schemas_dir / "adr-frontmatter.schema.json"
        schema_file.write_text(json.dumps(adr_schema))

        # Create ADR with valid frontmatter
        adr_content = """
# ADR-001

<!-- Machine-readable metadata -->
```yaml
title: Test Decision
status: Accepted
```

Content here
"""
        adr_file = adr_dir / "001-test.md"
        adr_file.write_text(adr_content)

        rules = ValidationRules(tmp_path)
        result = rules.validate_adr_files()

        assert result.is_valid


class TestValidationReporter:
    """Test validation reporting."""

    def test_report_success(self, capsys):
        """Test reporting successful validation."""
        reporter = ValidationReporter()
        reporter.print_header()

        result = ValidationResult(is_valid=True)
        reporter.report_result(result, "Test passed")

        success = reporter.print_summary()

        assert success
        captured = capsys.readouterr()
        assert "✅ All schema validations passed!" in captured.out

    def test_report_errors(self, capsys):
        """Test reporting validation errors."""
        reporter = ValidationReporter()

        result = ValidationResult(is_valid=False)
        result.add_error("Test error message")

        reporter.report_result(result)
        success = reporter.print_summary()

        assert not success
        assert reporter.get_exit_code() == 1

        captured = capsys.readouterr()
        assert "❌ Schema validation failed!" in captured.out
        assert "Test error message" in captured.out

    def test_report_warnings(self, capsys):
        """Test reporting warnings."""
        reporter = ValidationReporter()

        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")

        reporter.report_result(result)
        success = reporter.print_summary()

        assert success
        assert reporter.get_exit_code() == 0

        captured = capsys.readouterr()
        assert "Test warning" in captured.out


# Golden test cases
GOLDEN_VALID_INDEX = """
modules:
  - name: core
    files:
      - path: core/main.py
        role: entrypoint
"""

GOLDEN_VALID_ADR = """
# ADR-001

<!-- Machine-readable metadata -->
```yaml
title: Use LLM-First Architecture
status: Accepted
decision: Adopt vertical slice architecture
impact: high
```

## Context
..."""

GOLDEN_VALID_OBS_PLAN = """
# Observability Plan

```yaml
metrics:
  - name: request_latency
    type: histogram
    unit: ms
alerts:
  - name: high_latency
    condition: p95 > 500ms
```"""


def test_golden_valid_schemas(tmp_path):
    """Golden test with valid schemas."""
    # Setup directory structure
    (tmp_path / "docs" / "repo").mkdir(parents=True)
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "features" / "test_feature").mkdir(parents=True)
    (tmp_path / "schemas").mkdir()

    # Create minimal schemas
    schemas = {
        "index": {"type": "object", "properties": {"modules": {"type": "array"}}},
        "adr-frontmatter": {"type": "object", "properties": {"title": {"type": "string"}}},
        "obs-plan": {"type": "object", "properties": {"metrics": {"type": "array"}}},
    }

    for name, schema in schemas.items():
        schema_file = tmp_path / "schemas" / f"{name}.schema.json"
        schema_file.write_text(json.dumps(schema))

    # Create valid files
    (tmp_path / "docs" / "repo" / "INDEX.yaml").write_text(GOLDEN_VALID_INDEX)
    (tmp_path / "docs" / "adr" / "001-test.md").write_text(GOLDEN_VALID_ADR)
    (tmp_path / "features" / "test_feature" / "OBS_PLAN.md").write_text(GOLDEN_VALID_OBS_PLAN)

    # Run validation
    rules = ValidationRules(tmp_path)

    index_result = rules.validate_index_yaml()
    assert index_result.is_valid

    adr_result = rules.validate_adr_files()
    assert adr_result.is_valid

    obs_result = rules.validate_obs_plans()
    assert obs_result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
