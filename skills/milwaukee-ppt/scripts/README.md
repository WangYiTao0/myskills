# 生成器代码约定（给版式票的实现者）

- 三层：`mdparse.py` 只切页并取通用字段（`#` `##` `Layout:` `Tag:` `Next:`），其余正文行去掉首尾空白后放进 `page.lines`，行首缩进宽度放进一一对应的 `page.indents`（空格算 1，tab 算 4，空行 0）；`layouts/<版式>.py` 解析本版式字段并渲染；`generate_ppt.py` 装配封面 / 各页 / 收尾。
- 每个版式一个模块：`layouts/evidence.py`、`before_after.py`、`process.py`、`stats.py`、`stats_side.py`、`timeline.py`、`timeline_phase.py`、`image_text.py`，接口相同：`NAME`、`LAYOUT_INDEX`、`parse(page)`、`render(prs, page, ctx) -> slide`。
- `parse(page)` 读 `page.lines`（空行为 `""`），写 `page.fields`，把红条结论行追加到 `page.conclusion`；文稿有错抛 `DeckError`，信息里带 `页「{page.title}」`。
- `render` 用 `prs.slide_layouts[LAYOUT_INDEX]` 建页，`fill_titles` 填 idx 0/10，按 idx 取槽位画内容（槽位只用来定位的就 `take_slot` 取矩形并删掉占位框），最后调 `add_page_chrome(slide, page, ctx)` 画 Tag 和底部红条。
- 共用部件只放 `layouts/common.py`，版式模块之间不互相 import：
  - 页面：`warn`、`load_image`、`fill_titles`、`add_page_chrome`（Tag + 底部红条）；
  - 形状：`slot` / `take_slot` / `remove_shape`（按 idx 取槽位、删形状）、`fit_picture`（矩形内等比放图）、`add_run`（Arial + 中文 PingFang SC 的 run）、`strip_theme_style`（去 p:style）；
  - 估算：`text_width_in` / `text_lines`（CJK 1em、拉丁 0.55em），溢出警告一律用它；
  - 常量：`BRAND_RED`、`LATIN_FONT`、`EA_FONT`。
  - 例外：底部红条的加高算法是月报固定样式，不改用 `text_lines`；stats 的卡片几何（大数字字号、标签 / 说明行数）用本版式的逐字宽表。
  - 缩进子列表：`sub_item(page, i)`——`page.lines[i]` 是缩进（≥1 列）的 `- ` / `* ` / `+ ` 行时返回去掉列表符号的文字，否则 `None`。不缩进的 `- ` 行仍是本版式的条目行。stats 类版式用它把卡片行下面的解读挂到上一张卡上：
    ```python
    for i, line in enumerate(page.lines):
        sub = sub_item(page, i)
        if sub is not None:      # 解读：挂到 items[-1]；前面没有卡片行时按版式规则报错
            ...
    ```
  - 数字 + 缩小单位：`split_number(value) -> (数值, 单位)`，数值部分是开头的 `$ + -`、数字、千分位逗号、小数点，后面全算单位（已去掉前导空白）；不以数值开头时返回 `(原串, "")`。`add_number(paragraph, value, pt, color, unit_pt=UNIT_PT, unit_color=UNIT_COLOR) -> (数字 run, 单位 run 或 None)` 在同一段里写两个 run：数值 `pt` 号加粗 `color` 色，单位 28pt 灰色 `6B6B6B` 不加粗（同一段 = 同一基线），单位前补一个空格，`%` 紧贴。估算宽度时用 `split_number` 分别量两段。
  - 时间线状态（只用于时间线类版式）：`parse_status(text, page, n)` 把一条的状态原文转成 `DONE` / `DOING` / `TODO`（即 `"done"` / `"doing"` / `"todo"`），认 完成 / 已完成 / 进行中 / 未完成 和 done / doing / todo，不区分大小写；空串返回 `None`，写错抛 `DeckError`（含页标题和第 n 条）。`parse_statuses(page, raws, required=False)` 处理一页：返回与 `raws` 等长的状态列表；整页都没写且 `required=False` 时返回 `None`（旧写法，照黑白灰画）；只写了一部分、`required=True` 却有条没写、“进行中”多于一个都抛 `DeckError`。
  - 状态色常量：`STATUS_COLORS = {DONE: DONE_GREEN "2E7D32", DOING: DOING_AMBER "F2A900", TODO: BRAND_RED}`，进行中上面的字用 `DOING_INK "1A1A1A"`，已完成上面的字 / 对勾用白色；未完成只做描边或空心，不实心填红。图例文字 `STATUS_LABELS`（已完成 / 进行中 / 未完成）。
  - 占位实现：`default_parse(page)`（列表、`> `、`口径：` / `Source:` 等结构化行进 `fields["raw"]`，其余进红条）和 `render_stub(prs, page, ctx, layout_index)`（只填标题 + 红条 / Tag，打印“未实现”警告）。`stats-side`、`timeline-phase` 实现后没有版式再用它们，可以删掉。
- 注册表在 `layouts/__init__.py`，已登记 8 个版式；`stats-side`（layout 5）和 `timeline-phase`（layout 6）目前是占位实现，由 spec #20 的版式票替换。
- 测试：每个版式一个 `tests/test_<版式>.py`，只走“md 进、pptx 出”；辅助函数（`generate`、`body_slide`、`pictures`、`shapes_named`、`run_style` 等）和模板槽位常量都在 `tests/deckcheck.py`，测试文件里不要再各写一份。`python3 tests/run_all.py` 跑全部。
  - 新增辅助：`runs(shape, para=0)` 返回一段里每个 run 的 `(文字, 字号, 粗体, 颜色)`，查单位拆分；`fill_color` / `line_color` 取形状纯色填充 / 描边 hex（没有为 `None`）；`geometry(shape)` 取预设几何名（`ellipse`、`diamond`、`homePlate`、`chevron`…）；`inside(shape, rect_in)` 判断形状落在英寸矩形内（如 `CONTENT_SLOT_IN`）；`slide_xmls(path)` 取各页 slide XML 字节，用于和改动前逐字节比较；`deck_error(r, title, *needles)` 判断报错退出且信息含页标题。常量 `STATUS_COLORS`、`DONE_GREEN`、`DOING_AMBER`、`DOING_INK`、`UNIT_PT`、`UNIT_COLOR`。
  - 共用部件本身由 `tests/test_common_parts.py` 测：`generate(md, probe=True)` 时额外注册测试专用版式 `_probe`（`tests/probe_layout.py`），不进正式注册表，版式票不用动它。
- 新增或修改一个版式时，通常只动 `layouts/<版式>.py` + `tests/test_<版式>.py`；需要新的共用部件时再动 `common.py` / `deckcheck.py`。

## 检查命令 `inspect_ppt.py`

生成后细调时用它定位元素：

```
python3 scripts/inspect_ppt.py deck.pptx
```

每页一个标题行 `== 第 N 页 | layout: <名>`，下面每个形状一行：`名字 | 类型 | L= T= W= H=（英寸，两位小数） | 文字前约 30 字`（换行替换成空格）。文件不存在或不是 pptx 时，错误信息写到 stderr，退出码非零。
