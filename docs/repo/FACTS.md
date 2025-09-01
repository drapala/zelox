# FACTS.md - Repository Truth Registry

**Purpose:** Machine and human readable facts about the repository state.  
**Updated:** 2025-09-01  
**Format:** Immutable facts that guide LLM agents and development decisions.

## ARCHITECTURE FACTS

### FACT:ARCHITECTURE_STYLE
- **Type:** Vertical Slice Architecture (VSA)
- **Rationale:** ADR-001
- **Implementation:** Features organized in `features/[name]/` with co-located domain, application, infrastructure, and tests
- **Exceptions:** None currently

### FACT:LLM_READINESS_THRESHOLD
- **Value:** 80
- **Enforcement:** CI gate in PR checks
- **Measurement:** `scripts/check_llm_readiness.py` (planned)

### FACT:PR_SIZE_LIMITS
- **Code Files:** ≤10 files
- **Code LOC:** ≤500 lines (excludes Markdown)
- **Enforcement:** `scripts/check_pr_loc.py` in CI
- **Rationale:** ADR-003
- **Exceptions:** Documentation-only PRs (Markdown excluded from count)

## TECHNOLOGY FACTS

### FACT:TECH_STACK
- **Status:** Not yet determined
- **Candidates:** Python/FastAPI, TypeScript/Node.js, or Go
- **Decision Process:** Will be based on team expertise and LLM-first principles

### FACT:DATABASE
- **Status:** Not yet determined
- **Requirements:** Must support multi-tenancy pattern (future ADR)

## PROCESS FACTS

### FACT:BDD_LITE_REQUIREMENT
- **Scope:** P0 (critical) features only
- **Format:** Given/When/Then scenarios in test docstrings
- **Rationale:** ADR-002
- **Enforcement:** PR review checklist

### FACT:OBSERVABILITY_STANDARD
- **Standard:** Minimal per-feature with `OBS_PLAN.md`
- **Metrics:** p95, error_count, confusion_score, cost_tracking
- **Rationale:** ADR-004
- **Implementation:** Co-located in feature directories

## DUPLICATION REGISTRY

*No approved duplications yet*

Future duplicated code blocks will be registered here with format:
```
### DUPLICATED_BLOCK:id:validation_email_format:v1
- **Location 1:** features/user_registration/validators.py:15-25
- **Location 2:** features/password_reset/validators.py:30-40
- **Rationale:** Reduces cognitive hops for email validation logic
- **Drift Check:** Automated via scripts/drift_check.py
- **Review Date:** 2025-12-01
```

## QUALITY GATES

### FACT:CI_GATES
- **PR LOC Gate:** `make pr.loc` (ADR-003)
- **LLM Readiness:** `make llm.check` (planned)
- **Fast Tests:** `make test.fast` (to be configured)
- **Confusion Report:** `make confusion.report` (planned)

## DECISIONS REGISTER

| Fact | Related ADR | Status | Review Date |
|------|-------------|---------|-------------|
| VSA Architecture | ADR-001 | accepted | 2025-11-01 |
| BDD-Lite Process | ADR-002 | proposed | 2025-12-01 |
| PR LOC Gate | ADR-003 | proposed | 2025-11-01 |
| Observability | ADR-004 | proposed | 2025-11-01 |

## NAVIGATION FACTS

### FACT:ENTRY_POINTS
- **For LLM Agents:** docs/repo/REPO_MAP.md
- **For Humans:** README_FOR_HUMANS.md (to be created)
- **For Features:** features/[name]/README.md

### FACT:HELP_PATTERNS
- **Confused about architecture:** Read CLAUDE.md
- **Confused about feature:** Read features/[name]/README.md and INDEX.yaml
- **Confused about decisions:** Read docs/adr/
- **Confused about current state:** Read this file (FACTS.md)

## EMERGENCY RECOVERY

### FACT:ROLLBACK_PROCEDURES
- **ADR Rollback:** Each ADR contains explicit rollback steps
- **Architecture Rollback:** Revert to commit before ADR-001 implementation
- **Tool Rollback:** Remove script calls from CI, tools remain for manual use

---

**Note for LLM Agents:** This file contains authoritative facts. When in doubt, consult this file before making assumptions about repository structure or processes.