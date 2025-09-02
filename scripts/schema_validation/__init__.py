"""
Schema validation module for LLM-first architecture compliance.

This module provides modular, testable components for validating
repository schemas with minimal indirection and clear linear flow.
"""

from .schema_loader import SchemaLoader
from .schema_reporter import ValidationReporter
from .schema_rules import FrontmatterExtractor, ValidationRules
from .schema_validator import SchemaValidator, ValidationResult

__all__ = [
    "SchemaLoader",
    "SchemaValidator",
    "ValidationResult",
    "ValidationRules",
    "FrontmatterExtractor",
    "ValidationReporter",
]

__version__ = "2.0.0"
