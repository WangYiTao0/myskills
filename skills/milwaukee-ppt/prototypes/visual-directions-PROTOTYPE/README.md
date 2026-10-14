# PROTOTYPE，用完即弃：汇报 PPT 的三个视觉方向

不是正式代码。选定方向后按下文「落进生成器」开票重做，本目录整个删掉。

## 问题

用户觉得生成的汇报 PPT「很普通」。看基线（`out/overview-0.png`）：

- 底部红条（`Caption Bar`，月报模板复刻，约 1.2" 高、只放一行 14pt 白字）是每页最抢眼的东西，但它只装一句结论；
- process / team 卡片矮（约 2"），说明 14pt 灰字，内容浮在正文区上半，下面大片空白；process 说明折行难看；
- table 14pt 小字贴正文区上沿，行少时不放大、不居中；
- 全篇没有视觉锚点（没有图标、图形）。

## 怎么看

- 一条命令重跑全部：`python3 skills/milwaukee-ppt/prototypes/visual-directions-PROTOTYPE/make_variants.py`
  （正式生成器出基线 `out/deck-0.pptx` → 按形状名删掉正文形状、用 python-pptx 重画出 `deck-A/B/C.pptx` → soffice + pdftoppm 转 `out/<方向>/slide-N.png`（-r 80）→ 拼 `out/overview-<方向>.png`（第 2–7 页，2×3）→ 每份跑 `review_deck.py`，输出存 `out/review-<方向>.txt`）
- 双击 `index.html`，底部浮动条切换 `?variant=0|A|B|C`。
- 素材 `deck.md` 原样复制自主会话工作区 `docs/trials/2026-10-14-ppt-workflow/deck.md`（6 页正文：stats-side、process、timeline、stats、team、table），未改内容。

三个方向都守：模板 banner 不变；主标题 / 副标题仍在占位框 idx 0 / 10；正文区只用 DB011C 一个红；形状名沿用 `references/layouts.md` 的约定（新增的见下）。

## 三个方向各改了什么

| | A 保留红条，内容撑满 | B 薄结论条 | C 结论前置（lead） |
| --- | --- | --- | --- |
| 结论放哪 | 月报红条原样（`add_caption_bar`） | 底部 0.42" 细红条，一行 14pt 白字；结论加粗，Next 用「 ｜ 」接在同一行 | 标题下正文区顶部 lead：22pt 黑粗字 + 左侧 0.08" 红短竖线（`Lead` / `Lead Accent`）；底部不画红条；Next 放页底一行（`Next Rule` / `Next Line`，黑粗字） |
| 正文区 | 1.30–5.65" | 1.30–6.38"（多约 0.7"） | 2.05–6.95"（有 Next 时到 6.40"） |
| stats-side | 三卡撑满高度，数字 60pt，标签 20pt、说明 16pt 近黑；右侧要点 18pt | 同 A，数字 72pt | 同 B |
| process | 白卡撑满高度、顶部黑细条、`STEP n` 眉题、标题 24pt、说明 18pt 近黑、右下 96pt 浅灰大编号水印，卡间灰色 chevron 箭头 | 同 A（卡更高） | 不画卡：1.1" 黑底白字编号圆 + 灰色连接线，标题 24pt / 说明 18pt 居中在圆下 |
| timeline | 只放大字号（日期 14、标题 20/22、说明 16），整体垂直居中 | 同 A | 同 A，图例下移让开 lead |
| stats | 数字 72pt，标签 20pt、说明 16pt，解读 16pt 近黑，口径贴底 | 数字 88pt | 数字 88pt |
| team | 卡片 3.0" 高、垂直居中，顶部黑细条，姓名 28pt、角色 18pt、职责 18pt 近黑 | 卡片 3.4" | 不画卡：1.4" 黑底白字的姓名首字圆形头像，下面姓名 / 角色 / 短线 / 职责居中 |
| table | 18pt，按字号重算行高，整表在正文区垂直居中，`Table Key Bar` 跟着 ! 行 | 20pt | 18pt |
| banner 外红色面积（约） | 红条 12.99×1.2" ≈ 每页 15.6% | 细条 12.99×0.42" ≈ 5.5% | lead 竖线 ≈ 0.04% |

新增形状名：`Process Strip N`、`Process Mark N`、`Process Text N`、`Process Arrow N`（A/B）；`Process Title N`、`Process Desc N`、`Process Line N`（C）；`Member Strip N`（A/B）、`Member Avatar N`（C）；`Lead`、`Lead Accent`、`Next Rule`、`Next Line`（C）。

观察：

- A 解决了「空」，但红条仍是每页最重的元素，而且红条里那句结论反倒是字最小（14pt）的一行——视觉重心和信息重心错位没变。process 卡 4" 高、文字只占上半，靠水印撑；内容少时这招有限。
- B 红条退成「页脚注」，大数字成了主角；但 process / team 卡更高，空的问题比 A 更明显（卡片只是被拉长，信息量没变）。
- C 读序变成「banner 标题 → 黑粗 lead → 证据」，符合 SKILL.md §4 三层标题；编号圆和首字头像给了每页一个图形锚点，红色只剩重点数字和 lead 竖线，最贴 §6.3「红色做选择不做平铺」。代价：lead 和副标题（action title）常常意思接近，要靠写法区分（§4 本就要求 lead「重申结论 + 加数据支撑」）；去掉底部红条后和月报的视觉统一感变弱。

