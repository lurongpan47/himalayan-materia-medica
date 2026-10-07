# Phase 1 TODO · 核心 100 种

## 当前状态 (2026-10-07)

- ✅ 候选池：**101 条** stub（见 `data/phase1_candidates.csv` + `data/plants/*.yml`）
- ✅ Schema 验证全过（`python3 scripts/validate.py`）
- ✅ 静态站 101 页全部 build 通过（`build/`）
- ✅ OCR 骨架：`scripts/ocr_rgyud_bzhi_ch20.py`（**等待扫描源**）
- ✅ Stub 生成器：`scripts/gen_stubs_from_csv.py`（幂等，可重跑）
- ✅ 已有 3 条真 draft：红景天 / 藏红花 / 独一味
- ⏸️ 98 条 **UNVETTED stubs** — 都带了"⚠️ STUB · UNVETTED CANDIDATE · DO NOT CITE"banner

## 工具链

- `scripts/validate.py` ✅ schema + source_ref 完整性
- `scripts/build_site.py` ✅ 静态站生成
- `scripts/gen_stubs_from_csv.py` ✅ 批量 stub（从 CSV）
- `scripts/ocr_rgyud_bzhi_ch20.py` ⏸️ 等 Pan 提供扫描源
- 待写：`scripts/import_zhbc.py`（中华藏本草 OCR 批量）
- 待写：`scripts/fetch_gbif.py`（学名 → GBIF taxon key + 分布）
- 待写：`scripts/fetch_images_commons.py`（Wikimedia Commons CC 搜图）

## 候选池来源分布

- 四部医典根本续 ch.20 关联：~70 条（Tibetan name 存在）
- Ayurveda 三经典关联：~25 条（Sanskrit name 存在）
- 本草纲目关联：~20 条
- 中华藏本草独有：~30 条

> **警告**：以上数字是**声称**，不是**核实**。核实工作 = Phase 1 OCR + 典据对位任务。

## Phase 1 必须完成才能发布

1. [ ] **四部医典 ch.20 OCR**（block：Pan 提供扫描源）
2. [ ] 根据 ch.20 OCR 结果，修订候选池：剔除未出现在 ch.20 的 "声称有 rgyud_bzhi 典据" 条目
3. [ ] 每条有分布数据 + GBIF taxon key
4. [ ] 每条 ≥1 张公有领域/CC 图
5. [ ] 建索引页：按学名 / 中文 / 藏文 Wylie 查
6. [ ] 发布到 GitHub Pages `lurongpan47.github.io/himalayan-materia-medica`（2026-10-07 Pan 决定暂不买域名）

## 候选 100 种名单（已入 CSV）

**已入库 3 条 draft:**
- [x] Rhodiola crenulata 大花红景天 སྲོལ་གོང་དམར་པོ།
- [x] Crocus sativus 番红花/藏红花 གུར་གུམ།
- [x] Lamiophlomis rotata 独一味 དབང་ལག

**98 条 stub（见 `data/plants/*.yml`）** 覆盖：
- 藏医常用：雪莲、川贝、三果（诃子/毛诃子/余甘子）、乌头、龙胆、绿绒蒿、沙棘、大黄、麻黄、冬虫夏草、风毛菊、报春、杜鹃、柏……
- Ayurveda 常用：ashwagandha、brāhmī、tulasī、gokṣura、guḍūcī、kirātatikta、shatavari……
- 跨系经典：诃子（三系都有）、檀香、沉香、乳香、没药、胡椒、豆蔻、肉桂……
- 本草纲目：甘草、党参、灵芝、茯苓类……

## 图像来源优先级（不变）

1. Wikimedia Commons (CC-BY-SA / PD)
2. iNaturalist research-grade + CC-BY
3. Flora of China 1920s 之前的 PD 线图
4. 项目贡献者原创 CC-BY-SA 4.0 拍摄
5. **拒绝:** 任何商业图库、Google 图片搜索结果、Flora of China 2003+ 彩图

## OCR 扫描源 — Pan 需决定

OCR 骨架 `scripts/ocr_rgyud_bzhi_ch20.py` 已就绪，缺扫描源。候选（排序按**溯源可信度**）：

1. **Men-Tsee-Khang 1982 Dharamsala 木刻本复印** —— PD；Pan 若家中有书可扫；溯源最清
2. **Lhasa 1703 Zhol 木刻本** —— 若 BDRC 已数字化；需看许可
3. **内蒙古人民出版社 1982 简体版** —— 现代排印本，OCR 容易，但溯源弱；可作为对照

Pan 决定哪条优先 → 我这边装 tesseract-bod 或走图像 API。
