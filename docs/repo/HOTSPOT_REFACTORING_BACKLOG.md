# Hotspot Refactoring Backlog

## Overview
This document contains the prioritized refactoring backlog based on confusion report analysis.
Each task includes a ready-to-use prompt for LLM-assisted refactoring.

**Overall Status:**
- Total Files to Refactor: 10
- Total Confusion Score Reduction Target: 60%
- Estimated Total Effort: 40-80 hours
- Priority: HIGH

---

## 🔴 Priority 1: Critical Hotspots (Score > 70)

### Task 1: Refactor domain_analyzer.py
**File:** `scripts/domain_analyzer.py`
**Current Confusion Score:** 81.5
**Target Score:** < 30
**Estimated Effort:** 8 hours

#### Refactoring Prompt:
```
Refactor scripts/domain_analyzer.py following LLM-First Architecture principles:

CURRENT ISSUES:
- Cyclomatic complexity: 29 (target: <10)
- Indirection depth: 8 (target: <3)
- Context switches: 344 (target: <100)
- Single file with 486 lines

REFACTORING PLAN:
1. Split into vertical slices by responsibility:
   - domain_models.py (100-150 LOC): Domain entity extraction
   - domain_rules.py (100-150 LOC): Business rule analysis
   - domain_mapper.py (100-150 LOC): Mapping and visualization
   - domain_reporter.py (100-150 LOC): Report generation

2. Add YAML frontmatter to each file with:
   - title, purpose, inputs, outputs, effects
   - Explicit contracts for each function

3. Co-locate tests in scripts/tests/:
   - test_domain_models.py
   - test_domain_rules.py
   - test_domain_mapper.py
   - test_domain_reporter.py

4. Create scripts/domain_analysis/README.md with:
   - "How to Edit (5 lines)"
   - Common tasks
   - Entry points

5. Update INDEX.yaml and REPO_MAP.md

SUCCESS CRITERIA:
- Each file < 200 LOC
- Max 2 levels of indirection
- All functions < 20 lines
- Cyclomatic complexity < 10 per function
- 100% golden test coverage for critical paths
```

---

### Task 2: Refactor validate_schemas.py
**File:** `scripts/validate_schemas.py`
**Current Confusion Score:** 74.4
**Target Score:** < 30
**Estimated Effort:** 6 hours

#### Refactoring Prompt:
```
Refactor scripts/validate_schemas.py following LLM-First Architecture principles:

CURRENT ISSUES:
- Cyclomatic complexity: 12 (target: <10)
- Indirection depth: 10 (target: <3)
- Context switches: 329 (target: <100)
- Single file with 411 lines

REFACTORING PLAN:
1. Create scripts/schema_validation/ vertical slice:
   - schema_loader.py (80-100 LOC): Load and parse schemas
   - schema_validator.py (100-150 LOC): Core validation logic
   - schema_rules.py (80-100 LOC): Validation rules
   - schema_reporter.py (80-100 LOC): Error reporting

2. Simplify validation flow:
   - Remove unnecessary abstraction layers
   - Direct function calls instead of complex dispatch
   - Explicit validation pipelines

3. Add comprehensive frontmatter:
   - Clear input/output contracts
   - Effects and dependencies
   - Complexity markers for complex validations

4. Create golden tests for:
   - Valid schema scenarios
   - Each validation error type
   - Edge cases

5. Add local README.md with validation flow diagram

SUCCESS CRITERIA:
- Reduce indirection depth from 10 to 3
- Each validator function < 15 lines
- Clear linear flow: load → validate → report
- Test coverage > 90%
```

---

### Task 3: Refactor semantic_analyzer.py
**File:** `scripts/semantic_analyzer.py`
**Current Confusion Score:** 72.6
**Target Score:** < 30
**Estimated Effort:** 6 hours

