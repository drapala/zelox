# Zelox - LLM-First Repository Template

A repository template implementing LLM-First architecture principles for maximum AI agent effectiveness.

## 🎯 Purpose

This repository demonstrates best practices for structuring codebases to be optimally navigable and maintainable by LLM agents, following principles documented in our Architecture Decision Records (ADRs).

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Git

### Developer Setup

```bash
# Clone the repository
git clone https://github.com/drapala/zelox.git
cd zelox

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit on all files (optional)
pre-commit run --all-files
```

### Pre-commit Hooks

This repository uses pre-commit hooks to maintain code quality:

- **Ruff format**: Enforces consistent Python formatting
- **Ruff lint**: Catches code quality issues (pycodestyle, pyflakes, isort, etc.)
- **README coverage**: Ensures all features have documentation
- **Frontmatter coverage**: Validates Python files have proper metadata

Hooks run automatically on each commit. To run manually:

```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files
```

## 📁 Repository Structure

```
zelox/
├── features/           # Vertical Slice Architecture features
│   └── template/      # Feature template with placeholders
├── docs/
│   ├── repo/          # Repository navigation and metadata
│   │   ├── INDEX.yaml # Central module registry
│   │   ├── REPO_MAP.md # Navigation map
│   │   └── FACTS.md   # Key repository facts
│   └── adr/           # Architecture Decision Records
├── schemas/           # JSON schemas for validation
├── scripts/           # Validation and tooling scripts
├── shared/            # Cross-cutting concerns
└── .github/           # CI/CD workflows
```

## 🏗️ Architecture Principles

### LLM-First Design (ADR-001)

- **Vertical Slice Architecture**: Features are self-contained with co-located tests
- **Small PRs**: Maximum 500 LOC for application code, 1000 for tests (ADR-006)
- **Rich Metadata**: All files include frontmatter for LLM discovery
- **Machine-Readable Contracts**: JSON schemas define all configurations

### Quality Gates

Every PR must pass:

1. **Pre-commit checks**: Code formatting and linting
2. **PR size limits**: Categorized by file type
3. **Schema validation**: YAML/JSON files match schemas
4. **LLM readiness score**: ≥80/100 for discoverability
5. **Documentation coverage**: Features have READMEs

## 🛠️ Development Workflow

### Creating a Feature

```bash
# Copy the template
cp -r features/template features/my-feature

# Update placeholders
# Replace [FeatureName] with your feature name in all files
```

### Making Changes

1. Create a branch following naming conventions (ADR-005)
2. Make focused changes (≤500 LOC for code)
3. Ensure tests are co-located with code
4. Add/update documentation
5. Create PR with template checklist

### Running Validations

```bash
# Check PR size
python scripts/check_pr_loc.py

# Validate schemas
python scripts/validate_schemas.py

# Check LLM readiness
python scripts/check_llm_readiness.py

# Check README coverage
python scripts/check_readme_coverage.py
```

## 📊 LLM Readiness Metrics

The repository maintains an LLM Readiness Score based on:

- **Co-location** (25 points): Tests next to code
- **Import complexity** (20 points): Average ≤3 imports per file
- **Frontmatter coverage** (20 points): ≥90% of files have metadata
- **Documentation** (20 points): All required docs present
- **ADR structure** (10 points): Proper decision records
- **Feature structure** (5 points): Following VSA principles

Current score: Run `python scripts/check_llm_readiness.py` to check.

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Instructions for AI agents
- [Repository Map](docs/repo/REPO_MAP.md) - Navigation guide
- [INDEX.yaml](docs/repo/INDEX.yaml) - Module registry
- [Architecture Decisions](docs/adr/) - ADR records

## 🤝 Contributing

1. Read relevant ADRs before making architectural changes
2. Follow the PR template checklist
3. Ensure all quality gates pass
4. Keep PRs focused and small

## 📝 License

[Add your license here]

## 🔗 Links

- [Repository](https://github.com/drapala/zelox)
- [Issues](https://github.com/drapala/zelox/issues)