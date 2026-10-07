# Changelog

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
