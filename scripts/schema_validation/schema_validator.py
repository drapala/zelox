#!/usr/bin/env python3
"""
---
title: Schema Validator
purpose: Core validation logic for schema compliance
inputs:
  - name: data
    type: dict
  - name: schema
    type: dict
outputs:
  - name: validation_result
    type: ValidationResult
effects:
  - validates data against schemas
deps:
  - jsonschema
  - typing
  - dataclasses
owners: [llm-first-team]
stability: stable
since_version: 1.0.0
complexity: medium
---
"""

from dataclasses import dataclass, field
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    raise ImportError("jsonschema package required: pip install jsonschema")


@dataclass
class ValidationResult:
    """Result of a schema validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    path: str | None = None

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def merge(self, other: "ValidationResult") -> None:
        """Merge another result into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class SchemaValidator:
    """Validates data against JSON schemas."""

    def validate(self, data: Any, schema: dict) -> ValidationResult:
        """Validate data against a schema."""
        result = ValidationResult(is_valid=True)

        try:
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(data))

            if errors:
                for error in errors:
                    path = ".".join(str(p) for p in error.absolute_path)
                    message = error.message
                    if path:
                        message = f"{message} at path: {path}"
                    result.add_error(message)

        except jsonschema.exceptions.SchemaError as e:
            result.add_error(f"Invalid schema: {e.message}")
        except Exception as e:
            result.add_error(f"Validation failed: {str(e)}")

        return result

    def validate_with_context(self, data: Any, schema: dict, context_path: str) -> ValidationResult:
        """Validate with file context information."""
        result = self.validate(data, schema)
        result.path = context_path

        # Prepend context to error messages
        if result.errors:
            result.errors = [f"{context_path}: {error}" for error in result.errors]

        return result
