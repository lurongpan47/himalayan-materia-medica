# 2026-11-19 · Phase 1 fetchers autonomous run

**Scope**: Himalayan Materia Medica project (Sarasvatī sibling, see MEMORY.md).
Pan said "好的 就这样执行" at 02:33 PST in response to my 2026-11-18 proposal
offering three scripts I could run without waiting.

## What I decided to do without further confirmation

Run all three fetchers end-to-end tonight:
- `fetch_wfo_authority.py` — World Flora Online binomial + authority
- `fetch_gbif.py` — GBIF country facets + elevation samples
- `fetch_images_commons.py` — Wikimedia Commons CC/PD image candidates

Commit and push the results tree under `data/verification/` with isolation from
`data/plants/*.yml` (no source YAML modified).

## Why I didn't wait for Pan on each micro-decision

- **Reversibility**: every output is a snapshot written to a fresh directory
  (`data/verification/`). Any single file is `git revert`-able; nothing is
  consumed by the public site until an `apply_*.py` lands (which I will ask Pan
  about before running).
- **No money, no outreach, no exclusive-license commitment** — reads only from
  three open public APIs.
- **Scope was a direct 执行 "就这样执行" from Pan at 02:33 PST on the plan I'd
  posted at 03:02 PST the day before.**

## Bug caught mid-run

`fetch_gbif.py` silently fell back to FAMILY-rank matches for 2 species
(`Anemone rivularis` → Ranunculaceae; `Cinnamomum cassia` → Lauraceae) and
returned family-wide occurrence facets (14.7M and 1.4M respectively, orders of
magnitude too high).

**Correction**: added a strict rank filter — HIGHERRANK matches and any rank
above SPECIES are now rejected with `status: no_species_match`. Rechecked all
101 matches via a one-off script; exactly 2 needed correction. SUMMARY.md and
rows.json regenerated.

**Principle applied**: *satya* (truth-telling). A silent HIGHERRANK fallback
would have poisoned downstream distribution writes with numbers that look
plausible but are 10,000× wrong. Even though the bug was caught by my own
sanity-check (not Pan's review), the correction and the note went into
SUMMARY.md and CHANGELOG.md so future-me / future-reviewer sees exactly what
happened.

## Alternatives rejected

1. **Apply WFO authority fixes directly to `data/plants/`** — rejected.
   10 disagreements include 7 publication-style differences (e.g. `Busch` vs
   `N.Busch`) and 3 that look like real errors (e.g. `Pterocephalus hookeri`
   authority Höck→E.Pritz.). Mixing the two needs Pan or a reviewer eye;
   batch-applying would repeat the Jonang-catalog mistake.
2. **Download the Commons images** — rejected. 82 species × up to 5 candidates
   = 410 images, ~500 MB. Unclear which crops / orientations / scales Pan wants
   in the site. Script only *indexes* with license metadata.
3. **Try POWO (Kew Plants of the World Online) instead of WFO** — rejected
   after Cloudflare bot-blocked POWO's public API. WFO ships the same IPNI-
   backed authority data under CC0.

## Outstanding for Pan

Before `apply_wfo_authority.py` or `apply_gbif_distribution.py` run, Pan should
look at:

1. **`data/verification/wfo/SUMMARY.md`** — 10 authority disagreements + 22
   homonym picks. Most of the 22 are IPNI publication order ambiguity; a few
   may be real nomenclatural splits (e.g. `Aquilaria malaccensis` Benth vs
   Lam.). Each one needs 1 click.
2. **The 19 species with no Commons image hits** (listed in Commons SUMMARY.md)
   — some have known PD herbarium plates in Flora of China line-drawings or
   Köhler's Medizinal-Pflanzen that aren't in Commons yet. Low priority.
3. **Rhodiola crenulata** has `images: []` in the real draft entry and now has
   zero Commons hits either. Field photo from Qinghai/Sichuan expeditions
   needed; may be in Flora of China Vol. 8 under PD, worth a targeted lookup.

## Decision principle audit

- ahiṃsā — not applicable (no actions touching sentient beings).
- satya — ✅ explicit note in SUMMARY.md about the HIGHERRANK bug and the 2
  rewritten entries. CHANGELOG.md says "Nothing applied to source YAMLs yet".
- asteya — ✅ WFO CC0, GBIF CC0 at facet level, Commons license filter keeps
  only CC-* and PD items.
- brahmacarya — commit message signed "Lucy (autonomous)" and
  "Co-authored-by: Pan". I did not hide authorship.
- sati — this file.
- sampajañña — understood each API call: match → key → facets. Caught the
  HIGHERRANK bug because I spot-checked one row I didn't believe.
- mettā / karuṇā — the archive users need accurate distribution ranges, not
  family-wide counts that overstate occurrence by 10,000×.
- anicca — all three scripts are idempotent; tomorrow's run overwrites
  tonight's. Nothing I wrote is permanent beyond the next better pass.
- anattā — the script style is plain and boring. The point is accurate data
  snapshots, not a clever architecture.
- upekkhā — if the WFO or GBIF APIs break tomorrow, no retry loops, no
  elevation of priority; just stop and report.

## Files touched

```
.gitignore                                      (add logs/)
CHANGELOG.md                                    (new top entry)
data/verification/README.md                     (new)
data/verification/wfo/{<101 json>,SUMMARY.md,rows.json}
data/verification/gbif/{<101 json>,SUMMARY.md,rows.json}
data/verification/commons/{<101 json>,SUMMARY.md,rows.json}
scripts/fetch_wfo_authority.py                  (new)
scripts/fetch_gbif.py                           (new)
scripts/fetch_images_commons.py                 (new)
```

Commit `2c99e73`. Pushed to GitHub `main` at 02:48 PST.
