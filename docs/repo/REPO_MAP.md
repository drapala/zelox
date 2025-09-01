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

*None yet - this is a new repository*

## Hot Paths (Most Changed)

*To be populated by `scripts/gen_repo_map.py`*

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

## INDEX.yaml – New Fields Cheat Sheet

Use these optional fields to enrich context for agents. Keep entries concise; prefer links for long docs.

### Metadata / Dependencies / Gates / Navigation

```yaml
metadata:
  repo_url: "https://github.com/yourorg/zelox"
  default_branch: "main"

dependencies:
  package_manager: pnpm
  build_tool: turbo
  test_framework: pytest
  lint_tool: ruff

gates:
  coverage_threshold: 80      # 0–100
  max_file_loc: 800           # warn over this LOC/file

navigation:
  glossary: "docs/repo/GLOSSARY.md"
  diagrams: "docs/diagrams/INDEX.md"
```

### Feature Extras

```yaml
features:
  - name: user_management
    domain: identity
    capability: user_onboarding
    contracts:
      entrypoints:
        - name: register_user
          type: api
          file: api.py:register_user
          description: "Create a user and send verification email"
          io:
            input: { type: object, required: [email], properties: { email: { type: string, format: email } } }
            output: { type: object, properties: { id: { type: string } } }
          http:
            method: POST
            path: /users
            status_codes: [201, 400]
          auth:
            required_scopes: ["users:write"]
            roles: ["admin"]
          idempotent: false
          side_effects: ["db_write", "email"]
          examples:
            - name: happy_path
              request: { email: "user@example.com" }
              response: { id: "usr_123" }
        - name: verify_pending
          type: job
          file: jobs.py:verify_pending
          schedule: "0 * * * *"
        - name: on_user_created
          type: event_handler
          file: events.py:on_user_created
          event: { topic: users, name: user.created, source: auth_service }
    events:
      publishes: ["user.created"]
      consumes: ["user.verified"]
    docs:
      readme: features/user_management/README.md
      diagram: docs/diagrams/user_onboarding.png
    adr_links: [3, 4]
    risks: ["high churn"]
    files:
      - path: service.py
        role: application
        purpose: "business orchestration"
        coverage: 85
        exports: ["register_user"]
```

### Shared Module Extras

```yaml
shared:
  - name: auth
    path: shared/auth
    purpose: "JWT token management"
    used_by: ["user_management", "api_gateway"]
    version: "1.2.0"
    since_version: "0.1.0"
    replacement: null
    api_doc: docs/shared/auth.md
```

### Scripts – Ownership and IO

```yaml
scripts:
  - name: check_pr_loc
    path: scripts/check_pr_loc.py
    purpose: "Enforce PR size limits"
    owners: ["platform-team"]
    effects: ["ci_gate"]
    inputs: [{ name: diff, type: git }]
    outputs: [{ name: report, type: json }]
```

### Observability – Scoping Metrics

In each feature `OBS_PLAN.md`, scope metrics to a feature/entrypoint:

```yaml
metrics:
  - name: user_request_duration_p95
    type: latency
    budget: 200ms
    alert_threshold: 500ms
    applies_to:
      feature: user_management
      entrypoint: register_user
```

## Complexity Hotspots

*To be populated by `scripts/confusion_report.py`*

## Last Updated
- **Auto-generated:** Never (manual for now)
- **Manual update:** 2025-09-01
- **Next review:** When first feature is implemented
