# ADR-003: Adopt PR LOC Gate for LLM-Friendly Reviews (Exclude Markdown)

---
title: Adopt PR LOC Gate for LLM-Friendly Reviews (Exclude Markdown)
date: 2025-09-01
status: proposed
deciders: [Development Team, DevOps Team]
consulted: [LLM Agents, Backend Engineers, QA Team]
informed: [All Contributors]
---

## Front-matter (YAML)
```yaml
# Machine-readable metadata for LLM processing
adr_number: 003
title: "Adopt PR LOC Gate for LLM-Friendly Reviews (Exclude Markdown)"
date: "2025-09-01"
status: "proposed"
tags: ["ci", "quality-gates", "llm-first", "developer-experience", "pr-size"]
complexity: low
llm_impact: high
human_impact: medium
reversibility: easy
review_deadline: "2025-11-01"
supersedes: []
superseded_by: null
```

## Context and Problem Statement

LLM agents (and humans) review small, focused PRs more effectively. We have existing limits (≤10 files OR ≤500 LOC), but current counting includes text files (e.g., `.md`) that don't affect behavior and pollute metrics. We need an effective LOC gate that excludes Markdown and similar files to avoid blocking documentation while keeping code PRs small.

**Key Question:** How do we measure and enforce in CI a LOC limit per PR that excludes Markdown without allowing large code PRs to slip through?

## Decision Drivers

- [x] Reduces LLM cognitive hops by ≥30%
- [x] Improves time-to-tested-patch
- [x] Maintains LLM Readiness Score ≥80
- [x] Maintain ≤500 LOC of code and ≤10 code files limit
- [x] Don't penalize documentation/ADR/PROMPT.md changes
- [x] Easy to implement and audit in CI

## Considered Options

1. **Option 1: Total LOC** - Include all files in LOC count
2. **Option 2: Filtered LOC** - Exclude Markdown and pure documentation files
3. **Option 3: Weighted LOC** - Different weights for different file types

## Decision

**We will:** Adopt Option 2 - Filtered LOC: the gate considers only code files, excluding Markdown and purely textual documentation files.

### Option Details

#### Option 1: Total LOC
- **Description:** Count all lines in all files changed in PR, regardless of file type.
- **LLM Benefits:**
  - Simple to understand and implement
  - No special cases to remember
- **LLM Costs:**
  - Documentation changes block PRs unnecessarily
  - Discourages proper documentation updates
- **Human Impact:** Teams avoid updating docs to stay under limits.

#### Option 2: Filtered LOC
- **Description:** Count only lines in code files, excluding pure documentation formats like Markdown.
- **LLM Benefits:**
  - Accurate representation of code complexity
  - Encourages documentation without penalty
  - Clear distinction between code and docs
- **LLM Costs:**
  - None - aligns with LLM cognitive load principles
- **Human Impact:** Teams can update docs freely; code changes remain constrained.

#### Option 3: Weighted LOC
- **Description:** Apply different weights to different file types (e.g., 0.5x for config, 1x for code).
- **LLM Benefits:**
  - More nuanced complexity measurement
- **LLM Costs:**
  - Complex to understand and explain
  - Harder to predict if PR will pass
- **Human Impact:** Confusion about what counts how much; overkill for current needs.

## Consequences

### Positive
- ✅ Documentation/ADR PRs don't hit LOC limits
- ✅ More precise LLM reviews (size reflects actual code changes)
- ✅ Simple implementation with in-repo script
- ✅ Encourages proper documentation practices

### Negative
- ❌ Could incentivize moving logic to YAML/JSON; mitigated by including YAML/JSON in count
- ❌ Need to maintain list of excluded extensions

### Neutral
- ➖ Gate doesn't replace reviewer judgment
- ➖ Rare extensions may need fine-tuning

## Implementation

### LOC Policy
- **Hard gate:** `effective_code_loc_added + effective_code_loc_deleted ≤ 500`
- **File gate:** `code_files_changed ≤ 10`
- **Excluded from count:** `*.md`, `*.mdx`, `*.rst`, `*.adoc`, `LICENSE`, `NOTICE`
- **Included (counted):** `*.py`, `*.ts`, `*.tsx`, `*.js`, `*.go`, `*.java`, `*.kt`, `*.rs`, `*.sql`, `*.yml`, `*.yaml`, `*.json`, `Dockerfile`, `Makefile`, etc.

> Rationale: YAML/JSON and configs affect behavior; they remain included.

### Files Affected
```yaml
files:
  - path: scripts/check_pr_loc.py
    changes: Script for effective LOC counting (excludes Markdown)
  - path: Makefile
    changes: New target pr.loc
  - path: .github/workflows/pr-check.yml
    changes: Add LOC gate step before tests
  - path: docs/repo/FACTS.md
    changes: Register PR LOC policy
```

### Migration Steps
1. Add `scripts/check_pr_loc.py` and Makefile target `pr.loc`
2. Include step in PR workflow before running tests
3. Document policy in `docs/repo/FACTS.md` (e.g., FACT:PR_LOC_GATE)
4. Communicate to team and update PR templates (suggest chunking)
5. Monitor for 2 weeks and adjust thresholds if needed

### Rollback Plan
1. Remove `pr.loc` from workflow
2. Keep only global file/LOC gate from previous implementation
3. No code changes required

## Metrics and Validation

### Success Metrics
- [x] 100% of PRs pass through `pr.loc` gate
- [ ] Reduction in PRs blocked only by docs
- [ ] Average PR review time decreases (LLM proxy)
- [ ] LLM Readiness Score ≥80 maintained
- [ ] Documentation quality improves (more updates)

### Validation Commands
```bash
# Check current PR
make pr.loc

# Test against specific ref
python3 scripts/check_pr_loc.py origin/main...HEAD

# Dry run on recent PRs
git log --oneline -10 | while read sha _; do
  echo "PR $sha:"
  python3 scripts/check_pr_loc.py $sha^..$sha
done
```

## Notes for LLM Agents

### When Working With This Decision
- **Always check:** Run `make pr.loc` locally before opening PR
- **Never modify:** Excluded extensions without new ADR
- **Common pitfalls:** 
  - Don't try to "hide" large changes in YAML/JSON - they count
  - Split large PRs early, don't wait for CI to fail
  - Documentation PRs can be large - that's intentional

### Script Implementation
The `check_pr_loc.py` script will:
1. Get list of changed files via `git diff`
2. Filter out documentation-only files
3. Count added/deleted lines in remaining files
4. Fail if exceeding limits
5. Provide clear feedback on what counts

### Related Context
- **Dependencies:** ADR-001 (LLM-First Architecture)
- **See also:** 
  - `.github/workflows/pr-check.yml`
  - `scripts/check_pr_loc.py`
  - `docs/repo/FACTS.md`
  - `docs/repo/pr-guidelines.md`

## Review and Update

- **Review deadline:** 2025-11-01
- **Review criteria:** 
  - Gate reduces friction on doc PRs without loosening code PRs
  - Chunking rate increases appropriately
  - No gaming of the system observed
- **Update history:**
  - 2025-09-01: Initial proposal