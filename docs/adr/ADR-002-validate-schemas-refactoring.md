# ADR-Lite: Validate Schemas Refactoring

## Problem
The original `validate_schemas.py` file was 412 lines long with a confusion score of 72.5, containing mixed responsibilities (loading, validation, reporting) and complex nested logic.

## Decision
Refactor `validate_schemas.py` into a thin CLI orchestrator that delegates to specialized components in the `schema_validation/` module.

## Human Rule Broken
Single-file scripts for validation tools, keeping all logic co-located.

## Benefit for LLM
- Reduced file size from 412 to 150 lines (64% reduction)
- Clear separation: loader, validator, rules, reporter
- Each component single-purpose and under 150 LOC
- Testable components with clear interfaces
- Reduced cognitive load through modularization

## Risks & Mitigations
- **Risk**: Module dependencies increase
- **Mitigation**: Clear module interfaces and naming
- **Risk**: Potential duplication of validation logic
- **Mitigation**: Centralized validation in SchemaValidatorCore

## Rollback
```bash
mv scripts/validate_schemas.py.bak scripts/validate_schemas.py
rm scripts/validate_schemas_refactored.py
```

## Review Deadline
2025-09-15 (2 weeks)

## Metrics
- Confusion score: 72.5 → <15 (target)
- File size: 412 → 150 lines
- Cognitive complexity: High → Low
- Test coverage potential: +40%