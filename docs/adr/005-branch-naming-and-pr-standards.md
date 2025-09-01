# ADR-005: Branch Naming Convention and PR Standards

---
title: Branch Naming Convention and PR Standards for LLM-First Development
date: 2025-09-01
status: proposed
deciders: [Development Team, drapala]
consulted: [LLM Agents, DevOps Team]
informed: [All Contributors]
---

## Front-matter (YAML)
```yaml
# Machine-readable metadata for LLM processing
adr_number: 005
title: "Branch Naming Convention and PR Standards for LLM-First Development"
date: "2025-09-01"
status: "proposed"
tags: ["workflow", "ci", "llm-first", "gates", "pr-size", "co-location"]
complexity: low
llm_impact: high
human_impact: medium
reversibility: easy
review_deadline: "2025-10-15"
supersedes: []
superseded_by: null
```

## Context and Problem Statement

Inconsistent branch naming and PR practices lead to confusion for both LLM agents and human developers. We need standardized patterns that communicate intent clearly and enforce our LLM-first principles in every change.

**Key Question:** What branch naming and PR standards will maximize clarity for LLM agents while maintaining our co-location and minimal indirection principles?

## Decision Drivers

- [x] Reduces LLM cognitive hops by ≥30%
- [x] Improves time-to-tested-patch
- [x] Maintains LLM Readiness Score ≥80
- [x] Clear intent communication through branch names
- [x] Enforce co-location in every PR
- [x] Prevent architecture drift

## Considered Options

1. **Option 1: Prefix-based branch naming with strict PR template** - Clear prefixes + comprehensive checklist
2. **Option 2: Free-form naming with automated checks** - Flexible names, rely on CI
3. **Option 3: Ticket-based naming** - Branch names tied to issue numbers

## Decision

**We will:** Adopt Option 1 - Prefix-based branch naming with strict PR template and LLM-first validation checklist.

### Option Details

#### Option 1: Prefix-based branch naming with strict PR template
- **Description:** Standardized prefixes (feature/, test/, fix/, etc.) with descriptive suffixes and comprehensive PR checklist enforcing LLM-first principles.
- **LLM Benefits:**
  - Immediate understanding of change type from branch name
  - PR template ensures co-location is maintained
  - Checklist prevents architecture drift
  - Clear navigation for agents
- **LLM Costs:**
  - None - enhances clarity
- **Human Impact:** Small learning curve, but improves communication.

#### Option 2: Free-form naming with automated checks
- **Description:** Allow any branch name, rely on CI to enforce standards.
- **LLM Benefits:**
  - Flexibility in naming
- **LLM Costs:**
  - Ambiguous intent from branch names
  - Harder for agents to categorize changes
  - No preventive checks before CI
- **Human Impact:** More freedom but less clarity.

#### Option 3: Ticket-based naming
- **Description:** Branch names like "ZELOX-123-fix-bug".
- **LLM Benefits:**
  - Traceability to issues
- **LLM Costs:**
  - Requires external context (ticket system)
  - Numbers don't convey intent
  - Additional hop to understand purpose
- **Human Impact:** Requires ticket system integration.

## Consequences

### Positive
- ✅ Branch intent immediately clear to LLM agents
- ✅ PR checklist prevents co-location violations
- ✅ Consistent workflow across all contributors
- ✅ Early detection of LLM-first principle violations
- ✅ Reduced review cycles

### Negative
- ❌ Slightly more rigid workflow
- ❌ Requires discipline in following conventions

### Neutral
- ➖ Branch names become longer but more descriptive
- ➖ PR creation takes 1-2 minutes more

## Implementation

### Branch Naming Convention
```
<type>/<descriptive-kebab-case-name>

Types:
- feature/    - New functionality
- test/       - Test additions/improvements  
- fix/        - Bug fixes
- docs/       - Documentation only
- refactor/   - Code restructuring
- chore/      - Maintenance, tooling, dependencies

Examples:
- feature/user-authentication-jwt
- test/add-script-validation-unit-tests
- fix/pr-loc-calculation-error
- docs/update-adr-templates
- refactor/simplify-validation-logic
- chore/update-python-dependencies
```

