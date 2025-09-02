# ADR-012: Drift Check Modularization

## Problem
The original `drift_check.py` had a confusion score of 37.4 due to:
- Deep indirection (9 levels)
- 148 context switches
- Monolithic class structure mixing concerns
- Complex nested logic for block detection and drift calculation

## Decision
Refactor drift_check.py into a modular architecture with clear separation of concerns:
- `drift_detection/block_finder.py`: Find duplicate blocks (60 LOC)
- `drift_detection/drift_calculator.py`: Calculate drift metrics (120 LOC)  
- `drift_detection/drift_reporter.py`: Generate reports (100 LOC)
- Simplified main script orchestrating the modules (90 LOC)

## Human Rule Broken
Traditional OOP single-class encapsulation pattern replaced with module-based architecture.

## Benefit for LLM
- **Reduced indirection**: From 9 to 3 levels max
- **Clear boundaries**: Each module has single responsibility
- **Local context**: LLM can understand each module independently
- **Performance**: Added caching, hash-based comparisons
- **Testability**: Each component tested in isolation

## Risks & Mitigations
- **Risk**: More files to navigate
- **Mitigation**: Clear naming and focused responsibilities make navigation intuitive

## Rollback
Keep original drift_check.py backup; modules can be collapsed back if needed.

## Review Deadline
2 weeks (evaluate performance improvements and maintainability)