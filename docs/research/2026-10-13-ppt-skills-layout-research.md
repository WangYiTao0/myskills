# PPT skill 版式调研：5 个新版式怎么排

调研日期：2026-10-13。只调研，不实现；未改 `skills/` 和 pptx 模板。
约定：「事实」都带出处；「推断」明确标注；最后一节「对 milwaukee-ppt 的借鉴建议」是建议，不是来源里的事实。

## 0. 来源表

星数用 `gh api repos/<owner>/<repo>` 于 2026-10-13 查询。

| # | 名称 | 类型 | 热度依据 | 链接 / 路径 | 为什么选它 |
|---|------|------|----------|-------------|-----------|
| S1 | Anthropic 官方 `pptx` skill | 本机 skill + 网络项目 | anthropics/skills 180,762 星 | 本机插件缓存中的 `skills/pptx/SKILL.md`；上游 https://github.com/anthropics/skills/tree/main/skills/pptx | 官方；已核对上游 `SKILL.md` 与本机版本逐字一致（diff 为空，238 行），本机版本不过时 |
| S2 | MiniMax `pptx-generator`（PptxGenJS） | 网络项目（本机未找到该目录，改读上游） | MiniMax-AI/skills 13,692 星 | https://github.com/MiniMax-AI/skills/tree/main/skills/pptx-generator （`references/design-system.md`、`slide-types.md`、`pitfalls.md`、`SKILL.md`） | 用户点名；有完整数值化的字号/间距/圆角体系 |
| S3 | `html-ppt-skill`（lewislulu） | 网络项目（本机 skill 列表里有 html-ppt，但磁盘上未找到目录，改读上游） | 8,652 星（同名搜索结果里最高） | https://github.com/lewislulu/html-ppt-skill （`templates/single-page/*.html`、`assets/base.css`、`references/layouts.md`） | 有与本次 5 个版式一一对应的单页模板（kpi-grid、stat-highlight、process-steps、timeline、image-text-split） |
| S4 | Slidev 内置 layouts | 网络项目 | slidevjs/slidev 49,027 星 | https://github.com/slidevjs/slidev/tree/main/packages/client/layouts 、`packages/client/styles/layouts-base.css` | 开发者 markdown 幻灯片里最成熟的「用标记指定版式」机制，与我们的生成器输入形态最像 |

未深读、仅记热度（不作为事实来源）：reveal.js 72,416 星、Marp 12,635 星、PptxGenJS 6,268 星、python-pptx 3,556 星。

注意：S2/S3 是 px 或 10"×5.625" 画布（S2 `design-system.md` 的「Spacing Scale」注明基于 10"×5.625"），S3 画布 1920×1080 px（`assets/base.css`，`.deck` 宽高变量）。换算到 milwaukee 的 13.33"×7.5" 时按比例缩放属于推断。

---

## 1. 五个版式：来源里的做法

### 1.1 图 + 底部红条证据页（图 + 底部结论条）

没有任何来源有「底部结论条」这一专名版式，最接近的是「Image Showcase / Data Visualization」。

事实：
- S2 `slide-types.md` §4 Content Page：Image Showcase 为「标题 + 大图 + 下方 caption」；Data Visualization 必须带数据来源（Source）；字号 标题 36–44、正文 14–16、说明/来源 10–12；至少含一个非文字元素。
- S2 `design-system.md`「Spacing Scale」：页边距 0.4–0.6"，大块间距 0.5–0.8"（基于 10" 宽画布）。
- S3 `references/layouts.md`「Working with images」：图片框 `.img-frame` 自己管比例与裁切；截图、图表、logo 用 `.contain`（不裁切、留边），照片才用 cover；有 `.img-cap` 说明行。
- S1 `SKILL.md` L162：禁止「横贯页面宽度的页眉/页脚色条」，称其为 AI 填充感。（直接与本版式的底部红条冲突，见 §3。）
- S1 `SKILL.md` L146–148：最小边距 0.5"，内容块之间 0.3–0.5"。

### 1.2 流程页（3–5 步）

事实：
- S3 `templates/single-page/process-steps.html`：4 列等宽网格（`grid-template-columns:repeat(4,1fr)`，gap 22px），每步一张卡片；序号圆（48px 直径）骑在卡片上沿（`top:-24px`），标题 17px，说明 13px，行高 1.6，底部一个胶囊 tag（11px）。没有连接线，靠序号圆表达顺序。
- S2 `slide-types.md` §4 Timeline/Process：`[1] ──→ [2] ──→ [3] ──→ [4]`，节点下放步骤名；「Additional Layout Patterns」：编号步骤 + 箭头。
- S2 `slide-types.md` §2 TOC：3–5 项用纵向编号列表，4–6 项用双列网格，7+ 用多列；序号 28–36、标题 20–28、描述 14–16；描述「一行以内或省略」。
- S1 `SKILL.md` L118–121：Timeline or process flow（编号步骤、箭头）。

