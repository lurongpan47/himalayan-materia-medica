# Changelog

## 2026-11-19 — Phase 1 fetch snapshots (unilateral, Pan-authorized)
- Three batch fetchers added, run end-to-end against all 101 species:
  - `scripts/fetch_wfo_authority.py` → `data/verification/wfo/` (World Flora Online)
    - 79/101 matched; 69 authority agree, 10 differ (→ pending apply after review)
    - 22/101 ambiguous homonyms (listed in SUMMARY.md, need human picker)
  - `scripts/fetch_gbif.py` → `data/verification/gbif/` (GBIF)
    - 101/101 matched (100 %), 101/101 with ≥1 Himalayan-country occurrence
    - 98/101 with crowd-sourced elevation samples (median [min–max], n)
  - `scripts/fetch_images_commons.py` → `data/verification/commons/` (Wikimedia)
    - 82/101 have ≥1 CC/PD image candidate (top 5 per species, license-filtered)
    - 19/101 return no CC/PD candidates — need PD herbarium plates or field photos
- `data/verification/` is deliberately separate from `data/plants/`; no YAML in
  `data/plants/` was modified in this pass.
- Next step: write `apply_*.py` and promote stubs to `status: draft` only after
  Pan's review of the 10 authority disagreements and 22 WFO homonyms.

## 2026-10-07 — Phase 0 wrap, Phase 1 opens
- Project moved out of `~/clawd/wisdomhealth/` to its own root `~/clawd/himalayan-materia-medica/` (Pan decision: independent project).
- Added `LICENSE-DATA.md` (CC BY-SA 4.0), `LICENSE-CODE` (MIT), `CONTRIBUTORS.md`.
- README updated: removed "project mother = wisdomhealth" framing; publish target set to GitHub Pages `lurongpan47.github.io/himalayan-materia-medica` (no custom domain for now).
- Phase 1 TODO: candidate species list expanded from ~22 to 100 (`docs/PHASE1-TODO.md`).
- Added OCR skeleton `scripts/ocr_rgyud_bzhi_ch20.py` — awaiting source scan input.
- Local git init, first commit on `main`.

## 2026-10-06 — Phase 0 scaffold
- Directory layout, JSON Schema (`schemas/plant.schema.json`), build pipeline (`scripts/validate.py`, `scripts/build_site.py`).
- Three demo entries: Rhodiola crenulata, Crocus sativus, Lamiophlomis rotata.
- Static site Jinja templates (`site/`), build output (`build/`). Validator passes 0 errors.
- README with scope, data model, phase roadmap, project boundaries.
