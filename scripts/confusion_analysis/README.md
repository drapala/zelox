# Confusion Analysis Module

## Purpose
Analyzes Python codebase for confusion metrics and identifies hotspots that need refactoring.

## How to Edit (5 lines)
1. Keep each analyzer under 100 LOC
2. Update YAML frontmatter when changing contracts
3. Add tests in scripts/tests/test_confusion_*.py
4. Use pure functions for calculations
5. Cache expensive computations with @lru_cache

## Components

### complexity_analyzer.py (97 LOC)
- Measures cyclomatic complexity
- Calculates indirection depth
- Counts context switches
- Returns ComplexityMetrics dataclass

### confusion_scorer.py (95 LOC)
- Calculates weighted confusion scores
- Identifies specific issues
- Determines severity levels
- Returns ScoredFile dataclass

### hotspot_detector.py (79 LOC)
- Finds files exceeding thresholds
- Ranks hotspots by score
- Categorizes by severity
- Returns Hotspot list

### confusion_reporter.py (98 LOC)
- Generates JSON/Markdown reports
- Calculates summary statistics
- Formats output for humans
- Saves reports to files

## Common Tasks

### Analyze Repository
```python
from confusion_analysis import ComplexityAnalyzer, ConfusionScorer

# Analyze single file
content = Path("file.py").read_text()
metrics = ComplexityAnalyzer.analyze(content)
scored = ConfusionScorer.score_file("file.py", metrics)
```

### Find Hotspots
```python
from confusion_analysis import HotspotDetector

hotspots = HotspotDetector.find_hotspots(scored_files)
top_10 = HotspotDetector.get_top_hotspots(hotspots, 10)
```

### Generate Report
```python
from confusion_analysis import ConfusionReporter

report = ConfusionReporter.generate_report(scored_files, hotspots, time)
ConfusionReporter.print_report(report)
```

## Thresholds
- Cyclomatic Complexity: < 10
- Indirection Depth: < 3  
- Context Switches: < 100
- Lines of Code: < 200
- Confusion Score: < 50 (high), < 70 (critical)