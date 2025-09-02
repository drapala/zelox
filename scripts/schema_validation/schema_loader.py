#!/usr/bin/env python3
"""
---
title: Schema Loader
purpose: Load and parse JSON schemas with reference resolution
inputs:
  - name: schema_name
    type: str
  - name: repo_root
    type: Path
outputs:
  - name: schema_dict
    type: dict
effects: 
  - reads schema files from disk
deps:
  - json
  - pathlib
  - typing
owners: [llm-first-team]
stability: stable
since_version: 1.0.0
complexity: low
---
"""

import json
from pathlib import Path
from typing import Any


class SchemaLoader:
    """Loads and caches JSON schemas from the repository."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self._cache: dict[str, dict] = {}
        self._store: dict[str, dict] | None = None

    def load(self, schema_name: str) -> dict:
        """Load a schema by name. Returns cached if available."""
        if schema_name in self._cache:
            return self._cache[schema_name]

        schema_path = self.schemas_dir / f"{schema_name}.schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        self._cache[schema_name] = schema
        return schema

    def build_store(self) -> dict[str, dict]:
        """Build URI-based schema store for reference resolution."""
        if self._store is not None:
            return self._store

        store = {}
        for schema_file in self.schemas_dir.glob("*.schema.json"):
            try:
                with open(schema_file, encoding="utf-8") as f:
                    schema = json.load(f)

                # Map by $id if present
                if "$id" in schema:
                    store[schema["$id"]] = schema

                # Map by file URI
                store[schema_file.resolve().as_uri()] = schema

            except (json.JSONDecodeError, OSError):
                continue  # Skip malformed schemas

        self._store = store
        return store

    def resolve_refs(self, schema: Any) -> Any:
        """Resolve $ref references in schema recursively."""
        if not isinstance(schema, dict):
            if isinstance(schema, list):
                return [self.resolve_refs(item) for item in schema]
            return schema

        if "$ref" in schema:
            ref = schema["$ref"]
            if ref.startswith("#/"):
                return schema  # Internal refs not handled here

            if ref.endswith(".schema.json"):
                ref_name = ref.replace(".schema.json", "").split("/")[-1]
                try:
                    return self.load(ref_name)
                except FileNotFoundError:
                    return schema

            return schema

        return {k: self.resolve_refs(v) for k, v in schema.items()}
