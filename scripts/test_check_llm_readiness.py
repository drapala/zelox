#!/usr/bin/env python3
"""
Unit tests for check_llm_readiness.py

title: LLM Readiness Check Tests
purpose: Validate LLM readiness scoring logic
inputs: [{"name": "test_scenarios", "type": "functions"}]
outputs: [{"name": "test_results", "type": "pass_fail"}]
effects: ["validation"]
deps: ["pytest", "unittest.mock"]
owners: ["drapala"]
stability: stable
since_version: "0.2.0"
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from check_llm_readiness import LLMReadinessChecker


class TestCoLocationCheck:
    """Test co-location scoring logic."""
    
    def test_perfect_co_location(self, tmp_path):
        """Test 100% co-location scores maximum points."""
        # Create feature directory with code and tests
        features_dir = tmp_path / "features"
        feature1 = features_dir / "feature1"
        feature1.mkdir(parents=True)
        
        # Create code and test files
        (feature1 / "service.py").write_text("# Service code")
        (feature1 / "tests.py").write_text("# Tests")
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_co_location()
        
        assert score == 25  # Maximum points for co-location
        assert "✅" in message
        assert "100.0%" in message
    
    def test_no_co_location(self, tmp_path):
        """Test no co-location scores zero points."""
        # Create feature directory with only code, no tests
        features_dir = tmp_path / "features"
        feature1 = features_dir / "feature1"
        feature1.mkdir(parents=True)
        
        # Only code, no tests
        (feature1 / "service.py").write_text("# Service code")
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_co_location()
        
        assert score == 0  # No points for 0% co-location
        assert "❌" in message
        assert "0.0%" in message
    
    def test_partial_co_location(self, tmp_path):
        """Test partial co-location scores proportionally."""
        features_dir = tmp_path / "features"
        
        # Feature 1: has tests (co-located)
        feature1 = features_dir / "feature1"
        feature1.mkdir(parents=True)
        (feature1 / "service.py").write_text("# Service")
        (feature1 / "tests.py").write_text("# Tests")
        
        # Feature 2: no tests (not co-located)
        feature2 = features_dir / "feature2"
        feature2.mkdir(parents=True)
        (feature2 / "models.py").write_text("# Models")
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_co_location()
        
        # 50% co-location = 12.5 points
        assert score == 12
        assert "50.0%" in message
    
    def test_empty_features_directory(self, tmp_path):
        """Test empty features directory."""
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_co_location()
        
        assert score == 20  # Default score for empty
        assert "⚠️" in message
        assert "empty" in message.lower()


class TestAverageHopsCheck:
    """Test import complexity (average hops) calculation."""
    
    def test_low_import_complexity(self, tmp_path):
        """Test low import count scores well."""
        # Create Python file with few imports
        py_file = tmp_path / "simple.py"
        py_file.write_text("""
import os
from pathlib import Path

def main():
    pass
""")
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_average_hops()
        
        assert score == 20  # Maximum for ≤3 imports
        assert "✅" in message
        assert "≤3" in message
    
    def test_medium_import_complexity(self, tmp_path):
        """Test medium import count scores moderately."""
        # Create Python file with medium imports
        py_file = tmp_path / "medium.py"
        py_file.write_text("""
import os
import sys
from pathlib import Path
from typing import List

def main():
    pass
""")
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_average_hops()
        
        assert score == 15  # Medium score for 4-5 imports
        assert "⚠️" in message
    
    def test_high_import_complexity(self, tmp_path):
        """Test high import count scores poorly."""
        # Create Python file with many imports
        py_file = tmp_path / "complex.py"
        py_file.write_text("""
import os
import sys
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import requests

def main():
    pass
""")
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_average_hops()
        
        assert score == 5  # Low score for >5 imports
        assert "❌" in message
    
    def test_no_python_files(self, tmp_path):
        """Test when no Python files exist."""
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_average_hops()
        
        assert score == 15  # Default score
        assert "⚠️" in message
        assert "No Python files" in message


class TestFrontMatterCoverage:
    """Test front-matter coverage checking."""
    
    def test_full_frontmatter_coverage(self, tmp_path):
        """Test 100% front-matter coverage scores maximum."""
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        
        # Create file with proper front-matter
        py_file = features_dir / "service.py"
        py_file.write_text('''"""
