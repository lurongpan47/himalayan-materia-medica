# Contributors

## Maintainer
- **Dr. Lurong Pan (潘麓蓉)** — Project founder, maintainer, botanical/medical authority
  - GitHub: @lurongpan47
  - Timezone: America/Los_Angeles

## Autonomous Agent
- **Lucy** — Autonomous archivist agent operating under Pan's authorization dated 2026-09-13 (see Sarasvatī MEMORY.md). Builds schemas, generates draft entries, maintains OCR / data-ingest pipelines. **Does not** sign off on medical, botanical, or classical-source identifications; those require named human reviewers.

## Named Human Reviewers
_(empty — this section grows as scholars sign off on specific entries or sections. Each reviewer gets name, affiliation, and the scope they vouch for.)_

## How to contribute
1. Open an issue describing the plant you want to add / correct.
2. Fork, create a branch, add/edit `data/plants/<slug>.yml`.
3. Run `python3 scripts/validate.py` — must pass with 0 errors.
4. If adding a classical-source quotation (`uses_historical`), cite a **publicly available** scan with volume/chapter/page. No paywalled modern editions.
5. Open PR. Maintainer reviews.

All contributions are accepted under CC BY-SA 4.0 (data) + MIT (code).
