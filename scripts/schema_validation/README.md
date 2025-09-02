# Schema Validation Module

## Purpose
Validates repository files against JSON schemas for LLM-first compliance with minimal indirection and clear linear flow.

## Architecture

### Validation Flow
```
Load Schema → Validate Data → Report Results
     ↓             ↓              ↓
schema_loader  schema_validator  schema_reporter
                   ↑
              schema_rules
              (specific validations)
```

## Modules

### schema_loader.py (100 LOC)
- **Purpose**: Load and cache JSON schemas
- **Key Functions**:
  - `load(schema_name)`: Load schema from disk with caching
  - `build_store()`: Build URI-based schema store for references
  - `resolve_refs(schema)`: Resolve $ref references recursively

### schema_validator.py (93 LOC)
- **Purpose**: Core validation logic with context tracking
- **Key Classes**:
  - `ValidationResult`: Data class for validation results
  - `SchemaValidator`: Validates data against JSON schemas
- **Key Functions**:
  - `validate(data, schema)`: Basic validation
  - `validate_with_context(data, schema, path)`: Validation with file context

### schema_rules.py (165 LOC)
- **Purpose**: Specific validation rules for different file types
- **Key Classes**:
  - `FrontmatterExtractor`: Extract YAML/frontmatter from files
  - `ValidationRules`: File-specific validation logic
- **Key Functions**:
  - `validate_index_yaml()`: Validate INDEX.yaml structure
  - `validate_adr_files()`: Validate ADR frontmatter
  - `validate_obs_plans()`: Validate OBS_PLAN.md files
  - `check_source_frontmatter_coverage()`: Check Python file coverage

### schema_reporter.py (100 LOC)
- **Purpose**: Format and output validation results
- **Key Functions**:
  - `print_header()`: Print validation header
  - `report_result(result)`: Report individual validation
  - `print_summary()`: Print final summary with exit code

### test_schema_validation.py (400 LOC)
- **Purpose**: Comprehensive test suite with golden tests
- **Coverage**: 
  - Unit tests for each module
  - Integration tests for complete flow
  - Golden test cases for valid schemas

## How to Edit (5 lines)

1. Each validator function should be < 15 lines
2. Keep validation logic in schema_rules.py
3. Add new file types by extending ValidationRules
4. Update golden tests when adding new validations
5. Run `pytest test_schema_validation.py` to verify changes

## Usage

### Command Line
```bash
# Run all validations
python validate_schemas.py

# Check source file frontmatter only
python validate_schemas.py --check-source-files

# Run from different directory
python validate_schemas.py /path/to/repo
```

### Python API
```python
from schema_validation.schema_rules import ValidationRules
from schema_validation.schema_reporter import ValidationReporter

# Create validator
rules = ValidationRules(repo_root=".")
reporter = ValidationReporter()

# Run validations
reporter.print_header()

index_result = rules.validate_index_yaml()
reporter.report_result(index_result, "INDEX.yaml valid")

adr_result = rules.validate_adr_files()
reporter.report_result(adr_result, "ADRs valid")

# Print summary
success = reporter.print_summary()
exit_code = reporter.get_exit_code()
```

## Common Tasks

### Add a New Schema Validation
1. Create schema file in `schemas/` directory
2. Add validation method to `ValidationRules` class
3. Add test cases to `test_schema_validation.py`
4. Update main script to call new validation

### Debug Validation Errors
1. Check the specific error message for path/field
2. Use `--check-source-files` to isolate frontmatter issues
3. Verify YAML syntax with online validators
4. Check schema requirements in `schemas/` directory

### Performance Optimization
- Schemas are cached after first load
- Ref resolution is done once per schema
- Parallel validation possible (not implemented)

## Dependencies
- jsonschema: JSON schema validation
- PyYAML: YAML parsing
- Python 3.8+: Type hints and dataclasses

## Exit Codes
- 0: All validations passed
- 1: One or more validations failed