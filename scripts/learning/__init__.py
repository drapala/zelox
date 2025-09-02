"""
title: Learning System Package
purpose: Modular adaptive learning system for LLM architecture improvements
"""

from .adaptation_engine import AdaptationEngine, ImprovementSuggestion
from .learning_reporter import LearningReporter
from .metric_tracker import MetricTracker
from .pattern_learner import ArchitecturalPattern, PatternLearner
from .wiring import AdaptiveLearningSystem, build_learning_system

__all__ = [
    "AdaptiveLearningSystem",
    "build_learning_system",
    "PatternLearner",
    "ArchitecturalPattern",
    "MetricTracker",
    "AdaptationEngine",
    "ImprovementSuggestion",
    "LearningReporter",
]