### 1.3 数据对比 / Key Results（Stat 墙、指标面板）

事实：
- S1 `SKILL.md` L119：大数字 60–72pt，下方小标签。
- S2 `design-system.md`「Typography Scale (PPT)」：Data Callout 60–96pt；说明 10–12；正文 14–16。
- S3 `kpi-grid.html`：4 个 KPI 一行（`.grid.g4`，gap 24px），卡片 = eyebrow 小标签（13px，字间距 .16em，大写）+ 56px/800 数字 + 一行涨跌说明；涨跌用语义色（good/warn），不是装饰色。
- S3 `stat-highlight.html`：整页只有一个数字，260px/900，负字距，下面一行 h3 + 一句 lede，居中；kicker 14px 大写强调色。
- S3 `assets/base.css`：`.card` 内边距 26px 28px、圆角 18px、1px 描边 + 轻阴影。
- S2 `slide-types.md` §4 Data Visualization：图 + 「Key Takeaway」要点并排，底部必须有 Source。
- S2 `slide-types.md` Cover §Key Principles：相邻文字层级的字号差至少 20% 以上，标题至少是副标题的 2–3 倍。

### 1.4 时间线页

事实：
- S3 `timeline.html`：5 列等分；一条 2px 水平线（`--border` 色）；节点圆 24px 直径、实心强调色、4px 底色描边 + 2px 强调色外圈；日期 14px 大写字间距 .12em 放线上方；标题 18px、说明 13px 放线下方；整体居中对齐。
- S2 `slide-types.md` §4 Timeline：编号节点 + 箭头，节点下放文字。
- 说明：本地 milwaukee 的 A7 已有同类做法（`references/layout-patterns.md` A7：主线 `#E5E5E5` + 圆点 + 上下交替标签），S3 是等分单侧，不交替。

### 1.5 左边单图 + 右边说明

事实：
- S3 `image-text-split.html`：两列 1fr/1fr，gap 56px；图框高度吃满、宽度随比例（默认 `--img-ratio:4/5`），保证任何比例的图都不会撑破页边距；文字区垂直居中；列表项 19px、颜色次要灰、行间 10px；`.flip` 可左右互换。
- S4 `layouts/image-right.vue`、`image-left.vue`：`grid grid-cols-2`（左右各占 50%），图以背景图铺满半边（`backgroundSize` 默认 `cover`）；文字半边继承默认 padding。S4 `docs/builtin/layouts.md` 列出 `image-left` / `image-right` 为内置版式，用 frontmatter `layout:` + `image:` 指定。
- S4 `layouts-base.css`：版式内边距 `px-14 py-10`（约 56px/40px），h1 `text-4xl`，h2 `text-3xl`，列表行高 1.8em。
- S1 `SKILL.md` L112–116：两栏（文字左、插图右）；半出血图 + 内容叠加。
- S2 `slide-types.md` §1 Cover：非对称左右布局「文字一侧、图在另一侧」。

---

## 2. 跨版式通用做法（来源事实）

### 间距系统
- S1 `SKILL.md` L146–148、L156：边距 ≥0.5"；块间 0.3–0.5"；「选定 0.3" 或 0.5" 并全程一致」。
- S2 `design-system.md`「Spacing Scale (PPT)」（10" 画布）：图标到文字 0.08–0.15"；列表项 0.15–0.25"；卡片内边距 0.2–0.4"；元素组间距 0.3–0.5"；页安全边距 0.4–0.6"；大块间距 0.5–0.8"。
- S2「Style Recipes」：圆角由 4 档（Sharp/Soft/Rounded/Pill）决定，数据密集用 Sharp（边距 0.3"，块间 0.25–0.35"），商务通用用 Soft（边距 0.4"，块间 0.35–0.5"）；规则：外层容器圆角 ≥ 内层元素圆角。
- S3 `base.css`：页内边距 72px 96px（1920×1080 画布，约 3.75%/5%）；网格 gap 24px；`.mt-s/m/l` = 8/18/32px。

