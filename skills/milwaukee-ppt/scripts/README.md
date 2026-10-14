# 生成器代码约定（给版式票的实现者）

- 三层：`mdparse.py` 只切页并取通用字段（`#` `##` `Layout:` `Tag:` `Next:`），其余正文行去掉首尾空白后放进 `page.lines`，行首缩进宽度放进一一对应的 `page.indents`（空格算 1，tab 算 4，空行 0）；`layouts/<版式>.py` 解析本版式字段并渲染；`generate_ppt.py` 装配封面 / 各页 / 收尾。
- 每个版式一个模块：`layouts/evidence.py`、`before_after.py`、`process.py`、`stats.py`、`stats_side.py`、`timeline.py`、`timeline_phase.py`、`image_text.py`、`section.py`、`agenda.py`，接口相同：`NAME`、`LAYOUT_INDEX`、`parse(page)`、`render(prs, page, ctx) -> slide`。
- `parse(page)` 读 `page.lines`（空行为 `""`），写 `page.fields`，把红条结论行追加到 `page.conclusion`；文稿有错抛 `DeckError`，信息里带 `页「{page.title}」`。
- `render` 用 `prs.slide_layouts[LAYOUT_INDEX]` 建页，`fill_titles` 填 idx 0/10，按 idx 取槽位画内容（槽位只用来定位的就 `take_slot` 取矩形并删掉占位框），最后调 `add_page_chrome(slide, page, ctx)` 画 Tag 和底部红条。
- 共用部件只放 `layouts/common.py`，版式模块之间不互相 import：
  - 页面：`warn`、`load_image`、`fill_titles`、`add_page_chrome`（Tag + 底部红条）；
  - 形状：`slot` / `take_slot` / `remove_shape`（按 idx 取槽位、删形状）、`fit_picture`（矩形内等比放图）、`add_run`（Arial + 中文 PingFang SC 的 run）、`strip_theme_style`（去 p:style）；
  - 画形状：`add_textbox(slide, name, x, y, w, h, anchor=TOP, wrap=True) -> text_frame`（起名、内边距 0）、`add_shape(slide, kind, name, x, y, w, h, fill, line=None, line_pt=None)`（扁平自选图形：去主题样式、关阴影，`fill` / `line` 为 None 即无填充 / 无描边）、`add_line(slide, name, x1, y1, x2, y2, color, pt, dash=None)`（直线）。坐标都是 EMU，可为浮点。版式模块不要再各写一份；需要额外属性（如 timeline 的线关阴影、stats-side 的卡片段落左对齐）就在返回的形状上再设。
  - 估算：`text_width_in` / `text_lines`（CJK 1em、拉丁 0.55em），溢出警告一律用它；
  - 常量：`BRAND_RED`、`LATIN_FONT`、`EA_FONT`。
  - 例外：底部红条的加高算法是月报固定样式，不改用 `text_lines`；stats 的卡片几何（大数字字号、标签 / 说明行数）用本版式的逐字宽表。stats-side 的大数字字号用通用口径（`number_width_in`）。两边口径不同是有意保留的：stats 的逐字宽表直接决定栏内形状尺寸，改成通用口径会改变已有文稿（含示例文稿）的输出；stats-side 只用估算判断要不要缩小，用通用口径即可。
  - 缩进子列表：`sub_item(page, i)`——`page.lines[i]` 是缩进（≥1 列）的 `- ` / `* ` / `+ ` 行时返回去掉列表符号的文字，否则 `None`。不缩进的 `- ` 行仍是本版式的条目行。stats 类版式用它把卡片行下面的解读挂到上一张卡上：
    ```python
    for i, line in enumerate(page.lines):
        sub = sub_item(page, i)
        if sub is not None:      # 解读：挂到 items[-1]；前面没有卡片行时按版式规则报错
            ...
    ```
  - 数字 + 缩小单位：`split_number(value) -> (前缀, 大数字, 单位)`，三段拼起来就是去掉首尾空白的原文，不补、不删空白。
    - 大数字：可带 `$ + -` 的数字（千分位逗号、小数点），连同后面的数量级后缀（`K M B k m b x X`，后面不能紧跟字母）、`+`、`/数字`，如 `12.3M`、`5x`、`1,000+`、`24/7`。
    - 单位：大数字后面以 `%` 或 CJK 字符开头的尾巴（`100%`、`120件`、`120 件`），或空白后接英文单词（`5 d`）；空白原样留在单位里。其他尾巴（如 `10Mbps`）并进大数字。
    - 前缀：数字前的 `约 ~ ～ ≈ ≥ ≤ > < ＞ ＜ ± +/-` 之一，连同其后的空白（`约 5 天` → `("约 ", "5", " 天")`）。
    - 不以（前缀 +）数字开头（`Q3`、`N/A`）→ `("", 原文, "")`。
    - `add_number(paragraph, value, pt, color, unit_pt=UNIT_PT, unit_color=UNIT_COLOR) -> (数字 run, 单位 run 或 None)` 在同一段里写最多三个 run：前缀和单位 28pt 灰色 `6B6B6B` 不加粗，大数字 `pt` 号加粗 `color` 色（同一段 = 同一基线）。估算宽度用 `number_width_in(value, pt, unit_pt=UNIT_PT, width=text_width_in)`，量宽函数可换成版式自己的。
  - 时间线状态（只用于时间线类版式）：`parse_status(text, page, n)` 把一条的状态原文转成 `DONE` / `DOING` / `TODO`（即 `"done"` / `"doing"` / `"todo"`），认 完成 / 已完成 / 进行中 / 未完成 和 done / doing / todo，不区分大小写；空串返回 `None`，写错抛 `DeckError`（含页标题和第 n 条）。`parse_statuses(page, raws, required=False)` 处理一页：返回与 `raws` 等长的状态列表；整页都没写且 `required=False` 时返回 `None`（旧写法，照黑白灰画）；只写了一部分、`required=True` 却有条没写、“进行中”多于一个都抛 `DeckError`。
  - 状态色常量：`STATUS_COLORS = {DONE: DONE_GREEN "2E7D32", DOING: DOING_AMBER "F2A900", TODO: BRAND_RED}`，进行中上面的字用 `DOING_INK "1A1A1A"`，已完成上面的字 / 对勾用白色；未完成只做描边或空心，不实心填红。图例文字 `STATUS_LABELS`（已完成 / 进行中 / 未完成）。
  - 条目行：`LIST_ITEM`（不缩进的 `- ` / `* ` / `+ ` 行）、`SOURCE_LINE`（`口径：` / `Source:` 行）；`key_mark(body, page) -> (是否重点, 去掉 ! 的正文)` 处理条目开头的 `!`：只认一个，`!` 后的空白一并去掉，写成 `!!` 抛 `DeckError`。四个用 `!` 的版式（stats、stats-side、timeline、timeline-phase）都走它。
  - 数据卡片（stats 类）：`parse_stat_card(page, line)` 把「- [!]标签 | 数字 | 一句说明」解析成 `{"label", "value", "note", "key"}`，不是列表行返回 `None`；三段不全、重点行漏写列表符号（`!标签 | …`）时报错。`check_stat_cards(page, items, lo, hi)` 查条数和最多一个 `!`。
  - 状态图例：`add_legend(slide, right, top, entries, text_pad=LEGEND_TEXT_PAD)`，`entries = [(图形占位宽英寸, draw(name, cx, cy), 文字)]`，一行右对齐；第 n 项图形叫 `Legend Icon n`、文字叫 `Legend Label n`，图形上另加的形状也带编号（`Legend Check 1`）。文字 `LEGEND_STYLE` 12pt 灰，第 4 项文字用 `KEY_LABEL`（关键里程碑）。
