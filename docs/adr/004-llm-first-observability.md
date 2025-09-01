# ADR-004: Adopt LLM-First Observability Standards

---
title: Adopt LLM-First Observability Standards
date: 2025-09-01
status: proposed
deciders: [Development Team, DevOps Team, QA Team]
consulted: [LLM Agents, Backend Engineers, Product Owner]
informed: [All Contributors]
---

## Front-matter (YAML)
```yaml
# Machine-readable metadata for LLM processing
adr_number: 004
title: "Adopt LLM-First Observability Standards"
date: "2025-09-01"
status: "proposed"
tags: ["observability", "metrics", "llm-first", "telemetry", "logging", "vsa"]
complexity: medium
llm_impact: high
human_impact: medium
reversibility: easy
review_deadline: "2025-11-01"
supersedes: []
superseded_by: null
```

## Context and Problem Statement

Our application needs minimal but consistent observability per feature. Currently, logs/metrics are ad-hoc, scattered, and invisible to LLM agents. This makes automated diagnostics difficult, increases confusion, and makes testing expensive.

**Key Question:** What observability patterns should we adopt to ensure rapid diagnostics, low noise, and LLM-first editability?

## Decision Drivers

- [x] Reduces LLM cognitive hops by ≥30%
- [x] Improves time-to-tested-patch
- [x] Maintains LLM Readiness Score ≥80
- [x] Minimal observability, not inflated
- [x] Rapid diagnosis for agents (clear logs, standardized metrics)
- [x] Integration with `OBS_PLAN.md` per feature
- [x] Automated confusion/cost metrics in CI

## Considered Options

1. **Option 1: Minimal per-feature observability** - LLM-first standard with basic metrics
2. **Option 2: Full observability stack** - OpenTelemetry everywhere with detailed tracing
3. **Option 3: Hybrid approach** - Minimal baseline + deeper tracing for critical features only

## Decision

**We will:** Adopt Option 1 as baseline (LLM-first minimal standard). Option 3 (Hybrid) will be used only for critical features when needed.

### Option Details

#### Option 1: Minimal per-feature observability
- **Description:** Each feature slice generates `OBS_PLAN.md` with 2-3 essential metrics and explicit logs.
- **LLM Benefits:**
  - Simple and predictable patterns
  - Easy to navigate and understand
  - Clear signal-to-noise ratio
  - Co-located with feature code
- **LLM Costs:**
  - Less granularity in rare edge cases
- **Human Impact:** Fast diagnosis without dashboard overload; minimal operational overhead.

#### Option 2: Full observability stack
- **Description:** OpenTelemetry with detailed tracing on every request.
- **LLM Benefits:**
  - Rich data available for complex scenarios
- **LLM Costs:**
  - Too much noise, difficult for agents to interpret
  - Violates co-location and simplicity principles
  - High cognitive load to process traces
- **Human Impact:** High learning curve and heavy operational overhead.

#### Option 3: Hybrid approach
- **Description:** Minimal by default, advanced tracing only in critical features.
- **LLM Benefits:**
  - Balanced approach
  - Can escalate when needed
- **LLM Costs:**
  - Two different patterns in codebase
  - Complexity in determining what needs deeper observability
- **Human Impact:** More operational complexity managing two standards.

## Consequences

### Positive
- ✅ Each feature documents its `OBS_PLAN.md` with essential metrics
- ✅ Standardized logs/metrics (p95, error_count, cost, confusion)
- ✅ CI blocks regressions with confusion/cost metrics
- ✅ Perfect co-location with feature code
- ✅ LLM agents can easily understand and work with observability code

### Negative
- ❌ Advanced diagnostics may need additional instrumentation
- ❌ Not every bug will be detected with minimal metrics alone

### Neutral
- ➖ Can evolve to Hybrid approach later if needed
- ➖ May create some duplication between OBS_PLAN.md and human dashboards

## Implementation

