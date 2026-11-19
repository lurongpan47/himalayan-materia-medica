#!/usr/bin/env python3
"""
build_zh_bo_pdf.py — Chinese-Tibetan bilingual catalog PDF.

Renders the current 101-species corpus with:
  - 中文正名 + 别名
  - 藏文 Unicode + Wylie
  - 学名 + family
  - verification/gbif: Himalayan countries + elevation
  - verification/wfo: authority status
  - verification/commons: image availability flag
  - status (stub / draft) honestly shown

Output: build/himalayan-materia-medica-zh-bo-DATE.pdf
"""
from __future__ import annotations
import json, pathlib, yaml, datetime, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, KeepTogether)

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLANTS = ROOT / "data" / "plants"
VER = ROOT / "data" / "verification"
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)

# ── Fonts ─────────────────────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont("ZH",   "/System/Library/Fonts/STHeiti Medium.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("ZHS",  "/System/Library/Fonts/Supplemental/Songti.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("BO",   "/System/Library/Fonts/Supplemental/Kailasa.ttc", subfontIndex=0))

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Title"],  fontName="ZH", fontSize=22,
                   leading=28, spaceAfter=10, alignment=TA_CENTER)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="ZH", fontSize=14,
                   leading=18, spaceBefore=8, spaceAfter=6, textColor=colors.HexColor("#4A3B2A"))
SUBTLE = ParagraphStyle("Sub", parent=styles["Normal"], fontName="ZHS", fontSize=9,
                        leading=12, textColor=colors.HexColor("#666"), alignment=TA_CENTER)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontName="ZH", fontSize=10,
                      leading=14)
ZH_PRIMARY = ParagraphStyle("ZhPrimary", parent=styles["Normal"], fontName="ZH",
                            fontSize=16, leading=20, spaceAfter=2,
                            textColor=colors.HexColor("#1B3A5B"))
ZH_ALIAS = ParagraphStyle("ZhAlias", parent=styles["Normal"], fontName="ZHS",
                          fontSize=9.5, leading=13, textColor=colors.HexColor("#555"))
BO_UNI = ParagraphStyle("BoUni", parent=styles["Normal"], fontName="BO",
                        fontSize=16, leading=24, spaceAfter=2,
                        textColor=colors.HexColor("#8B2323"))
BO_WYLIE = ParagraphStyle("BoWylie", parent=styles["Normal"], fontName="ZHS",
                          fontSize=9.5, leading=13, textColor=colors.HexColor("#555"),
                          fontStyle=None)
BINOM = ParagraphStyle("Binom", parent=styles["Normal"], fontName="ZHS",
                       fontSize=11, leading=14,
                       textColor=colors.HexColor("#2E5A3B"))
LABEL = ParagraphStyle("Label", parent=styles["Normal"], fontName="ZH",
                       fontSize=8.5, leading=11,
                       textColor=colors.HexColor("#888"))
STATUS_STUB = ParagraphStyle("StStub", parent=styles["Normal"], fontName="ZH",
                             fontSize=8, textColor=colors.HexColor("#AA5500"))
STATUS_DRAFT = ParagraphStyle("StDraft", parent=styles["Normal"], fontName="ZH",
                              fontSize=8, textColor=colors.HexColor("#006633"))

# ── Load data ─────────────────────────────────────────────────────────────────
def load_plant(p):
    return yaml.safe_load(open(p))

# Load consolidated verification rows (keyed by id) once
_VER_ROWS = {}
for _kind in ("wfo", "gbif", "commons"):
    _rows_f = VER / _kind / "rows.json"
    if _rows_f.exists():
        _VER_ROWS[_kind] = {r["id"]: r for r in json.load(open(_rows_f))}
    else:
        _VER_ROWS[_kind] = {}

def load_ver(kind, pid):
    return _VER_ROWS.get(kind, {}).get(pid)

