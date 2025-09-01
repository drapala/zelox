# README for Humans 👋

Welcome to the **zelox** repository! This README is specifically for human developers who need to understand our LLM-first architecture approach and navigate this codebase effectively.

## 🤖 LLM-First Architecture Philosophy

This codebase is optimized for AI agent effectiveness, not just human readability. Here's what that means:

**Traditional codebases** optimize for human cognition - familiar patterns, extensive abstractions, DRY principles above all else.

**Our LLM-first approach** optimizes for both human AND artificial intelligence, enabling:
- ⚡ Faster AI-assisted development cycles
- 🔄 More reliable automated refactoring 
- 🎯 Better code generation and completion
- 🧠 Reduced cognitive load for both humans and LLMs
- 🔍 Improved code comprehension through explicit context

## 🚀 Why This Matters

LLM agents struggle with the same complexity that makes code hard for humans to maintain:
- **Deep indirection** - following chains of abstractions
- **Scattered context** - business logic spread across multiple files
- **Implicit conventions** - "magic" that requires tribal knowledge
- **High cognitive hops** - needing to understand many modules to make a simple change

By co-locating related code, minimizing abstractions, and providing explicit metadata, we make the codebase more comprehensible to both artificial and human intelligence.

## 🏃‍♀️ Quick Start

