#!/usr/bin/env python3
"""
fetch_images_commons.py — Wikimedia Commons CC/PD image lookup.

For every data/plants/*.yml:
  1. Try Category:<Binomial>  — Commons convention for taxon-grouped media
  2. Fall back to full-text file search within namespace 6
  3. Keep only image/* MIME types with CC-* or PD licenses
  4. Record up to 5 candidates per species with: url, thumb, license, artist, credit

Writes:
  data/verification/commons/<id>.json — raw candidates (NOT downloaded)
  data/verification/commons/SUMMARY.md

Downloads happen in a separate apply step after review. This script only INDEXES
license-clean candidates — it does not copy any media into the repo.
"""
from __future__ import annotations
import json, re, sys, time, pathlib, requests, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLANTS = ROOT / "data" / "plants"
OUT = ROOT / "data" / "verification" / "commons"
OUT.mkdir(parents=True, exist_ok=True)

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "HimalayanMateriaMedica/0.1 (+https://github.com/lurongpan47/himalayan-materia-medica)"}

OK_LICENSE_RX = re.compile(
    r"^(Public domain|CC0|CC[- ]BY(?:[- ]SA)?(?:[- ]\d(?:\.\d)?)?)$",
    re.IGNORECASE,
)

def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "").strip()

def pack_candidate(title: str, ii: dict) -> dict | None:
    em = ii.get("extmetadata", {})
    lic = (em.get("LicenseShortName") or {}).get("value", "").strip()
    if not OK_LICENSE_RX.match(lic.replace("–", "-")):
        return None
    if not (ii.get("mime", "") or "").startswith("image/"):
        return None
    return {
        "title": title,
        "url": ii.get("url"),
        "descriptionurl": ii.get("descriptionurl"),
        "mime": ii.get("mime"),
        "license_short": lic,
        "license_url": (em.get("LicenseUrl") or {}).get("value"),
        "artist": strip_tags((em.get("Artist") or {}).get("value", "")),
        "credit": strip_tags((em.get("Credit") or {}).get("value", "")),
        "date": strip_tags((em.get("DateTime") or {}).get("value", "")),
        "object_name": strip_tags((em.get("ObjectName") or {}).get("value", "")),
    }

def query(params: dict) -> dict:
    r = requests.get(API, params=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r.json()

def search_category(binomial: str, limit: int = 15) -> list[dict]:
    d = query({
        "action": "query", "format": "json", "prop": "imageinfo",
        "generator": "categorymembers",
        "gcmtitle": f"Category:{binomial}",
        "gcmtype": "file", "gcmlimit": limit,
        "iiprop": "url|extmetadata|mime",
    })
    out = []
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        c = pack_candidate(p.get("title", ""), ii)
        if c: out.append(c)
    return out

def search_text(binomial: str, limit: int = 15) -> list[dict]:
    d = query({
        "action": "query", "format": "json", "prop": "imageinfo",
        "generator": "search",
        "gsrsearch": binomial, "gsrnamespace": 6, "gsrlimit": limit,
        "iiprop": "url|extmetadata|mime",
    })
    out = []
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        c = pack_candidate(p.get("title", ""), ii)
        if c: out.append(c)
    return out

def main():
    files = sorted(PLANTS.glob("*.yml"))
    rows = []
    for i, f in enumerate(files, 1):
        with f.open() as fh:
            d = yaml.safe_load(fh)
        pid = d["id"]
        binomial = d["scientific_name"]["binomial"]
        cands = []
        src = None
        try:
            cands = search_category(binomial)
            if cands: src = "category"
            if len(cands) < 3:
                more = search_text(binomial)
                # dedupe by title
                seen = {c["title"] for c in cands}
                for m in more:
                    if m["title"] not in seen:
                        cands.append(m); seen.add(m["title"])
                src = src or "text"
        except Exception as e:
            print(f"[{i:3d}/{len(files)}] ERR  {pid}: {e}", file=sys.stderr)
            rows.append({"id": pid, "binomial": binomial, "status": "error", "error": str(e)})
            continue
        row = {"id": pid, "binomial": binomial, "source": src,
               "n_candidates": len(cands), "candidates": cands[:5]}
        (OUT / f"{pid}.json").write_text(json.dumps(row, indent=2, ensure_ascii=False))
        rows.append(row)
        print(f"[{i:3d}/{len(files)}] {len(cands):2d}  {pid:40s} ({src or 'none'})")
        time.sleep(0.5)

    out = OUT / "SUMMARY.md"
    with out.open("w") as fh:
        fh.write("# Wikimedia Commons image candidates — SUMMARY\n\n")
        fh.write(f"Run: {time.strftime('%Y-%m-%d %H:%M %Z')}\n\n")
        has = sum(1 for r in rows if r.get("n_candidates", 0) > 0)
        fh.write(f"- species with ≥1 CC/PD image candidate: **{has}** / {len(rows)}\n\n")
        fh.write("| id | binomial | n | best license | top candidate |\n|---|---|---|---|---|\n")
        for r in rows:
            cs = r.get("candidates", [])
            if not cs:
                fh.write(f"| {r['id']} | {r['binomial']} | 0 | | |\n")
                continue
            top = cs[0]
            fh.write(f"| {r['id']} | {r['binomial']} | {r['n_candidates']} | {top['license_short']} | [{top['title'][:60]}]({top['descriptionurl']}) |\n")
    print(f"\nwrote {out}")
    (OUT / "rows.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
