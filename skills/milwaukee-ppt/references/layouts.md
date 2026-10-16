# 生成器版式参考

把文稿整理成生成器能读的 md 时读本文件（总览）和用到的版式文件 `layouts/<版式名>.md`：每个版式怎么写、什么时候选、什么时候别选、生成器会报什么错和警告。本文件放文稿格式、报错与警告总表、各版式共用的排版（正文区 / lead / Next 几何、共用字号）、「选版速查」、形状命名约定与审核的几何豁免；各版式的字段写法、画法、容量、反例、警告和本版式的字号行、形状名在 `layouts/` 下各自的文件里（清单见「各版式文件」）。完整示例见 `examples/demo/deck.md`（12 种版式齐全：Agenda 目录 + 3 张隔断页 + 其余各一页；各版式写法见对应的版式文件）。生成后要按形状改细节时，形状名见文末「形状命名约定」。Before/After 的槽位几何与事实对比验收另见 `before-after.md`。

## 文稿格式

下面的代码块可以照抄生成（代码块里不能写行尾注释，生成器会把它当成内容），各行的含义写在块后。

```markdown
---
title: 工具借还线上化 项目汇报
subtitle: 示例文稿 · 虚构数据
author: 示例改进小组
date: 13 Oct 2026
closing: Thank You
report: project
---

# 项目背景 / BACKGROUND
## 纸质登记让借还记录难以追溯
Layout: evidence
Tag: Oct
PDCA: P
![](img/paper-log.png)
抽查 3 个月的登记本，约三成借出记录没有归还登记
Next: 10 月底前完成全部工具贴码
```

- frontmatter：写了 `title` = 通用模式；`subtitle`、`author`、`date`、`closing` 都可选。`date` 里的 4 位年份用于给 Tag 补年份；不写 `closing` 就没有收尾页。
- `report: project` 可选 = 项目汇报模式（只在用户明确说"这是一个项目的完整汇报"时写，规则见 SKILL.md「适用范围」B 类）；不是项目汇报就整行不写。`report` 只认 `project`，写别的值报错。
- `# ` 是主标题（banner 右上，填 idx 0），`## ` 是 action title（填 idx 10）。
- `Layout:` 选版式，不写 = evidence，不区分大小写。
- `Tag:` 可选，正文区右上角灰字；没写年份时补上文稿年份。
- `PDCA:` 可选，只在项目汇报模式下用：`P` / `D` / `C` / `A`，组合用 `/`（`PDCA: D/C`），不区分大小写；所有版式都支持。生成器在 banner 下沿和正文区上沿之间（1.02–1.30"）插 0.28" 见方的 PDCA 图标（`assets/pdca/` 的 PNG），右缘贴正文区右缘，组合按写的顺序从左到右排；不压任何版式的内容。同页写了 `Tag:` 时月份标识让到图标左侧、和图标纵向居中对齐。不写 `PDCA:` 的页没有图标。生成器只管画，不检查章节顺序和每节写没写 PDCA（交给审核，规则见 `scripts/README.md`「审核命令」）。
- 版式字段（上例是 evidence 的图）见各版式文件 `layouts/<版式名>.md`。
- 普通文字行是一句话结论。通用模式和项目汇报模式下画成标题下的 lead（见「共用排版」）；月报模式进底部红条。
- `Next:` 可选，写已确定的下一步；写成「下一步：」时页底 Next 行 / 红条也显示「下一步」。
- 各版式文件里说的「结论」「进红条」按模式理解：通用 / 项目模式是 lead + 页底 Next 行，月报模式是底部红条；md 写法两种模式一样。
- 每个 `# ` 开一页；第一个 `# ` 之前的内容和 `<!-- -->` 注释都会被忽略。
- 封面：主标题 = title；副标题第一行 subtitle，第二行「date   author」，空的省略。
- 月报模式：frontmatter 不写 title、写 `month: YYYY-MM` + `author`（`date` 可选）。封面固定为「<Mon>. YYYY Working Summary」，结尾固定加 Thank You，Tag 年份取 month。旧月报 md 不用改。
- 图片写 `![](路径)`：相对路径（相对文稿所在目录）、绝对路径、http(s) URL 都行。URL 下载后缓存在 `~/.cache/milwaukee-ppt/url-images`（环境变量 `MILWAUKEE_PPT_CACHE` 可改），之后离线也能重复生成。
- 输出：`-o` 指定；不指定时通用模式为 `<title>.pptx`，月报模式为 `Monthly Working Summary_<author>_<Mon>_<YYYY>.pptx`，都放在文稿所在目录。

