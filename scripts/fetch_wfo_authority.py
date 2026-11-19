#!/usr/bin/env python3
"""
fetch_wfo_authority.py — World Flora Online binomial + authority verification.

Reads every data/plants/*.yml, queries WFO matching API, and writes:
  data/verification/wfo/<id>.json  — raw API match
  data/verification/wfo/SUMMARY.md — human-readable table

Does NOT modify data/plants/*.yml. Verification is a separate step; application
of verified authorities to source YAML happens via apply_wfo_authority.py after
Pan (or a reviewer) reviews SUMMARY.md.

License: MIT (code). Data outputs: WFO (CC0 per WFO licensing).
"""
from __future__ import annotations
import json, sys, time, pathlib, re
import requests, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLANTS = ROOT / "data" / "plants"
OUT = ROOT / "data" / "verification" / "wfo"
OUT.mkdir(parents=True, exist_ok=True)

WFO_URL = "https://list.worldfloraonline.org/matching_rest.php"
HEADERS = {"User-Agent": "HimalayanMateriaMedica/0.1 (+https://github.com/lurongpan47/himalayan-materia-medica)"}

def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()

def query_wfo(binomial: str) -> dict:
    r = requests.get(WFO_URL, params={"input_string": binomial}, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def main():
    files = sorted(PLANTS.glob("*.yml"))
    rows = []
    for i, f in enumerate(files, 1):
        with f.open() as fh:
            d = yaml.safe_load(fh)
        pid = d["id"]
        binomial = d["scientific_name"]["binomial"]
        current_auth = d["scientific_name"].get("authority") or ""
        try:
            resp = query_wfo(binomial)
        except Exception as e:
            print(f"[{i:3d}/{len(files)}] {pid}  ERROR {e}", file=sys.stderr)
            rows.append({"id": pid, "binomial": binomial, "status": "error", "error": str(e)})
            continue
        (OUT / f"{pid}.json").write_text(json.dumps(resp, indent=2, ensure_ascii=False))
        match = resp.get("match")
        candidates = resp.get("candidates") or []
        if match:
            wfo_id = match.get("wfo_id")
            full = match.get("full_name_plain", "")
            placement = match.get("placement", "")
            # Extract authority from full_name_plain
            auth = full.replace(binomial, "").strip() if full.startswith(binomial) else ""
            agrees = (auth.replace(" ", "") == current_auth.replace(" ", "")) if current_auth else None
            row = {
                "id": pid, "binomial": binomial, "status": "matched",
                "wfo_id": wfo_id, "wfo_full": full,
                "wfo_authority": auth, "yaml_authority": current_auth,
                "authority_agrees": agrees, "placement": placement,
            }
        elif candidates:
            # Ambiguous — record top candidates
            top = []
            for c in candidates[:5]:
                top.append({"wfo_id": c.get("wfo_id"),
                            "full_name_plain": c.get("full_name_plain"),
                            "placement": c.get("placement")})
            row = {"id": pid, "binomial": binomial, "status": "ambiguous",
                   "yaml_authority": current_auth, "candidates": top}
        else:
            row = {"id": pid, "binomial": binomial, "status": "unmatched",
                   "yaml_authority": current_auth}
        rows.append(row)
        flag = {"matched": "OK ", "ambiguous": "AMB", "unmatched": "???", "error": "ERR"}[row["status"]]
        print(f"[{i:3d}/{len(files)}] {flag}  {pid:40s} {binomial}")
        time.sleep(0.5)  # polite: WFO is a free community service

    # Write summary
    out = OUT / "SUMMARY.md"
    with out.open("w") as fh:
        fh.write("# WFO authority verification — SUMMARY\n\n")
        fh.write(f"Run: {time.strftime('%Y-%m-%d %H:%M %Z')}\n\n")
        stats = {"matched":0,"ambiguous":0,"unmatched":0,"error":0}
        auth_agree = auth_disagree = auth_added = 0
        for r in rows:
            stats[r["status"]] = stats.get(r["status"],0)+1
            if r["status"]=="matched":
                if r["authority_agrees"] is True: auth_agree += 1
                elif r["authority_agrees"] is False: auth_disagree += 1
                elif not r["yaml_authority"] and r["wfo_authority"]: auth_added += 1
        fh.write("## Counts\n\n")
        for k,v in stats.items():
            fh.write(f"- {k}: **{v}**\n")
        fh.write(f"- authority agrees with YAML: **{auth_agree}**\n")
        fh.write(f"- authority disagrees with YAML: **{auth_disagree}**  ← review these\n")
        fh.write(f"- authority newly suppliable (YAML was empty): **{auth_added}**\n\n")
        fh.write("## Disagreements (authority differs)\n\n")
        fh.write("| id | binomial | YAML authority | WFO authority | WFO id |\n|---|---|---|---|---|\n")
        for r in rows:
            if r.get("status")=="matched" and r.get("authority_agrees") is False:
                fh.write(f"| {r['id']} | {r['binomial']} | `{r['yaml_authority']}` | `{r['wfo_authority']}` | {r['wfo_id']} |\n")
        fh.write("\n## Ambiguous\n\n")
        for r in rows:
            if r.get("status")=="ambiguous":
                fh.write(f"- **{r['id']}** `{r['binomial']}` → {len(r['candidates'])} candidates\n")
                for c in r["candidates"]:
                    fh.write(f"  - {c['full_name_plain']}  (`{c['wfo_id']}`)\n")
        fh.write("\n## Unmatched\n\n")
        for r in rows:
            if r.get("status")=="unmatched":
                fh.write(f"- **{r['id']}** `{r['binomial']}`\n")
    print(f"\nwrote {out}")
    (OUT / "rows.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
