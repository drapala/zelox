# ADR-[NUMBER]: [TITLE]

---
title: [Descriptive title of the decision]
date: [YYYY-MM-DD]
status: [proposed|accepted|rejected|deprecated|superseded]
deciders: [List of people involved in the decision]
consulted: [List of people consulted]
informed: [List of people informed]
---

## Front-matter (YAML)
```yaml
# Machine-readable metadata for LLM processing
adr_number: [NUMBER]
title: "[TITLE]"
date: "[YYYY-MM-DD]"
status: "[proposed|accepted|rejected|deprecated|superseded]"
tags: ["architecture", "llm-first", "refactor", etc.]
complexity: [low|medium|high]
llm_impact: [low|medium|high]
human_impact: [low|medium|high]
reversibility: [easy|moderate|hard]
review_deadline: "[YYYY-MM-DD]"
supersedes: [] # List of ADR numbers this supersedes
superseded_by: null # ADR number that supersedes this
```

## Context and Problem Statement

[1-3 sentences describing the context and the problem we're trying to solve]

**Key Question:** [The main question this ADR answers]

## Decision Drivers

- [ ] Reduces LLM cognitive hops by ≥30%
- [ ] Improves time-to-tested-patch
- [ ] Maintains LLM Readiness Score ≥80
- [ ] [Additional project-specific drivers]

## Considered Options

1. **Option 1: [Name]** - [One-line description]
2. **Option 2: [Name]** - [One-line description]
3. **Option 3: [Name]** - [One-line description]

## Decision

**We will:** [1-2 sentences stating the decision]

### Option Details

#### Option 1: [Name]
- **Description:** [2-3 sentences]
- **LLM Benefits:**
  - [Benefit 1]
  - [Benefit 2]
- **LLM Costs:**
  - [Cost 1]
  - [Cost 2]
- **Human Impact:** [1 sentence]

#### Option 2: [Name]
[Same structure as Option 1]

#### Option 3: [Name]
[Same structure as Option 1]

## Consequences

### Positive
- ✅ [Consequence 1]
- ✅ [Consequence 2]
- ✅ [Consequence 3]

### Negative
- ❌ [Consequence 1]
- ❌ [Consequence 2]

### Neutral
- ➖ [Consequence 1]
- ➖ [Consequence 2]

## Implementation

### Files Affected
```yaml
files:
  - path: [file1.py]
    changes: [brief description]
  - path: [file2.py]
    changes: [brief description]
```

### Migration Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Rollback Plan
1. [Rollback step 1]
2. [Rollback step 2]
3. [Rollback step 3]

## Metrics and Validation

### Success Metrics
- [ ] LLM Readiness Score remains ≥80
- [ ] Average cognitive hops reduced from X to Y
- [ ] Time-to-tested-patch improved by X%
- [ ] [Additional metrics]

### Validation Commands
```bash
# Commands to validate the implementation
make llm.check
make test.fast
```

## Notes for LLM Agents

### When Working With This Decision
- **Always check:** [What to verify before implementing]
- **Never modify:** [What should remain unchanged]
- **Common pitfalls:** [Known issues to avoid]

### Related Context
- **Dependencies:** [Related ADRs, modules, or systems]
- **See also:** 
  - `docs/repo/REPO_MAP.md`
  - `docs/repo/INDEX.yaml`
  - [Other relevant files]

## Review and Update

- **Review deadline:** [YYYY-MM-DD]
- **Review criteria:** [What triggers a review]
- **Update history:**
  - [YYYY-MM-DD]: [Change description]