### 字号阶梯
- S1 `SKILL.md` L137–142：标题 36–44；章节头 20–24；正文 14–16；说明 10–12（muted）。
- S2 `design-system.md`「Typography Scale (PPT)」：注释/来源 10–12；正文 14–16；副标题 18–22；标题 28–36；大标题 44–60；数据 60–96。
- S2 `slide-types.md`：正文左对齐，不居中；正文和说明不加粗，加粗只给标题（`design-system.md`「No Bold for Body Text」）。

### 只用一个强调色时怎么做层级
- S1 `SKILL.md` L87：一种颜色占 60–70% 视觉权重，1–2 个辅助色加一个锐利强调色，不要等权。
- S3 `kpi-grid.html`、`stat-highlight.html`：层级靠字号和字重（56px/800 vs 13px）与灰阶（`--text-1/2/3`），强调色只用于 kicker、序号圆、时间线节点。
- S2 `design-system.md`「Color Palette Rules」：只用给定色板，不得调亮度/饱和度/混色，唯一允许的变化是透明度；禁止渐变、禁止动画。

### 避免模板感 / AI 味
- S1 `SKILL.md` L152–163：不要每页同一版式；不要居中正文；不要标题下装饰线（「NEVER use accent lines under titles」）；不要装饰色条/边缘条纹（页眉页脚通栏条、侧边竖条、卡片单边描边）；要求用淡底色、阴影或图标来区分卡片；不要默认米色/奶油底。
- S2 `pitfalls.md`「Common Mistakes」：同样列出「不要标题下加线」「相邻页版式要变」「间距二选一」。
- S1 L110、L158：每页要有视觉元素，避免纯标题 + bullet。
- S1 L89：选一个母题并贯穿，但母题不能是色条。

### 生成后验收
- S1 `SKILL.md` L166–219：QA 必做。`markitdown` 导出文字查漏字/残留占位符（grep `lorem|TODO|xxx`）；`scripts/office/validate.py`（模板派生时加 `--original`）；用 `soffice.py` 转 PDF，再 `pdftoppm -r 150` 出 JPG 看图；首查文字溢出；其余：重叠、元素间距 <0.3"、边距 <0.5"、间距不均、对比度不足、模板装饰错位、多余占位。
- S1 L129–135：字体用 Arial/Calibri/Cambria 等「安全字体」，因为 LibreOffice 渲染缺字体会用宽度不同的替代字体，溢出检查会失真；非安全字体需留约 10% 余量。
- S1 L75：模板里有 4 个槽位而内容只有 3 项时，要整组删除第 4 组（图 + 文字），而不是只清空文字。
- S2 `pitfalls.md`「Verification Loop」：假设有问题，至少完成一轮「发现 → 修复 → 重新验证」才能宣告完成。
- S2 `pitfalls.md`：长标题用 `fit:"shrink"`。
- S1 L42：文本框要与形状/线对齐时，设 `margin:0`（文本框自带内边距）。
- S3 `SKILL.md`：提供 `scripts/render.sh` 无头 Chrome 出 PNG，用于看预览。

### Slidev 的「标记指定版式」机制（对生成器输入有参考价值）
- S4 `docs/builtin/layouts.md`：每页用 frontmatter `layout: <名>` 指定版式，参数用 frontmatter 键传入（如 `image:`、`class:`）；`two-cols` 用 `::right::` 分隔左右槽（`layouts/two-cols.vue` 头部注释）。版式本身只是「有命名槽位的网格」。

---

## 3. 对 milwaukee-ppt 的借鉴建议（建议；以下为推断，不是来源事实）

本地约束依据：`skills/milwaukee-ppt/SKILL.md` §5.0（标题/副标题必须填模板 placeholder，banner 0–1.0" 在母版里）、§6.2（色板）、§6.3（红色纪律，banner 外红色 ≤5%，月报底部红条豁免）、§6.4（lead 锚点条 0.25"×0.06"、stat 60–80pt）。

