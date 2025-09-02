# ADR-011: PR Validation Module Refactoring

## Status
Implemented

## Problem
The original `check_pr_loc.py` had a confusion score of 36.8 with:
- 159 context switches in a single 337-line file
- Mixed responsibilities (git operations, categorization, validation, reporting)
- Complex nested logic for PR validation
- Difficult to test individual components

## Decision
Refactor into a modular `pr_validation/` package with separate responsibilities:
- `loc_counter.py`: Git operations and line counting
- `file_categorizer.py`: File categorization logic
- `pr_validator.py`: Validation against limits
- `pr_reporter.py`: Report generation
- `config.yaml`: Externalized configuration

## Human Rule Broken
Breaking the traditional "single script for single task" pattern.

## Benefit for LLM
- Reduced confusion score from 36.8 to ~10
- Each module under 100 LOC with single responsibility
- Clear interfaces between components
- Configurable thresholds without code changes
- Testable individual components

## Risks & Mitigations
- **Risk**: More files to navigate
- **Mitigation**: Clear module names and `__init__.py` exports

- **Risk**: Import overhead
- **Mitigation**: Minimal dependencies, lazy imports where possible

## Rollback
Keep original `check_pr_loc.py` as backup, rename to `check_pr_loc_legacy.py`

## Review Deadline
2 weeks (evaluate if confusion score improvement justified complexity)