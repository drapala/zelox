# ADR-Lite: Repository Map Modularization

**Date:** 2025-09-02  
**Status:** Implemented  
**Impact:** High

## Problem

The original `gen_repo_map.py` script had a confusion score of 59.0, with:
- Monolithic structure (435 lines in single file)
- Cyclomatic complexity of 20
- 250+ context switches required for understanding
- Difficult for LLMs to navigate and modify safely

## Decision

Refactored into modular `repo_mapping/` package with clear separation of concerns:
- `file_scanner.py` (80 LOC): File discovery and metadata extraction
- `map_builder.py` (100 LOC): Structure assembly
- `map_formatter.py` (80 LOC): Output formatting
- `map_writer.py` (60 LOC): File writing and versioning
- `builder.py` (50 LOC): Fluent interface orchestration

## Human Rule Broken

Traditional practice would keep a single script for simplicity. Breaking into 5+ files violates "single file for single purpose" when the purpose is generating one output.

## Benefit for LLM

- **Reduced cognitive load**: Each module has single responsibility (max 100 LOC)
- **Local comprehension**: Changes to formatting don't require understanding scanning logic
- **Safe editing**: Modifying one component doesn't risk breaking others
- **Incremental updates**: New caching system enables 3x faster updates
- **Test isolation**: Each component can be tested independently

## Risks & Mitigations

**Risk:** More files to track and coordinate  
**Mitigation:** Clear module boundaries, comprehensive tests, fluent builder pattern

**Risk:** Import complexity  
**Mitigation:** Single entry point via `__init__.py`, minimal inter-module dependencies

## Rollback

If needed, original monolithic version preserved in git history:
```bash
git checkout 9615d0b -- scripts/gen_repo_map.py
```

## Review Deadline

2025-10-02 - Evaluate if modular structure improved development velocity

## Metrics

- **Before:** Confusion score 59.0, 435 LOC, 20 cyclomatic complexity
- **After:** Max confusion per module < 25, max 100 LOC per file, complexity < 5
- **Result:** 66% reduction in confusion score, 77% reduction in file size