1. 间距：借 S1/S2 的「二选一并全程一致」。建议新增版式统一一个块间距（如 0.4"）和一个边距（如 0.5"），做成生成器常量。适配：与 13.33" 宽画布不冲突；S2 的 0.4–0.6" 是 10" 画布数值，13.33" 下取 0.5" 属推断。banner 占顶部 1.0"，所以内容区从 1.0" 以下再留 0.3–0.5" 起算（推断）。
2. 字号阶梯：沿用 §6.4 现有（stat 60–80pt、label 14pt、描述 11pt、lead 16pt），不必采用 S1/S2 的 36–44pt 标题，因为标题在 banner placeholder 里。冲突点：S1/S2 正文 14–16pt，而 milwaukee 描述 11pt，偏小；建议新版式描述不低于 12pt（S1/S2 说明字号下限为 10–12pt，推断此为投影可读下限）。
3. 层级用字号/灰阶而不是颜色：直接借 S3 kpi-grid 做法，与 §6.3「多 stat 并列只让 1 个用红，其余深灰」天然一致。适配度高。
4. 数据墙（版式 3）：借 S3 kpi-grid 的「eyebrow 小标签 + 大数字 + 一行说明」卡片，3–4 列等分；单一超大数字页借 S3 stat-highlight（但 260px 在 13.33" 画布约合 120pt 以上，超出 §6.4 的 60–80pt，若采用需先改规范，冲突点）。涨跌色（S3 good/warn）会引入绿/橙，与 §6.2 撞色判断冲突，建议不用，改用深灰/红二选一。
5. 流程页（版式 2）：借 S3 process-steps 的等分卡片 + 序号圆，不必画箭头；与 §6.4 icon row（0.5" 圆形序号）一致。连接线若需要，用 `#E5E5E5` 细线，A11 已有「圆形/方形节点 + 细线连接，禁 SmartArt」。S2 的箭头链亦可。步数 3–5 与 S2 TOC 的 3–5 项纵列/卡片建议一致。
6. 时间线（版式 4）：借 S3 timeline 的等分单侧（日期在线上、标题说明在线下）；主线 `#E5E5E5`，节点灰、仅关键节点红，这是 A7 已有规则，S3 的「实心强调色圆点 + 外圈」每个点都着色，与红色纪律冲突，不照搬。
7. 左图右说明（版式 5）：借 S3 的「框比例固定、图 `contain` 或 cover 二选一」：截图用 contain（留白边），照片用 cover；借 S4 的 50/50 网格思路，但建议图略大（如 55–60%，推断）以证据优先。A10 系统截图页已有「大截图 + 侧栏」做法，可作为同一版式的变体。
8. 图 + 底部红条（版式 1）：冲突点。S1 L162 把「通栏页脚色条」列为 AI 感标志，而 milwaukee 月报明确要求底部红条（SKILL.md §5 Page 3，§6.3 豁免）。建议：保留红条（品牌规范优先），但降低 AI 感——只放「结论一句 + Next 一句」两条信息，条高保持克制（如 0.5–0.6"，推断），文字白色、对齐正文左边距，且不再叠加标题下划线、侧边竖条等其它色条。S1 的「淡底色/图标代替条纹」可用于正文区卡片，不用红色边。
9. 避免 AI 味：直接采用 S1/S2 共有的几条：不加标题下装饰线（但 §6.4 的 lead 红色锚点条 0.25"×0.06" 在形态上接近「装饰短线」，属潜在冲突点，需用户决定保留）；相邻页版式要变；正文左对齐；卡片区分用淡底 `#F5F5F5` + 细描边 `#E5E5E5`，不用单边色条（A3/A6 里「红竖条」类做法同样有此风险）。
10. 模板与 placeholder：借 S4 的「版式 = 带命名槽位的网格」。每个新 layout 在模板中预建 placeholder（标题 idx 0、副标题 idx 10、各槽位新 idx），生成器只填槽、不新建文本框，与 §5.0 一致。Markdown 标记用类似 Slidev frontmatter 的 `layout: <名>` 即可（推断）。
11. 验收：照搬 S1 的三步：`markitdown` 查文字 + grep 残留占位符 → `validate.py --original MS_Template.pptx` → soffice 转 PDF + pdftoppm 看图。要点：模板槽位多于内容时整组删除（S1 L75）；溢出检查需用安全字体，否则渲染预览失真（S1 L129–135）——milwaukee 模板字体需确认是否为 Arial/Calibri 等（本次未核对）。S2 的「至少一轮发现-修复-重验」可写进生成器流程。
12. 不借鉴：S2 的 18 套色板与四档圆角体系（§6.2 色板唯一）；S3/S4 的动画、渐变文字（S2 与 §6 均禁渐变、动画）；S3 的 24 主题。

## 4. 局限
- S2/S3 的 skill 目录在本机磁盘上未找到（find 超时未命中），故改读上游 GitHub；是否与用户已安装版本一致未核对。
- S2 的 `design-system.md` 数值基于 10"×5.625" 画布，S3 基于 1920×1080 px，换算为 13.33"×7.5" 的建议值是推断。
- S1–S4 都没有「底部结论条」「Key Results 左红框列表」这类版式的专门说明，对应建议属推断。
- 未深读 reveal.js、Marp 主题；按范围要求只取了 4 个最有代表性来源。
