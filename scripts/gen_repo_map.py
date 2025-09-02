#!/usr/bin/env python3
"""
title: Repository Map Generator (Core)
purpose: Auto-generate REPO_MAP.md from current codebase state
inputs: [{"name": "repo_root", "type": "path"}, {"name": "output_path", "type": "path"}]
outputs: [{"name": "repo_map", "type": "markdown_file"}]
effects: ["file_generation", "documentation_update"]
deps: ["pathlib", "argparse", "datetime"]
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

            # Look for module docstring (first triple-quoted string after imports/shebang)
            # This pattern ensures we get the module-level docstring, not inline strings
            lines = content.split("\n")
            docstring_start = -1
            docstring_end = -1

            # Skip shebang, encoding, imports and find first docstring
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('"""') and not any(
                    kw in line for kw in ["def ", "class ", "if ", "for ", "while "]
                ):
                    docstring_start = i
                    if stripped.endswith('"""') and len(stripped) > 3:
                        # Single line docstring
                        docstring_end = i
                    else:
                        # Multi-line docstring, find closing
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().endswith('"""'):
                                docstring_end = j
                                break
                    break

            if docstring_start == -1 or docstring_end == -1:
                return {}

            # Extract docstring content
            if docstring_start == docstring_end:
                # Single line docstring
                docstring = lines[docstring_start].strip()[3:-3]
            else:
                # Multi-line docstring
                docstring_lines = [lines[docstring_start].strip()[3:]]  # Remove opening """
                for i in range(docstring_start + 1, docstring_end):
                    docstring_lines.append(lines[i])
                docstring_lines.append(lines[docstring_end].strip()[:-3])  # Remove closing """
                docstring = "\n".join(docstring_lines).strip()

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
                        elif line.startswith(("deps:", "owners:", "effects:")):
                            # These are arrays, extract the content
                            key = line.split(":")[0].strip()
                            # Use re.escape to safely include key in regex pattern
                            escaped_key = re.escape(key)
                            array_match = re.search(
                                rf"{escaped_key}:\s*\[(.*?)\]", docstring, re.DOTALL
                            )
                            if array_match:
                                array_content = array_match.group(1).strip()
                                if array_content:
                                    items = [
                                        item.strip().strip("\"'")
                                        for item in array_content.split(",")
                                    ]
                                    frontmatter[key] = [item for item in items if item]  # type: ignore
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
        }

        if name in purpose_map:
            return purpose_map[name]

        # Try to extract from frontmatter
        if file_path.suffix == ".py":
            frontmatter = FileAnalyzer.extract_python_frontmatter(file_path)
            if "purpose" in frontmatter:
                return frontmatter["purpose"]

        # Fallback based on extension
        if name.endswith(".py"):
            return "Python module"

        return "Unknown"


class StructureMapper:
    """Build hierarchical project structure."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.analyzer = FileAnalyzer()

    def scan_features(self) -> list[dict[str, Any]]:
        """Scan features directory for VSA structure."""
        features: list[dict[str, Any]] = []
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
                "capabilities": [],
            }

            for file_path in feature_dir.glob("*.py"):
                file_info = {
                    "name": file_path.name,
                    "purpose": self.analyzer.get_file_purpose(file_path),
                }
                feature_info["files"].append(file_info)  # type: ignore

                # Track key capabilities
                if file_path.name == "tests.py":
                    capabilities = feature_info["capabilities"]
                    if isinstance(capabilities, list):
                        capabilities.append("Tests")
                elif file_path.name == "api.py":
                    capabilities = feature_info["capabilities"]
                    if isinstance(capabilities, list):
                        capabilities.append("HTTP API")
                elif file_path.name == "service.py":
                    capabilities = feature_info["capabilities"]
                    if isinstance(capabilities, list):
                        capabilities.append("Business Logic")

            features.append(feature_info)

        return features

    def scan_scripts(self) -> list[dict[str, Any]]:
        """Scan scripts directory for tooling."""
        scripts: list[dict[str, Any]] = []
        scripts_dir = self.repo_root / "scripts"

        if not scripts_dir.exists():
            return scripts

        for script_path in scripts_dir.glob("*.py"):
            if script_path.name.startswith("test_"):
                continue  # Skip test files

            script_info = {
                "name": script_path.name,
                "purpose": self.analyzer.get_file_purpose(script_path),
            }
            scripts.append(script_info)

        return scripts

    def scan_adrs(self) -> list[dict[str, Any]]:
        """Scan docs/adr directory for Architecture Decision Records."""
        adrs: list[dict[str, Any]] = []
        adr_dir = self.repo_root / "docs" / "adr"

        if not adr_dir.exists():
            return adrs

        for adr_path in sorted(adr_dir.glob("*.md")):
            # Extract ADR number from filename using regex (e.g., "001-title.md" -> "001")
            # Look for first numeric sequence in filename
            match = re.search(r"(\d+)", adr_path.stem)
            if match:
                adr_number = match.group(1)
                # Extract everything after the number for title
                remainder = adr_path.stem[match.end() :]
                raw_title = remainder.lstrip("-_")  # Remove leading separators
            else:
                adr_number = ""
                raw_title = adr_path.stem

            # Clean up title from filename
            title = raw_title.replace("-", " ").replace("_", " ").strip().title()

            # Generate relative path from REPO_MAP.md location
            relative_path = f"../adr/{adr_path.name}"

            # Default values - could be enhanced to parse frontmatter from markdown files
            adr_info = {
                "number": adr_number,
                "path": relative_path,
                "title": title,
                "status": "accepted",  # Default, could be parsed from content
                "impact": "medium",  # Default, could be parsed from content
            }
            adrs.append(adr_info)

        return adrs


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

            if feature["capabilities"]:
                section += f"- **Capabilities:** {', '.join(feature['capabilities'])}\n"

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
        """Generate ADR table from discovered ADR files."""
        adrs = self.structure_mapper.scan_adrs()

        if not adrs:
            return "\n## Architecture Decisions\n\n*No ADR files found in docs/adr/*\n\n"

        section = "\n## Architecture Decisions\n\n"
        section += "| ADR | Title | Status | Impact |\n"
        section += "|-----|-------|---------|---------|\n"

        for adr in adrs:
            section += (
                f"| [{adr['number']}]({adr['path']}) | "
                f"{adr['title']} | {adr['status']} | {adr['impact']} |\n"
            )

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


def main():
    parser = argparse.ArgumentParser(description="Auto-generate REPO_MAP.md")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--output", help="Output path (default: docs/repo/REPO_MAP.md)")
    parser.add_argument("--dry-run", action="store_true", help="Show output without writing")

    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = Path(args.output) if args.output else repo_root / "docs" / "repo" / "REPO_MAP.md"

    if not repo_root.exists():
        print(f"Error: Repository root '{repo_root}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Generate new content
    generator = MarkdownGenerator(repo_root)
    new_content = generator.generate_full_map()

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
