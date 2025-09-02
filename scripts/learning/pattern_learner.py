#!/usr/bin/env python3
"""
title: Pattern Learning Module
purpose: Learn successful architectural patterns from telemetry data
inputs: [{"name": "telemetry_events", "type": "list[dict]"}, {"name": "days_back", "type": "int"}]
outputs: [{"name": "patterns", "type": "list[ArchitecturalPattern]"}]
effects: ["pattern_extraction", "success_rate_calculation"]
deps: ["json", "datetime", "pathlib", "dataclasses"]
owners: ["drapala"]
stability: experimental
since_version: "0.5.0"
complexity: medium
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class ArchitecturalPattern:
    """Represents a learned architectural pattern."""

    pattern_id: str
    description: str
    success_rate: float
    context_features: list[str]
    architectural_traits: dict[str, float]
    sample_size: int
    confidence_score: float


class PatternLearner:
    """Learn successful patterns from telemetry data."""

    def __init__(self, telemetry_log_path: str):
        self.telemetry_log = Path(telemetry_log_path)
        self.patterns: dict[str, Any] = {}
        self.failure_patterns: dict[str, Any] = {}

    def learn_patterns(self, days_back: int = 30) -> list[ArchitecturalPattern]:
        """Learn patterns from recent telemetry data."""
        events = self._load_events(days_back)
        if not events:
            return []

        context_groups = self._group_by_context(events)
        patterns = []

        for context_signature, group_events in context_groups.items():
            if len(group_events) < 3:
                continue

            pattern = self._analyze_pattern(context_signature, group_events)
            if pattern and pattern.confidence_score > 0.3:
                patterns.append(pattern)

        return sorted(patterns, key=lambda p: p.success_rate, reverse=True)

    def _load_events(self, days_back: int) -> list[dict[str, Any]]:
        """Load telemetry events from specified time period."""
        if not self.telemetry_log.exists():
            return []

        cutoff_date = datetime.now() - timedelta(days=days_back)
        events = []

        try:
            with open(self.telemetry_log, encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event.get("timestamp", ""))
                        if event_time >= cutoff_date:
                            events.append(event)
                    except Exception:
                        continue
        except Exception:
            return []

        return events

    def _group_by_context(self, events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group events by similar context features."""
        groups = defaultdict(list)

        for event in events:
            if "files_modified" not in event:
                continue

            features = self._extract_context_features(event)
            context_signature = ",".join(sorted(features))
            groups[context_signature].append(event)

        return groups

    def _extract_context_features(self, event: dict[str, Any]) -> list[str]:
        """Extract context features from an event."""
        features = []

        file_count = len(event.get("files_modified", []))
        if file_count == 1:
            features.append("single_file")
        elif file_count <= 3:
            features.append("few_files")
        else:
            features.append("many_files")

        hops = event.get("cognitive_hops", 0)
        if hops == 0:
            features.append("no_hops")
        elif hops <= 2:
            features.append("low_hops")
        else:
            features.append("high_hops")

        coherence = event.get("domain_coherence", 0.5)
        if coherence > 0.8:
            features.append("high_coherence")
        elif coherence > 0.4:
            features.append("medium_coherence")
        else:
            features.append("low_coherence")

        edit_type = event.get("edit_type", "update")
        features.append(f"edit_{edit_type}")

        return features

    def _analyze_pattern(
        self, context_signature: str, events: list[dict[str, Any]]
    ) -> ArchitecturalPattern | None:
        """Analyze a group of events to extract pattern."""
        if not events:
            return None

        successful_events = [e for e in events if e.get("success", False)]
        success_rate = len(successful_events) / len(events)

        architectural_traits = self._calculate_traits(successful_events)
        confidence = min(1.0, len(events) / 10) * (0.5 + success_rate * 0.5)
        pattern_id = f"pattern_{abs(hash(context_signature)) % 10000}"

        return ArchitecturalPattern(
            pattern_id=pattern_id,
            description=self._generate_pattern_description(context_signature, architectural_traits),
            success_rate=success_rate,
            context_features=context_signature.split(","),
            architectural_traits=architectural_traits,
            sample_size=len(events),
            confidence_score=confidence,
        )

    def _calculate_traits(self, events: list[dict[str, Any]]) -> dict[str, float]:
        """Calculate architectural traits from successful events."""
        if not events:
            return {}

        total_hops = sum(e.get("cognitive_hops", 0) for e in events)
        total_coherence = sum(e.get("domain_coherence", 0.5) for e in events)
        total_context_size = sum(len(e.get("files_modified", [])) for e in events)

        return {
            "avg_cognitive_hops": total_hops / len(events),
            "avg_domain_coherence": total_coherence / len(events),
            "avg_context_size": total_context_size / len(events),
        }

    def _generate_pattern_description(self, context: str, traits: dict[str, float]) -> str:
        """Generate human-readable pattern description."""
        features = context.split(",")
        desc_parts = []

        if "single_file" in features:
            desc_parts.append("Single-file edits")
        elif "few_files" in features:
            desc_parts.append("Small-scope edits")
        else:
            desc_parts.append("Large-scope edits")

        if "high_coherence" in features:
            desc_parts.append("with high domain coherence")
        elif "low_coherence" in features:
            desc_parts.append("with low domain coherence")

        if "low_hops" in features:
            desc_parts.append("and minimal cognitive hops")
        elif "high_hops" in features:
            desc_parts.append("with complex dependency chains")

        return " ".join(desc_parts)