## 报错与警告

**报错**：以非零退出，不留半坏的文件。出在某一页的错误（版式名、条目、图片），信息里带 `页「标题」`；整份文稿的错误（输入文件找不到、frontmatter、没有任何页、输出路径）不带页标题。

- frontmatter 缺必填项（通用模式缺 title；月报模式缺 month / author，或 month 不是 YYYY-MM）
- frontmatter 的 `report` 写了 `project` 以外的值
- 没写 `report: project` 却写了 `PDCA:`；`PDCA:` 的字母不是 P / D / C / A，或有重复（带页标题）
- 文稿里没有任何 `# ` 页
- `Layout:` 写了未知名字
- 条目数超出该版式范围，或条目格式不对（各版式文件里列出）
- 时间线状态写错、只写了一部分、“进行中”多于一个（见 `layouts/timeline.md`）
- 图片不存在、URL 下载失败

**警告**：打印 `警告: …` 到 stderr，照常生成。看到警告就去 PNG 里看对应那页，按提示精简文字。

- 结论（lead）估计超过两行（通用 / 项目模式；正文区会被压低）
- 流程说明折行难看（通用 / 项目模式）：说明超过两行，或末行只剩 2 个字以内；审核同样报「流程说明折行」
- 团队职责折行难看（通用 / 项目模式）：职责超过 3 行，或末行只剩 2 个字以内；审核同样报「团队职责折行」
- 文字估计溢出：红条（月报模式）、流程卡片 / 流程步骤名和说明、数据页的解读 / 卡片文字 / 结论要点 / 口径、时间线列、阶段条、Before/After 的短文、caption（超过一行）、lead（超过一行）
- 数据页大数字放不下，整页统一缩小
- 图多于版式能用的张数（多出的不用）、image-text 要点超过 5 条

## 共用排版（各版式统一，生成器写死）

内容区（正文区）在 banner（0–1.0"）以下，左右边距 0.56"（宽 12.20"）；上下沿随模式变（生成器 `common.body_area` 统一算，各版式都排在里面）：

- 月报模式：上沿 1.30"，下沿 5.60"（下面留给底部红条）。
- 通用 / 项目模式（方向 C）：上沿在 lead 下方 0.19"（lead 一行时 2.05"；没有结论时 1.30"），下沿 6.95"；写了 `Next:` 时在 Next 细线上方 0.10"（Next 一行时 6.40"）。
- section、agenda 不画 lead，正文区按月报口径（1.30–5.60"）居中，两种模式一样。

块间距统一 0.3"，卡片内边距 0.2"。

下表是跨版式共用的字号行；只属于某一版式的字号行（如 stats / stats-side / 时间线 / 表格 / 流程 / 团队的通用 / 项目模式字号、流程序号圆）在该版式文件的「字号」一节。

| 用途 | 字号与样式（Arial；中文 PingFang SC） |
| --- | --- |
| 数据大数字（月报模式） | 60pt bold，重点那个 #DB011C，其余 #1A1A1A；单位（件、%、秒…）自动拆出，28pt #6B6B6B 不加粗、同一基线 |
| 数据标签（月报模式） | 16pt bold #1A1A1A |
| 条目标题（月报模式） | 18pt bold #1A1A1A（时间线普通节点 16pt） |
| 正文 / 要点（月报模式） | 16pt #1A1A1A（stats 的解读 14pt） |
| 说明（月报模式） | 14pt #6B6B6B |
| 日期 / 口径 / 图例 | 12pt #6B6B6B，日期加粗（全套最小字号；通用 / 项目模式的时间线日期见 `layouts/timeline.md`「字号」） |
| 底部红条（月报模式） | 14pt 白字 |
| lead（通用 / 项目模式） | 22pt bold #1A1A1A |
| Next 行（通用 / 项目模式） | 16pt bold #1A1A1A |