#### Refactoring Prompt:
```
Refactor scripts/semantic_analyzer.py following LLM-First Architecture principles:

CURRENT ISSUES:
- Cyclomatic complexity: 25 (target: <10)
- Context switches: 308 (target: <100)
- Single file with 396 lines
- High cognitive load from mixed concerns

REFACTORING PLAN:
1. Split into semantic analysis pipeline:
   - semantic_parser.py (100 LOC): Parse code for semantic elements
   - semantic_extractor.py (100 LOC): Extract semantic patterns
   - semantic_scorer.py (80 LOC): Score semantic quality
   - semantic_reporter.py (80 LOC): Generate reports

2. Implement linear pipeline pattern:
   ```python
   # In semantic_pipeline.py
   def analyze(file_path):
       parsed = parse(file_path)
       patterns = extract(parsed)
       scores = score(patterns)
       return report(scores)
   ```

3. Reduce complexity:
   - Break nested conditionals into guard clauses
   - Extract complex calculations to pure functions
   - Use data classes for semantic models

4. Add smoke tests for each stage:
   - test_parse_python_file()
   - test_extract_patterns()
   - test_score_semantics()
   - test_generate_report()

5. Document with examples in README.md

SUCCESS CRITERIA:
- Max complexity of 8 per function
- Pipeline stages clearly separated
- Each stage independently testable
- Reduced context switches by 70%
```

---

## 🟡 Priority 2: High Complexity (Score 50-70)

### Task 4: Refactor confusion_report.py
**File:** `scripts/confusion_report.py`
**Current Confusion Score:** 63.0
**Target Score:** < 25
**Estimated Effort:** 5 hours

#### Refactoring Prompt:
```
Refactor scripts/confusion_report.py (self-improvement opportunity!):

CURRENT ISSUES:
- Cyclomatic complexity: 24
- Context switches: 259
- Mixed analysis and reporting concerns

REFACTORING PLAN:
1. Create scripts/confusion_analysis/ module:
   - complexity_analyzer.py (100 LOC): Measure complexity
   - confusion_scorer.py (100 LOC): Calculate confusion scores
   - hotspot_detector.py (80 LOC): Find hotspots
   - confusion_reporter.py (100 LOC): Generate reports

2. Simplify scoring algorithm:
   - Extract magic numbers to constants
   - Create ConfusionMetrics dataclass
   - Linear scoring pipeline

3. Add caching for expensive computations:
   - Cache AST parsing results
   - Memoize complexity calculations

4. Create focused tests:
   - Test each metric calculation
   - Test threshold detection
   - Test report generation

SUCCESS CRITERIA:
- Each analyzer < 100 LOC
- Scoring logic in pure functions
- Cached analysis results
- 50% reduction in runtime
```

---

### Task 5: Refactor gen_repo_map.py
**File:** `scripts/gen_repo_map.py`
**Current Confusion Score:** 59.0
**Target Score:** < 25
**Estimated Effort:** 5 hours

#### Refactoring Prompt:
```
Refactor scripts/gen_repo_map.py for better LLM navigation:

CURRENT ISSUES:
- Cyclomatic complexity: 20
- Context switches: 250
- Monolithic file with 435 lines

REFACTORING PLAN:
1. Split into repo_mapping/ module:
   - file_scanner.py (80 LOC): Scan repository files
   - map_builder.py (100 LOC): Build repo structure
   - map_formatter.py (80 LOC): Format output
   - map_writer.py (60 LOC): Write to files

2. Implement builder pattern:
   ```python
   RepoMapBuilder()
       .scan(path)
       .filter(patterns)
       .build()
       .format(style)
       .write(output)
   ```

3. Add incremental update support:
   - Track file changes since last run
   - Update only changed sections
   - Maintain map version history

4. Create integration tests:
   - Test full repo scan
   - Test incremental updates
   - Test different output formats

SUCCESS CRITERIA:
- Modular, composable design
- Support incremental updates
- 3x faster for large repos
- Clear separation of concerns
```

---

### Task 6: Refactor adaptive_learner.py
**File:** `scripts/adaptive_learner.py`
**Current Confusion Score:** 55.5
**Target Score:** < 25
**Estimated Effort:** 5 hours