def esc(s):
    if s is None: return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def norm_zh(zh):
    """Return (primary, aliases_list)."""
    if zh is None: return ("—", [])
    if isinstance(zh, str): return (zh, [])
    primary = zh.get("primary") or zh.get("name") or "—"
    aliases = zh.get("aliases") or []
    return (primary, aliases)

def norm_bo(bo):
    """Return (unicode, wylie, aliases)."""
    if not isinstance(bo, dict): return ("", "", [])
    uni = bo.get("unicode") or ""
    wyl = bo.get("wylie") or ""
    al = bo.get("aliases") or []
    return (uni, wyl, al)

def country_label(code):
    return {"CN":"中国","IN":"印度","NP":"尼泊尔","BT":"不丹","PK":"巴基斯坦","MM":"缅甸","AF":"阿富汗"}.get(code, code)

def status_badge(status):
    if status == "draft":
        return Paragraph("● 草稿 / draft", STATUS_DRAFT)
    return Paragraph("○ 占位候选 / stub (未经校对)", STATUS_STUB)

# ── Build species block ──────────────────────────────────────────────────────
def species_block(d):
    pid = d["id"]
    binomial = d["scientific_name"]["binomial"]
    authority = d["scientific_name"].get("authority") or ""
    family = d.get("family") or "—"
    genus = d.get("genus") or ""
    status = d.get("status", "stub")

    zh_prim, zh_al = norm_zh(d["names"].get("zh"))
    bo_uni, bo_wyl, bo_al = norm_bo(d["names"].get("bo"))

    gbif = load_ver("gbif", pid)
    wfo = load_ver("wfo", pid)
    commons = load_ver("commons", pid)

    # Left column: Chinese
    left_cells = [Paragraph(esc(zh_prim), ZH_PRIMARY)]
    if zh_al:
        left_cells.append(Paragraph("别名: " + esc("、".join(zh_al)), ZH_ALIAS))

    # Right column: Tibetan
    right_cells = []
    if bo_uni:
        right_cells.append(Paragraph(esc(bo_uni), BO_UNI))
        if bo_wyl:
            right_cells.append(Paragraph("Wylie: " + esc(bo_wyl), BO_WYLIE))
        for a in bo_al:
            if isinstance(a, dict) and a.get("unicode"):
                right_cells.append(Paragraph(esc(a["unicode"]), BO_UNI))
                if a.get("wylie"):
                    right_cells.append(Paragraph("Wylie: " + esc(a["wylie"]), BO_WYLIE))
    else:
        right_cells.append(Paragraph("—", BO_UNI))
        right_cells.append(Paragraph("(藏文名未定 / Tibetan name tbd)", BO_WYLIE))

    name_row = Table([[left_cells, right_cells]], colWidths=[85*mm, 85*mm])
    name_row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("BACKGROUND", (0,0), (0,0), colors.HexColor("#F4F0E8")),
        ("BACKGROUND", (1,0), (1,0), colors.HexColor("#F8EEE8")),
    ]))

    # Scientific name line
    sci_line = Paragraph(
        f"<b>{esc(binomial)}</b> {esc(authority)}  &nbsp;·&nbsp; "
        f"<font color='#666'>{esc(family)}科</font>",
        BINOM)

    # Distribution line (GBIF)
    if gbif and gbif.get("status") == "matched":
        him = gbif.get("himalayan_countries") or {}
        if him:
            parts = [f"{country_label(c)} {n}" for c, n in sorted(him.items(), key=lambda x: -x[1])]
            dist_str = "、".join(parts[:7])
        else:
            dist_str = "喜马拉雅弧内暂无 GBIF 记录"
        elev = gbif.get("elevation") or {}
        if elev.get("n"):
            elev_str = f"海拔 {elev['min']}–{elev['max']} m (中位 {elev['median']}, n={elev['n']})"
        else:
            elev_str = "海拔数据不足"
        dist_line = Paragraph(
            f"<font name='ZH' color='#888'>分布 (GBIF):</font> {esc(dist_str)}<br/>"
            f"<font name='ZH' color='#888'>Elevation:</font> {esc(elev_str)}",
            BODY)
    else:
        dist_line = Paragraph(
            "<font color='#888'>分布 (GBIF): 无物种级匹配</font>", BODY)

    # Verification status line
    checks = []
    if wfo:
        s = wfo.get("status")
        if s == "matched":
            agrees = wfo.get("authority_agrees")
            if agrees is True: checks.append("✓ WFO 命名人一致")
            elif agrees is False: checks.append(f"⚠ WFO 命名人分歧: {esc(wfo.get('wfo_authority',''))}")
            else: checks.append("✓ WFO 匹配")
        elif s == "ambiguous":
            checks.append(f"⚠ WFO 同名歧义 ({len(wfo.get('candidates',[]))} 候选)")
        else:
            checks.append(f"× WFO: {s}")
    if commons:
        n = commons.get("n_candidates", 0)
        if n:
            lic = commons.get("candidates", [{}])[0].get("license_short", "")
            checks.append(f"✓ Commons: {n} 张 CC/PD 图 (首张: {esc(lic)})")
        else:
            checks.append("× Commons: 未发现 CC/PD 图")
    ver_line = Paragraph(
        "<font name='ZH' color='#888'>核验:</font> " + " &nbsp;·&nbsp; ".join(checks),
        BODY)

    # Historical use (if real draft)
    uses = d.get("uses_historical") or []
    use_elems = []
    if uses and isinstance(uses, list) and len(uses) > 0:
        for u in uses[:3]:
            if not isinstance(u, dict): continue
            sys_ = u.get("system", "")
            sys_cn = {"tibetan_sowa_rigpa":"藏医 (Sowa Rigpa)",
                      "tcm":"中医 (TCM)",
                      "ayurveda":"Ayurveda 阿育吠陀"}.get(sys_, sys_)
            src = u.get("source_ref", "")
            ch = u.get("chapter", "")
            txt = u.get("text_translation", "") or ""
            rev = u.get("review_status") or ""
            rev_tag = f" <font color='#AA5500'>⟨{esc(rev)}⟩</font>" if rev else ""
            if txt:
                txt_short = txt if len(txt) < 220 else txt[:217] + "…"
                use_elems.append(Paragraph(
                    f"<font color='#555'><b>{esc(sys_cn)}</b>"
                    + (f" · {esc(src)}" if src else "")
                    + (f" 卷/章 {esc(ch)}" if ch else "")
                    + f":{rev_tag}</font> {esc(txt_short)}",
                    BODY))

    block = [name_row, Spacer(1, 2*mm), sci_line, Spacer(1, 1*mm),
             dist_line, Spacer(1, 1*mm), ver_line]
    if use_elems:
        block.append(Spacer(1, 2*mm))
        block.append(Paragraph("<font color='#888'>典据记载:</font>", LABEL))
        block.extend(use_elems)
    block.append(Spacer(1, 1*mm))
    block.append(status_badge(status))
    # Divider
    block.append(Spacer(1, 2*mm))
    div = Table([[""]], colWidths=[170*mm], rowHeights=[0.6])
    div.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#D0C8B8"))]))
    block.append(div)
    block.append(Spacer(1, 3*mm))

    return KeepTogether(block)