**lead 和 Next 行**（通用 / 项目模式各版式共用，section / agenda 除外）：lead 是本页结论，在标题下 1.30" 起，左缘 0.80"，一行框高 0.56"（每多一行加 0.38"），垂直居中；左侧 `Lead Accent` 红竖线 0.08" 宽，比 lead 框上下各短 0.06"。写了 Tag 时 lead 右端让到月份标识框左侧 0.1"（PDCA 图标在 1.30" 以上，不用让）。Next 行在页底，下沿 6.94"，一行框高 0.36"，上方 0.08" 处一条 0.75pt #BFBFBF 细线（`Next Rule`），左右和正文区一样宽。

**底部红条**（月报模式各版式共用）：月报模板固定样式——品牌红底、0.75pt 黑描边、白字 ❖ 项目符号、行距 150%。底边固定在 7.08"，最低 1.2" 高；文字多时向上加高，最高顶到 5.60"（内容区下沿），再多就警告。结论一行、Next 一行最合适。

**红色**：banner 以外只有这几处用品牌红——lead 竖线（月报为底部红条）、数据页标了 `!` 的那条（数字 + stats 的顶线 / stats-side 的竖条）、Before/After 的 AFTER 标题。流程序号圆（月报）和编号圆（通用 / 项目模式）一律黑白灰。时间线类版式写了状态时用状态色（SKILL.md §6.3「时间线状态色」例外）：已完成 #2E7D32、进行中 #F2A900（上面的字 #1A1A1A）、未完成用品牌红但只描边或空心；不写状态的时间线仍是黑白灰。

## 各版式文件

每种版式一份文件，写该版式的字段写法、画法、容量、适用与反例、报错与警告、审核说明，以及本版式专属的字号行和形状名：

- `layouts/evidence.md`：evidence（默认）· 证据页
- `layouts/before-after.md`：before-after · 改前改后对比
- `layouts/process.md`：process · 流程
- `layouts/stats.md`：stats · 数据对比 / Key Results
- `layouts/stats-side.md`：stats-side · 左数字右结论
- `layouts/timeline.md`：timeline · 时间线
- `layouts/timeline-phase.md`：timeline-phase · 阶段条
- `layouts/image-text.md`：image-text · 左图右文
- `layouts/agenda.md`：agenda · Agenda 目录页
- `layouts/team.md`：team · 团队页
- `layouts/table.md`：table · 表格页
- `layouts/section.md`：section · 隔断页

## 选版速查

用户没有提供图片时，不选 `evidence`、`image-text`（这两种必须配图）；`before-after` 两侧都写短文，不放图。只在手上有对应图片时才选这两种。这条和 ppt-grill「素材清单为"无"」的选版规则一致。

| 内容 | 版式 |
| --- | --- |
| 一个工作项的截图 / 实物证据 | evidence |
| 同一件事改前、改后 | before-after |
| 3–5 个有先后的步骤 | process |
| 2–4 个结果数字，每个数字跟几条解读 | stats |
| 2–3 个数字 + 一组结论，结论比数字重要 | stats-side |
| 3–6 个时间节点（带状态时看得出进度） | timeline |
| 3–6 个前后衔接的阶段，强调推进到哪一段 | timeline-phase |
| 一张图 + 几条解释 | image-text |
| 开场列出本次汇报的 3–8 个章节 | agenda |
| 章节之间的过渡（编号 + 章节名） | section |
| 2–8 个成员的角色和分工 | team |
| 同一组对象在几个维度上的对比（≤8 行 × ≤6 列） | table |
| 都不匹配（Agenda 八宫格等） | 生成器没有对应版式；先用最接近的生成，再在 PowerPoint 里按 SKILL.md §6 和 `layout-patterns.md` 手工调整 |

