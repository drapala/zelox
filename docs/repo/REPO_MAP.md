# REPO_MAP.md - Repository Navigation Guide

**Generated:** 2025-09-01  
**Purpose:** LLM-first navigation and context discovery

## Repository Structure

```
zelox/
├── docs/                    # Documentation & decisions
│   ├── adr/                # Architecture Decision Records
│   └── repo/               # Repository metadata
├── features/               # Vertical feature slices (VSA)
├── shared/                 # Truly shared utilities only
└── scripts/                # LLM-first tooling
```

## Quick Navigation

### For Feature Development
1. **Start here:** `features/[feature_name]/README.md`
2. **Business logic:** `features/[feature_name]/service.py`
3. **Tests:** `features/[feature_name]/tests.py`
4. **API:** `features/[feature_name]/api.py`

### For Architecture Changes
1. **Decisions:** `docs/adr/`
2. **Patterns:** `CLAUDE.md`
3. **Current state:** `docs/repo/FACTS.md`

### For LLM Agents
1. **Entry point:** This file (REPO_MAP.md)
2. **Module index:** `docs/repo/INDEX.yaml`
3. **Recovery patterns:** `docs/repo/recovery_patterns.yaml`

## Current Features

### Template
- **Path:** `features/template/`
- **Capabilities:** HTTP API, Business Logic, Tests
- **Files:** 6 Python modules


## LLM-First Tooling

- **`validate_schemas.py`**: Python module
- **`check_llm_readiness.py`**: Python module
- **`check_readme_coverage.py`**: Python module
- **`check_pr_loc.py`**: Python module
- **`gen_repo_map.py`**: Auto-generate REPO_MAP.md from current codebase state


## Architecture Decisions

| ADR | Title | Status | Impact |
|-----|-------|---------|---------|
| [001](../adr/001-adopt-llm-first-architecture.md) | Adopt LLM-First Architecture | accepted | high |
| [002](../adr/002-adopt-bdd-lite.md) | Adopt BDD-Lite for Critical Features | proposed | medium |
| [003](../adr/003-pr-loc-gate.md) | PR LOC Gate (Exclude Markdown) | proposed | medium |
| [004](../adr/004-llm-first-observability.md) | LLM-First Observability Standards | proposed | high |

## Common Tasks

### Adding a New Feature
1. `mkdir features/[feature_name]`
2. Copy template from `features/template/`
3. Update `docs/repo/INDEX.yaml`
4. Run `make llm.check`

### Making Changes
1. Check `features/[feature]/README.md` first
2. Look for BDD-Lite scenarios in tests
3. Update `OBS_PLAN.md` if changing APIs
4. Run `make pr.loc` before committing

## Last Updated
- **Auto-generated:** 2025-09-01
- **Script:** `scripts/gen_repo_map.py`
- **Next review:** When repository structure changes significantly
