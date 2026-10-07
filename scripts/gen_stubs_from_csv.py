#!/usr/bin/env python3
"""Generate minimal-schema plant stub YAMLs from data/phase1_candidates.csv.

Behavior:
- Skips rows whose slug already has a file in data/plants/ (never overwrites existing drafts).
- Writes schema-minimal stubs: id, scientific_name, family, names, sources, status=stub.
- Each stub carries a prominent comment banner: UNVETTED, awaiting OCR confirmation.
- Prints a report; exits 0 even if nothing new to write.

Rerun safely. Idempotent.
"""
from pathlib import Path
import csv
import sys

try:
    import yaml  # noqa
except ImportError:
    sys.exit("pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data/phase1_candidates.csv"
PLANTS_DIR = ROOT / "data/plants"
SOURCES_YML = ROOT / "data/sources/_sources.yml"

BANNER = """# ⚠️ STUB · UNVETTED CANDIDATE · DO NOT CITE
# This entry was auto-generated from data/phase1_candidates.csv on 2026-10-07
# as part of Phase 1 scaffolding. All identifications are tentative.
# Required before promoting to status=draft:
#   1. OCR of Rgyud-bzhi rtsa-rgyud chapter 20 to confirm Tibetan name & inclusion
#   2. Cross-check binomial authority via Kew Plants of the World Online or TPL
#   3. Add at least one classical uses_historical reference with volume/chapter/page
#   4. Attach ≥1 CC/PD image with per-file license metadata
# Do not treat any field below as authoritative scholarship.
"""


def load_sources_keys():
    txt = SOURCES_YML.read_text()
    out = []
    for line in txt.splitlines():
        if line and not line.startswith((" ", "#", "\t")) and line.endswith(":"):
            out.append(line[:-1])
    return set(out)


def validate_source_keys(row, known):
    raw = (row.get("priority_source") or "").strip()
    if not raw:
        return []
    keys = [k.strip() for k in raw.split(";") if k.strip()]
    unknown = [k for k in keys if k not in known]
    if unknown:
        print(f"  ⚠ unknown source key(s) in {row['slug']}: {unknown}", file=sys.stderr)
    return [k for k in keys if k in known]


def build_names_yaml(row):
    """Emit the names: block, preserving null for empty optional fields."""
    lines = ["names:"]
    zh = row.get("zh_name", "").strip()
    lines.append(f"  zh: {zh if zh else 'null'}")
    bo_wylie = (row.get("bo_wylie") or "").strip()
    bo_uni = (row.get("bo_unicode") or "").strip()
    if bo_wylie or bo_uni:
        lines.append("  bo:")
        lines.append(f"    unicode: {bo_uni if bo_uni else 'null'}")
        lines.append(f"    wylie: {('\"' + bo_wylie + '\"') if bo_wylie else 'null'}")
    else:
        lines.append("  bo: null")
    en = (row.get("common_en") or "").strip()
    if en:
        lines.append("  en:")
        for part in [x.strip() for x in en.split("/") if x.strip()]:
            lines.append(f"    - \"{part}\"")
    else:
        lines.append("  en: []")
    sa = (row.get("sa_iast") or "").strip()
    if sa:
        lines.append("  sa:")
        lines.append(f"    devanagari: null  # TODO: Devanagari from Bhāvaprakāśa or Caraka")
        lines.append(f"    iast: \"{sa}\"")
    else:
        lines.append("  sa: null")
    return "\n".join(lines)


def build_stub(row, known_sources):
    slug = row["slug"]
    binomial = row["binomial"].strip()
    authority = (row.get("authority") or "").strip()
    family = row.get("family", "").strip() or "UNKNOWN"
    genus = binomial.split()[0] if binomial else "UNKNOWN"

    valid_srcs = validate_source_keys(row, known_sources)
    if not valid_srcs:
        valid_srcs = ["rgyud_bzhi"]  # schema requires minItems=1; fallback

    out = [BANNER]
    out.append(f"id: {slug}")
    out.append(f"scientific_name:")
    out.append(f"  binomial: \"{binomial}\"")
    out.append(f"  authority: {('\"' + authority + '\"') if authority else 'null'}")
    out.append(f"  synonyms: []")
    out.append(f"family: {family}")
    out.append(f"genus: {genus}")
    out.append(build_names_yaml(row))
    out.append("distribution:")
    out.append("  elevation_m: null")
    out.append("  regions: []  # TODO: fill from Flora of China + GBIF")
    out.append("  habitat: null")
    out.append("  gbif_taxon_key: null")
    out.append("morphology: null")
    out.append("parts_used: []")
    out.append("uses_historical: []  # TODO: add classical refs with chapter/page after OCR")
    out.append("chemistry: {}")
    out.append("conservation: {}")
    out.append("images: []")
    out.append("sources:")
    for key in valid_srcs:
        out.append(f"  - key: {key}")
        out.append(f"    retrieved: 2026-10-07")
        out.append(f"    notes: \"Candidate flag only (verification_status={row.get('verification_status','ocr_pending')}); content pending OCR.\"")
    out.append("status: stub")
    out.append("last_updated: 2026-10-07")
    return "\n".join(out) + "\n"


def main():
    PLANTS_DIR.mkdir(parents=True, exist_ok=True)
    known = load_sources_keys()
    created = []
    skipped_existing = []
    skipped_rows = []

    with CSV_PATH.open() as f:
        for row in csv.DictReader(f):
            slug = (row.get("slug") or "").strip()
            if not slug:
                skipped_rows.append("(blank slug)")
                continue
            target = PLANTS_DIR / f"{slug}.yml"
            if target.exists():
                skipped_existing.append(slug)
                continue
            try:
                content = build_stub(row, known)
            except Exception as e:
                print(f"  ✗ build failed for {slug}: {e}", file=sys.stderr)
                skipped_rows.append(slug)
                continue
            target.write_text(content)
            created.append(slug)

    print(f"Created: {len(created)} new stub(s)")
    print(f"Skipped (already exist): {len(skipped_existing)}")
    if skipped_rows:
        print(f"Skipped (errors): {skipped_rows}")
    if created:
        print(f"\nNext: run `python3 scripts/validate.py` to confirm schema compliance.")


if __name__ == "__main__":
    main()
