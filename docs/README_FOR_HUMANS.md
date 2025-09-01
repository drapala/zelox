# README_FOR_HUMANS.md - LLM-First Development Guide

**Purpose:** Human-readable guide for working with this LLM-first repository  
**Author:** Drapala  
**Updated:** 2025-09-01

## Why LLM-First Architecture?

This repository is optimized for **LLM agent effectiveness** rather than traditional human conventions. We prioritize:

- **Co-location** over separation of concerns
- **Explicit code** over clever abstractions  
- **Duplication** over wrong abstractions
- **Linear flows** over deep indirection

This approach reduces the time from idea → tested patch by 50%+ when working with AI assistants.

## How to Edit (5 Lines)

1. **Keep one purpose per file** (150–300 LOC ideal, 500 max)
2. **Update YAML front-matter** at file top when changing contracts
3. **Co-locate tests** (smoke/golden) in the same feature folder
4. **Update INDEX.yaml** after moving files or adding features
5. **Split large PRs** (>10 files or >500 LOC) into PATCH_PLAN_PART_[n].md

## Repository Structure

```
zelox/
├── features/           # Vertical slices (VSA)
│   └── [name]/        # Complete feature with all layers
├── shared/            # Only truly shared code (2+ consumers)
├── docs/              
│   ├── adr/          # Architecture decisions
│   └── repo/         # Navigation metadata
├── schemas/          # Modular JSON schemas
└── scripts/          # LLM-first tooling
```

## Navigation for Humans

### Finding Things
1. **Start:** `docs/repo/REPO_MAP.md` - Overview and navigation
2. **Features:** `features/[name]/README.md` - Feature documentation
3. **Decisions:** `docs/adr/` - Why things are the way they are
4. **Contracts:** `docs/repo/INDEX.yaml` - Machine-readable structure

### Common Tasks

#### Add New Feature
```bash
cp -r features/template features/my_feature
# Edit placeholders
make llm.index.validate  # Validate structure
```

#### Run Quality Gates
```bash
make pr.check           # All gates (LOC, schemas, readiness)
make llm.check         # LLM readiness score
make llm.index.validate # INDEX.yaml validation
```

#### Check PR Size
```bash
make pr.loc            # Check if PR exceeds limits
```

## LLM-First Principles

### Co-location
All related code lives together:
```
features/user_auth/
├── README.md       # Documentation
├── models.py       # Domain models
├── service.py      # Business logic
├── api.py         # HTTP endpoints
├── tests.py       # All tests
└── OBS_PLAN.md    # Observability
```

### Front-matter
Every Python file starts with YAML metadata:
```python
"""
title: User Authentication Service
purpose: Handle user login and session management
inputs: [{"name": "credentials", "type": "UserCredentials"}]
outputs: [{"name": "session", "type": "Session"}]
deps: ["bcrypt", "jwt"]
owners: ["auth-team"]
"""
```

### Minimal Indirection
- One `wiring.py` per feature
- No magic DI containers
- Explicit imports and dependencies
- Clear, traceable execution paths

## Working with Schemas

Our schemas are modular for easier maintenance:

- `schemas/index.schema.json` - Main orchestrator
- `schemas/feature.schema.json` - Feature module validation  
- `schemas/file-info.schema.json` - File metadata
- `schemas/entrypoint.schema.json` - API contracts
- `schemas/script.schema.json` - Tooling scripts
- `schemas/shared.schema.json` - Shared modules

Validate with: `make llm.index.validate`

## Quality Gates

### PR Limits
- **Files:** ≤10 code files (Markdown excluded)
- **LOC:** ≤500 lines (Markdown excluded)
- **Readiness:** Score ≥80

### Required Files
- `CLAUDE.md` - LLM-first principles
- `docs/repo/REPO_MAP.md` - Navigation
- `docs/repo/INDEX.yaml` - Structure
- `docs/repo/FACTS.md` - Truth registry

## Tips for Humans

1. **Let LLMs do the heavy lifting** - They navigate this structure better than traditional layouts
2. **Don't fight the co-location** - It reduces context switching
3. **Embrace duplication** - Small, stable snippets can be copied
4. **Keep files focused** - One clear purpose per file
5. **Update navigation** - Keep INDEX.yaml and REPO_MAP.md current

## Common Pitfalls

### For Humans
- Trying to create deep abstractions (don't)
- Moving tests away from code (keep co-located)
- Creating shared modules too early (wait for 2+ consumers)
- Exceeding file size limits (split at 500 LOC)

### For LLMs
- Not updating front-matter when changing contracts
- Missing cross-references in INDEX.yaml
- Creating circular dependencies
- Ignoring PR size limits

## Getting Help

- **Architecture questions:** Read `docs/adr/`
- **Navigation issues:** Check `docs/repo/REPO_MAP.md`
- **Validation errors:** Run `make llm.index.validate`
- **LLM readiness:** Run `make llm.check`

## Contributing

1. Follow the 5-line editing rules above
2. Run `make pr.check` before submitting
3. Keep LLM Readiness Score ≥80
4. Document decisions in ADRs for significant changes

---

**Remember:** This repository is optimized for AI-assisted development. Embrace the patterns even if they feel unusual - they're designed to minimize the time from idea to tested code.