## 形状命名约定

生成器给每个画出来的形状起固定的名字，生成后细调时按名字找元素（流程见 SKILL.md「生成后细调」）。`python3 scripts/inspect_ppt.py <输出.pptx>` 每页先给一行 `== 第 N 页 | layout: <模板 layout> | 版式: <生成器版式>`，再列出每个形状的名字、类型（占位框带 `idx=N`）、位置（英寸）和文字开头。

- 编号 N 从 1 起，和文稿里条目的顺序一致（左到右、上到下）。
- 名字是对 AI 的契约：版式改画法时，名字不变或同步改本节 / 该版式文件的「形状名」。
- 下表只列各版式共用的形状；各版式自己的形状名在 `layouts/<版式名>.md` 的「形状名」一节（evidence、before-after、image-text 没有专属形状名行）。
- 主标题、action title 是模板占位框，名字由 PowerPoint 决定，按 idx 0 / 10 找（`slide.placeholders[idx]`），不按名字找；inspect 输出里占位框的类型写成 `PLACEHOLDER idx=N`。

| 范围 | 形状名 |
| --- | --- |
| 各版式共用 | `Caption Bar`（底部红条，月报模式）、`Lead`（结论 lead，通用 / 项目模式）、`Lead Accent`（lead 左侧红竖线）、`Next Rule`（页底 Next 行上方细线）、`Next Line`（页底 Next 行）、`Month Tag`（`Tag:` 月份标识）、`PDCA Icon N`（`PDCA:` 图标，图片形状，N 按文稿里字母的顺序从左到右） |

其他版式的形状名（如 before-after 月报模式的 `Lead`）以 `inspect_ppt.py` 的输出为准。

### 审核的几何豁免

`scripts/review_deck.py` 的几何检查按上面和各版式文件「形状名」里的形状名判断哪些叠放是有意的。改形状名时同步这里、对应版式文件和 `review_deck.py` 的 `OVERLAP_EXEMPT` / `OVERLAP_PAIRS` / `OVERLAP_TWINS`。

- 重叠不报：
  - 模板占位框（主标题、action title、各版式槽位，包括被图片盖住的 Before/After 13 / 14）；
  - `Caption Bar`（叠在最上层）、`Month Tag`（框比字大，下沿伸进内容区 0.12"；有 PDCA 图标时框让到图标左侧，不和图标相压）；
  - 同一组件：名字第一个词相同、编号 N 相同，如 `Process Card 2` 和 `Process Number 2`、`Process Mark 2` 和 `Process Title 2` / `Process Desc 2` / `Process Line 2`、`Side Card 1` 和 `Side Number 1`、`Member Card 4` 和 `Member Duty 4`、`Member Avatar 4` 和 `Member Name 4`、`Milestone Node 3` 和 `Milestone Check 3`、`Legend Icon 1` 和 `Legend Check 1`；
  - `Current Ring` 和 `Milestone …`（外圈套在进行中节点上）；
  - `Lead` 和 `Lead Accent`、`Next Rule` 和 `Next Line`（两两豁免；它们和正文形状相压照样报）。
- 原生表格（table 的 `Data Table`）整张算一个形状，出界、重叠照常按外框查；单元格不另加豁免。文字溢出按单元格估算（同文本框口径：字宽 `text_width_in`、行高字号 × 1.2），某行估计高过行高才报。
- 错位只比同类形状：名字去掉末尾编号后相同（如 `Process Card 1–4`、`Process Mark 1–4`、`Side Card 1–3`；占位框不比）。同一行比上沿 / 中线 / 下沿，同一列比左沿 / 中线 / 右沿，有一条对齐（差不到半像素）就算对齐；都没对齐且最近的差值小于 5 像素时报告。大小不同、中线对齐的节点（关键里程碑、进行中）不算错位。