### Files Affected
```yaml
files:
  - path: features/*/OBS_PLAN.md
    changes: Add metrics p95, error_count, cost/confusion context per feature
  - path: features/*/service.py
    changes: Add standardized logging and metrics collection
  - path: scripts/confusion_report.py
    changes: Generate confusion_report.md per feature
  - path: scripts/cost_report.py
    changes: Generate cost_dashboard.md per feature
  - path: Makefile
    changes: Add targets confusion.report and cost.report
  - path: docs/repo/observability-patterns.md
    changes: Document standard patterns for metrics and logging
```

### OBS_PLAN.md Template
Each feature must include:
```yaml
# OBS_PLAN.md Template
metrics:
  - name: feature_request_duration_p95
    budget: 200ms
    alert_threshold: 500ms
  - name: feature_error_rate
    budget: 1%
    alert_threshold: 5%
  - name: feature_confusion_score
    budget: 0.2
    alert_threshold: 0.5

cost_tracking:
  - tokens_per_request: estimated
  - database_calls_per_request: tracked
  - llm_api_calls: tracked

confusion_hotspots:
  - indirection_depth: measured
  - cross_file_references: counted
```

### Migration Steps
1. Create `OBS_PLAN.md` template and documentation
2. Add minimal observability to existing features:
   - p95 latency per entrypoint
   - error_count tracking
   - confusion hotspots (LLM metrics)
   - cost per PR tracking
3. Implement `scripts/confusion_report.py` and `scripts/cost_report.py`
4. Run `make confusion.report` and `make cost.report` in CI
5. Configure minimal alerts (CI fails if p95 > budget or confusion spikes)
6. Update repository maps (`REPO_MAP.md`, `INDEX.yaml`)

### Rollback Plan
1. Remove `OBS_PLAN.md` files from feature slices
2. Disable confusion/cost scripts in CI
3. Revert to ad-hoc logging patterns
4. Remove observability targets from Makefile

## Metrics and Validation

### Success Metrics
- [x] LLM Readiness Score remains ≥80 with observability enabled
- [ ] 100% of feature slices have valid `OBS_PLAN.md`
- [ ] Confusion metrics reported per PR
- [ ] Cost metrics dashboard updated weekly
- [ ] 50% faster diagnosis of feature issues
- [ ] Reduced false positive alerts

### Validation Commands
```bash
# Generate observability reports
make confusion.report
make cost.report

# Validate observability setup
make llm.check

# Test feature observability
python3 scripts/check_obs_plan.py features/*/OBS_PLAN.md
```

## Notes for LLM Agents

### When Working With This Decision
- **Always check:** Update `OBS_PLAN.md` when changing API or critical flows
- **Never modify:** Core observability patterns without new ADR
- **Common pitfalls:** 
  - Forgetting to include structured logging in new endpoints
  - Adding metrics without budgets/thresholds
  - Over-instrumenting non-critical paths

### Standard Patterns
```python
# Standard logging pattern
import structlog
logger = structlog.get_logger()

def process_request(request_id: str, tenant_id: str):
    logger.info(
        "processing_request",
        request_id=request_id,
        tenant_id=tenant_id,
        feature="user_registration"
    )
    
    # Standard metrics pattern
    with metrics.timer("user_registration.duration"):
        result = do_processing()
    
    if result.success:
        metrics.increment("user_registration.success")
    else:
        metrics.increment("user_registration.error")
        logger.error(
            "request_failed",
            request_id=request_id,
            error=str(result.error)
        )
```

### Related Context
- **Dependencies:** ADR-001 (LLM-First Architecture with VSA)
- **See also:** 
  - `features/*/OBS_PLAN.md` - Feature-specific observability plans
  - `docs/repo/observability-patterns.md` - Standard patterns
  - `scripts/confusion_report.py` - LLM confusion analysis
  - `scripts/cost_report.py` - Cost tracking

## Review and Update

- **Review deadline:** 2025-11-01
- **Review criteria:** 
  - Validate if confusion/cost metrics are guiding LLM-first refactors
  - Check if diagnosis time has improved
  - Assess if minimal approach is sufficient or needs Hybrid evolution
- **Update history:**
  - 2025-09-01: Initial proposal