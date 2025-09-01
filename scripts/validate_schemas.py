#!/usr/bin/env python3
"""
Schema Validation Script
Validates repository files against JSON schemas for LLM-first compliance.
"""
import json
import yaml
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re

try:
    import jsonschema
except ImportError:
    print("❌ jsonschema package required: pip install jsonschema")
    sys.exit(1)

class SchemaValidator:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self.errors = []
        self.warnings = []
    
    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """Load a JSON schema file."""
        schema_path = self.schemas_dir / f"{schema_name}.schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_index_yaml(self) -> bool:
        """Validate docs/repo/INDEX.yaml against schema."""
        index_path = self.repo_root / "docs" / "repo" / "INDEX.yaml"
        if not index_path.exists():
            self.errors.append("❌ INDEX.yaml not found at docs/repo/INDEX.yaml")
            return False
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = yaml.safe_load(f)
            
            schema = self.load_schema("index")
            jsonschema.validate(index_data, schema)
            
            print("✅ INDEX.yaml schema validation passed")
            return True
            
        except yaml.YAMLError as e:
            self.errors.append(f"❌ INDEX.yaml YAML syntax error: {e}")
            return False
        except jsonschema.ValidationError as e:
            self.errors.append(f"❌ INDEX.yaml validation error: {e.message}")
            if e.absolute_path:
                self.errors.append(f"   Path: {'.'.join(str(p) for p in e.absolute_path)}")
            return False
        except Exception as e:
            self.errors.append(f"❌ INDEX.yaml validation failed: {e}")
            return False
    
    def extract_yaml_frontmatter(self, content: str) -> Tuple[Dict[str, Any], bool]:
        """Extract YAML frontmatter from markdown file."""
        lines = content.strip().split('\n')
        
        # Look for YAML frontmatter block in ADR
        yaml_start = None
        yaml_end = None
        
        for i, line in enumerate(lines):
            if line.strip() == '```yaml' and 'Machine-readable metadata' in lines[i-1] if i > 0 else False:
                yaml_start = i + 1
            elif yaml_start is not None and line.strip() == '```':
                yaml_end = i
                break
        
        if yaml_start is None or yaml_end is None:
            return {}, False
        
        yaml_content = '\n'.join(lines[yaml_start:yaml_end])
        try:
            return yaml.safe_load(yaml_content), True
        except yaml.YAMLError:
            return {}, False
    
    def validate_adr_frontmatter(self) -> bool:
        """Validate ADR front-matter against schema."""
        adr_dir = self.repo_root / "docs" / "adr"
        if not adr_dir.exists():
            self.warnings.append("⚠️  No docs/adr directory found")
            return True
        
        schema = self.load_schema("adr-frontmatter")
        adr_files = list(adr_dir.glob("*.md"))
        
        if not adr_files:
            self.warnings.append("⚠️  No ADR files found")
            return True
        
        valid_count = 0
        
        for adr_file in adr_files:
            # Skip template
            if "template" in adr_file.name:
                continue
                
            try:
                with open(adr_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                frontmatter, found = self.extract_yaml_frontmatter(content)
                
                if not found:
                    self.warnings.append(f"⚠️  No YAML frontmatter in {adr_file.name}")
                    continue
                
                jsonschema.validate(frontmatter, schema)
                valid_count += 1
                
            except jsonschema.ValidationError as e:
                self.errors.append(f"❌ {adr_file.name} frontmatter error: {e.message}")
            except Exception as e:
                self.errors.append(f"❌ {adr_file.name} validation failed: {e}")
        
        total_adrs = len([f for f in adr_files if "template" not in f.name])
        if total_adrs > 0:
            print(f"✅ ADR frontmatter: {valid_count}/{total_adrs} files valid")
        
        return len(self.errors) == 0
    
    def validate_obs_plans(self) -> bool:
        """Validate OBS_PLAN.md files against schema."""
        features_dir = self.repo_root / "features"
        if not features_dir.exists():
            self.warnings.append("⚠️  No features directory found")
            return True
        
        obs_plans = list(features_dir.rglob("OBS_PLAN.md"))
        if not obs_plans:
            self.warnings.append("⚠️  No OBS_PLAN.md files found")
            return True
        
        schema = self.load_schema("obs-plan")
        valid_count = 0
        
        for obs_plan in obs_plans:
            try:
                with open(obs_plan, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract YAML from markdown (look for ```yaml blocks)
                yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)
                
                if not yaml_blocks:
                    self.warnings.append(f"⚠️  No YAML block in {obs_plan.relative_to(self.repo_root)}")
                    continue
                
                # Validate the first YAML block
                obs_data = yaml.safe_load(yaml_blocks[0])
                jsonschema.validate(obs_data, schema)
                valid_count += 1
                
            except yaml.YAMLError as e:
                self.errors.append(f"❌ {obs_plan.relative_to(self.repo_root)} YAML error: {e}")
            except jsonschema.ValidationError as e:
                self.errors.append(f"❌ {obs_plan.relative_to(self.repo_root)} schema error: {e.message}")
            except Exception as e:
                self.errors.append(f"❌ {obs_plan.relative_to(self.repo_root)} validation failed: {e}")
        
        if obs_plans:
            print(f"✅ OBS_PLAN validation: {valid_count}/{len(obs_plans)} files valid")
        
        return len(self.errors) == 0
    
    def run_all_validations(self) -> bool:
        """Run all schema validations."""
        print("=" * 60)
        print("SCHEMA VALIDATION")
        print("=" * 60)
        
        results = []
        
        # Validate each schema type
        results.append(self.validate_index_yaml())
        results.append(self.validate_adr_frontmatter())
        results.append(self.validate_obs_plans())
        
        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        all_passed = all(results) and len(self.errors) == 0
        
        if all_passed:
            print("\n✅ All schema validations passed!")
        else:
            print("\n❌ Schema validation failed!")
        
        return all_passed

def main():
    """Main entry point."""
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    validator = SchemaValidator(repo_root)
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()