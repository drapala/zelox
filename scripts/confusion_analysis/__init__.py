"""
---
title: Confusion Analysis Module
purpose: Analyze codebase for confusion metrics and hotspots
inputs:
  - name: repository_path
    type: Path
outputs:
  - name: confusion_report
    type: Dict
effects:
  - Parses Python AST
  - Generates reports
deps:
  - ast
  - pathlib
owners: ['llm-architect']
stability: stable
since_version: 1.0.0
---

Confusion Analysis Module - Analyzes code complexity and confusion metrics.
"""

from .complexity_analyzer import ComplexityAnalyzer
from .confusion_reporter import ConfusionReporter
from .confusion_scorer import ConfusionScorer
from .hotspot_detector import HotspotDetector

__all__ = ["ComplexityAnalyzer", "ConfusionScorer", "HotspotDetector", "ConfusionReporter"]
