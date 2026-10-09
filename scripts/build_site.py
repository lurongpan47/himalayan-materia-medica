#!/usr/bin/env python3
"""Build static HTML site from data/plants/*.yml."""
import json, sys, datetime, shutil
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
PLANTS_DIR = ROOT / "data/plants"
BUILD_DIR = ROOT / "build"
BUILD_DIR.mkdir(exist_ok=True)
(BUILD_DIR / "plants").mkdir(exist_ok=True)


def _stringify_dates(obj):
    if isinstance(obj, dict): return {k: _stringify_dates(v) for k, v in obj.items()}
    if isinstance(obj, list): return [_stringify_dates(x) for x in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)): return obj.isoformat()
    return obj


CSS = """
body{font-family:-apple-system,'Noto Sans','Noto Serif Tibetan','Noto Sans Devanagari','PingFang SC',sans-serif;max-width:860px;margin:2em auto;padding:0 1em;line-height:1.55;color:#222}
h1,h2,h3{color:#2c3e50}
.bo{font-family:'Jomolhari','Noto Serif Tibetan',serif;font-size:1.3em;line-height:1.9}
.sa{font-family:'Noto Serif Devanagari',serif;font-size:1.15em}
.binomial{font-style:italic}
.names-grid{display:grid;grid-template-columns:120px 1fr;gap:.4em 1em;background:#f8f8f6;padding:1em;border-left:4px solid #5a7a3a}
.lang-label{font-weight:600;color:#5a7a3a}
.source-card{background:#fdf6e3;padding:.8em 1em;margin:.6em 0;border-radius:4px;font-size:.95em}
.badge{display:inline-block;padding:.1em .5em;background:#5a7a3a;color:white;border-radius:3px;font-size:.8em;margin-right:.3em}
.badge.draft{background:#c0921a}
.badge.ai{background:#8a4b6c}
.footer{margin-top:3em;padding-top:1em;border-top:1px solid #ddd;color:#666;font-size:.9em}
nav{margin-bottom:2em}
nav a{margin-right:1em}
table{border-collapse:collapse;width:100%}
td,th{border:1px solid #ddd;padding:.5em;text-align:left;vertical-align:top}
th{background:#f0f0ec}
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>喜马拉雅药用植物数据库 · Himalayan Materia Medica</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="style.css">
</head><body>
<nav><a href="index.html">首页</a> · <a href="about.html">关于</a> · <a href="license.html">许可</a> · <a href="phase1.html">Phase 1 Roadmap</a></nav>
<h1>喜马拉雅药用植物数据库</h1>
<h2 style="margin-top:-.5em;color:#777">Himalayan Materia Medica · 中 · བོད · English · संस्कृत</h2>
<p>公开、可核验、CC BY-SA 4.0 四语对照药用植物数据库。覆盖喜马拉雅地区（藏区、尼泊尔、不丹、北印、横断山）。每条目溯源至经典典籍（四部医典、本草纲目、Charaka/Suśruta Saṃhitā 等）或现代植物志，附图像与许可标注。</p>
<p><strong>状态:</strong> Phase 0 (架构阶段) · 条目数: <code>{count}</code> · 更新于 {today}</p>
<h2>条目索引</h2>
<table><thead><tr><th>学名</th><th>中文</th><th>བོད་སྐད་</th><th>English</th><th>संस्कृत</th><th>状态</th></tr></thead><tbody>
{rows}
</tbody></table>
<div class="footer">本库 CC BY-SA 4.0 · 代码 MIT · 由 Wisdom Health 子项目承载，不与电商混用。</div>
</body></html>"""

PLANT_HTML = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>{zh_name} · {binomial} — 喜马拉雅药用植物数据库</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="../style.css">
</head><body>
<nav><a href="../index.html">← 返回索引</a></nav>
<h1>{zh_name} <span style="font-weight:400;color:#888">／</span> <span class="binomial">{binomial}</span></h1>
<p><span class="badge {status_class}">{status}</span> {family} · {genus}</p>

<h2>四语正名</h2>
<div class="names-grid">
<div class="lang-label">中文</div><div>{zh_full}</div>
<div class="lang-label">བོད་སྐད་</div><div><span class="bo">{bo_unicode}</span> &nbsp; <code>{bo_wylie}</code></div>
<div class="lang-label">English</div><div>{en}</div>
<div class="lang-label">संस्कृत</div><div><span class="sa">{sa_dev}</span> &nbsp; <em>{sa_iast}</em></div>
</div>