- 注册表在 `layouts/__init__.py`，已登记 10 个版式。
- 形状命名：每个画出来的形状都 `name = "<角色> N"`（N 从 1 起，与条目顺序一致），这是生成后细调时对 AI 的契约；各版式的名字列在 `references/layouts.md`「形状命名约定」，改名时同步改那一节。
- 测试：每个版式一个 `tests/test_<版式>.py`，只走“md 进、pptx 出”；辅助函数（`generate`、`body_slide`、`pictures`、`shapes_named`、`run_style` 等）和模板槽位常量都在 `tests/deckcheck.py`，测试文件里不要再各写一份。`python3 tests/run_all.py` 跑全部。
  - 新增辅助：`runs(shape, para=0)` 返回一段里每个 run 的 `(文字, 字号, 粗体, 颜色)`，查单位拆分；`fill_color` / `line_color` 取形状纯色填充 / 描边 hex（没有为 `None`）；`geometry(shape)` 取预设几何名（`ellipse`、`diamond`、`homePlate`、`chevron`…）；`inside(shape, rect_in)` 判断形状落在英寸矩形内（如 `CONTENT_SLOT_IN`）；`slide_xmls(path)` 取各页 slide XML 字节，用于和改动前逐字节比较；`deck_error(r, title, *needles)` 判断报错退出且信息含页标题。`review(md, pptx=None)` 跑审核脚本、返回 `CompletedProcess`；`registered_layouts()` 从未知版式的报错信息里读出注册表全部版式名（只走外部切入点）。`inside_shape(inner, outer)` 判断形状落在另一个形状里；`center_x` / `center_y` / `bottom` 取中心坐标和底边；`named(slide, name)` 取名字恰为 name 的全部形状，`one(slide, name)` 恰好一个时返回它。常量 `STATUS_COLORS`、`DONE_GREEN`、`DOING_AMBER`、`DOING_INK`、`UNIT_PT`、`UNIT_COLOR`。
  - 守逐字节：`test_generate.py` 的 `MONTHLY_SHA`（月报各页 slide XML，取自 master e282570）、`test_timeline.py` 的 `LEGACY_SHA`（不写状态也不写 `!` 的旧 timeline）。改共用部件后这两项不过，就是改动了月报或旧写法的输出。
  - 跨版式不变量：`test_title_invariant.py` 给注册表里每个版式各生成一页，断言主标题、副标题在 idx 0 / 10 占位框里、banner 区（0–1.0"）上没有另画的形状。新版式登记进注册表后会自动纳入，在它的 `SAMPLES` 里补一页最小示例即可（漏补时测试失败）。
  - `test_finetune_doc.py` 抽出 SKILL.md「生成后细调」的 python 示例实际跑一遍；改那段示例时保持它能照抄运行。
  - 共用部件本身由 `tests/test_common_parts.py` 测：`generate(md, probe=True)` 时额外注册测试专用版式 `_probe`（`tests/probe_layout.py`），不进正式注册表，版式票不用动它。
