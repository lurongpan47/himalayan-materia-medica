#!/usr/bin/env python3
"""Validate every data/plants/*.yml against schemas/plant.schema.json."""
import json, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")
try:
    from jsonschema import Draft7Validator
except ImportError:
    sys.exit("pip install jsonschema")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schemas/plant.schema.json").read_text())
SOURCES = yaml.safe_load((ROOT / "data/sources/_sources.yml").read_text()) or {}
PLANTS = sorted((ROOT / "data/plants").glob("*.yml"))

v = Draft7Validator(SCHEMA)
errors = 0
def _stringify_dates(obj):
    import datetime
    if isinstance(obj, dict):
        return {k: _stringify_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_dates(x) for x in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj

for p in PLANTS:
    doc = _stringify_dates(yaml.safe_load(p.read_text()))
    # schema check
    for err in v.iter_errors(doc):
        print(f"[SCHEMA] {p.name}: {err.message} at {list(err.path)}")
        errors += 1
    # slug == filename
    if doc.get("id") + ".yml" != p.name:
        print(f"[SLUG]   {p.name}: id={doc.get('id')} does not match filename")
        errors += 1
    # every source_ref must exist in _sources.yml (or be null)
    for s in doc.get("sources", []):
        if s["key"] not in SOURCES:
            print(f"[SOURCE] {p.name}: unknown source key '{s['key']}'")
            errors += 1
    for u in doc.get("uses_historical", []):
        ref = u.get("source_ref")
        if ref and ref not in SOURCES:
            print(f"[SOURCE] {p.name}: uses_historical references unknown source '{ref}'")
            errors += 1
    # image license required
    for im in doc.get("images", []):
        if not im.get("license") or not im.get("credit"):
            print(f"[IMAGE]  {p.name}: image missing license/credit")
            errors += 1

print(f"\n{len(PLANTS)} plant entries checked. {errors} error(s).")
sys.exit(1 if errors else 0)
