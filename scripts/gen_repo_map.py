#!/usr/bin/env python3
"""
title: Repository Map Generator
purpose: Auto-generate REPO_MAP.md from current codebase state
inputs: [{"name": "repo_root", "type": "path"}, {"name": "output_path", "type": "path"}]
outputs: [{"name": "repo_map", "type": "markdown_file"}]
effects: ["file_generation", "documentation_update"]
deps: ["pathlib", "yaml", "re", "datetime"]
owners: ["drapala"]
stability: stable
since_version: "0.3.0"
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class FileAnalyzer:
    """Extract metadata from different file types."""

    @staticmethod
    def extract_python_frontmatter(file_path: Path) -> dict[str, Any]:
        """Extract YAML frontmatter from Python files."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Look for docstring with YAML-like content
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if not docstring_match:
                return {}

            docstring = docstring_match.group(1).strip()

            # Try to parse as YAML-like content
            frontmatter = {}
            for line in docstring.split("\n"):
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    try:
                        # Handle simple key: value pairs
                        if line.startswith(("title:", "purpose:", "stability:", "since_version:")):
                            key, value = line.split(":", 1)
                            frontmatter[key.strip()] = value.strip()
                        elif line.startswith(
                            ("inputs:", "outputs:", "effects:", "deps:", "owners:")
                        ):
                            # These are arrays, extract the content
                            key = line.split(":")[0].strip()
                            # Simple extraction - look for the array content
                            array_match = re.search(rf"{key}:\s*\[(.*?)\]", docstring, re.DOTALL)
                            if array_match:
                                array_content = array_match.group(1).strip()
                                if array_content:
                                    # Parse simple arrays
                                    if key in ["deps", "owners", "effects"]:
                                        items = [
                                            item.strip().strip("\"'")
                                            for item in array_content.split(",")
                                        ]
                                        frontmatter[key] = [item for item in items if item]
                                    else:
                                        # For complex arrays like inputs/outputs, store as string
                                        frontmatter[key] = array_content
                    except Exception:
                        continue

            return frontmatter

        except Exception:
            return {}

    @staticmethod
    def get_file_purpose(file_path: Path) -> str:
        """Extract purpose from file based on name and content."""
        name = file_path.name.lower()

        # Common file type mappings
        purpose_map = {
            "service.py": "Business logic orchestration",
            "models.py": "Domain entities and value objects",
            "api.py": "HTTP endpoints and request handling",
            "repository.py": "Data access layer",
            "tests.py": "Test suite",
            "wiring.py": "Dependency injection setup",
            "makefile": "Build automation",
            "pyproject.toml": "Python project configuration",
            "readme.md": "Documentation",
            "index.yaml": "Module metadata and contracts",
        }

        if name in purpose_map:
            return purpose_map[name]

        # Try to extract from frontmatter
        if file_path.suffix == ".py":
            frontmatter = FileAnalyzer.extract_python_frontmatter(file_path)
            if "purpose" in frontmatter:
                return frontmatter["purpose"]

        # Fallback based on directory and extension
        if "test" in name:
            return "Test suite"
        elif name.endswith(".md"):
            return "Documentation"
        elif name.endswith(".py"):
            return "Python module"
        elif name.endswith((".yml", ".yaml")):
            return "Configuration"

        return "Unknown"


