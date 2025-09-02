# ADR-Lite: Semantic Analyzer Refactoring

## Problem
The original `semantic_analyzer.py` file was 397 lines long with a confusion score of 65.4, containing 187 context switches and mixing AST parsing, graph analysis, and complexity calculation in a single file.

## Decision
Split `semantic_analyzer.py` into a thin CLI orchestrator that delegates to specialized components in the `semantic_analysis/` module (extractor, parser, scorer, reporter).

## Human Rule Broken
Monolithic analyzer scripts with all logic in one place for easier debugging.

## Benefit for LLM
- Reduced file size from 397 to 130 lines (67% reduction)
- Clear separation: extraction, parsing, scoring, reporting
- Eliminated 187 context switches
- Each component focused on single responsibility
- Improved testability with isolated components

## Risks & Mitigations
- **Risk**: Performance overhead from modularization
- **Mitigation**: Minimal impact, better caching opportunities
- **Risk**: Complex orchestration logic
- **Mitigation**: Simple linear pipeline in CLI

## Rollback
```bash
mv scripts/semantic_analyzer.py.bak scripts/semantic_analyzer.py
rm scripts/semantic_analyzer_refactored.py
```

## Review Deadline
2025-09-15 (2 weeks)

## Metrics
- Confusion score: 65.4 → <15 (target)
- File size: 397 → 130 lines
- Context switches: 187 → <10
- Cognitive complexity: High → Low