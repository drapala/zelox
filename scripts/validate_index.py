#!/usr/bin/env python3
"""
INDEX.yaml Validator with Cross-Validation Logic

title: INDEX.yaml Cross-Validator
purpose: Validate INDEX.yaml with modular schemas and cross-reference checks
inputs: [{"name": "INDEX.yaml", "type": "file"}]
outputs: [{"name": "validation_report", "type": "json"}]
effects: ["validation", "ci_gate"]
deps: ["jsonschema", "pyyaml"]
owners: ["drapala"]
stability: stable
since_version: "0.2.0"
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import jsonschema
from jsonschema import Draft7Validator

class IndexValidator:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self.errors = []
        self.warnings = []
        self.schema_cache = {}
        
    def load_schema(self, schema_file: str) -> Dict[str, Any]:
        """Load and cache JSON schema."""
        if schema_file in self.schema_cache:
            return self.schema_cache[schema_file]
            
        schema_path = self.schemas_dir / schema_file
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        self.schema_cache[schema_file] = schema
        return schema
    
    def validate_schema_structure(self, index_data: Dict) -> bool:
        """Validate INDEX.yaml against modular schemas."""
        try:
            # Load main schema
            main_schema = self.load_schema("index.schema.json")
            
            # Load all sub-schemas for local resolution
            for schema_file in ['feature.schema.json', 'entrypoint.schema.json', 
                                'file-info.schema.json', 'script.schema.json', 
                                'shared.schema.json']:
                self.load_schema(schema_file)
            
            # Simple local ref resolution
            def resolve_refs(obj, base_path=self.schemas_dir):
                if isinstance(obj, dict):
                    if '$ref' in obj:
                        ref_file = obj['$ref'].replace('./', '')
                        return self.load_schema(ref_file)
                    return {k: resolve_refs(v, base_path) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [resolve_refs(item, base_path) for item in obj]
                return obj
            
            # Resolve refs in main schema
            resolved_schema = resolve_refs(main_schema)
            
            # Create validator
            validator = Draft7Validator(resolved_schema)
            
            # Validate
            errors = list(validator.iter_errors(index_data))
            
            if errors:
                for error in errors:
                    path = " > ".join(str(p) for p in error.absolute_path)
                    self.errors.append(f"Schema violation at {path}: {error.message}")
                return False
                
            print("✅ Schema structure validation passed")
            return True
            
        except Exception as e:
            self.errors.append(f"Schema validation error: {str(e)}")
            return False
    
    def cross_validate_references(self, index_data: Dict) -> bool:
        """Cross-validate internal references."""
        valid = True
        
        # Build feature name set
        feature_names = {f['name'] for f in index_data.get('features', [])}
        
        # Check internal dependencies
        for feature in index_data.get('features', []):
            deps = feature.get('dependencies', {}).get('internal', [])
            for dep in deps:
                if dep not in feature_names and dep != feature['name']:
                    self.errors.append(
                        f"Feature '{feature['name']}' depends on unknown feature '{dep}'"
                    )
                    valid = False
        
        # Check shared module usage
        for shared in index_data.get('shared', []):
            used_by = shared.get('used_by', [])
            for user in used_by:
                if user not in feature_names:
                    self.warnings.append(
                        f"Shared module '{shared['name']}' used by unknown feature '{user}'"
                    )
            
            if len(used_by) < 2:
                self.errors.append(
                    f"Shared module '{shared['name']}' used by <2 features (not justified)"
                )
                valid = False
        
        # Check path consistency
        for feature in index_data.get('features', []):
            expected_path = f"features/{feature['name']}"
            if feature.get('path') != expected_path:
                self.warnings.append(
                    f"Feature path mismatch: '{feature['path']}' != '{expected_path}'"
                )
        
        if valid:
            print("✅ Cross-reference validation passed")
        
        return valid
    
    def validate_business_rules(self, index_data: Dict) -> bool:
        """Validate LLM-first business rules."""
        valid = True
        
        # Check file LOC limits
        for feature in index_data.get('features', []):
            for file_info in feature.get('files', []):
                loc = file_info.get('loc', 0)
                if loc > 500:
                    self.warnings.append(
                        f"File '{file_info['path']}' has {loc} LOC (>500 recommended)"
                    )
        
        # Check minimum owners
        for feature in index_data.get('features', []):
            if not feature.get('owners'):
                self.errors.append(f"Feature '{feature['name']}' has no owners")
                valid = False
        
        # Check script executability
        for script in index_data.get('scripts', []):
            if script.get('status') == 'active' and not script.get('executable', True):
                self.warnings.append(
                    f"Active script '{script['name']}' not marked executable"
                )
        
        # Check complexity consistency
        for feature in index_data.get('features', []):
            high_complexity_files = sum(
                1 for f in feature.get('files', [])
                if f.get('complexity') == 'high'
            )
            if feature.get('complexity') == 'low' and high_complexity_files > 0:
                self.warnings.append(
                    f"Feature '{feature['name']}' marked 'low' but has high-complexity files"
                )
        
        if valid:
            print("✅ Business rules validation passed")
        
        return valid
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "checks_performed": [
                "schema_structure",
                "cross_references", 
                "business_rules"
            ]
        }
    
    def run_validation(self, index_path: str = None) -> bool:
        """Run complete validation pipeline."""
        if index_path is None:
            index_path = self.repo_root / "docs" / "repo" / "INDEX.yaml"
        
        print("=" * 60)
        print("INDEX.yaml VALIDATION")
        print("=" * 60)
        
        # Load INDEX.yaml
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Failed to load INDEX.yaml: {str(e)}")
            return False
        
        # Run validations
        schema_valid = self.validate_schema_structure(index_data)
        refs_valid = self.cross_validate_references(index_data)
        rules_valid = self.validate_business_rules(index_data)
        
        # Generate report
        report = self.generate_report()
        
        # Print results
        print("\n" + "=" * 60)
        print("VALIDATION REPORT")
        print("=" * 60)
        
        if report['errors']:
            print("\n❌ ERRORS:")
            for error in report['errors']:
                print(f"  • {error}")
        
        if report['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in report['warnings']:
                print(f"  • {warning}")
        
        if report['valid']:
            print("\n✅ INDEX.yaml validation PASSED!")
        else:
            print(f"\n❌ INDEX.yaml validation FAILED with {report['error_count']} errors")
        
        # Write report to file
        report_path = self.repo_root / ".reports" / "index_validation.json"
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report['valid']

def main():
    """Main entry point."""
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    validator = IndexValidator(repo_root)
    valid = validator.run_validation()
    
    sys.exit(0 if valid else 1)

if __name__ == "__main__":
    main()