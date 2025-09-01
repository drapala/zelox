# ADR-006: Differentiated LOC Limits by File Category

---
title: Implement Differentiated LOC Limits by File Category
date: 2025-09-01
status: accepted
deciders: [drapala, LLM-First Architecture Team]
consulted: [Development Team, LLM Agents]
informed: [All Contributors]
---

## Front-matter (YAML)
```yaml
# Machine-readable metadata for LLM processing
adr_number: 006
title: "Implement Differentiated LOC Limits by File Category"
date: "2025-09-01"
status: "accepted"
tags: ["ci", "quality-gates", "testing", "llm-first", "pr-size", "developer-experience"]
complexity: medium
llm_impact: high
human_impact: high
reversibility: easy
review_deadline: "2025-11-01"
supersedes: []
superseded_by: null
related_features: ["pr_validation", "ci_pipeline"]
drivers: ["test_coverage", "code_quality", "cognitive_load", "developer_productivity"]
alternatives: ["flat_limit", "no_test_limit", "dynamic_limits"]
```

## Context and Problem Statement

ADR-003 established a flat 500 LOC limit for all non-documentation code changes. However, this creates an unintended consequence: developers are discouraged from writing comprehensive tests because test code counts against the same limit as application code.

**Key Question:** How can we maintain small, reviewable PRs while incentivizing thorough testing and proper configuration?

## Decision Drivers

- [x] Incentivize comprehensive testing without penalizing developers
- [x] Maintain cognitive load limits for both humans and LLMs
- [x] Prevent abuse through unlimited test/config additions
- [x] Support different review patterns for different file types
- [x] Align with LLM-first principles of clarity and focus

## Considered Options

1. **Option 1: Differentiated Limits** - Category-based limits with different thresholds
2. **Option 2: Flat Limit** - Keep current 500 LOC for everything (status quo)
3. **Option 3: No Test Limit** - Exclude tests entirely from LOC counting
4. **Option 4: Dynamic Limits** - Adjust limits based on PR content ratio

## Decision

**We will:** Adopt Option 1 - Implement differentiated LOC limits based on file categories, with tests and configuration having more generous limits than application code.

### Option Details

#### Option 1: Differentiated Limits (CHOSEN)
- **Description:** Categorize files and apply different LOC limits per category
  - Application code: 500 LOC, 10 files
  - Test code: 1000 LOC, 20 files
  - Configuration: 250 LOC, 5 files
  - Documentation: No limit (already excluded)
  - Total safety net: 25 files maximum

- **LLM Benefits:**
  - Clear cognitive boundaries for different types of changes
  - Encourages comprehensive test coverage
  - Maintains focus on small application changes
  
- **LLM Costs:**
  - Slightly more complex validation logic
  - Need to categorize files correctly
  
- **Human Impact:** 
  - Removes disincentive for writing tests
  - Clearer expectations for different PR types
  - Better alignment with development workflow

#### Option 2: Flat Limit (REJECTED)
- **Description:** Keep current 500 LOC for all code
- **Why Rejected:** Creates perverse incentive to write fewer tests

#### Option 3: No Test Limit (REJECTED)  
- **Description:** Completely exclude tests from LOC counting
- **Why Rejected:** Risk of massive test PRs that are still hard to review

#### Option 4: Dynamic Limits (REJECTED)
- **Description:** Adjust limits based on test-to-code ratio
- **Why Rejected:** Too complex, unpredictable for developers

## Consequences

### Positive
- ✅ Developers can write comprehensive tests without PR rejection
- ✅ Application changes remain small and focused (500 LOC limit)
- ✅ Configuration changes are properly constrained (250 LOC)
- ✅ Clear mental model: different file types have different limits
- ✅ Incentivizes test-driven development practices

### Negative
- ❌ Validation logic becomes more complex
- ❌ Edge cases in file categorization may occur
- ❌ Total PR size could be larger (up to 1750 LOC theoretically)

### Neutral
- ➖ Requires updating existing validation scripts
- ➖ Teams need to understand the categorization rules

## Implementation

### File Categorization Rules

```python
CATEGORIES = {
    "TEST": [
        r"/test_[^/]*\.py$",      # test_*.py files
        r"/[^/]*_test\.py$",       # *_test.py files  
        r"\.test\.[tj]sx?$",       # *.test.js/ts
        r"\.spec\.[tj]sx?$",       # *.spec.js/ts
        r"^tests?/",               # test directories
    ],
    "CONFIG": [
        r"^\.github/.*\.ya?ml$",   # GitHub workflows
        r"^schemas/.*\.json$",     # JSON schemas
        r"Dockerfile$",             # Docker files
        r"^\..*rc(\..*)?$",        # Dotfiles
    ],
    "DOCUMENTATION": [
        r"\.md$",                   # Markdown (no limit)
    ],
    "APPLICATION": [
        # Everything else defaults to application code
    ]
}
```

### Limit Structure

| Category | LOC Limit | File Limit | Rationale |
|----------|-----------|------------|-----------|
| Application | 500 | 10 | Maintain focus, reduce cognitive load |
| Test | 1000 | 20 | Encourage comprehensive testing |
| Config | 250 | 5 | Config changes should be minimal |
| Documentation | None | None | Always encourage documentation |
| **Total (safety)** | - | 25 | Prevent extremely large PRs |

### Files Affected
```yaml
files:
  - path: scripts/check_pr_loc.py
    changes: Refactored to implement categorization logic
  - path: .github/workflows/pr-check.yml
    changes: Updated comments to explain categorization
  - path: docs/adr/006-differentiated-loc-limits.md
    changes: Created this ADR
```

## Metrics and Validation

### Success Metrics
- [ ] Average test coverage increases by >20%
- [ ] PR rejection rate for "too many LOC" decreases by >50%
- [ ] Developer satisfaction with PR process improves
- [ ] No abuse cases (massive test-only PRs) observed

### Validation Commands
```bash
# Test the new categorization locally
python3 scripts/check_pr_loc.py origin/main...HEAD

# Verify specific category limits
git diff --name-only origin/main...HEAD | \
  xargs -I {} python3 -c "from check_pr_loc import categorize_file; print('{}: ', categorize_file('{}'))"
```

## Notes for LLM Agents

### When Working With This Decision
- **Always check:** File category before suggesting PR splits
- **Remember:** Tests can be larger (1000 LOC) than application code (500 LOC)
- **Common pitfalls:** 
  - Don't suggest splitting test files unnecessarily
  - Config files have the strictest limit (250 LOC)
  - Total file count still matters (25 max)

### Category Detection Examples
```python
# These are TEST files:
"tests/test_user_service.py"      → TEST (1000 LOC limit)
"src/user_test.py"                → TEST
"components/Button.test.tsx"       → TEST

# These are CONFIG files:
".github/workflows/ci.yml"         → CONFIG (250 LOC limit)
"schemas/user.json"                → CONFIG
"Dockerfile"                       → CONFIG

# These are APPLICATION files:
"src/user_service.py"              → APPLICATION (500 LOC limit)
"components/Button.tsx"            → APPLICATION
"utils/helpers.js"                 → APPLICATION
```

## Review and Update

- **Review deadline:** 2025-11-01
- **Review criteria:** 
  - After 50+ PRs processed with new limits
  - If abuse patterns emerge
  - If categorization needs adjustment
- **Update history:**
  - 2025-09-01: Initial implementation