- 新增或修改一个版式时，通常只动 `layouts/<版式>.py` + `tests/test_<版式>.py`；需要新的共用部件时再动 `common.py` / `deckcheck.py`。

## 检查命令 `inspect_ppt.py`

生成后细调时用它定位元素：

```
python3 scripts/inspect_ppt.py deck.pptx
```

每页一个标题行 `== 第 N 页 | layout: <模板 layout 名> | 版式: <生成器版式名>`，下面每个形状一行：`名字 | 类型 | L= T= W= H=（英寸，两位小数） | 文字前约 30 字`（换行替换成空格）；占位框的类型写成 `PLACEHOLDER idx=N`。文件不存在或不是 pptx 时，错误信息写到 stderr，退出码非零。

生成器版式名不写进成稿：写进 slide（如 `cSld name`）会改动月报和旧 timeline 的逐字节输出。inspect 从模板 layout 推断：一个模板 layout 只对应一个版式时直接得出；共用模板 layout 的版式靠版式模块的 `MARK_SHAPE`（stats-side 的 `Side Card 1`、timeline-phase 的 `Phase Segment 1`、section 的 `Section Number`、agenda 的 `Agenda Number 1`）区分，没有该形状的算另一个（stats / timeline / evidence）。封面、收尾为 `-`。新增共用模板 layout 的版式时，给它定一个 `MARK_SHAPE`。

## 审核命令 `review_deck.py`

生成后机械审核，输入 md 文稿和生成的 pptx（pptx 可省略，只审文稿）：

```
python3 scripts/review_deck.py deck.md deck.pptx
```

- 输出：每条问题一行 `[规则] 位置：问题 → 怎么改`；全部通过时只打印一行 `REVIEW OK`，有问题时最后一行是 `REVIEW: N 条问题`。
- 只报告、不改文件。审完退出码总是 0（有问题也是 0）；文稿读不了（找不到、写错）或 pptx 打不开时退出码 1，错误写到 stderr。
- 和生成器共用 `mdparse` 与版式注册表：文稿按生成器同一套规则解析，生成器会报错的文稿审核也报错。
- 内容检查（只看文稿）：页数过多（> 10 页）、相邻两页版式相同、目录式副标题（不到 8 字或和主标题中文部分相同）、缺结论行（`NO_CONCLUSION` 里的版式不报，目前是按设计不放红条的 section、agenda）、章节和版式不配（TARGET / SCOPE 用 process / before-after，USE CASES 用 before-after）、内容重复（两页流程步骤名一半以上相同）、数字卡不是数字、数据缺失（`[数据缺失]` 占位）、用词（浮夸 / 空洞词表）、关键标记过多（时间线 3 个以上节点、超过一半标了 `!`）。
- 真伪检查（看 pptx，确认是生成器按当前文稿做的）：页数不符（封面 + 正文 + 收尾页）、不是生成脚本做的（正文页 idx 0 / 10 占位框里的文字和文稿的主标题、副标题不一致，或 banner 0–1.0" 上另画了文本框）。位置写成 `pptx 第 N 页（页「主标题」）`。
- 测试在 `tests/test_review.py`：正样本是生成器的正常输出（含示例文稿），负样本用 python-pptx 把正常输出改坏。新增规则时规则名放进 `[]`，测试按 `[规则]` 行首匹配。