class StructureMapper:
    """Build hierarchical project structure."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.analyzer = FileAnalyzer()

    def scan_features(self) -> list[dict[str, Any]]:
        """Scan features directory for VSA structure."""
        features = []
        features_dir = self.repo_root / "features"

        if not features_dir.exists():
            return features

        for feature_dir in features_dir.iterdir():
            if not feature_dir.is_dir() or feature_dir.name.startswith("."):
                continue

            feature_info = {
                "name": feature_dir.name,
                "path": str(feature_dir.relative_to(self.repo_root)),
                "files": [],
                "has_tests": False,
                "has_api": False,
                "has_service": False,
            }

            for file_path in feature_dir.glob("*.py"):
                file_info = {
                    "name": file_path.name,
                    "purpose": self.analyzer.get_file_purpose(file_path),
                    "frontmatter": self.analyzer.extract_python_frontmatter(file_path),
                }
                feature_info["files"].append(file_info)

                # Track key files
                if file_path.name == "tests.py":
                    feature_info["has_tests"] = True
                elif file_path.name == "api.py":
                    feature_info["has_api"] = True
                elif file_path.name == "service.py":
                    feature_info["has_service"] = True

            features.append(feature_info)

        return features

    def scan_scripts(self) -> list[dict[str, Any]]:
        """Scan scripts directory for tooling."""
        scripts = []
        scripts_dir = self.repo_root / "scripts"

        if not scripts_dir.exists():
            return scripts

        for script_path in scripts_dir.glob("*.py"):
            if script_path.name.startswith("test_"):
                continue  # Skip test files

            script_info = {
                "name": script_path.name,
                "path": str(script_path.relative_to(self.repo_root)),
                "purpose": self.analyzer.get_file_purpose(script_path),
                "frontmatter": self.analyzer.extract_python_frontmatter(script_path),
            }
            scripts.append(script_info)

        return scripts

    def scan_docs(self) -> list[dict[str, Any]]:
        """Scan documentation structure."""
        docs = []
        docs_dir = self.repo_root / "docs"

        if not docs_dir.exists():
            return docs

        for doc_path in docs_dir.rglob("*.md"):
            doc_info = {
                "name": doc_path.name,
                "path": str(doc_path.relative_to(self.repo_root)),
                "purpose": self.analyzer.get_file_purpose(doc_path),
            }
            docs.append(doc_info)

        return docs

    def get_key_files(self) -> list[dict[str, Any]]:
        """Identify key configuration and root files."""
        key_files = []

        key_patterns = [
            "Makefile",
            "pyproject.toml",
            "README.md",
            "CLAUDE.md",
            ".pre-commit-config.yaml",
            ".github/workflows/*.yml",
        ]

        for pattern in key_patterns:
            if "*" in pattern:
                # Handle glob patterns
                for file_path in self.repo_root.glob(pattern):
                    if file_path.is_file():
                        key_files.append(
                            {
                                "name": file_path.name,
                                "path": str(file_path.relative_to(self.repo_root)),
                                "purpose": self.analyzer.get_file_purpose(file_path),
                            }
                        )
            else:
                file_path = self.repo_root / pattern
                if file_path.exists():
                    key_files.append(
                        {
                            "name": file_path.name,
                            "path": str(file_path.relative_to(self.repo_root)),
                            "purpose": self.analyzer.get_file_purpose(file_path),
                        }
                    )

        return key_files


class MarkdownGenerator:
    """Generate properly formatted REPO_MAP.md."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.structure_mapper = StructureMapper(repo_root)

    def generate_header(self) -> str:
        """Generate header section."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"""# REPO_MAP.md - Repository Navigation Guide

