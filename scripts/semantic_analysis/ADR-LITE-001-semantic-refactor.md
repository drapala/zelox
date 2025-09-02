# ADR-Lite: Semantic Analyzer Refactoring

**Date:** 2025-09-02  
**Status:** Implemented  
**Review Deadline:** 2025-09-16 (2 sprints)

## Problem

The original `semantic_analyzer.py` had a confusion score of 72.6, making it difficult for LLMs to understand and modify:
- Single 396-line file with mixed concerns
- Cyclomatic complexity of 25 (target: <10)
- 308 context switches required for comprehension
- Nested logic depth up to 6 levels
- Multiple responsibilities in single classes

## Decision

Split the monolithic analyzer into a linear pipeline with 5 focused modules:
1. **semantic_parser.py** - Parse AST and extract elements
2. **semantic_extractor.py** - Extract patterns and dependencies
3. **semantic_scorer.py** - Calculate quality scores
4. **semantic_reporter.py** - Generate reports
5. **semantic_pipeline.py** - Orchestrate pipeline stages

## Human Rule Broken

**Violated DRY principle** - Some utility functions are duplicated across modules (e.g., `_should_skip_file` logic appears in both parser and pipeline).

## Benefit for LLM

- **70% reduction in context switches** (308 → ~90)
- **68% reduction in cyclomatic complexity** (25 → 8 max per function)
- **Clear linear flow** reduces cognitive load: parse → extract → score → report
- **Independent modules** allow targeted edits without full context
- **Each file under 100 LOC** fits in single LLM context window
- **Explicit data flow** through dataclasses removes implicit state

## Risks & Mitigations

**Risk 1:** Module coupling through shared data structures
- **Mitigation:** Use explicit dataclasses as contracts between stages

**Risk 2:** Performance overhead from multiple file operations
- **Mitigation:** Negligible for analysis tools; benefits outweigh costs

**Risk 3:** Duplicated utility code
- **Mitigation:** Limited duplication (<5%); easier for LLMs than deep imports

## Rollback

To rollback:
1. Keep original `semantic_analyzer.py` as backup
2. Update imports in any dependent scripts
3. Remove `semantic_analysis/` directory
4. Restore original file from git history

## Metrics

**Before:**
- Confusion Score: 72.6
- Cyclomatic Complexity: 25
- Context Switches: 308
- File Size: 396 LOC

**After:**
- Confusion Score: <30 (estimated)
- Max Complexity: 8
- Context Switches: ~90
- Max File Size: 100 LOC
- Test Coverage: 5 test classes with smoke tests

## Implementation Notes

The refactoring follows LLM-First principles:
- Linear pipeline pattern for deterministic flow
- Guard clauses instead of nested conditionals
- Explicit return types via dataclasses
- Co-located tests in same directory
- Rich docstrings with YAML frontmatter