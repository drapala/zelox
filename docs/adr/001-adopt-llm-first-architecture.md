# ADR-001: Adopt LLM-First Architecture

---
title: Adopt LLM-First Architecture for Repository Organization
date: 2025-09-01
status: accepted
deciders: [Project Team]
consulted: [LLM Agents, Development Team]
informed: [All Contributors]
---

## Front-matter (YAML)
```yaml
# Machine-readable metadata for LLM processing
adr_number: 001
title: "Adopt LLM-First Architecture for Repository Organization"
date: "2025-09-01"
status: "accepted"
tags: ["architecture", "llm-first", "foundational", "vsa", "co-location"]
complexity: high
llm_impact: high
human_impact: medium
reversibility: moderate
review_deadline: "2025-11-01"
supersedes: []
superseded_by: null
```

## Context and Problem Statement

Traditional repository structures optimize for human navigation through layered architectures and DRY principles, but this creates significant cognitive overhead for LLM agents who must "hop" between multiple files to understand and modify features.

**Key Question:** Should we restructure our repository to prioritize LLM agent effectiveness over traditional human-centric conventions?

## Decision Drivers

- [x] Reduces LLM cognitive hops by ≥30%
- [x] Improves time-to-tested-patch
- [x] Maintains LLM Readiness Score ≥80
- [x] Enables faster feature development with AI assistance
- [x] Reduces context switching for both LLMs and humans
- [x] Improves code discoverability through explicit navigation aids

## Considered Options

1. **Option 1: Full LLM-First with VSA** - Complete vertical slice architecture with co-location
2. **Option 2: Hybrid Approach** - Keep critical shared code separate, co-locate features
3. **Option 3: Status Quo** - Maintain traditional layered architecture with better documentation

## Decision

**We will:** Adopt Option 1 - Full LLM-First architecture with Vertical Slice Architecture, co-locating all feature-related code and accepting controlled duplication where it reduces cognitive complexity.

### Option Details

#### Option 1: Full LLM-First with VSA
- **Description:** Organize code by features with complete co-location of domain, application, infrastructure, and tests. Accept controlled duplication to minimize cross-references.
- **LLM Benefits:**
  - Single directory contains entire feature context
  - Reduces average hops from 5-7 to 1-2
  - Natural language prompts map directly to feature directories
  - Faster comprehension and modification
- **LLM Costs:**
  - Initial migration effort
  - Need for drift-check tooling
- **Human Impact:** Requires adjustment period but ultimately improves feature isolation

#### Option 2: Hybrid Approach
- **Description:** Co-locate most feature code but maintain shared utilities and core domain separately.
- **LLM Benefits:**
  - Partial reduction in cognitive hops
  - Some improvement in context locality
- **LLM Costs:**
  - Still requires cross-directory navigation
  - Ambiguous boundaries between shared and feature code
- **Human Impact:** Easier transition but perpetuates some navigation issues

#### Option 3: Status Quo
- **Description:** Keep traditional layers but add extensive documentation and navigation aids.
- **LLM Benefits:**
  - No migration required
  - Familiar structure
- **LLM Costs:**
  - Maintains high cognitive load
  - Documentation alone doesn't reduce hops
- **Human Impact:** No change required but doesn't address core issues

## Consequences

### Positive
- ✅ 70% reduction in cross-file navigation for feature changes
- ✅ Direct mapping between user requests and code locations
- ✅ Improved testability through co-located tests
- ✅ Faster onboarding for both LLMs and new developers
- ✅ Natural boundaries for microservice extraction if needed

### Negative
- ❌ Some controlled code duplication (mitigated by drift-check)
- ❌ Initial learning curve for team members
- ❌ Requires tooling investment for maps/indexes

### Neutral
- ➖ Different from industry conventions
- ➖ Requires explicit governance and review processes

## Implementation

### Files Affected
```yaml
files:
  - path: CLAUDE.md
    changes: Created LLM-first directive file
  - path: docs/adr/
    changes: Established ADR structure
  - path: docs/repo/
    changes: Will contain REPO_MAP.md, INDEX.yaml, FACTS.md
  - path: features/
    changes: New directory for vertical slices
  - path: scripts/
    changes: Will contain LLM support tooling
```

### Migration Steps
1. Create initial scaffold directories (docs/, features/, scripts/)
2. Implement core tooling (gen_repo_map.py, check_llm_readiness.py)
3. Migrate first feature as pilot to features/ directory
4. Document patterns in README_FOR_HUMANS.md
5. Migrate remaining features incrementally
6. Set up CI/CD gates for LLM readiness score

### Rollback Plan
1. Git revert to pre-migration commit
2. Move features back to layered structure
3. Remove LLM-first tooling and checks
4. Update documentation to reflect traditional structure

## Metrics and Validation

### Success Metrics
- [x] LLM Readiness Score remains ≥80
- [ ] Average cognitive hops reduced from 5-7 to ≤2
- [ ] Time-to-tested-patch improved by 50%
- [ ] 90% of changes require editing files in single feature directory
- [ ] Drift-check identifies 100% of unintended divergence

### Validation Commands
```bash
# Commands to validate the implementation
make llm.check
make test.fast
python scripts/check_llm_readiness.py
python scripts/drift_check.py
```

## Notes for LLM Agents

### When Working With This Decision
- **Always check:** Feature's local README.md before making changes
- **Never modify:** Core navigation files (REPO_MAP.md, INDEX.yaml) without updating all references
- **Common pitfalls:** 
  - Don't create unnecessary abstractions to avoid duplication
  - Always update front-matter when modifying files
  - Run drift-check after duplicating code blocks

### Related Context
- **Dependencies:** None (foundational ADR)
- **See also:** 
  - `CLAUDE.md` - Full LLM-first architecture specification
  - `docs/repo/REPO_MAP.md` - Repository navigation map
  - `docs/repo/INDEX.yaml` - Module index and contracts
  - `features/*/README.md` - Feature-specific documentation

## Review and Update

- **Review deadline:** 2025-11-01
- **Review criteria:** 
  - After migrating 3+ features
  - If LLM Readiness Score drops below 80
  - If time-to-tested-patch exceeds baseline
- **Update history:**
  - 2025-09-01: Initial adoption