### PR Template (.github/pull_request_template.md)
```markdown
## Description
Brief description of changes (2-3 sentences)

## Type of Change
- [ ] feature/ - New functionality
- [ ] test/ - Test additions/improvements
- [ ] fix/ - Bug fix
- [ ] docs/ - Documentation only
- [ ] refactor/ - Code restructuring
- [ ] chore/ - Maintenance/tooling

## LLM-First Compliance Checklist

### Co-location
- [ ] Tests are in the same directory as code
- [ ] Documentation is with the feature (not in separate docs/)
- [ ] No new shared modules (unless used by 2+ features)

### File Standards
- [ ] All Python files have YAML front-matter
- [ ] Files are 150-500 LOC (split if larger)
- [ ] One clear purpose per file

### Navigation Updates
- [ ] INDEX.yaml updated if features/structure changed
- [ ] REPO_MAP.md updated for significant changes
- [ ] Front-matter updated if contracts changed

### Quality Gates
- [ ] `make pr.loc` passes (≤10 files, ≤500 LOC)
- [ ] `make llm.check` score ≥80
- [ ] `make llm.index.validate` passes
- [ ] BDD-Lite scenarios for P0 features

### Observability (if applicable)
- [ ] OBS_PLAN.md updated for new operations
- [ ] Structured logging with request_id/tenant_id
- [ ] Metrics have budgets and thresholds

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests if external dependencies
- [ ] Golden tests for critical flows

## Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes documented in ADR

## Related Issues
Closes #(issue number)

## Additional Context
Any additional information for reviewers
```

### Files Affected
```yaml
files:
  - path: .github/pull_request_template.md
    changes: Create comprehensive PR template
  - path: docs/adr/005-branch-naming-and-pr-standards.md
    changes: This ADR documenting the decision
  - path: scripts/validate_branch_name.py
    changes: Script to validate branch naming (optional)
  - path: .github/workflows/pr-check.yml
    changes: Add branch name validation
```

### Migration Steps
1. Create PR template in `.github/pull_request_template.md`
2. Update CI to validate branch names
3. Communicate standards to team
4. Update contribution guidelines
5. Monitor compliance for 2 weeks

### Rollback Plan
1. Remove PR template
2. Disable branch name validation in CI
3. Return to previous workflow

## Metrics and Validation

### Success Metrics
- [x] LLM Readiness Score remains ≥80
- [ ] 95% of PRs follow naming convention
- [ ] 90% reduction in co-location violations
- [ ] 50% faster PR review cycles
- [ ] Zero architecture drift incidents

### Validation Commands
```bash
# Validate branch name
git branch --show-current | grep -E '^(feature|test|fix|docs|refactor|chore)/[a-z0-9-]+$'

# Run all PR checks
make pr.check
```

## Notes for LLM Agents

### When Working With This Decision
- **Always check:** Branch name matches change type
- **Never modify:** Skip PR template sections
- **Common pitfalls:** 
  - Creating feature/ branch for test additions
  - Forgetting to update INDEX.yaml
  - Splitting related changes across multiple PRs

### Branch Name Examples
```bash
# Good
feature/add-payment-processing
test/payment-processing-edge-cases
fix/payment-validation-regex
docs/payment-api-examples

# Bad
feature/fix-bug          # Wrong prefix
test-payment             # Missing prefix
feature/PAYMENT-123      # Uppercase/ticket number
misc/various-changes     # Invalid prefix
```

### Related Context
- **Dependencies:** ADR-001 (LLM-First Architecture), ADR-003 (PR LOC Gate)
- **See also:** 
  - `.github/pull_request_template.md`
  - `CONTRIBUTING.md`
  - `.github/workflows/pr-check.yml`

## Review and Update

- **Review deadline:** 2025-10-15
- **Review criteria:** 
  - Adoption rate >90%
  - No significant workflow friction
  - Measurable improvement in PR quality
- **Update history:**
  - 2025-09-01: Initial proposal