"""
Readiness Metrics Definitions
Define individual metrics for LLM readiness assessment.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MetricResult:
    """Result from a metric calculation."""

    score: float
    max_score: float
    status: str  # ✅, ⚠️, ❌
    message: str
    details: dict | None = None


@dataclass
class ReadinessMetric:
    """Individual readiness metric configuration."""

    name: str
    weight: float
    target_threshold: float
    description: str
    category: str  # co-location, complexity, documentation, etc.


class MetricPlugin(ABC):
    """Base class for metric plugins."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    @abstractmethod
    def calculate(self) -> MetricResult:
        """Calculate the metric and return result."""
        pass

    @property
    @abstractmethod
    def metric_definition(self) -> ReadinessMetric:
        """Return the metric definition."""
        pass

    def _calculate_status(self, ratio: float, threshold: float) -> str:
        """Calculate status emoji based on ratio vs threshold."""
        if ratio >= threshold:
            return "✅"
        elif ratio >= threshold * 0.7:
            return "⚠️"
        return "❌"


class CoLocationMetric(MetricPlugin):
    """Metric for test co-location with code."""

    @property
    def metric_definition(self) -> ReadinessMetric:
        return ReadinessMetric(
            name="Co-location Index",
            weight=25.0,
            target_threshold=0.8,
            description="Tests co-located with feature code",
            category="co-location",
        )

    def calculate(self) -> MetricResult:
        """Check if tests are co-located with code."""
        features_dir = self.repo_root / "features"
        if not features_dir.exists():
            return MetricResult(
                score=0, max_score=25, status="❌", message="No features/ directory found"
            )

        feature_dirs = [d for d in features_dir.iterdir() if d.is_dir()]
        if not feature_dirs:
            return MetricResult(
                score=5,
                max_score=25,
                status="⚠️",
                message="Features directory exists but is empty",
            )

        co_located = sum(1 for d in feature_dirs if self._has_code_and_tests(d))
        ratio = co_located / len(feature_dirs) if feature_dirs else 0

        return MetricResult(
            score=ratio * self.metric_definition.weight,
            max_score=self.metric_definition.weight,
            status=self._calculate_status(ratio, self.metric_definition.target_threshold),
            message=f"Co-location: {co_located}/{len(feature_dirs)} ({ratio:.1%})",
            details={"co_located": co_located, "total": len(feature_dirs), "ratio": ratio},
        )

    def _has_code_and_tests(self, feature_dir: Path) -> bool:
        """Check if directory has both code and tests."""
        code_files = ["service.py", "models.py", "api.py", "operations.py"]
        has_code = any((feature_dir / f).exists() for f in code_files)
        has_tests = (feature_dir / "tests.py").exists()
        return has_code and has_tests


class FrontMatterMetric(MetricPlugin):
    """Metric for front-matter coverage in files."""

    @property
    def metric_definition(self) -> ReadinessMetric:
        return ReadinessMetric(
            name="Front-matter Coverage",
            weight=20.0,
            target_threshold=0.9,
            description="Files have structured front-matter",
            category="documentation",
        )

    def calculate(self) -> MetricResult:
        """Check front-matter coverage in feature files."""
        features_dir = self.repo_root / "features"
        if not features_dir.exists():
            return MetricResult(
                score=0, max_score=20, status="❌", message="No features/ directory found"
            )

        python_files = [
            f
            for f in features_dir.rglob("*.py")
            if "test" not in f.name and "__init__" not in f.name
        ]

        if not python_files:
            return MetricResult(
                score=10,
                max_score=20,
                status="⚠️",
                message="No Python files in features/ to check",
            )

        with_frontmatter = sum(1 for f in python_files if self._has_frontmatter(f))
        ratio = with_frontmatter / len(python_files) if python_files else 0

        return MetricResult(
            score=ratio * self.metric_definition.weight,
            max_score=self.metric_definition.weight,
            status=self._calculate_status(ratio, self.metric_definition.target_threshold),
            message=f"Front-matter: {with_frontmatter}/{len(python_files)} ({ratio:.1%})",
            details={
                "with_frontmatter": with_frontmatter,
                "total": len(python_files),
                "ratio": ratio,
            },
        )

    def _has_frontmatter(self, file_path: Path) -> bool:
        """Check if file has front-matter."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                keywords = ["title:", "purpose:", "inputs:", "outputs:"]
                return ('"""' in content and any(k in content.lower() for k in keywords)) or (
                    content.startswith("---")
                )
        except Exception:
            return False
