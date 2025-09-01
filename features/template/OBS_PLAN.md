# OBS_PLAN.md - [FEATURE_NAME] Observability Plan

**Feature:** [FEATURE_NAME]  
**Purpose:** Define minimal observability for LLM-first diagnostics  
**Updated:** [DATE]

## Machine-Readable Plan

```yaml
metrics:
  - name: feature_name_request_duration_p95
    budget: "200ms"
    alert_threshold: "500ms"
    type: latency
    description: "P95 response time for [FEATURE_NAME] operations"
    applies_to:
      feature: "[feature_name]"
      entrypoint: "[entrypoint_name]"

  - name: feature_name_error_rate
    budget: "1%"
    alert_threshold: "5%"
    type: error_rate
    description: "Percentage of failed [FEATURE_NAME] operations"
    applies_to:
      feature: "[feature_name]"
      entrypoint: "[entrypoint_name]"

  - name: feature_name_active_count
    budget: "1000"
    alert_threshold: "10000"
    type: gauge
    description: "Current number of active [FEATURE_NAME] entities"

cost_tracking:
  - item: database_calls_per_request
    tracking_method: tracked
    budget: "3"
    unit: "requests"
  
  - item: compute_time
    tracking_method: measured
    budget: "50ms"
    unit: "request"
  
  - item: storage_usage
    tracking_method: estimated
    budget: "1KB"
    unit: "entity"

confusion_hotspots:
  - metric: cross_file_references
    measurement_method: static_analysis
    target_value: 2
    current_value: null
    
  - metric: indirection_depth
    measurement_method: automated
    target_value: 2
    current_value: null
    
  - metric: import_complexity
    measurement_method: static_analysis
    target_value: 5
    current_value: null

alerts:
  - metric_name: feature_name_request_duration_p95
    condition: "> 500ms"
    action: log
    severity: warning
    
  - metric_name: feature_name_error_rate
    condition: "> 5%"
    action: ci_fail
    severity: error

dependency_freshness:
  check_frequency: weekly
  critical_deps:
    - database_driver
    - validation_library
    - logging_framework
```

## Essential Metrics

```yaml
metrics:
  - name: "[feature_name]_request_duration_p95"
    budget: 200ms
    alert_threshold: 500ms
    type: latency
    description: P95 response time for [FEATURE_NAME] operations
    applies_to:
      feature: [feature_name]
      entrypoint: [entrypoint_name]

  - name: "[feature_name]_error_rate"
    budget: 1%
    alert_threshold: 5%
    type: error_rate
    description: Percentage of failed [FEATURE_NAME] operations
    applies_to:
      feature: [feature_name]
      entrypoint: [entrypoint_name]

  - name: "[feature_name]_active_count"
    budget: 1000
    alert_threshold: 10000
    type: gauge
    description: Current number of active [FEATURE_NAME] entities
```

## Cost Tracking

```yaml
cost_tracking:
  - item: database_calls_per_request
    tracking_method: tracked
    budget: 3
    unit: requests
    
  - item: compute_time
    tracking_method: measured
    budget: 50ms
    unit: request
    
  - item: storage_usage
    tracking_method: estimated
    budget: 1KB
    unit: entity
```

## Confusion Hotspots

```yaml
confusion_hotspots:
  - metric: cross_file_references
    measurement_method: static_analysis
    target_value: 2
    current_value: null
    
  - metric: indirection_depth
    measurement_method: automated
    target_value: 2
    current_value: null
    
  - metric: import_complexity
    measurement_method: static_analysis
    target_value: 5
    current_value: null
```

## Alert Rules

```yaml
alerts:
  - metric_name: "[feature_name]_request_duration_p95"
    condition: "> 500ms"
    action: log
    severity: warning
    
  - metric_name: "[feature_name]_error_rate"
    condition: "> 5%"
    action: ci_fail
    severity: error
```

## Standard Logging Pattern

All [FEATURE_NAME] operations should use this structured logging pattern:

```python
import structlog
logger = structlog.get_logger(__name__)

# Success operations
logger.info(
    "[feature_name]_operation_success",
    entity_id=str(entity.id),
    operation="create|update|delete|get",
    request_id=request_id,
    tenant_id=tenant_id,
    duration_ms=duration
)

# Error operations
logger.error(
    "[feature_name]_operation_error",
    error=str(error),
    operation="create|update|delete|get", 
    request_id=request_id,
    entity_id=entity_id_if_available,
    tenant_id=tenant_id
)
```

## Dependency Freshness

```yaml
dependency_freshness:
  check_frequency: weekly
  critical_deps:
    - database_driver
    - validation_library
    - logging_framework
```

## Diagnostics Runbook

### High Error Rate (>5%)
1. Check recent deployments
2. Examine error logs for patterns
3. Verify database connectivity  
4. Check input validation errors

### High Latency (>500ms P95)
1. Check database query performance
2. Examine N+1 query patterns
3. Review external service calls
4. Monitor connection pool health

### Entity Count Anomalies
1. Check for bulk operations
2. Examine cleanup job status
3. Review business logic changes
4. Verify tenant isolation

## Notes for LLM Agents

When working with [FEATURE_NAME] observability:

- **Always log with structured format** using the patterns above
- **Include request_id and tenant_id** in all log entries  
- **Measure duration** for operations >10ms
- **Emit metrics** at service layer boundaries
- **Update this plan** when adding new operations

Common patterns to avoid:
- Generic log messages without context
- Metrics without clear business meaning
- Alerts without actionable thresholds
