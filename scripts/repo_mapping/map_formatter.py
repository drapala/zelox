#!/usr/bin/env python3
"""
title: Map Formatter Component
purpose: Format repository map into various output formats
stability: stable
since_version: "0.4.0"
"""

from datetime import datetime
from typing import Any


class MapFormatter:
    """Format repository map for different output styles."""

    def __init__(self, structure: dict[str, Any]):
        """Initialize formatter with repository structure."""
        self.structure = structure
        self.timestamp = datetime.now().strftime("%Y-%m-%d")

    def format_markdown(self) -> str:
        """Format repository map as Markdown."""
        sections = [
            self._format_header(),
            self._format_structure_overview(),
            self._format_navigation(),
            self._format_features(),
            self._format_scripts(),
            self._format_adrs(),
            self._format_common_tasks(),
            self._format_footer(),
        ]
        return "".join(sections)

    def format_json(self) -> dict[str, Any]:
        """Format repository map as JSON structure."""
        return {
            "generated": self.timestamp,
            "version": "0.4.0",
            "structure": self.structure,
        }

    def format_yaml(self) -> str:
        """Format repository map as YAML."""
        import yaml

        data = {
            "repo_map": {
                "generated": self.timestamp,
                "version": "0.4.0",
                **self.structure,
            }
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def _format_header(self) -> str:
        """Generate Markdown header."""
        return f"""# REPO_MAP.md - Repository Navigation Guide

**Generated:** {self.timestamp}  
**Purpose:** LLM-first navigation and context discovery
"""

    def _format_structure_overview(self) -> str:
        """Generate repository structure overview."""
        return """
## Repository Structure

```
zelox/
├── docs/                    # Documentation & decisions
│   ├── adr/                # Architecture Decision Records
│   └── repo/               # Repository metadata
├── features/               # Vertical feature slices (VSA)
├── shared/                 # Truly shared utilities only
└── scripts/                # LLM-first tooling
```
"""

    def _format_navigation(self) -> str:
        """Generate quick navigation section."""
        return """
## Quick Navigation

### For Feature Development
1. **Start here:** `features/[feature_name]/README.md`
2. **Business logic:** `features/[feature_name]/service.py`
3. **Tests:** `features/[feature_name]/tests.py`
4. **API:** `features/[feature_name]/api.py`

### For Architecture Changes
1. **Decisions:** `docs/adr/`
2. **Patterns:** `CLAUDE.md`
3. **Current state:** `docs/repo/FACTS.md`

### For LLM Agents
1. **Entry point:** This file (REPO_MAP.md)
2. **Module index:** `docs/repo/INDEX.yaml`
3. **Recovery patterns:** `docs/repo/recovery_patterns.yaml`
"""

    def _format_features(self) -> str:
        """Format features section."""
        features = self.structure.get("features", [])

        if not features:
            return "\n## Current Features\n\n*None yet - this is a new repository*\n"

        section = "\n## Current Features\n\n"
        for feature in features:
            name_display = feature["name"].replace("_", " ").title()
            section += f"### {name_display}\n"
            section += f"- **Path:** `features/{feature['name']}/`\n"

            if feature.get("capabilities"):
                caps = ", ".join(c.replace("_", " ").title() for c in feature["capabilities"])
                section += f"- **Capabilities:** {caps}\n"

            metrics = feature.get("metrics", {})
            if metrics.get("loc"):
                section += f"- **Lines of Code:** {metrics['loc']:,}\n"

            section += f"- **Files:** {len(feature.get('files', []))} modules\n\n"

        return section

    def _format_scripts(self) -> str:
        """Format scripts section."""
        scripts = self.structure.get("scripts", [])

        if not scripts:
            return ""

        section = "\n## LLM-First Tooling\n\n"
        for script in scripts:
            section += f"- **`{script['name']}`**: {script['purpose']}\n"

        return section + "\n"

    def _format_adrs(self) -> str:
        """Format Architecture Decision Records table."""
        adrs = self.structure.get("docs", {}).get("adrs", [])

        if not adrs:
            return "\n## Architecture Decisions\n\n*No ADR files found in docs/adr/*\n\n"

        section = "\n## Architecture Decisions\n\n"
        section += "| ADR | Title | Status | Path |\n"
        section += "|-----|-------|--------|------|\n"

        for adr in adrs:
            relative_path = f"../adr/{adr['path'].split('/')[-1]}"
            section += (
                f"| {adr.get('number', 'N/A')} | "
                f"{adr['title']} | "
                f"{adr.get('status', 'unknown')} | "
                f"[View]({relative_path}) |\n"
            )

        return section + "\n"

    def _format_common_tasks(self) -> str:
        """Format common tasks section."""
        return """
## Common Tasks

### Adding a New Feature
1. `mkdir features/[feature_name]`
2. Copy template from `features/template/`
3. Update `docs/repo/INDEX.yaml`
4. Run `make llm.check`

### Making Changes
1. Check `features/[feature]/README.md` first
2. Look for BDD-Lite scenarios in tests
3. Update `OBS_PLAN.md` if changing APIs
4. Run `make pr.loc` before committing
"""

    def _format_footer(self) -> str:
        """Generate footer with update information."""
        return f"""
## Last Updated
- **Auto-generated:** {self.timestamp}
- **Script:** `scripts/gen_repo_map.py`
- **Next review:** When repository structure changes significantly
"""
