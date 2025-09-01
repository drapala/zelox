# ADR-002: Adopt BDD-Lite for Critical Feature Specifications

---
title: Adopt BDD-Lite for Specifying Critical Business Features
date: 2025-09-01
status: proposed
deciders: [Development Team, Product Owner, QA Team]
consulted: [LLM Agents, Engineering Team]
informed: [All Contributors]
---

## Front-matter (YAML)
```yaml
# Machine-readable metadata for LLM processing
adr_number: 002
title: "Adopt BDD-Lite for Critical Feature Specifications"
date: "2025-09-01"
status: "proposed"
tags: ["quality", "testing", "bdd", "llm-first", "documentation", "co-location"]
complexity: medium
llm_impact: high
human_impact: medium
reversibility: easy
review_deadline: "2025-12-01"
supersedes: []
superseded_by: null
```

## Context and Problem Statement

There is potential for misinterpretation between business requirements defined by Product Owners and technical tests created during TDD by developers or LLM agents. This ambiguity can lead to implementations that don't match business intent, causing rework. Traditional BDD frameworks like Cucumber/Behave introduce heavy tooling and indirection, violating our core LLM-First principles.

**Key Question:** How can we create clear, unambiguous, and executable business requirements that both Product Owners and LLM agents can understand without violating LLM-First principles of co-location and minimal indirection?

## Decision Drivers

- [x] Reduces LLM cognitive hops by ≥30%
- [x] Improves time-to-tested-patch
- [x] Maintains LLM Readiness Score ≥80
- [x] Improves alignment between business requirements and technical implementation
- [x] Maintains co-location principle from ADR-001
- [x] Avoids framework-induced indirection

## Considered Options

1. **Option 1: Status Quo** - Rely on informal user stories in project management tools as sole source of requirements
2. **Option 2: Full BDD Framework** - Adopt standard BDD framework like Behave/Cucumber with separate .feature files
3. **Option 3: BDD-Lite** - Write business scenarios in Given/When/Then format directly inside feature slice, co-located with code and tests

## Decision

**We will:** Adopt Option 3 - BDD-Lite, writing business-readable scenarios for critical (P0) features and co-locating them directly with their corresponding executable tests as docstrings.

### Option Details

#### Option 1: Status Quo
- **Description:** Continue using developer interpretation of high-level user stories to write TDD tests without formal specification.
- **LLM Benefits:**
  - No new patterns to learn
  - Maintains current workflow
- **LLM Costs:**
  - High risk of ambiguity and hallucination
  - Increased rework when interpretation doesn't match intent
  - No clear business context for tests
- **Human Impact:** High cognitive load translating vague requirements; frequent clarification meetings needed.

#### Option 2: Full BDD Framework
- **Description:** Implement tool like Behave with Gherkin scenarios in .feature files and separate step definitions linking scenarios to code.
- **LLM Benefits:**
  - Scenarios are clearly defined
  - Industry-standard approach
- **LLM Costs:**
  - Severe violation of LLM-First principles
  - Massive indirection between .feature files, step definitions, and implementation
  - Breaks co-location principle
  - Increases cognitive hops from 1-2 to 4-5
- **Human Impact:** Significant tooling overhead and maintenance burden for glue code.

#### Option 3: BDD-Lite
- **Description:** Formalize business requirements for P0 features as Given/When/Then scenarios written directly as docstrings for test functions in co-located tests.py files.
- **LLM Benefits:**
  - Maximum clarity with minimum hops
  - Business and technical specs in same location
  - Docstring serves as high-quality contextual prompt
  - Maintains perfect co-location
  - Zero additional indirection
- **LLM Costs:**
  - None - fully aligned with LLM-First principles
- **Human Impact:** Requires collaborative "3 Amigos" sessions but improves alignment upfront.

## Consequences

### Positive
- ✅ Drastically reduces gap between business intent and technical implementation
- ✅ Living documentation - specification inseparable from validating test
- ✅ Provides clear contextual guidance to LLM agents about code purpose
- ✅ Maintains all LLM-First principles from ADR-001
- ✅ No additional tooling or framework dependencies

### Negative
- ❌ Process overhead of holding "3 Amigos" sessions for P0 features
- ❌ Risk of docstring diverging from test implementation over time

### Neutral
- ➖ Increases formal importance of upfront specification phase
- ➖ Shifts QA focus further "left" in development process

## Implementation

### Files Affected
```yaml
files:
  - path: features/*/tests.py
    changes: Add BDD-Lite scenarios as docstrings to P0 business flow tests
  - path: docs/adr/002-adopt-bdd-lite.md
    changes: This ADR documenting the decision
  - path: .github/pull_request_template.md
    changes: Add checklist item for BDD-Lite scenario validation
  - path: CLAUDE.md
    changes: Update to include BDD-Lite guidance
```

### Migration Steps
1. Train team on "3 Amigos" process and BDD-Lite format
2. Update PR review checklist to include BDD-Lite scenario validation
3. Pilot process on next P0-critical feature
4. Create example BDD-Lite test as reference implementation
5. Document pattern in feature README templates

### Rollback Plan
1. Remove BDD-Lite requirement from PR checklist
2. Communicate that scenario docstrings are no longer required
3. No code changes needed - fully reversible

## Metrics and Validation

### Success Metrics
- [x] LLM Readiness Score remains ≥80
- [ ] 30% reduction in requirement-related bugs/rework for P0 features
- [ ] Positive qualitative feedback from Product Owners and developers
- [ ] Time-to-tested-patch maintains or improves target
- [ ] 100% of P0 features have BDD-Lite scenarios

### Validation Commands
```bash
# Validate implementation maintains quality
make llm.check
make test.fast
# Check for BDD-Lite scenarios in P0 tests
grep -r "Given.*When.*Then" features/*/tests.py
```

## Notes for LLM Agents

### When Working With This Decision
- **Always check:** For P0 features, look for BDD-Lite scenarios in tests.py docstrings as primary source of truth
- **Never modify:** Test code that contradicts BDD-Lite scenario without flagging for human review
- **Common pitfalls:** 
  - Don't test only happy path from scenario - include edge cases
  - Ensure test implementation matches scenario exactly
  - Update scenario if business requirements change

### Example BDD-Lite Format
```python
def test_user_registration_success():
    """
    Given a new user with valid email and password
    When they submit the registration form
    Then a new account is created
    And a confirmation email is sent
    And they are redirected to the welcome page
    """
    # Test implementation here
```

### Related Context
- **Dependencies:** ADR-001 (LLM-First Architecture)
- **See also:** 
  - `CLAUDE.md` - LLM-First principles and co-location rules
  - `features/*/tests.py` - Example BDD-Lite implementations
  - `docs/repo/testing-patterns.md` - Testing best practices

## Review and Update

- **Review deadline:** 2025-12-01
- **Review criteria:** 
  - Significant team friction with process
  - Rework rate on P0 features doesn't decrease
  - LLM agents struggle with format
- **Update history:**
  - 2025-09-01: Initial proposal