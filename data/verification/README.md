# Verification snapshots

This folder holds **snapshots of external public-data checks** against our 101
candidate species. It is deliberately kept **separate from `data/plants/`**: the
primary YAML entries are not modified by fetcher runs. Application of any field
from these snapshots back into source YAML must be reviewed first — see the
Phase 1 promotion checklist in `README.md` (OCR + authority + classical refs +
images).

## Layout

```
verification/
├── wfo/      # World Flora Online — binomial + authority
│   ├── <id>.json       # raw per-species match payload
│   ├── rows.json       # consolidated rows
│   └── SUMMARY.md      # human-readable summary + disagreement table
├── gbif/     # GBIF — country facets + elevation samples
│   ├── <id>.json
│   ├── rows.json
│   └── SUMMARY.md
└── commons/  # Wikimedia Commons — CC/PD image candidates (NOT downloaded)
    ├── <id>.json
    ├── rows.json
    └── SUMMARY.md
```

## Run log

- **2026-11-19 02:37–02:43 PST** — initial run (all 101 species)
  - WFO: 79 matched (69 agree, 10 differ), 22 ambiguous homonyms, 0 unmatched.
  - GBIF: 101/101 matched, 101/101 ≥1 Himalayan-country occurrence, 98/101 elevation.
  - Commons: 82/101 have ≥1 CC/PD image candidate.

## Source scripts

- `scripts/fetch_wfo_authority.py`
- `scripts/fetch_gbif.py`
- `scripts/fetch_images_commons.py`

Each is idempotent — rerunning overwrites `<id>.json` and the summaries.

## Licensing

- WFO data: WFO terms (CC0 for the matching API output).
- GBIF data: facet counts are CC0 at aggregate level.
- Commons: each file carries its own license in the JSON (`license_short` /
  `license_url`). Only `Public domain`, `CC0`, `CC BY*`, `CC BY-SA*` entries are
  recorded; other licenses are filtered out at fetch time.

## Promotion to `data/plants/`

Do **not** blindly copy these fields into `data/plants/*.yml`. A separate
`scripts/apply_*.py` (one per source) will land after human review, with:

- Each modified field tracked in commit messages.
- `_orig` sidecars preserved during batch updates (per the Jonang-catalog
  lesson on batch application — see `MEMORY.md`).
- `status: stub` stays until all four Phase-1 conditions are satisfied.
