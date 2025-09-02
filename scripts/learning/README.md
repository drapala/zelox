# Learning System Module

## Purpose
Modular adaptive learning system for discovering architectural patterns and generating improvement recommendations from telemetry data.

## Structure
```
learning/
├── pattern_learner.py    # Pattern extraction from telemetry
├── metric_tracker.py      # Metrics aggregation and predictions
├── adaptation_engine.py   # Strategy-based recommendations
├── learning_reporter.py   # Report generation and insights
├── wiring.py             # Component integration and CLI
└── test_learning_system.py # Comprehensive unit tests
```

## How to Edit (5 lines)
1. Each module handles one concern - modify only the relevant file
2. Add new adaptation strategies by extending AdaptationStrategy in adaptation_engine.py
3. Update wiring.py if adding new components or changing initialization
4. Run tests after changes: `python3 -m pytest scripts/learning/`
5. Update front-matter YAML when changing module contracts

## Common Tasks

### Run Learning Analysis
```bash
python3 scripts/learning/wiring.py --analyze --telemetry .reports/llm_telemetry.jsonl
```

### Generate Markdown Report
```bash
python3 scripts/learning/wiring.py --analyze --output report.md
```

### Test Specific Component
```bash
python3 -m pytest scripts/learning/test_learning_system.py::TestPatternLearner
```

## Entry Points
- CLI: `wiring.py:main()`
- API: `wiring.py:build_learning_system()`

## Key Interfaces
- `PatternLearner.learn_patterns()` - Extract patterns from telemetry
- `AdaptationEngine.generate_recommendations()` - Create improvement suggestions
- `LearningReporter.generate_report()` - Build comprehensive reports