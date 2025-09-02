"""
Documentation Metrics
Check documentation structure and completeness.
"""

from pathlib import Path

from .readiness_metrics import MetricPlugin, MetricResult, ReadinessMetric


class DocumentationStructureMetric(MetricPlugin):
    """Metric for required documentation files."""

    @property
    def metric_definition(self) -> ReadinessMetric:
        return ReadinessMetric(
            name="Documentation Structure",
            weight=20.0,
            target_threshold=1.0,
            description="Required documentation files present",
            category="documentation",
        )

    def calculate(self) -> MetricResult:
        """Check for required documentation files."""
        required_files = [
            ("CLAUDE.md", 5),
            ("docs/repo/REPO_MAP.md", 5),
            ("docs/repo/INDEX.yaml", 5),
            ("docs/repo/FACTS.md", 5),
        ]

        score = 0
        missing = []

        for file_path, points in required_files:
            if (self.repo_root / file_path).exists():
                score += points
            else:
                missing.append(file_path)

        if missing:
            status = "❌" if len(missing) > 2 else "⚠️"
            message = f"Missing docs: {', '.join(missing)}"
        else:
            status = "✅"
            message = "All required documentation files present"

        return MetricResult(
            score=score,
            max_score=self.metric_definition.weight,
            status=status,
            message=message,
            details={"missing": missing, "found": len(required_files) - len(missing)},
        )


class ADRMetric(MetricPlugin):
    """Metric for ADR structure and completeness."""

    @property
    def metric_definition(self) -> ReadinessMetric:
        return ReadinessMetric(
            name="ADR Structure",
            weight=10.0,
            target_threshold=0.8,
            description="ADR files properly formatted",
            category="documentation",
        )

    def calculate(self) -> MetricResult:
        """Check ADR structure and completeness."""
        adr_dir = self.repo_root / "docs" / "adr"

        if not adr_dir.exists():
            return MetricResult(
                score=0, max_score=10, status="❌", message="No docs/adr/ directory found"
            )

        adr_files = list(adr_dir.glob("*.md"))
        if len(adr_files) < 2:
            return MetricResult(
                score=3,
                max_score=10,
                status="⚠️",
                message="Need at least 2 ADR files (template + decisions)",
            )

        valid_adrs = sum(1 for f in adr_files if self._is_valid_adr(f))
        ratio = valid_adrs / len(adr_files) if adr_files else 0

        if ratio >= 0.8:
            score = 10
            status = "✅"
        else:
            score = 5
            status = "⚠️"

        return MetricResult(
            score=score,
            max_score=self.metric_definition.weight,
            status=status,
            message=f"ADR structure: {valid_adrs}/{len(adr_files)} properly formatted",
            details={"valid": valid_adrs, "total": len(adr_files), "ratio": ratio},
        )

    def _is_valid_adr(self, adr_file: Path) -> bool:
        """Check if ADR has proper structure."""
        try:
            with open(adr_file, encoding="utf-8") as f:
                content = f.read()
                return "adr_number:" in content and "status:" in content
        except Exception:
            return False
