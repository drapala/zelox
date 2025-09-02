# ADR-Lite: Adaptive Learner Refactoring

## Problem
The `scripts/adaptive_learner.py` file had high complexity (cyclomatic complexity: 20, context switches: 230) with all learning algorithms consolidated in a single 466-line file, making it difficult for LLMs to understand and modify safely.

## Decision
Refactored into a modular `scripts/learning/` package with clear separation of concerns:
- `pattern_learner.py` (198 LOC): Pattern extraction and analysis
- `metric_tracker.py` (79 LOC): Metrics aggregation and predictions
- `adaptation_engine.py` (99 LOC): Strategy-based recommendation generation
- `learning_reporter.py` (97 LOC): Report generation and insights
- `wiring.py` (97 LOC): Component integration and CLI

## Human Rule Broken
Introduced some duplication of simple validation logic across modules (e.g., empty list checks) instead of creating a shared validation utility.

## Benefit for LLM
- Reduced cognitive hops from ~230 to ~50 per module
- Each file now has single responsibility (100 LOC average)
- Strategy pattern enables adding new adaptation strategies without modifying existing code
- Co-located tests with implementation for context locality
- Clear dependency injection via wiring.py

## Risks & Mitigations
- Risk: Import complexity between modules
- Mitigation: Explicit wiring.py manages all dependencies
- Risk: Potential drift between duplicated validations
- Mitigation: Simple validations unlikely to change; unit tests verify behavior

## Rollback
```bash
git checkout HEAD~1 scripts/adaptive_learner.py
rm -rf scripts/learning/
```

## Review Deadline
2025-02-15