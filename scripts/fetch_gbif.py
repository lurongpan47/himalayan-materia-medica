#!/usr/bin/env python3
"""
fetch_gbif.py — GBIF distribution + elevation batch fetch.

For every data/plants/*.yml, uses GBIF species-match API to get taxonKey, then:
  - fetches occurrence facets (country, elevation)
  - writes data/verification/gbif/<id>.json (raw facets + match)
  - writes data/verification/gbif/SUMMARY.md

Fills a distribution snapshot that can be applied to source YAMLs after review.
GBIF data is CC0 at facet level (aggregate counts).
"""
from __future__ import annotations
import json, sys, time, pathlib, requests, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLANTS = ROOT / "data" / "plants"
OUT = ROOT / "data" / "verification" / "gbif"
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "HimalayanMateriaMedica/0.1 (+https://github.com/lurongpan47/himalayan-materia-medica)"}

HIMALAYAN_COUNTRIES = {
    "CN": "China",
    "IN": "India",
    "NP": "Nepal",
    "BT": "Bhutan",
    "PK": "Pakistan",
    "MM": "Myanmar",
    "AF": "Afghanistan",
}

def match_species(binomial: str) -> dict:
    r = requests.get("https://api.gbif.org/v1/species/match",
                     params={"name": binomial}, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def country_facets(taxon_key: int) -> dict:
    r = requests.get("https://api.gbif.org/v1/occurrence/search",
                     params={"taxonKey": taxon_key, "facet": "country",
                             "facetLimit": 50, "limit": 0},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    d = r.json()
    counts = {}
    for f in d.get("facets", []):
        if f["field"] == "COUNTRY":
            for c in f["counts"]:
                counts[c["name"]] = c["count"]
    return {"total": d.get("count", 0), "by_country": counts}

def elevation_stats(taxon_key: int) -> dict:
    """Pull up to 300 occurrences with elevation to compute min/max/median."""
    r = requests.get("https://api.gbif.org/v1/occurrence/search",
                     params={"taxonKey": taxon_key,
                             "hasCoordinate": "true",
                             "elevation": "0,9000",
                             "limit": 300},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    elevs = []
    for rec in r.json().get("results", []):
        e = rec.get("elevation")
        if isinstance(e, (int, float)) and 0 < e < 9000:
            elevs.append(float(e))
    if not elevs:
        return {"n": 0}
    elevs.sort()
    return {"n": len(elevs),
            "min": int(min(elevs)),
            "max": int(max(elevs)),
            "p10": int(elevs[int(0.1*len(elevs))]),
            "p90": int(elevs[int(0.9*len(elevs))]),
            "median": int(elevs[len(elevs)//2])}

def main():
    files = sorted(PLANTS.glob("*.yml"))
    rows = []
    for i, f in enumerate(files, 1):
        with f.open() as fh:
            d = yaml.safe_load(fh)
        pid = d["id"]
        binomial = d["scientific_name"]["binomial"]
        row = {"id": pid, "binomial": binomial}
        try:
            m = match_species(binomial)
            key = m.get("usageKey") or m.get("acceptedUsageKey")
            rank = (m.get("rank") or "").upper()
            mt = (m.get("matchType") or "").upper()
            # Reject anything that isn't a true species-level hit — HIGHERRANK
            # matches return the family/genus key and wildly inflate facet counts.
            if (not key) or mt in ("NONE", "HIGHERRANK") or rank not in ("SPECIES", "SUBSPECIES", "VARIETY"):
                row["status"] = "no_species_match"
                row["match_meta"] = {"usageKey": key, "rank": rank, "matchType": mt,
                                     "scientificName": m.get("scientificName")}
                (OUT / f"{pid}.json").write_text(json.dumps(row, indent=2, ensure_ascii=False))
                rows.append(row)
                print(f"[{i:3d}/{len(files)}] NONE {pid:40s} (rank={rank}, mt={mt})")
                time.sleep(0.4)
                continue
            row["status"] = "matched"
            row["usageKey"] = key
            row["accepted_name"] = m.get("scientificName")
            row["confidence"] = m.get("confidence")
            row["matchType"] = m.get("matchType")
            cf = country_facets(key)
            row["total_occurrences"] = cf["total"]
            row["countries_raw"] = cf["by_country"]
            # Filter to Himalayan geography
            him = {c: n for c, n in cf["by_country"].items() if c in HIMALAYAN_COUNTRIES}
            row["himalayan_countries"] = him
            row["elevation"] = elevation_stats(key)
            print(f"[{i:3d}/{len(files)}] OK   {pid:40s} n={cf['total']:5d}  him={sum(him.values())}")
        except Exception as e:
            row["status"] = "error"
            row["error"] = str(e)
            print(f"[{i:3d}/{len(files)}] ERR  {pid}: {e}", file=sys.stderr)
        (OUT / f"{pid}.json").write_text(json.dumps(row, indent=2, ensure_ascii=False))
        rows.append(row)
        time.sleep(0.4)

    # Summary
    out = OUT / "SUMMARY.md"
    with out.open("w") as fh:
        fh.write("# GBIF distribution verification — SUMMARY\n\n")
        fh.write(f"Run: {time.strftime('%Y-%m-%d %H:%M %Z')}\n\n")
        n_match = sum(1 for r in rows if r.get("status")=="matched")
        n_none  = sum(1 for r in rows if r.get("status")=="no_match")
        n_err   = sum(1 for r in rows if r.get("status")=="error")
        n_him   = sum(1 for r in rows if r.get("status")=="matched" and r.get("himalayan_countries"))
        n_elev  = sum(1 for r in rows if r.get("status")=="matched" and r.get("elevation",{}).get("n",0) > 0)
        fh.write(f"- matched: **{n_match}** / 101\n")
        fh.write(f"- unmatched: **{n_none}**\n")
        fh.write(f"- errors: **{n_err}**\n")
        fh.write(f"- with ≥1 Himalayan-country occurrence: **{n_him}**\n")
        fh.write(f"- with elevation data: **{n_elev}**\n\n")
        fh.write("## Per-species\n\n| id | binomial | GBIF key | n | Himalayan countries | elev (median [min–max], n) |\n|---|---|---|---|---|---|\n")
        for r in rows:
            if r.get("status") != "matched":
                fh.write(f"| {r['id']} | {r['binomial']} | — | **{r.get('status')}** | | |\n")
                continue
            him = r.get("himalayan_countries", {})
            him_str = ", ".join(f"{c}:{n}" for c, n in sorted(him.items(), key=lambda x: -x[1]))
            el = r.get("elevation", {})
            el_str = f"{el.get('median','–')} [{el.get('min','–')}–{el.get('max','–')}] n={el.get('n',0)}" if el.get("n") else "no data"
            fh.write(f"| {r['id']} | {r['binomial']} | {r['usageKey']} | {r.get('total_occurrences','?')} | {him_str} | {el_str} |\n")
    print(f"\nwrote {out}")
    (OUT / "rows.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
