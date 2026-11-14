#!/usr/bin/env python3
"""Validate Zuhura OpenAPI documents and JSON Schemas.

Rejects the previous npm echo script. This checks every schema against the
JSON Schema 2020-12 metaschema, validates a dataset instance, and checks that
the OpenAPI document is structurally sound with resolvable local $refs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
OPENAPI_PATH = ROOT / "openapi" / "zuhura-v1.yaml"
STAC_PATH = ROOT / "stac" / "mars-stac-extension.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must be a JSON object")
    return data


def check_schema_file(path: Path) -> None:
    schema = load_json(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise SystemExit(f"Invalid JSON Schema {path.name}: {exc.message}") from exc
    print(f"schema ok: {path.relative_to(ROOT)}")


def validate_dataset_instances() -> None:
    schema = load_json(SCHEMA_DIR / "dataset.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    valid = {
        "id": "zuhura-mola-megdr-128",
        "title": "MGS MOLA MEGDR",
        "description": "Global elevation grid referenced to the MOLA areoid.",
        "category": "topography",
        "processing_level": "derived_product",
        "provider": "NASA Planetary Data System",
        "original_url": "https://pds-geosciences.wustl.edu/",
        "citation": "Smith et al., MOLA MEGDR",
        "license": "Public domain (NASA)",
        "crs_wkt": "IAU:49902",
        "spatial_extent": {
            "min_lon": -180.0,
            "max_lon": 180.0,
            "min_lat": -88.0,
            "max_lat": 88.0,
            "longitude_convention": "east_positive",
            "latitude_convention": "planetocentric",
        },
        "spatial_resolution_m": 463.0,
        "scientific_limitations": "Polar coverage is outside MEG128.",
        "last_verified_at": "2026-11-14T00:00:00Z",
    }
    validator.validate(valid)

    invalid = dict(valid)
    invalid["category"] = "not-a-real-category"
    try:
        validator.validate(invalid)
    except ValidationError:
        print("instance ok: dataset.json accepts a valid record and rejects a bad category")
        return
    raise SystemExit("dataset.json failed to reject an invalid category")


def _local_refs(node: object, found: list[str]) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and not ref.startswith("#"):
            found.append(ref)
        for value in node.values():
            _local_refs(value, found)
    elif isinstance(node, list):
        for item in node:
            _local_refs(item, found)


def validate_openapi() -> None:
    if not OPENAPI_PATH.is_file():
        raise SystemExit(f"Missing OpenAPI document: {OPENAPI_PATH}")
    with OPENAPI_PATH.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise SystemExit("OpenAPI root must be a mapping")
    version = str(document.get("openapi", ""))
    if not version.startswith("3."):
        raise SystemExit(f"Unsupported OpenAPI version: {version!r}")
    info = document.get("info")
    paths = document.get("paths")
    if not isinstance(info, dict) or "title" not in info or "version" not in info:
        raise SystemExit("OpenAPI info.title and info.version are required")
    if not isinstance(paths, dict) or not paths:
        raise SystemExit("OpenAPI paths must be a non-empty mapping")
    for path, operations in paths.items():
        if not isinstance(path, str) or not path.startswith("/"):
            raise SystemExit(f"Invalid path key: {path!r}")
        if not isinstance(operations, dict):
            raise SystemExit(f"Path {path} must be a mapping of operations")
        for method, operation in operations.items():
            if method.startswith("x-") or method in {"parameters", "summary", "description"}:
                continue
            if method not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                raise SystemExit(f"Unknown method {method} on {path}")
            if not isinstance(operation, dict) or "responses" not in operation:
                raise SystemExit(f"{method.upper()} {path} is missing responses")

    refs: list[str] = []
    _local_refs(document, refs)
    for ref in refs:
        file_part, _, fragment = ref.partition("#")
        target = (OPENAPI_PATH.parent / file_part).resolve()
        if not target.is_file():
            raise SystemExit(f"OpenAPI $ref does not resolve: {ref}")
        if target.suffix == ".json":
            schema = load_json(target)
            Draft202012Validator.check_schema(schema)
            if fragment:
                pointer = fragment.lstrip("/")
                node: object = schema
                for part in pointer.split("/"):
                    if not isinstance(node, dict) or part not in node:
                        raise SystemExit(f"OpenAPI $ref fragment is missing: {ref}")
                    node = node[part]
    print(f"openapi ok: {OPENAPI_PATH.relative_to(ROOT)} ({len(paths)} paths, {len(refs)} local refs)")


def main() -> None:
    schema_files = sorted(SCHEMA_DIR.glob("*.json"))
    if not schema_files:
        raise SystemExit(f"No schemas found in {SCHEMA_DIR}")
    for schema_path in schema_files:
        check_schema_file(schema_path)
    if STAC_PATH.is_file():
        check_schema_file(STAC_PATH)
    validate_dataset_instances()
    validate_openapi()
    print("Zuhura API schemas validated")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - top-level validator should report any failure
        print(f"Schema validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
