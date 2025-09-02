# ADR-015: Schema Validation Vertical Slice Refactoring

<!-- Machine-readable metadata -->
```yaml
title: Refactor validate_schemas.py to Vertical Slice Architecture
status: Implemented
decision: Split monolithic validation script into focused modules
impact: medium
author: llm-first-team
date: 2025-01-02
tags: [refactoring, llm-first, vertical-slice]
```

## Problem
The original `validate_schemas.py` file had:
- High confusion score of 74.4 (target: <30)
- Cyclomatic complexity of 12 (target: <10)
- Indirection depth of 10 (target: <3)
- 411 lines in a single file
- Mixed concerns: loading, validation, rules, and reporting

## Decision
Refactored into vertical slice architecture with 5 focused modules:
1. `schema_loader.py` (100 LOC) - Schema loading and caching
2. `schema_validator.py` (93 LOC) - Core validation logic
3. `schema_rules.py` (165 LOC) - File-specific validation rules
4. `schema_reporter.py` (100 LOC) - Result formatting and reporting
5. `validate_schemas.py` (143 LOC) - Simple orchestrator

## Human Rule Broken
Traditional "DRY at all costs" - Some validation patterns are duplicated across modules to maintain locality and reduce cognitive hops.

## Benefit for LLM
- **Reduced indirection**: From 10 levels to 3 levels max
- **Clear linear flow**: Load → Validate → Report
- **Local context**: Each module self-contained with frontmatter
- **Focused editing**: Changes isolated to specific modules
- **Explicit contracts**: All inputs/outputs documented

## Risks & Mitigations
- **Risk**: Module boundaries might evolve
  - **Mitigation**: Clear interfaces via dataclasses, easy to refactor
- **Risk**: Duplication might drift
  - **Mitigation**: Comprehensive test suite with golden tests

## Rollback
```bash
# Restore original file
git checkout HEAD~1 scripts/validate_schemas.py
# Remove new directory
rm -rf scripts/schema_validation/
```

## Review Deadline
2025-02-01 - Evaluate if module boundaries are optimal

## Metrics
- **Before**: Confusion score 74.4, indirection depth 10
- **After**: Estimated confusion score <30, indirection depth 3
- **Lines per module**: All under 200 LOC
- **Test coverage**: 400 LOC of tests including golden tests