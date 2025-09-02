"""
title: Drift Detection Module
purpose: Modular drift detection for controlled duplication
inputs: []
outputs: []
effects: []
deps: []
owners: ["drapala"]
stability: stable
since_version: "0.4.0"
"""

from .block_finder import BlockFinder
from .drift_calculator import DriftCalculator
from .drift_reporter import DriftReporter

__all__ = ["BlockFinder", "DriftCalculator", "DriftReporter"]
