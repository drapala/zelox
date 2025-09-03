# Domain Analysis Module

## Purpose
Extract and analyze domain patterns, bounded contexts, and provide VSA recommendations for LLM-friendly architecture.

## How to Edit (5 lines)

1. Keep each module under 150 LOC (domain_models, domain_rules, domain_mapper, domain_reporter)
2. Update YAML frontmatter when changing module contracts
3. Add golden tests in tests/ for any new domain extraction logic
4. Run `python3 -m pytest tests/` to verify all tests pass
5. Use `python3 domain_reporter.py --report` to generate analysis reports

## Entry Points

- **CLI**: `python3 domain_reporter.py [--repo-root PATH] [--report] [--json]`
- **Python API**: `from domain_reporter import DomainPatternDetector`

## Common Tasks

### Analyze a Repository
```bash
python3 domain_reporter.py --repo-root /path/to/repo --report
```

### Get JSON Output
```bash
python3 domain_reporter.py --repo-root /path/to/repo --json
```

### Run Tests
```bash
python3 -m pytest tests/ -v
```

## Module Structure

```
domain_analysis/
├── domain_models.py     # Domain entity extraction (AST parsing)
├── domain_rules.py      # Business rule analysis & violations
├── domain_mapper.py     # Repository mapping & aggregation  
├── domain_reporter.py   # Report generation & CLI
├── tests/
│   ├── test_domain_models.py
│   ├── test_domain_rules.py
│   ├── test_domain_mapper.py
│   └── test_domain_reporter.py
└── README.md
```

## Key Components

### domain_models.py
- `DomainLanguageExtractor`: AST visitor for extracting domain concepts
- `extract_domain_language()`: Main extraction function
- Filters technical terms, extracts from names/docstrings

### domain_rules.py
- `detect_boundary_violations()`: Find context overlaps
- `calculate_coherence_score()`: Measure domain consistency
- `generate_vsa_recommendations()`: Suggest refactorings

### domain_mapper.py
- `BoundedContextAnalyzer`: Maps domain across files
- `map_domain_boundaries()`: Complete repository analysis
- Aggregates by features, skips test files

### domain_reporter.py
- `DomainPatternDetector`: Main analysis orchestrator
- `generate_report()`: Human-readable reports
- CLI interface with multiple output formats

## Performance Metrics

- Target cyclomatic complexity: < 10 per function
- Max indirection depth: 2 levels
- File size: < 150 LOC per module
- Test coverage: 100% for critical paths