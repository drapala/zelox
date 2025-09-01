# LLM-First Makefile for Zelox
# Provides consistent targets for LLM-friendly development workflow

.PHONY: help pr.loc llm.check test.fast clean confusion.report cost.report pr.check validate.schemas llm.index.validate

# Default target
help:
	@echo "LLM-First Development Targets:"
	@echo "  pr.loc          - Check PR size limits (excludes Markdown)"
	@echo "  llm.check       - Run LLM readiness checks"
	@echo "  test.fast       - Run fast test suite"
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

# Generate confusion report (planned)
confusion.report:
	@echo "Generating confusion report..."
	@echo "⚠️  Configure confusion metrics analysis here"

# Generate cost report (planned)
cost.report:
	@echo "Generating cost report..."
	@echo "⚠️  Configure cost tracking analysis here"

# Full PR check (all gates)
pr.check:
	@echo "Running full PR quality gates..."
	@make pr.loc
	@make validate.schemas  
	@make llm.check
	@echo "✅ All PR quality gates passed!"

# Validate all schemas
validate.schemas:
	@echo "Validating repository schemas..."
	@python3 scripts/validate_schemas.py

# Validate INDEX.yaml with modular schemas and cross-checks
llm.index.validate:
	@echo "Validating INDEX.yaml with cross-validation..."
	@python3 scripts/validate_schemas.py

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true