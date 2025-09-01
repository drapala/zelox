# Feature Template

**Purpose:** Template for creating new LLM-first vertical slice features.

## Usage

1. Copy this template directory to `features/[feature_name]/`
2. Replace all `[FEATURE_NAME]` placeholders with your feature name
3. Update `docs/repo/INDEX.yaml` with new feature entry
4. Run `make llm.check` to validate structure

## Template Structure

```
features/[FEATURE_NAME]/
├── README.md           # This file - feature documentation
├── models.py           # Domain entities and value objects
├── service.py          # Business logic and application services  
├── repository.py       # Data access layer
├── api.py             # HTTP endpoints and external interfaces
├── tests.py           # Co-located tests with BDD-Lite scenarios
├── OBS_PLAN.md        # Observability plan (required)
└── wiring.py          # Dependency injection (if needed)
```

## LLM-First Principles

This template follows VSA (Vertical Slice Architecture) with:
- **Co-location:** All feature code in single directory
- **Minimal indirection:** Clear, linear flows
- **Explicit contracts:** Well-documented entrypoints
- **BDD-Lite scenarios:** For P0 (critical) features
- **Observability by design:** Built-in metrics and logging

## Common Tasks

### Add New Feature
```bash
cp -r features/template features/my_feature
cd features/my_feature
# Replace placeholders and implement
```

### Run Feature Tests
```bash
cd features/my_feature
python -m pytest tests.py -v
```

### Check Feature Health  
```bash
make llm.check
grep -r "my_feature" docs/repo/INDEX.yaml
```