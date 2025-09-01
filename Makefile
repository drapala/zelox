# LLM-First Makefile for Zelox
# Provides consistent targets for LLM-friendly development workflow

.PHONY: help pr.loc llm.check test.fast clean confusion.report cost.report pr.check validate.schemas llm.index.validate drift.check drift.report llm.map llm.map.check

# Default target
help:
	@echo "LLM-First Development Targets:"
	@echo "  pr.loc          - Check PR size limits (excludes Markdown)"
	@echo "  llm.check       - Run LLM readiness checks"
	@echo "  llm.map         - Auto-generate REPO_MAP.md from codebase"
	@echo "  llm.map.check   - Validate REPO_MAP.md is up-to-date"
	@echo "  test.fast       - Run fast test suite"
	@echo "  drift.check     - Check for uncontrolled duplication drift"
	@echo "  drift.report    - Generate detailed drift analysis report"
	@echo "  clean           - Clean temporary files"

# PR LOC gate - excludes documentation from limits
pr.loc:
	@echo "Checking PR size limits..."
	@python3 scripts/check_pr_loc.py

# LLM readiness check - calculate and validate LLM Readiness Score
llm.check:
	@echo "Checking LLM readiness..."
	@python3 scripts/check_llm_readiness.py

# Fast test suite (placeholder - adapt to your test framework)
test.fast:
	@echo "Running fast tests..."
	@echo "⚠️  Configure your test framework here (pytest, npm test, etc.)"

# Generate semantic dependency analysis
llm.semantic:
	@echo "Analyzing semantic dependencies..."
	@python3 scripts/semantic_analyzer.py --repo-root . --report

# Generate domain pattern analysis
llm.domain:
	@echo "Analyzing domain patterns..."
	@python3 scripts/domain_analyzer.py --repo-root . --report

# Generate adaptive learning recommendations
llm.learn:
	@echo "Learning from telemetry and generating recommendations..."
	@python3 scripts/adaptive_learner.py --repo-root . --analyze

# Generate confusion report (telemetry analysis)
confusion.report:
	@echo "Generating confusion report..."
	@python3 scripts/telemetry_collector.py --analyze --days 7

# Generate cost report (planned)
cost.report:
	@echo "Generating cost report..."
	@echo "⚠️  Configure cost tracking analysis here"

# Check for uncontrolled duplication drift
drift.check:
	@echo "Checking for uncontrolled duplication drift..."
	@python3 scripts/drift_check.py

# Generate detailed drift analysis report  
drift.report:
	@echo "Generating detailed drift analysis report..."
	@python3 scripts/drift_check.py --report

# Full PR check (all gates)
pr.check:
	@echo "Running full PR quality gates..."
	@make pr.loc
	@make validate.schemas  
	@make llm.check
	@make drift.check
	@echo "✅ All PR quality gates passed!"

# Validate all schemas
validate.schemas:
	@echo "Validating repository schemas..."
	@python3 scripts/validate_schemas.py

# Validate INDEX.yaml with modular schemas and cross-checks
llm.index.validate:
	@echo "Validating INDEX.yaml with cross-validation..."
	@python3 scripts/validate_schemas.py

# Auto-generate REPO_MAP.md from codebase
llm.map:
	@echo "Auto-generating REPO_MAP.md..."
	@python3 scripts/gen_repo_map.py

# Validate REPO_MAP.md is up-to-date
llm.map.check:
	@echo "Validating REPO_MAP.md is up-to-date..."
	@python3 scripts/gen_repo_map.py --dry-run

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true