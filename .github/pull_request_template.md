## Description
<!-- Brief description of changes (2-3 sentences) -->

## Type of Change
<!-- Check the one that applies -->
- [ ] `feature/` - New functionality
- [ ] `test/` - Test additions/improvements
- [ ] `fix/` - Bug fix
- [ ] `docs/` - Documentation only
- [ ] `refactor/` - Code restructuring
- [ ] `chore/` - Maintenance/tooling

## LLM-First Compliance Checklist

### Co-location
- [ ] Tests are in the same directory as code
- [ ] Documentation is with the feature (not in separate docs/)
- [ ] No new shared modules (unless used by 2+ features)

### File Standards
- [ ] All Python files have YAML front-matter
- [ ] Files are 150-500 LOC (split if larger)
- [ ] One clear purpose per file

### Navigation Updates
- [ ] INDEX.yaml updated if features/structure changed
- [ ] REPO_MAP.md updated for significant changes
- [ ] Front-matter updated if contracts changed

### Quality Gates
- [ ] `make pr.loc` passes (≤10 files, ≤500 LOC)
- [ ] `make llm.check` score ≥80
- [ ] `make llm.index.validate` passes
- [ ] BDD-Lite scenarios for P0 features (if applicable)

### Observability (if applicable)
- [ ] OBS_PLAN.md updated for new operations
- [ ] Structured logging with request_id/tenant_id
- [ ] Metrics have budgets and thresholds

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests if external dependencies
- [ ] Golden tests for critical flows (P0 features)

## Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes documented in ADR

## Related Issues
<!-- Closes #(issue number) -->

## Additional Context
<!-- Any additional information for reviewers -->