title: Test Service
purpose: Handle test operations
inputs: [{"name": "data", "type": "dict"}]
outputs: [{"name": "result", "type": "bool"}]
"""

def process():
    pass
''')
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_front_matter_coverage()
        
        assert score == 20  # Maximum for 100% coverage
        assert "✅" in message
        assert "100.0%" in message
    
    def test_no_frontmatter_coverage(self, tmp_path):
        """Test no front-matter scores zero."""
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        
        # Create file without front-matter
        py_file = features_dir / "service.py"
        py_file.write_text('''
def process():
    pass
''')
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_front_matter_coverage()
        
        assert score == 0  # No points for 0% coverage
        assert "❌" in message
        assert "0.0%" in message
    
    def test_yaml_frontmatter_detected(self, tmp_path):
        """Test YAML front-matter format is detected."""
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        
        # Create file with YAML front-matter
        py_file = features_dir / "config.py"
        py_file.write_text('''---
title: Config Module
purpose: Configuration management
---

CONFIG = {}
''')
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_front_matter_coverage()
        
        assert score > 0  # Should detect the front-matter
        assert "%" in message


class TestDocumentationStructure:
    """Test required documentation file checks."""
    
    def test_all_docs_present(self, tmp_path):
        """Test all required docs present scores maximum."""
        # Create all required documentation files
        (tmp_path / "CLAUDE.md").touch()
        docs_repo = tmp_path / "docs" / "repo"
        docs_repo.mkdir(parents=True)
        (docs_repo / "REPO_MAP.md").touch()
        (docs_repo / "INDEX.yaml").touch()
        (docs_repo / "FACTS.md").touch()
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_documentation_structure()
        
        assert score == 20  # 5 points per file, 4 files
        assert "✅" in message
        assert "All required documentation files present" in message
    
    def test_some_docs_missing(self, tmp_path):
        """Test missing docs reduces score."""
        # Create only some documentation files
        (tmp_path / "CLAUDE.md").touch()
        docs_repo = tmp_path / "docs" / "repo"
        docs_repo.mkdir(parents=True)
        (docs_repo / "REPO_MAP.md").touch()
        # Missing INDEX.yaml and FACTS.md
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_documentation_structure()
        
        assert score == 10  # 5 points each for 2 present files
        assert "❌" in message or "⚠️" in message
        assert "Missing docs:" in message
        assert "INDEX.yaml" in message
        assert "FACTS.md" in message
    
    def test_no_docs_present(self, tmp_path):
        """Test no docs scores zero."""
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_documentation_structure()
        
        assert score == 0
        assert "❌" in message
        assert "Missing docs:" in message


class TestADRStructure:
    """Test ADR structure and completeness checks."""
    
    def test_valid_adr_structure(self, tmp_path):
        """Test valid ADR structure scores well."""
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        
        # Create template
        (adr_dir / "000-template.md").write_text("# Template")
        
        # Create ADR with proper front-matter
        (adr_dir / "001-decision.md").write_text("""
# ADR-001: Test Decision

```yaml
adr_number: 1
status: accepted
```
""")
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_adr_structure()
        
        assert score == 10  # Maximum for good structure
        assert "✅" in message
        assert "properly formatted" in message
    
    def test_no_adr_directory(self, tmp_path):
        """Test missing ADR directory scores zero."""
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_adr_structure()
        
        assert score == 0
        assert "❌" in message
        assert "No docs/adr/ directory" in message
    
    def test_insufficient_adrs(self, tmp_path):
        """Test too few ADRs scores lower."""
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        
        # Only one ADR file
        (adr_dir / "001-decision.md").touch()
        
        checker = LLMReadinessChecker(tmp_path)
        score, message = checker.check_adr_structure()
        
        assert score == 3  # Lower score for insufficient ADRs
        assert "⚠️" in message
        assert "at least 2 ADR files" in message


class TestOverallScore:
    """Test overall scoring and thresholds."""
    
    def test_perfect_score(self, tmp_path):
        """Test repository with perfect setup scores 100."""
        # Create perfect repository structure
        features_dir = tmp_path / "features"
        feature1 = features_dir / "feature1"
        feature1.mkdir(parents=True)
        
        # Co-located code and tests with front-matter
        (feature1 / "service.py").write_text('''"""
title: Service
purpose: Business logic
"""
import os

def process():
    pass
''')
        (feature1 / "tests.py").write_text("# Tests")
        
        # All documentation
        (tmp_path / "CLAUDE.md").touch()
        docs_repo = tmp_path / "docs" / "repo"
        docs_repo.mkdir(parents=True)
        (docs_repo / "REPO_MAP.md").touch()
        (docs_repo / "INDEX.yaml").touch()
        (docs_repo / "FACTS.md").touch()
        
        # ADRs
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)
        (adr_dir / "000-template.md").write_text("# Template")
        (adr_dir / "001-decision.md").write_text("""
```yaml
adr_number: 1
status: accepted
```
""")
        
        checker = LLMReadinessChecker(tmp_path)
        results = checker.run_all_checks()
        
        # Should score high (not necessarily 100 due to import complexity)
        assert results["score"] >= 80
        assert "Repository meets LLM-first standards!" in results["recommendations"][0]
    
    def test_failing_score(self, tmp_path):
        """Test poor repository scores below threshold."""
        # Create minimal structure
        checker = LLMReadinessChecker(tmp_path)
        results = checker.run_all_checks()
        
        assert results["score"] < 60
        assert len(results["recommendations"]) > 0
        assert "Create basic repository structure" in results["recommendations"][0]
    
    def test_recommendations_for_medium_score(self, tmp_path):
        """Test medium score generates appropriate recommendations."""
        # Create partial structure
        features_dir = tmp_path / "features"
        features_dir.mkdir()
        (tmp_path / "CLAUDE.md").touch()
        
        checker = LLMReadinessChecker(tmp_path)
        results = checker.run_all_checks()
        
        # Should be in medium range
        assert 60 <= results["score"] < 80
        assert any("co-location" in rec.lower() for rec in results["recommendations"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])