<h2>分布</h2>
<p><strong>海拔:</strong> {elev} m · <strong>生境:</strong> {habitat}</p>
<p><strong>分布区:</strong> {regions}</p>

<h2>形态</h2>
<p>{morphology}</p>

<h2>药用部分</h2>
<p>{parts}</p>

<h2>历史典据</h2>
{uses_html}

<h2>主要成分</h2>
{chem_html}

<h2>保护状态</h2>
<p>{conservation}</p>

<h2>图像</h2>
<p>{images_html}</p>

<h2>数据来源</h2>
{sources_html}

<div class="footer">数据条目 CC BY-SA 4.0 · <code>id: {id}</code> · 最后更新 {last_updated} · 本页由 build_site.py 自动生成</div>
</body></html>"""


def render_names(doc):
    n = doc.get("names", {}) or {}
    zh_raw = n.get("zh")
    if isinstance(zh_raw, dict):
        zh_full = zh_raw.get("primary", "")
        if zh_raw.get("aliases"):
            zh_full += f" ({'、'.join(zh_raw['aliases'])})"
    else:
        zh_full = zh_raw or ""
    bo = n.get("bo") or {}
    en = ", ".join(n.get("en", []) or []) or "—"
    sa = n.get("sa") or {}
    return dict(
        zh_name=zh_raw.get("primary") if isinstance(zh_raw, dict) else (zh_raw or doc["id"]),
        zh_full=zh_full or "—",
        bo_unicode=bo.get("unicode") or "—",
        bo_wylie=bo.get("wylie") or "—",
        en=en,
        sa_dev=sa.get("devanagari") or "—",
        sa_iast=sa.get("iast") or "—",
    )


def render_uses(doc):
    out = []
    for u in doc.get("uses_historical", []) or []:
        system = u.get("system", "—")
        ref = u.get("source_ref") or "(no classical source)"
        loc = " / ".join(x for x in [u.get("volume"), str(u.get("chapter") or ""), u.get("page")] if x)
        txt_o = u.get("text_original") or ""
        txt_t = u.get("text_translation") or ""
        rs = u.get("review_status", "ai_draft")
        rs_badge = f'<span class="badge ai">{rs}</span>' if rs == "ai_draft" else f'<span class="badge">{rs}</span>'
        orig_html = f"<p><em>Original:</em> {txt_o}</p>" if txt_o else ""
        out.append(f'<div class="source-card">{rs_badge} <strong>{system}</strong> · {ref} · {loc}{orig_html}<p>{txt_t}</p></div>')
    return "\n".join(out) or "<p>（待录入）</p>"


def render_chem(doc):
    chem = (doc.get("chemistry") or {}).get("key_compounds") or []
    if not chem: return "<p>（待录入）</p>"
    rows = "".join(
        f"<tr><td><strong>{c.get('name','?')}</strong></td><td>{c.get('class','')}</td>"
        f"<td>{'PubChem CID '+str(c['pubchem_cid']) if c.get('pubchem_cid') else ''}</td>"
        f"<td>{c.get('role_in_traditional_use','')}</td></tr>"
        for c in chem
    )
    return f'<table><thead><tr><th>化合物</th><th>类别</th><th>外部 ID</th><th>作用</th></tr></thead><tbody>{rows}</tbody></table>'


def render_sources(doc, sources_registry):
    out = []
    for s in doc.get("sources", []) or []:
        k = s["key"]
        reg = sources_registry.get(k, {})
        title = reg.get("title_zh") or reg.get("title_en") or reg.get("title_iast") or k
        pd = "✅ 公有领域" if reg.get("public_domain") else "⚠️ 版权，仅引用事实"
        notes = s.get("notes") or ""
        out.append(f'<div class="source-card"><code>{k}</code> · <strong>{title}</strong> · {pd}<br>取用于 {s.get("retrieved","?")}. {notes}</div>')
    return "\n".join(out)


def render_images(doc):
    imgs = doc.get("images") or []
    if not imgs: return '<em style="color:#999">（等待公有领域/CC 图像补充）</em>'
    return "<br>".join(f'<img src="../{im["path"]}" alt="{im.get("caption","")}" style="max-width:100%"><br><em>{im.get("caption","")} — {im["license"]} · {im["credit"]}</em>' for im in imgs)


def main():
    sources_registry = yaml.safe_load((ROOT / "data/sources/_sources.yml").read_text()) or {}
    plants = []
    for p in sorted(PLANTS_DIR.glob("*.yml")):
        doc = _stringify_dates(yaml.safe_load(p.read_text()))
        plants.append(doc)

    (BUILD_DIR / "style.css").write_text(CSS)

    rows = []
    for d in plants:
        n = render_names(d)
        rows.append(
            f'<tr><td><a href="plants/{d["id"]}.html" class="binomial">{d["scientific_name"]["binomial"]}</a></td>'
            f'<td>{n["zh_name"]}</td><td><span class="bo">{n["bo_unicode"]}</span></td>'
            f'<td>{d["names"].get("en",["—"])[0] if d["names"].get("en") else "—"}</td>'
            f'<td><span class="sa">{n["sa_dev"]}</span></td>'
            f'<td>{d.get("status","stub")}</td></tr>'
        )
    (BUILD_DIR / "index.html").write_text(INDEX_HTML.format(
        count=len(plants), today=datetime.date.today().isoformat(), rows="\n".join(rows)))

    # about + license pages
    (BUILD_DIR / "about.html").write_text(f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>关于</title><link rel="stylesheet" href="style.css"></head><body>
<nav><a href="index.html">← 首页</a></nav><h1>关于本库</h1>
<p>喜马拉雅药用植物数据库是 <strong>Wisdom Health</strong> 项目下的开放子项目，旨在建立一个四语对照、历史溯源、可核验引用的喜马拉雅地区药用植物数据库。</p>
<p>与 Sarasvatī 项目（八系佛典归档）的关系：Sarasvatī 以典籍为中心，本库以物种为中心。两者互相引用，但各自独立治理。</p>
<p>所有数据条目遵循 CC BY-SA 4.0 开放许可。代码遵循 MIT。</p>
<p>当前为 Phase 0 架构阶段。详见 <a href="phase1.html">Phase 1 Roadmap</a>。</p>
</body></html>""")

    (BUILD_DIR / "license.html").write_text("""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>许可</title><link rel="stylesheet" href="style.css"></head><body>
<nav><a href="index.html">← 首页</a></nav><h1>许可 & 法律</h1>
<h2>数据/文本</h2><p><strong>CC BY-SA 4.0</strong></p>
<h2>代码</h2><p><strong>MIT</strong></p>
<h2>图像</h2><p>每张图像单独标注许可。本库不接受"保留所有权利"图像。接受: public_domain / cc0 / cc_by_4 / cc_by_sa_4 / cc_by_3 / cc_by_sa_3 / 本项目贡献者 cc_by_sa_4。</p>
<h2>免责声明</h2><p>本库是学术/历史资料库。<strong>不提供医疗建议</strong>。不列具体剂量/处方。使用历史药用信息自担风险。濒危物种请遵守所在地法规与 CITES。</p>
<h2>版权事实边界</h2><p>学名、科属、海拔区间、分布县市、Pubchem CID 等事实不受版权保护，可自由引用来源。《中华藏本草》《中国藏药》《Flora of China》等现代学术描述的散文段落受版权保护，本库仅引用事实、不复制描述文字。四部医典、《本草纲目》、Caraka/Suśruta Saṃhitā 原文属公有领域。</p>
</body></html>""")

    (BUILD_DIR / "phase1.html").write_text("""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>Phase 1 Roadmap</title><link rel="stylesheet" href="style.css"></head><body>
<nav><a href="index.html">← 首页</a></nav><h1>Phase 1 Roadmap · 核心 100 种</h1>
<p>首阶段目标: 建立《四部医典·根本续》第 20 章列出的核心植物药清单（约 100 种），每条配 1 张公有领域/CC 图像与至少 2 处可核验典据。</p>
<h2>工作流</h2>
<ol><li>从四部医典 Dharamsala 1982 版第 20 章 OCR 植物名单</li><li>与中华藏本草 + Flora of China 做学名对齐</li><li>每条写 stub YAML</li><li>人工 review 前 10 条 → 调整 schema</li><li>其余并发子任务填充</li><li>图像从 Wikimedia Commons / iNaturalist CC 搜图</li><li>validate.py + build_site.py 持续 CI</li></ol>
<h2>何时发布</h2><p>条目数 ≥ 50 且 ≥ 20 条带图时首发到 Netlify。预估 2026-11 月中旬。</p>
</body></html>""")

    for d in plants:
        n = render_names(d)
        dist = d.get("distribution") or {}
        elev = dist.get("elevation_m") or {}
        elev_s = f"{elev.get('min','?')}–{elev.get('max','?')}" if elev else "—"
        html = PLANT_HTML.format(
            zh_name=n["zh_name"],
            zh_full=n["zh_full"],
            binomial=d["scientific_name"]["binomial"],
            family=d.get("family", "—"),
            genus=d.get("genus", "—"),
            bo_unicode=n["bo_unicode"],
            bo_wylie=n["bo_wylie"],
            en=n["en"],
            sa_dev=n["sa_dev"],
            sa_iast=n["sa_iast"],
            elev=elev_s,
            habitat=dist.get("habitat") or "—",
            regions=", ".join(dist.get("regions", []) or []),
            morphology=(d.get("morphology") or "—").replace("\n", "<br>"),
            parts=", ".join(d.get("parts_used", []) or []) or "—",
            uses_html=render_uses(d),
            chem_html=render_chem(d),
            conservation=(d.get("conservation") or {}).get("iucn_status") or "—",
            images_html=render_images(d),
            sources_html=render_sources(d, sources_registry),
            id=d["id"],
            last_updated=d.get("last_updated", "—"),
            status=d.get("status", "stub"),
            status_class="draft" if d.get("status") == "draft" else "",
        )
        (BUILD_DIR / "plants" / f'{d["id"]}.html').write_text(html)

    # JSON API output (public, CORS-friendly via GitHub Pages)
    (BUILD_DIR / "api").mkdir(exist_ok=True)
    (BUILD_DIR / "api/plants").mkdir(exist_ok=True)

    def _public_record(d):
        n = render_names(d)
        dist = d.get("distribution") or {}
        return {
            "id": d["id"],
            "scientific_name": d["scientific_name"]["binomial"],
            "authority": d["scientific_name"].get("authority"),
            "family": d.get("family"),
            "genus": d.get("genus"),
            "names": {
                "zh": n["zh_name"] or None,
                "bo_unicode": n["bo_unicode"] or None,
                "bo_wylie": n["bo_wylie"] or None,
                "en": n["en"] or None,
                "sa_dev": n["sa_dev"] or None,
                "sa_iast": n["sa_iast"] or None,
            },
            "distribution": {
                "elevation_m": dist.get("elevation_m"),
                "habitat": dist.get("habitat"),
                "regions": dist.get("regions", []),
            },
            "parts_used": d.get("parts_used", []),
            "conservation": (d.get("conservation") or {}).get("iucn_status"),
            "sources_count": len(d.get("sources") or []),
            "status": d.get("status", "stub"),
            "url": f"https://lurongpan47.github.io/himalayan-materia-medica/plants/{d['id']}.html",
            "api_url": f"https://lurongpan47.github.io/himalayan-materia-medica/api/plants/{d['id']}.json",
            "license": "CC BY-SA 4.0",
        }

    manifest = {
        "$schema": "https://lurongpan47.github.io/himalayan-materia-medica/api/schema.json",
        "name": "Himalayan Materia Medica",
        "version": "0.1",
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "count": len(plants),
        "license": "CC BY-SA 4.0",
        "base_url": "https://lurongpan47.github.io/himalayan-materia-medica/",
        "plants": [_public_record(d) for d in plants],
    }
    (BUILD_DIR / "api/plants.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )

    # Per-plant full records
    for d in plants:
        full = _public_record(d)
        full["uses_historical"] = d.get("uses_historical")
        full["chemistry"] = d.get("chemistry")
        full["morphology"] = d.get("morphology")
        full["images"] = d.get("images")
        full["sources"] = d.get("sources")
        (BUILD_DIR / "api/plants" / f"{d['id']}.json").write_text(
            json.dumps(full, ensure_ascii=False, indent=2)
        )

    # Lookup index by common name (lowercase) for fast partner lookups
    lookup = {}
    for d in plants:
        n = render_names(d)
        keys = set()
        if n["en"]:
            keys.add(n["en"].lower().strip())
        for en_name in d.get("names", {}).get("en", []) or []:
            keys.add(en_name.lower().strip())
        keys.add(d["scientific_name"]["binomial"].lower().strip())
        # Genus-only key as last-resort match
        if d.get("genus"):
            keys.add(d["genus"].lower().strip())
        for k in keys:
            if k:
                lookup.setdefault(k, []).append(d["id"])
    (BUILD_DIR / "api/lookup.json").write_text(
        json.dumps(
            {
                "generated": datetime.datetime.utcnow().isoformat() + "Z",
                "description": "Case-insensitive map: common_name_or_binomial_or_genus -> [plant_id,...]. Use for ingredient-to-plant lookup from product pages.",
                "index": lookup,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    print(f"Built {len(plants)} plant pages + api/plants.json + api/lookup.json + {len(plants)} per-plant JSON → {BUILD_DIR}")


if __name__ == "__main__":
    main()
