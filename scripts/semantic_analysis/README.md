# Semantic Analysis Pipeline

A modular, LLM-first semantic analysis pipeline for Python codebases. This refactored version reduces complexity from 72.6 to under 30 through clear separation of concerns and linear pipeline architecture.

## Architecture

The pipeline consists of four independent stages:

```
parse → extract → score → report
```

Each stage has a single responsibility and can be tested independently.

## Modules

### 1. semantic_parser.py (100 LOC)
Parses Python files and extracts basic semantic elements.

```python
from semantic_parser import parse_file

parsed = parse_file(Path("example.py"))
print(f"Functions: {len(parsed.functions)}")
print(f"Classes: {len(parsed.classes)}")
print(f"Imports: {len(parsed.imports)}")
```

### 2. semantic_extractor.py (100 LOC)
Extracts patterns and dependencies from parsed data.

```python
from semantic_extractor import extract_patterns

patterns = extract_patterns([parsed_file1, parsed_file2])
print(f"Call chains: {len(patterns.call_chains)}")
print(f"Hotspots: {len(patterns.hotspots)}")
print(f"Cycles: {len(patterns.cyclic_deps)}")
```

### 3. semantic_scorer.py (80 LOC)
Calculates quality scores and LLM readiness.

```python
from semantic_scorer import calculate_scores

scores = calculate_scores(patterns)
print(f"LLM Readiness: {scores.llm_readiness_score}/100")
print(f"Insights: {scores.insights}")
```

### 4. semantic_reporter.py (80 LOC)
Generates analysis reports in multiple formats.

```python
from semantic_reporter import generate_report

report = generate_report(scores, patterns, file_count=10)
# Export as JSON or Markdown
reporter.export_json(report, Path("report.json"))
reporter.export_markdown(report, Path("report.md"))
```

### 5. semantic_pipeline.py (Orchestrator)
Coordinates all stages in a linear pipeline.

```python
from semantic_pipeline import SemanticAnalysisPipeline

pipeline = SemanticAnalysisPipeline(repo_root=".")
result = pipeline.analyze()

if result["llm_readiness_score"] < 80:
    print("Warning: Low LLM readiness!")

pipeline.save_report("analysis.json")
```

## Usage

### Command Line

```bash
# Basic analysis
python semantic_pipeline.py

# With custom repo root
python semantic_pipeline.py --repo-root /path/to/repo

# Generate report
python semantic_pipeline.py --report --output report.json

# Set custom threshold
python semantic_pipeline.py --threshold 90
```

### As a Module

```python
from semantic_pipeline import analyze_codebase

result = analyze_codebase(
    repo_root="/path/to/repo",
    output_path="report.json"
)

if result["llm_readiness_score"] >= 80:
    print("✅ Codebase is LLM-ready")
else:
    print("❌ Refactoring needed")
```

## Running Tests

```bash
# Run all smoke tests
python test_semantic_modules.py

# Run specific test suite
python -m unittest test_semantic_modules.TestSemanticParser
```

## Metrics Explained

### LLM Readiness Score (0-100)
- **90-100**: Excellent - optimal for LLM editing
- **80-89**: Good - acceptable for most tasks
- **70-79**: Fair - some refactoring recommended
- **60-69**: Poor - significant refactoring needed
- **<60**: Critical - major architectural issues

### Key Metrics
- **Average Imports**: Target < 8 per file
- **Call Chain Depth**: Target < 6 levels
- **Cyclic Dependencies**: Target = 0
- **Feature Isolation**: Target > 0.8

## Examples

### Analyzing a Feature Module

```python
from pathlib import Path
from semantic_parser import parse_file
from semantic_extractor import extract_patterns
from semantic_scorer import calculate_scores

# Parse feature files
feature_path = Path("features/user_auth")
parsed_files = []
for py_file in feature_path.rglob("*.py"):
    parsed_files.append(parse_file(py_file))

# Extract and score
patterns = extract_patterns(parsed_files)
scores = calculate_scores(patterns)

# Check feature isolation
if patterns.feature_isolation.get("user_auth", 0) < 0.8:
    print("Warning: Feature has external dependencies")
```

### Custom Analysis Pipeline

```python
class CustomPipeline(SemanticAnalysisPipeline):
    def _should_skip_file(self, file_path):
        # Add custom skip logic
        if "generated" in str(file_path):
            return True
        return super()._should_skip_file(file_path)
    
    def _score_stage(self):
        super()._score_stage()
        # Add custom scoring
        if self.scores.llm_readiness_score < 70:
            self.scores.recommendations.append(
                "Consider full VSA migration"
            )

pipeline = CustomPipeline()
pipeline.analyze()
```

## Integration with CI/CD

```yaml
# .github/workflows/llm-readiness.yml
name: LLM Readiness Check

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Semantic Analysis
        run: |
          python scripts/semantic_analysis/semantic_pipeline.py \
            --threshold 80 \
            --output llm-report.json
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: llm-readiness-report
          path: llm-report.json
```

## Benefits of Refactoring

### Before (semantic_analyzer.py)
- Single file with 396 lines
- Cyclomatic complexity: 25
- Context switches: 308
- Confusion score: 72.6

### After (Pipeline Modules)
- 5 focused modules, each <100 LOC
- Max complexity: 8 per function
- Clear linear flow
- Confusion score: <30
- Each stage independently testable

## How to Edit (5 Lines)

1. Each module has one purpose - edit only that concern
2. Run smoke tests after changes: `python test_semantic_modules.py`
3. Pipeline stages are independent - test in isolation
4. Update docstrings when changing contracts
5. Keep functions under 20 lines for LLM readability