## 审核结果（`review_deck.py deck.md deck-<方向>.pptx`）

四份（0 / A / B / C）都是 `REVIEW OK`。这本身就是信息：

1. **真伪检查没拦住后处理稿**。审核只核对页数、标题占位框等，按形状名删光正文重画的稿子照样过——如果「不要自己写代码画幻灯片」是要守的规则，真伪检查需要加指纹（例如比对各版式标记形状的几何 / 数量和生成器重新渲染的结果）。
2. **审核不查结论落在哪**。只查 md 里有没有结论（`check` 第 122 行附近），不查 pptx 里有没有 `Caption Bar`；C 整页没有红条也过。落 C 时要改成「结论在 `Caption Bar` 或 `Lead` 里出现」。
3. **重叠豁免靠名字**。B 的细条沿用 `Caption Bar` 名字，自动吃到 `OVERLAP_EXEMPT`；C 的 `Lead` / `Lead Accent`、`Next Line` 不重叠所以没报，但落地时要么进豁免、要么保证几何不交。A/B 的 `Process Mark N` 压在 `Process Card N` 上，靠「首词 + 编号相同」豁免通过——新形状名必须保持 `Process … N` / `Member … N` 的首词。
4. **没有红色面积检查**。B/C 降红、A 不降，审核都不知道；§6.3 的面积配额目前只能靠人看。

## 落进生成器时涉及什么

- 共用部件（`scripts/layouts/common.py`）：
  - B：`add_caption_bar` 加一个细条画法（或新 `add_caption_strip`），`add_page_chrome` 按模式选；`CAPTION_*` 常量是月报几何，不能动，细条另起常量。
  - C：新 `add_lead(slide, page)`（lead + 红竖线）和 `add_next_line`，`add_page_chrome` 改为画 lead；各版式的「正文区上沿」从常量 `IMG_TOP` 变成由 chrome 决定（有 lead 时下移约 0.75"），PDCA 图标 / Month Tag 的位置也要随之核对。
  - 都需要：「正文区上下沿」从各版式里的写死值收拢成一个 `content_box(page, mode)`，版式按它撑满、居中——这是 A/B/C 共同的前提，单独做就能解决「浮在上半」。
- 版式（`scripts/layouts/`）：`process.py`（卡片高度 = 可用高度、说明字号、箭头 / 水印或编号圆 + 连接线）、`team.py`（卡片高度、字号、头像）、`table.py`（字号随行数放大、垂直居中；`row_height` / `MAX_CELL_LINES` 的估算跟着字号走）、`stats.py` / `stats_side.py`（`NUMBER_PT` 上调、说明色改近黑）、`timeline.py`（字号）。
- 文档：`references/layouts.md` 的字号定稿值和「形状命名约定」表、SKILL.md §5 Page 2 / §6.3（C 改了「底部红条」的约定，§6.3 面积表里「底部红条不计入配额」一句要改）、`scripts/README.md`。
- 审核：见上一节 1–4。
- 测试：`tests/` 里断言字号、几何、`Caption Bar` 存在的用例要跟着改。

## 对月报逐字节回归（`MONTHLY_SHA`）的影响

`tests/test_generate.py` 的月报样例三页都没写 `Layout:`，全是 evidence 版式，靠 `add_caption_bar` 画红条。

- A：只改 process / team / table / stats / stats-side 和 timeline 的内部几何与字号，红条不动、evidence 不动 → `MONTHLY_SHA` 不变。
- B / C：动的是共用的 `add_page_chrome` / `add_caption_bar`，月报 evidence 页也会走到 → 直接破坏 `MONTHLY_SHA`。可选方案：
  1. **只在通用模式生效**（推荐）：`add_page_chrome` 按 `is_monthly(meta)` 分支，月报模式继续用原红条，通用 / 项目汇报模式用细条或 lead。`Context` 加一个 mode 字段即可，SHA 不变，代价是两种模式的结论样式不同（月报本来就是复刻历史模板，可以接受）。
  2. frontmatter 加开关（如 `conclusion: bar | strip | lead`），默认值按模式取，月报默认 bar。比 1 灵活，但多一个要文档化、要审核的字段。
  3. 接受重算 SHA：等于宣布月报样式改版，需要用户明确同意，不建议。

## 推荐

C，叠加 A 的「撑满 + 放大」（作为所有方向的共同前提，按 `content_box` 实现），只在通用 / 项目汇报模式生效，月报保持原红条。理由见上文「观察」：C 是唯一同时解决「红条抢眼」「没有锚点」「结论字最小」三件事的方向，且最贴 SKILL.md §4 / §6.3；B 是保守折中，如果用户舍不得底部红条的「月报感」可选 B。