### For New Developers
1. **Start here** - Read this file completely (you're doing great!)
2. **LLM Agent Guide** - Review `CLAUDE.md` for complete AI agent guidance  
3. **Navigation** - Check `docs/repo/REPO_MAP.md` for repository structure
4. **Patterns** - Explore `features/template/` for coding conventions
5. **Quality Gates** - Run `make llm.check` to validate changes

### For AI Agents
Start with `CLAUDE.md` - it contains comprehensive guidance for LLM agents working on this codebase, including front-matter standards, architectural patterns, and quality gates.

## 🧠 Key LLM-First Concepts

### Vertical Slice Architecture (VSA)
Instead of horizontal layers (controllers, services, repositories), we organize by **business features**:

```
features/
├── user_management/
│   ├── README.md        # Feature documentation
│   ├── models.py        # Domain entities
│   ├── service.py       # Business logic  
│   ├── repository.py    # Data access
│   ├── api.py          # HTTP endpoints
│   ├── tests.py        # Co-located tests
│   └── wiring.py       # Dependency injection
└── payment_processing/
    ├── README.md
    ├── models.py
    └── ...
```

**Benefits for LLMs:**
- All related code is in one directory
- Changes typically affect only one feature slice
- Context switching between modules is minimized
- Business logic is co-located with its tests

### Controlled Duplication
We accept strategic duplication to reduce indirection:

```python
    try:
        jwt.decode(token, SECRET_KEY)
        return True
    except Exception:
        return False
# END_DUPLICATED_BLOCK: user_validation_v1
```

- Use `DUPLICATED_BLOCK` tags to track intentional duplication
- Run `make drift.check` to monitor duplication health
- Prefer small duplications over wrong abstractions

### Front-matter Documentation  
Python files include structured metadata for AI agents:

```python
"""
title: User Service
purpose: Handle user registration and authentication
inputs: [{"name": "user_data", "type": "dict"}]
outputs: [{"name": "user_id", "type": "str"}] 
effects: ["database_write", "email_send"]
deps: ["auth", "database", "email"]
owners: ["team-identity"]
stability: stable
since_version: "1.2.0"
"""
```

This enables automated discovery and understanding by LLM agents.

## 🔧 Development Workflow

### Before Making Changes
```bash
# Check current LLM readiness
make llm.check

# Understand the feature you're changing
cat features/[feature]/README.md

# Run quality gates
make pr.check

# Check for complexity hotspots  
make confusion.report
```

### Adding New Features
```bash
# Copy template structure
cp -r features/template/ features/your_feature/

# Update documentation
vim features/your_feature/README.md

# Add to module index  
vim docs/repo/INDEX.yaml

# Validate your changes
make llm.check
```

### Making Changes to Existing Features
```bash
# Navigate to the feature
cd features/[feature_name]/

# Check local documentation first
cat README.md

# Make your changes (prefer editing over creating new files)
vim service.py

# Run tests locally
python tests.py

# Check impact on complexity
make confusion.focus  # Enter: features/[feature_name]
```

## 🛡️ Quality Gates

### Differentiated LOC Limits
We have different size limits based on code purpose:

- **Application code**: 500 LOC max (focus on business logic)  
- **Test code**: 1000 LOC max (comprehensive testing encouraged)
- **Configuration files**: 250 LOC max (keep config focused)
- **Documentation**: No strict limits (thorough docs encouraged)

### Automated Checks
- **LLM Readiness Score**: Must be ≥80/100 (`make llm.check`)
- **Schema Validation**: All contracts validated (`make validate.schemas`)  
- **README Coverage**: All features documented
- **Front-matter Coverage**: All Python files have structured metadata
- **Drift Monitoring**: Controlled duplication stays synchronized (`make drift.check`)
- **Complexity Analysis**: Cognitive complexity hotspots identified (`make confusion.report`)

### Understanding Quality Gates
```bash
# Check your PR will pass
make pr.check

# Get detailed readiness breakdown
python scripts/check_llm_readiness.py

# See what needs documentation  
python scripts/check_readme_coverage.py

# Find complexity hotspots
python scripts/confusion_report.py --verbose
```

## 🚨 Troubleshooting

### Common Issues

**"LLM Readiness Score Too Low"**
```bash
# Get detailed breakdown
python scripts/check_llm_readiness.py

# Common fixes:
# - Add front-matter docstrings to Python files
# - Co-locate tests with features (create tests.py in feature dir)
# - Reduce import complexity (remove unnecessary imports)
```

**"Schema Validation Failed"**
```bash
# Get specific errors
python scripts/validate_schemas.py

# Check schema files for reference
ls schemas/

# Common fixes:
# - Update INDEX.yaml with proper structure
# - Fix front-matter YAML syntax in docstrings  
# - Ensure all required fields are present
```

**"Confusion Report Shows Hotspots"** 
```bash
# Generate refactoring plan
python scripts/confusion_report.py --plan --output refactoring_plan.md

# Focus on specific high-complexity areas
python scripts/confusion_report.py --focus features/problematic_feature/

# Common fixes:
# - Extract helper functions to reduce cyclomatic complexity
# - Split large files into focused modules  
# - Move scattered logic into vertical slices
# - Use early returns to reduce nesting
```

**"Drift Check Fails"**
```bash
# See what duplication has diverged  
make drift.report

# Common fixes:
# - Synchronize DUPLICATED_BLOCK sections manually
# - Update drift tolerance settings in .drift_check_config.yaml
# - Consider if diverged blocks should remain duplicated
```

**"PR LOC Gate Fails"**
```bash
# Check what's being counted
python scripts/check_pr_loc.py

# Remember: documentation (*.md) doesn't count toward limits
# Consider splitting large changes into multiple PRs
# Focus on one feature per PR when possible
```

### Recovery Patterns

**When Confused About Architecture:**
1. Read `docs/repo/FACTS.md` for architectural decisions
2. Check `docs/repo/INDEX.yaml` for module relationships  
3. Look for `wiring.py` files to understand dependencies
4. Review feature `README.md` files for context

**When Tests Are Failing:**
1. Check if you need to update co-located tests
2. Look for BDD-Lite scenarios in test files
3. Ensure test data matches actual implementation
4. Run `make test.fast` for quick feedback

**When Build/CI Is Failing:**
1. Run `make pr.check` locally first  
2. Check pre-commit hooks are passing
3. Ensure all schemas validate
4. Verify LLM readiness score is ≥80

## 🎯 Key Makefile Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `make llm.check` | Validate LLM readiness | Before committing changes |
| `make pr.check` | All quality gates | Before creating PR |
| `make confusion.report` | Find complexity hotspots | When refactoring |
| `make confusion.plan` | Get refactoring recommendations | Planning improvements |
| `make drift.check` | Validate duplication | Regular maintenance |
| `make test.fast` | Quick test run | During development |
| `make validate.schemas` | Check all contracts | After structural changes |

## 📚 Essential Files for Navigation

- **`CLAUDE.md`** - Complete LLM agent guidance and system architecture
- **`docs/repo/REPO_MAP.md`** - Repository overview and hot paths
- **`docs/repo/INDEX.yaml`** - Structured module relationships  
- **`docs/repo/FACTS.md`** - Key architectural decisions and invariants
- **`features/template/`** - Reference implementation patterns
- **`schemas/`** - JSON schemas for validation

## 🔄 Contributing to LLM-First Architecture

When adding new tooling or making architectural changes:

1. **Follow existing patterns** - Look at how other scripts are structured
2. **Add comprehensive front-matter** - Include all required metadata
3. **Write extensive tests** - Test coverage is more important than DRY
4. **Update documentation** - Keep REPO_MAP.md and INDEX.yaml current
5. **Consider LLM impact** - Will this make the codebase easier for AI to understand?

## 🎓 Learning More

- **ADR Documents**: `docs/adr/` for architectural decision records
- **System Prompts**: `CLAUDE.md` for complete LLM-first methodology  
- **Quality Tools**: All scripts in `scripts/` directory have comprehensive front-matter
- **Examples**: Study existing features for implementation patterns

---

**Welcome to LLM-first development!** 🤖✨ 

This approach may feel different initially, but it enables unprecedented collaboration between human developers and AI agents. The result is code that's not only more maintainable for humans, but also more comprehensible and modifiable by AI systems.

Questions? Check the troubleshooting section above, or examine similar patterns in existing features.