**Generated:** {timestamp}  
**Purpose:** LLM-first navigation and context discovery
"""

    def generate_structure_overview(self) -> str:
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

    def generate_navigation_section(self) -> str:
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

    def generate_features_section(self) -> str:
        """Generate current features section."""
        features = self.structure_mapper.scan_features()

        if not features:
            return "\n## Current Features\n\n*None yet - this is a new repository*\n"

        section = "\n## Current Features\n\n"
        for feature in features:
            section += f"### {feature['name'].replace('_', ' ').title()}\n"
            section += f"- **Path:** `{feature['path']}/`\n"

            # Show key capabilities
            capabilities = []
            if feature["has_api"]:
                capabilities.append("HTTP API")
            if feature["has_service"]:
                capabilities.append("Business Logic")
            if feature["has_tests"]:
                capabilities.append("Tests")

            if capabilities:
                section += f"- **Capabilities:** {', '.join(capabilities)}\n"

            section += f"- **Files:** {len(feature['files'])} Python modules\n\n"

        return section

    def generate_scripts_section(self) -> str:
        """Generate tooling section."""
        scripts = self.structure_mapper.scan_scripts()

        if not scripts:
            return ""

        section = "\n## LLM-First Tooling\n\n"
        for script in scripts:
            section += f"- **`{script['name']}`**: {script['purpose']}\n"

        return section + "\n"

    def generate_adr_section(self) -> str:
        """Generate ADR table from existing REPO_MAP.md."""
        # For now, preserve the existing ADR section
        adr_data = [
            (
                "001",
                "../adr/001-adopt-llm-first-architecture.md",
                "Adopt LLM-First Architecture",
                "accepted",
                "high",
            ),
            (
                "002",
                "../adr/002-adopt-bdd-lite.md",
                "Adopt BDD-Lite for Critical Features",
                "proposed",
                "medium",
            ),
            (
                "003",
                "../adr/003-pr-loc-gate.md",
                "PR LOC Gate (Exclude Markdown)",
                "proposed",
                "medium",
            ),
            (
                "004",
                "../adr/004-llm-first-observability.md",
                "LLM-First Observability Standards",
                "proposed",
                "high",
            ),
        ]

        section = "\n## Architecture Decisions\n\n"
        section += "| ADR | Title | Status | Impact |\n"
        section += "|-----|-------|---------|---------|\n"

        for num, path, title, status, impact in adr_data:
            section += f"| [{num}]({path}) | {title} | {status} | {impact} |\n"

        return section + "\n"

    def generate_common_tasks(self) -> str:
        """Generate common tasks section."""
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

    def generate_footer(self) -> str:
        """Generate footer with update information."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"""
## Last Updated
- **Auto-generated:** {timestamp}
- **Script:** `scripts/gen_repo_map.py`
- **Next review:** When repository structure changes significantly
"""

    def generate_full_map(self) -> str:
        """Generate complete REPO_MAP.md content."""
        sections = [
            self.generate_header(),
            self.generate_structure_overview(),
            self.generate_navigation_section(),
            self.generate_features_section(),
            self.generate_scripts_section(),
            self.generate_adr_section(),
            self.generate_common_tasks(),
            self.generate_footer(),
        ]

        return "".join(sections)


def validate_against_existing(repo_root: Path, new_content: str) -> list[str]:
    """Validate new content against existing REPO_MAP.md."""
    warnings = []
    existing_path = repo_root / "docs" / "repo" / "REPO_MAP.md"

    if not existing_path.exists():
        warnings.append("No existing REPO_MAP.md found")
        return warnings

    try:
        with open(existing_path, encoding="utf-8") as f:
            existing_content = f.read()

        # Check for significant structural changes
        if len(new_content.split("\n")) < len(existing_content.split("\n")) * 0.7:
            warnings.append("Generated content is significantly shorter than existing")

        # Check for missing key sections
        key_sections = ["## Repository Structure", "## Quick Navigation", "## Common Tasks"]
        for section in key_sections:
            if section not in new_content:
                warnings.append(f"Missing key section: {section}")

    except Exception as e:
        warnings.append(f"Error reading existing file: {e}")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Auto-generate REPO_MAP.md")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output", help="Output path (default: docs/repo/REPO_MAP.md)")
    parser.add_argument("--dry-run", action="store_true", help="Show output without writing")
    parser.add_argument("--validate", action="store_true", help="Validate against existing")

    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = Path(args.output) if args.output else repo_root / "docs" / "repo" / "REPO_MAP.md"

    if not repo_root.exists():
        print(f"Error: Repository root '{repo_root}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Generate new content
    generator = MarkdownGenerator(repo_root)
    new_content = generator.generate_full_map()

    # Validate if requested
    if args.validate:
        warnings = validate_against_existing(repo_root, new_content)
        if warnings:
            print("⚠️  Validation warnings:")
            for warning in warnings:
                print(f"  - {warning}")
            if not args.dry_run:
                print("\nContinuing with generation...")

    # Output results
    if args.dry_run:
        print("Generated REPO_MAP.md content:")
        print("=" * 50)
        print(new_content)
    else:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Generated REPO_MAP.md at {output_path}")
        newline_char = "\n"
        words = len(new_content.split())
        lines = len(new_content.split(newline_char))
        print(f"📊 Content: {words} words, {lines} lines")


if __name__ == "__main__":
    main()