#### Refactoring Prompt:
```
Refactor scripts/adaptive_learner.py for clarity and testability:

CURRENT ISSUES:
- Cyclomatic complexity: 20
- Context switches: 230
- Complex learning algorithms in single file

REFACTORING PLAN:
1. Create scripts/learning/ module:
   - pattern_learner.py (100 LOC): Learn code patterns
   - metric_tracker.py (80 LOC): Track metrics
   - adaptation_engine.py (100 LOC): Adapt strategies
   - learning_reporter.py (80 LOC): Report insights

2. Simplify learning logic:
   - Use strategy pattern for algorithms
   - Explicit state management
   - Clear feedback loops

3. Add observability:
   - Log learning decisions
   - Track adaptation effectiveness
   - Export metrics

4. Create unit tests:
   - Mock learning inputs
   - Test adaptation logic
   - Verify metric tracking

SUCCESS CRITERIA:
- Each component < 100 LOC
- Pluggable learning strategies
- Testable adaptation logic
- Clear audit trail
```

---

## 🟢 Priority 3: Moderate Complexity (Score 30-50)

### Task 7: Refactor check_llm_readiness.py
**File:** `scripts/check_llm_readiness.py`
**Current Confusion Score:** 46.7
**Target Score:** < 20
**Estimated Effort:** 4 hours

#### Refactoring Prompt:
```
Refactor scripts/check_llm_readiness.py for better modularity:

CURRENT ISSUES:
- Cyclomatic complexity: 20
- Context switches: 191
- Mixed scoring and reporting

REFACTORING PLAN:
1. Split into readiness_check/ module:
   - readiness_metrics.py (80 LOC): Define metrics
   - readiness_calculator.py (100 LOC): Calculate scores
   - readiness_validator.py (80 LOC): Validate thresholds
   - readiness_reporter.py (80 LOC): Generate reports

2. Create ReadinessScore dataclass:
   - Individual metric scores
   - Overall score calculation
   - Recommendations list

3. Add metric plugins:
   - Allow custom metrics
   - Configurable weights
   - Dynamic thresholds

SUCCESS CRITERIA:
- Pluggable metric system
- Each calculator < 20 lines
- Clear score aggregation
- Extensible design
```

---

### Task 8: Refactor drift_check.py
**File:** `scripts/drift_check.py`
**Current Confusion Score:** 37.4
**Target Score:** < 15
**Estimated Effort:** 3 hours

#### Refactoring Prompt:
```
Refactor scripts/drift_check.py for simplicity:

CURRENT ISSUES:
- Indirection depth: 9 (too deep)
- Context switches: 148
- Complex duplicate detection

REFACTORING PLAN:
1. Create drift_detection/ module:
   - block_finder.py (60 LOC): Find duplicate blocks
   - drift_calculator.py (60 LOC): Calculate drift
   - drift_reporter.py (60 LOC): Report findings

2. Simplify detection:
   - Use hash-based comparison
   - Direct AST traversal
   - Clear drift metrics

3. Add performance optimizations:
   - Cache parsed ASTs
   - Parallel file processing
   - Incremental checks

SUCCESS CRITERIA:
- Max 3 levels of indirection
- 50% faster execution
- Clear drift reports
- Memory efficient
```

---

### Task 9: Refactor check_pr_loc.py
**File:** `scripts/check_pr_loc.py`
**Current Confusion Score:** 36.8
**Target Score:** < 15
**Estimated Effort:** 3 hours

#### Refactoring Prompt:
```
Refactor scripts/check_pr_loc.py for clarity:

CURRENT ISSUES:
- Context switches: 159
- Complex PR validation logic
- Mixed git operations

REFACTORING PLAN:
1. Split into pr_validation/ module:
   - loc_counter.py (80 LOC): Count lines
   - pr_validator.py (80 LOC): Validate limits
   - pr_reporter.py (60 LOC): Generate reports

2. Simplify validation:
   - Clear threshold checks
   - Simple boolean returns
   - Explicit error messages

3. Add configuration:
   - Configurable LOC limits
   - File count limits
   - Exclusion patterns

SUCCESS CRITERIA:
- Each validator < 15 lines
- Configurable thresholds
- Clear pass/fail status
- Helpful error messages
```

---


## Notes
- Each refactoring should include ADR-Lite documentation
- Update REPO_MAP.md and INDEX.yaml after each task
- Run confusion report after each phase to track progress
- Consider pairing on Priority 1 tasks for knowledge sharing