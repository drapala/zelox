---
adr_number: 007
status: accepted
title: Refactor check_llm_readiness.py into Modular Plugin System
date: 2025-01-02
---

# ADR-007: Refactor check_llm_readiness.py into Modular Plugin System

## Problem
The original `check_llm_readiness.py` had high cognitive complexity (Cyclomatic: 20, Context switches: 191) with mixed responsibilities for scoring, validation, and reporting in a single monolithic file.

## Decision
Refactored into a modular plugin-based architecture with clear separation of concerns:
- Metric plugins for individual assessments
- Calculator for score aggregation
- Validator for threshold checking
- Reporter for multi-format output

## Human Rule Broken
Breaking the "single file simplicity" principle - split one 420-line file into 6 modules totaling ~600 lines.

## Benefit for LLM
- **Reduced cognitive load**: Each module < 100 LOC with single responsibility
- **Pluggable metrics**: Add new metrics without modifying core logic
- **Clear data flow**: MetricPlugin → Calculator → Validator → Reporter
- **Testable units**: Each component independently testable

## Risks & Mitigations
- **Risk**: More files to navigate
- **Mitigation**: Clear module naming and consistent patterns

## Rollback
Restore original `check_llm_readiness.py` from git history if needed.

## Review Deadline
2025-01-16 (2 weeks)