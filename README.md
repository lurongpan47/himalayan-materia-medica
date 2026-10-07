# 喜马拉雅药用植物大数据库 · Himalayan Materia Medica Database

> 中 · བོད · English · संस्कृत — 四语对照、历史溯源、原生图像、可核验引用

**独立项目**（2026-10-07 从 `wisdomhealth/` 搬出，与 wisdomhealth.store 电商运营**完全解耦**）。
**许可:** CC BY-SA 4.0 (数据) + MIT (代码)，Sarasvatī 同款开放治理。**非商业数据库**。
**启动:** 2026-10-06 · Pan 授权 · Lucy 建骨架 · GitHub: `lurongpan47/himalayan-materia-medica`

---

## 一、目标 (Scope)

记录喜马拉雅地区（范围：藏区、尼泊尔、不丹、北印度、锡金/大吉岭、青藏高原东缘、横断山）的**所有药用植物**。每条目收录：

1. **四语正名** — 中文 / 藏文 (Wylie + Unicode) / 英语学名+俗名 / 梵文 (Devanāgarī + IAST)
2. **植物学身份** — 学名 (binomial, authority)、科、属、同义词、保护等级 (IUCN/CITES)
3. **分布与生境** — 海拔区间、省/县级分布点、生境类型
4. **历史典据** — 来自 Rgyud-bzhi (四部医典)、Charaka Saṃhitā、Suśruta Saṃhitā、本草纲目、中华藏本草、Bhāvaprakāśa Nighaṇṭu、西藏常用中草药 等 **可核验**典籍，附卷/篇/页码
5. **药用部分 & 性味归经** — 四系医学 (Tibetan Sowa Rigpa / Ayurveda / TCM / 现代植化) 对照
6. **图像** — 优先野外活体照片，次为植物志线图 (Flora of China 等 PD)、typing specimen 扫描；每张标注来源 + 许可
7. **引用** — 每条数据点必有可追溯来源 (DOI / 卷页 / 公开数据库 ID)

**非目标 (不做):**
- 不做剂量/处方建议（医学建议责任边界）
- 不做购买/销售链接（学术库，不与电商混）
- 不收录只出现在非公开手稿/未经同行评审来源的"民间秘方"
- 不复刻受版权保护的现代学术图版 (如 Flora of China 2003 后彩色图)

---

## 二、规模评估

| 来源 | 条目 | 备注 |
|---|---|---|
| 中华藏本草 (青海人民出版社) | ~2,200 | 已有藏文名+中文名+学名 |
| 中国藏药 (Zhongguo Zangyao, 3卷) | ~1,500 | 与前者重叠高 |
| 四部医典植物药部分 | ~400 (核心) | 典据必录 |
| Nepal Medicinal Plant Database (DPR) | ~1,800 | 公开 |
| Flora of China (喜马拉雅相关 taxa) | 预估 3,000+ | 筛分布 |
| 去重后预计 | **~4,500–6,000 独立 taxa** | |

**不期望一次做完。** 架构必须支持 10 年增量。

---

## 三、数据模型（见 `schemas/plant.schema.json`）

每条目 = 一个 YAML 文件 `data/plants/<slug>.yml`
- slug 规则: 学名小写 + 下划线，e.g. `rhodiola_crenulata.yml`
- 必填字段: `id`, `scientific_name`, `family`, `names`, `distribution`, `sources` (至少 1)
- 可选: `images`, `uses_historical`, `morphology`, `chemistry`, `conservation`

四语名字段分离：
```yaml
names:
  zh: 红景天
  bo:
    unicode: སྲོལ་གོང་།
    wylie: srol gong
  en:
    - Crenate rhodiola
    - Rhodiola (common)
  sa:
    devanagari: null  # 很多藏药无梵名
    iast: null
```

### 典据引用必带页码
```yaml
uses_historical:
  - system: tibetan_sowa_rigpa
    source_ref: rgyud_bzhi
    volume: "rtsa_rgyud"
    chapter: 20
    page: "ff. 42b-43a"
    text_bo: "..."
    text_zh_translation: "..."
    translator: null  # 待人工审核
```

---

## 四、分阶段路线图

### Phase 0 (本周 · 骨架) · ✅ 已启动 2026-10-06
- [x] 目录架构
- [x] JSON Schema
- [x] 本 README + 法律/许可页
- [x] 示范条目 ×3 (红景天 / 藏红花 / 独一味)
- [x] 静态站生成器雏形 (Jinja2)
- [ ] 发给 Pan 审核架构

### Phase 1 (10 月 · 核心 100 种)
- [ ] 《四部医典·根本续》第 20 章植物名单（约 100 种）
- [ ] 每条配 ≥1 张公有领域/CC 图
- [ ] 建索引：按学名 / 中文 / 藏文 Wylie 查
- [ ] 发布到 GitHub Pages (`lurongpan47.github.io/himalayan-materia-medica`)，域名待定

### Phase 2 (11-12 月 · 扩至 500 种)
- [ ] 《中华藏本草》前 500 条批量导入 (需 OCR + 人工对齐)
- [ ] 分布地图 (Leaflet + GBIF occurrence)
- [ ] 加入 Ayurveda 对照 (Bhāvaprakāśa Nighaṇṭu)

### Phase 3 (2027 · 全库 2000+)
- [ ] 众包/贡献者流程 (类似 Sarasvatī 的 reviewed-pending 标记)
- [ ] API 端点 (JSON)
- [ ] Bitcoin anchor manifest (每月 OTS 时间戳，防篡改，Sarasvatī 同款)

### Phase 4 (长期)
- [ ] 田野照片众包（与当地科研单位、藏医院合作）
- [ ] 现代药理学链接 (PubChem / ChEMBL)
- [ ] 保护状态监测仪表板

---

## 五、与现有项目的边界

- **vs Sarasvatī**: 医典典据可以互相引用，但本库是**物种为中心**；Sarasvatī 是**典籍为中心**。四部医典的扫描+校勘属 Sarasvatī 范畴。
- **vs wisdomhealth.store**: 完全独立项目，无代码/品牌/数据共享。本库是学术开放数据库；wisdomhealth.store 是独立电商。未来**可能**单向引用（电商页链到本库条目作科学背书），但本库不含任何电商功能。
- **vs Sushruta-Tibetan**: Sushruta 梵→藏翻译项目仍独立；本库引用 Sushruta Saṃhitā 时按本库引证格式即可。

---

## 六、许可 & 治理

- 文本/数据: **CC BY-SA 4.0**
- 代码: **MIT**
- 图像: 每张单独标注许可 (PD / CC-BY / CC-BY-SA / 本项目贡献者 CC-BY-SA)
- 不接受: 任何需要撤回权的"保留权利"图像
- 治理: Pan 为 maintainer；贡献者需走 PR + review

---

## 七、本次 Session 产出 (2026-10-06)

- 项目架构 + schema + README
- 示范条目 ×3 (见 `data/plants/`)
- 静态站骨架 (见 `site/`)
- 第一版待办列表 (见 `docs/PHASE1-TODO.md`)
- **等 Pan 决定:** 子域名 / 是否纳入 Netlify / 是否招募初始贡献者