# ── Cover ─────────────────────────────────────────────────────────────────────
def cover_story(stats):
    story = []
    story.append(Spacer(1, 35*mm))
    story.append(Paragraph("喜马拉雅藏医本草", H1))
    story.append(Paragraph("中藏对照工作稿", H1))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Himalayan Materia Medica &middot; Chinese-Tibetan Bilingual Working Draft",
                           SUBTLE))
    story.append(Spacer(1, 25*mm))
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    meta_rows = [
        ["版本 Version", f"Phase-1 snapshot · {today}"],
        ["收录 Species", f"{stats['total']} 种 (草稿 draft: {stats['draft']} · 占位 stub: {stats['stub']})"],
        ["学名核验 WFO", f"{stats['wfo_match']} / {stats['total']} 匹配; "
                        f"{stats['wfo_disagree']} 处命名人分歧待审; "
                        f"{stats['wfo_ambig']} 处同名歧义"],
        ["分布核验 GBIF", f"{stats['gbif_match']} / {stats['total']} 物种级匹配; "
                         f"{stats['gbif_him']} 条有喜马拉雅出现记录"],
        ["图库 Commons", f"{stats['commons_hit']} / {stats['total']} 有 CC/PD 候选图"],
        ["许可 License", "数据 CC BY-SA 4.0 · 代码 MIT"],
        ["仓库 Repo", "github.com/lurongpan47/himalayan-materia-medica"],
    ]
    t = Table(meta_rows, colWidths=[45*mm, 115*mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "ZH"),
        ("FONTNAME", (1,0), (1,-1), "ZHS"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#666")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 20*mm))
    disclaimer = (
        "<b>工作稿说明.</b> 本册所有条目标注 <font color='#AA5500'>⟨ai_draft⟩</font> 或 "
        "<font color='#AA5500'>⟨stub⟩</font> 者，为 AI 首稿或仅做源表核对的候选词条，<b>未经藏医学家 / "
        "本草学家审定</b>，不得作为学术或临床引用。校订者署名将在 "
        "<font color='#4A3B2A'>CONTRIBUTORS.md</font> 公开登记。"
        "<br/><br/>"
        "<b>Working draft.</b> Entries marked ⟨ai_draft⟩ or ⟨stub⟩ are AI first-drafts or scaffolded "
        "candidate records; they have NOT been reviewed by domain experts and must not be cited "
        "academically or clinically. Reviewer names will be recorded in CONTRIBUTORS.md."
    )
    story.append(Paragraph(disclaimer, BODY))
    story.append(PageBreak())
    return story

# ── Build ─────────────────────────────────────────────────────────────────────
def main():
    plants = sorted(PLANTS.glob("*.yml"))
    entries = [load_plant(p) for p in plants]

    # stats
    stats = {"total": len(entries), "draft": 0, "stub": 0,
             "wfo_match": 0, "wfo_disagree": 0, "wfo_ambig": 0,
             "gbif_match": 0, "gbif_him": 0, "commons_hit": 0}
    for d in entries:
        if d.get("status") == "draft": stats["draft"] += 1
        else: stats["stub"] += 1
        pid = d["id"]
        w = load_ver("wfo", pid)
        if w:
            if w.get("status") == "matched":
                stats["wfo_match"] += 1
                if w.get("authority_agrees") is False: stats["wfo_disagree"] += 1
            elif w.get("status") == "ambiguous":
                stats["wfo_ambig"] += 1
        g = load_ver("gbif", pid)
        if g and g.get("status") == "matched":
            stats["gbif_match"] += 1
            if g.get("himalayan_countries"): stats["gbif_him"] += 1
        c = load_ver("commons", pid)
        if c and c.get("n_candidates", 0) > 0: stats["commons_hit"] += 1

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    outpath = BUILD / f"himalayan-materia-medica-zh-bo-{today}.pdf"

    doc = SimpleDocTemplate(str(outpath), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm,
                            title="Himalayan Materia Medica (ZH-BO draft)",
                            author="Lucy / Himalayan Materia Medica project")

    story = []
    story.extend(cover_story(stats))

    # Group by family for readability
    by_family = {}
    for d in entries:
        fam = d.get("family") or "Unassigned"
        by_family.setdefault(fam, []).append(d)

    for fam in sorted(by_family.keys()):
        story.append(Paragraph(f"{esc(fam)} 科 · {esc(fam)}", H2))
        for d in sorted(by_family[fam], key=lambda x: x["scientific_name"]["binomial"]):
            story.append(species_block(d))

    # Footer per page
    def on_page(canvas, doc_):
        canvas.saveState()
        canvas.setFont("ZHS", 8)
        canvas.setFillColor(colors.HexColor("#888"))
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"喜马拉雅藏医本草 · 中藏对照工作稿 · {today} · 第 {doc_.page} 页")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"wrote {outpath}")
    print(f"size: {outpath.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
