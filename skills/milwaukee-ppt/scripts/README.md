# 生成器代码约定（给版式票的实现者）

- 三层：`mdparse.py` 只切页并取通用字段（`#` `##` `Layout:` `Tag:` `PDCA:` `Next:`；`PDCA:` 解析成 `page.pdca`，如 `["D", "C"]`，frontmatter 没写 `report: project` 时报错），其余正文行去掉首尾空白后放进 `page.lines`，行首缩进宽度放进一一对应的 `page.indents`（空格算 1，tab 算 4，空行 0）；`layouts/<版式>.py` 解析本版式字段并渲染；`generate_ppt.py` 装配封面 / 各页 / 收尾。
- 每个版式一个模块：`layouts/evidence.py`、`before_after.py`、`process.py`、`stats.py`、`stats_side.py`、`timeline.py`、`timeline_phase.py`、`image_text.py`、`section.py`、`agenda.py`、`team.py`、`table.py`，接口相同：`NAME`、`LAYOUT_INDEX`、`parse(page)`、`render(prs, page, ctx) -> slide`。
- `parse(page)` 读 `page.lines`（空行为 `""`），写 `page.fields`，把结论行追加到 `page.conclusion`（月报进底部红条，通用 / 项目模式画成 lead）；文稿有错抛 `DeckError`，信息里带 `页「{page.title}」`。
- `render` 用 `prs.slide_layouts[LAYOUT_INDEX]` 建页，`fill_titles` 填 idx 0/10，按 idx 取槽位画内容（槽位只用来定位的就 `take_slot` 取矩形并删掉占位框），最后调 `add_page_chrome(slide, page, ctx)` 画 Tag 和结论 / Next。内容排在 `body_area(page, ctx)` 给的正文区里（槽位类版式用 `fit_body(take_slot(...), page, ctx)`），不要写死 1.30" / 5.60"。
- 共用部件只放 `layouts/common.py`，版式模块之间不互相 import：
  - 页面：`warn`、`load_image`、`fill_titles`、`add_page_chrome`（PDCA 图标 + Tag + 结论 / Next）；版式模块不用管 PDCA：图标在 banner 下沿和 1.30" 之间的窄条（1.02–1.30"），正文区不会高过 1.30"，不需要让位；有图标时 `add_month_tag` 由 `add_page_chrome` 让到图标左侧。
  - 模式：`ctx.lead`（`mdparse.uses_lead(meta)`：通用模式和项目汇报模式为 True，月报为 False）。月报走原路径：`add_caption_bar` 画底部红条，输出逐字节不变（`MONTHLY_SHA`）。方向 C：`add_lead`（`Lead` + 左侧红竖线 `Lead Accent`）、`add_next_line`（`Next Rule` 细线 + `Next Line`）；文字由 `conclusion_text(page)` / `next_text(page)` 给，审核脚本用同一对函数核对。
  - 正文区：`body_area(page, ctx) -> Area`（英寸；`left` / `top` / `width` / `height` / `right` / `bottom`，`emu()` 转 EMU 元组）。月报模式恒为 0.56 / 1.30 / 12.20 × 4.30"；方向 C 下上沿在 lead 下方（`lead_area(page)`），下沿在 Next 细线上方（`next_area(page)`）或 6.95"。`fit_body(rect, page, ctx)` 把模板槽位矩形（EMU）的上下沿换成正文区（月报原样返回）。section / agenda 不用它。
  - 形状：`slot` / `take_slot` / `remove_shape`（按 idx 取槽位、删形状）、`fit_picture`（矩形内等比放图）、`add_run`（Arial + 中文 PingFang SC 的 run）、`strip_theme_style`（去 p:style）；
  - 画形状：`add_textbox(slide, name, x, y, w, h, anchor=TOP, wrap=True) -> text_frame`（起名、内边距 0）、`add_shape(slide, kind, name, x, y, w, h, fill, line=None, line_pt=None)`（扁平自选图形：去主题样式、关阴影，`fill` / `line` 为 None 即无填充 / 无描边）、`add_line(slide, name, x1, y1, x2, y2, color, pt, dash=None)`（直线）。坐标都是 EMU，可为浮点。版式模块不要再各写一份；需要额外属性（如 timeline 的线关阴影、stats-side 的卡片段落左对齐）就在返回的形状上再设。
  - 估算：`text_width_in` / `text_lines`（CJK 1em、拉丁 0.55em），溢出警告一律用它；`wrap_lines`（同一字宽贪心断行，返回各行文字）和 `wrap_problem(text, pt, width_in, max_lines)`（超过 max_lines 行或末行只剩 ≤ `WIDOW_CHARS` 个字时返回原因）供折行判断用（process「流程说明折行」、team「团队职责折行」）；
  - 常量：`BRAND_RED`、`LATIN_FONT`、`EA_FONT`；黑白灰 `INK "1A1A1A"`、`MUTED "6B6B6B"`、`RULE "BFBFBF"` 和行高倍数 `LINE_SPACING = 1.25`（section / agenda / team / table 排框高用；审核估算溢出用 1.2，见下文审核脚本一节）。
  - 章节行（section、agenda）：`chapter_row(line)` 把「编号 | 中文名 | 英文名」拆成三段（去首尾空白），不是三段返回 `None`；`check_chapter_row(page, kind, row, show_row=False)` 查三段非空且不超字数（`CHAPTER_FIELDS`：编号 3、中文名 12、英文名 40），否则抛 `DeckError`。
  - 例外：底部红条的加高算法是月报固定样式，不改用 `text_lines`；stats 的卡片几何（大数字字号、标签 / 说明行数）用本版式的逐字宽表。stats-side 的大数字字号用通用口径（`number_width_in`）。两边口径不同是有意保留的：stats 的逐字宽表直接决定栏内形状尺寸，改成通用口径会改变已有文稿（含示例文稿）的输出；stats-side 只用估算判断要不要缩小，用通用口径即可。
  - 缩进子列表：`sub_item(page, i)`——`page.lines[i]` 是缩进（≥1 列）的 `- ` / `* ` / `+ ` 行时返回去掉列表符号的文字，否则 `None`。不缩进的 `- ` 行仍是本版式的条目行。stats 类版式用它把卡片行下面的解读挂到上一张卡上：
    ```python
    for i, line in enumerate(page.lines):
        sub = sub_item(page, i)
        if sub is not None:      # 解读：挂到 items[-1]；前面没有卡片行时按版式规则报错
            ...
    ```
  - 数字 + 缩小单位：`split_number(value) -> (前缀, 大数字, 单位)`，三段拼起来就是去掉首尾空白的原文，不补、不删空白。`is_number(value)` 判断是否「（前缀 +）数字」开头，和 `split_number` 同一条规则；审核脚本的「数字卡不是数字」直接用它。
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
- 注册表在 `layouts/__init__.py`，已登记 12 个版式。
- PDCA 图标资产：`assets/pdca/{P,D,C,A}_icon.png` 由同名 SVG 预转，提交进仓库，生成器运行时只插 PNG、不做转换。改了 SVG 后在 skill 目录下重转（macOS 自带 `sips`；SVG 只有 viewBox，先加上 320×320 的 width / height 再转（不加只出 80px），得到 320px 带透明底的 PNG）：
  ```
  for L in P D C A; do
    sed 's/<svg viewBox="0 0 80 80"/<svg width="320" height="320" viewBox="0 0 80 80"/' assets/pdca/${L}_icon.svg > /tmp/${L}_icon.svg
    sips -s format png /tmp/${L}_icon.svg --out assets/pdca/${L}_icon.png
  done
  ```
  （bash / zsh 写法；在 fish 里先 `bash` 再贴。）转完和 SVG 并排看一眼（如用浏览器打开两者），确认圆弧、颜色、字母一致。
- 形状命名：每个画出来的形状都 `name = "<角色> N"`（N 从 1 起，与条目顺序一致），这是生成后细调时对 AI 的契约；共用形状的名字列在 `references/layouts.md`「形状命名约定」，各版式的名字列在 `references/layouts/<版式名>.md`「形状名」，改名时同步改对应那一节。
- 测试：每个版式一个 `tests/test_<版式>.py`，只走“md 进、pptx 出”；辅助函数（`generate`、`body_slide`、`pictures`、`shapes_named`、`run_style` 等）和模板槽位常量都在 `tests/deckcheck.py`，测试文件里不要再各写一份。`python3 tests/run_all.py` 跑全部。
  - 各版式测试文件的文稿用月报 frontmatter（`month` + `author`），守住月报的底部红条路径；方向 C（通用 / 项目模式）的 lead、Next 行、正文区在 `tests/test_lead.py` 里按全部内容版式统一查。版式改方向 C 样式时，在自己的测试文件里另加通用模式的用例。
  - 新增辅助：`runs(shape, para=0)` 返回一段里每个 run 的 `(文字, 字号, 粗体, 颜色)`，查单位拆分；`fill_color` / `line_color` 取形状纯色填充 / 描边 hex（没有为 `None`）；`geometry(shape)` 取预设几何名（`ellipse`、`diamond`、`homePlate`、`chevron`…）；`inside(shape, rect_in)` 判断形状落在英寸矩形内（如 `CONTENT_SLOT_IN`）；`slide_xmls(path)` 取各页 slide XML 字节，用于和改动前逐字节比较；`deck_error(r, title, *needles)` 判断报错退出且信息含页标题。`review(md, pptx=None)` 跑审核脚本、返回 `CompletedProcess`；`generated(md, images=None)` 生成并返回 `(文稿路径, pptx 路径)`（失败抛出），`reviewed(md, images=None)` 生成后再审；`lines_with(out, rule)` 取审核输出里 `[rule]` 开头的行；`broken(pptx, change)` 把生成结果另存一份、用 `change(prs)` 改坏，做审核负样本。`registered_layouts()` 从未知版式的报错信息里读出注册表全部版式名（只走外部切入点）。`inside_shape(inner, outer)` 判断形状落在另一个形状里；`center_x` / `center_y` / `bottom` 取中心坐标和底边；`named(slide, name)` 取名字恰为 name 的全部形状，`one(slide, name)` 恰好一个时返回它。常量 `STATUS_COLORS`、`DONE_GREEN`、`DOING_AMBER`、`DOING_INK`、`UNIT_PT`、`UNIT_COLOR`。
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

生成器版式名不写进成稿：写进 slide（如 `cSld name`）会改动月报和旧 timeline 的逐字节输出。inspect 从模板 layout 推断：一个模板 layout 只对应一个版式时直接得出；共用模板 layout 的版式靠版式模块的 `MARK_SHAPE`（stats-side 的 `Side Card 1`、timeline-phase 的 `Phase Segment 1`、section 的 `Section Number`、agenda 的 `Agenda Number 1`、team 的 `Member Name 1`、table 的 `Data Table`）区分，没有该形状的算另一个（stats / timeline / evidence）。封面、收尾为 `-`。新增共用模板 layout 的版式时，给它定一个 `MARK_SHAPE`。

## 审核命令 `review_deck.py`

生成后机械审核，输入 md 文稿和生成的 pptx（pptx 可省略，只审文稿）：

```
python3 scripts/review_deck.py deck.md deck.pptx
```

- 输出：每条问题一行 `[规则] 位置：问题 → 怎么改`；全部通过时只打印一行 `REVIEW OK`，有问题时最后一行是 `REVIEW: N 条问题`。
- 只报告、不改文件。审完退出码总是 0（有问题也是 0）；文稿读不了（找不到、写错）或 pptx 打不开时退出码 1，错误写到 stderr。
- 和生成器共用 `mdparse` 与版式注册表：文稿按生成器同一套规则解析，生成器会报错的文稿审核也报错。
- 内容检查（只看文稿，所有文稿都查）：页数过多（> 10 页，不含目录页、隔断页）、相邻两页版式相同（连着两张隔断页不报）、目录式副标题（不到 6 字，或只是主标题中文部分加两三个字，如「项目目标介绍」；6 字以上的短结论不报）、缺结论行（`NAV_LAYOUTS` 里的导航页不报，目前是按设计不放结论的 section、agenda）、lead 和副标题相同（通用 / 项目模式：结论行和 action title 去掉标点和空白（含全角）后相同）、对比页两个 lead（通用 / 项目模式：before-after 第一个 `###` 前还写了文字，生成器不画它）、流程说明折行（通用 / 项目模式：process 的说明超过两行或末行只剩 ≤2 个字；和生成器的折行警告同用 `layouts/process.py` 的 `desc_wrap_problem`，按 `text_width_in` 字宽贪心断行估算）、团队职责折行（通用 / 项目模式：team 的职责按生成器选中那一档的字号和文字框宽断行，超过 3 行或末行只剩 ≤2 个字；和生成器警告同用 `layouts/team.py` 的 `duty_wrap_problems`，断行与判断共用 `layouts/common.py` 的 `wrap_lines` / `wrap_problem`）、表格太高（月报模式：table 表格总高放不进正文区；生成器渲染时同样报错退出，两边同用 `layouts/table.py` 的 `monthly_height_problem`）、内容重复（两页流程步骤名一半以上相同）、数字卡不是数字、数据缺失（`[数据缺失]` 占位）、用词（浮夸 / 空洞词表）、关键标记过多（时间线 3 个以上节点、超过一半标了 `!`）、目录和隔断页不一致（文稿有目录页时，隔断页的中文章节名不在目录里）。
- 配图检查（只看文稿，所有文稿都查）：缺配图（evidence 页没放图；evidence 是唯一"必须配图、但解析不强制"的版式）、图片不存在（evidence 的图、image-text 的图、before-after 两侧写了的图，本地路径相对文稿找不到；URL 不查）。image-text 没图在解析时就报错（和生成器同一条规则，审核退出码 1）；before-after 每侧按设计可放图或短文，不要求配图。
- 项目汇报模式检查（只在 frontmatter 写了 `report: project` 时查，对应 SKILL.md §1、§2）：页按主标题英文部分（`中文 / 英文`）认 §1 八节 `BACKGROUND → TARGET → SCOPE → USE CASES → MILESTONE → OUTCOMES → TEAM → LESSONS`，英文名不在八节里的页是子节点，归到前面最近的一节。
  - 章节顺序：八节的页倒序出现；目录页列出的八节顺序不对。
  - 缺章节：八节少了哪节（整份文稿）。
  - 缺 PDCA：页没写 `PDCA:`（团队页、目录页、隔断页不要求）。
  - 团队页带 PDCA：`team` 版式或 TEAM 节的页写了 `PDCA:`。
  - PDCA 和章节不符：标的阶段和所属节不对应（01–04 P、05 D、06 D 或 C、08 A），或一页标了多个阶段（§2：06 节一页只放一个；生成器允许 `D/C` 组合，由审核报）。还没进入八节的页不比对。
  - 章节和版式不配：TARGET / SCOPE 用 process / before-after，USE CASES 用 before-after。
- 真伪检查（看 pptx，确认是生成器按当前文稿做的）：页数不符（封面 + 正文 + 收尾页）、不是生成脚本做的（正文页 idx 0 / 10 占位框里的文字和文稿的主标题、副标题不一致，或 banner 0–1.0" 上另画了文本框）、结论没画出来 / Next 没画出来（导航页除外：通用 / 项目模式下 `Lead` / `Next Line` 各段拼起来、去掉空白后要和 `conclusion_text` / `next_text` 一致，细调时拆段或加手动换行不报；月报模式下这两句要各是 `Caption Bar` 里的一段）、正文形状被改过（审核时用 `generate_ppt.build` 按当前 md 在内存里重新渲染一份，逐页比较占位框以外形状的名字和个数（同名形状复制一个也算多出），多出、缺少都报并列出形状名；`Lead` / `Next Line` / `Caption Bar` 归上一条查，不在这里重复报；只比名字、不比几何和字号，挪位置、改字号的手工细调不报；局限：按原名删掉正文形状、再用同样的名字重画，这条查不出来；重新渲染失败时——如图片找不到、月报表格太高，原因已由文稿检查报出——改报一条「正文形状无法比对」，带生成器的报错）、红色面积超配额（只在通用 / 项目模式查，月报豁免：banner 以外、填充或描边为品牌红（直接写的 `srgbClr`，或按母版主题解析的 `schemeClr`，如模板的 accent1）的形状按外框面积求和，组合形状递归算各子形状，直线按长 × 线宽，超过页面面积的 `RED_QUOTA`（5%，SKILL.md §6.3）就报；timeline / timeline-phase 里只有描边是红的状态色不计入；红色文字、图片、表格单元格底色不计入）。位置写成 `pptx 第 N 页（页「主标题」）`。
- 几何检查（看 pptx 正文页，只用 python-pptx 和计算，不依赖 LibreOffice）：出界（超出页面）、压 banner（上沿高于 1.0"，idx 0 / 10 标题框除外）、压页脚（下沿低于 7.25"）、文字溢出（字宽用 `layouts/common.py` 的 `text_width_in`，行高 = 字号 × 1.2，与 process / stats / stats-side / timeline / timeline-phase / before-after 的溢出警告同一口径；section / agenda / team / table 按 `common.LINE_SPACING`（1.25）排框高，比审核宽 4%，生成器的框不会被报溢出；字号继承模板的占位框不估；原生表格按单元格估，某行估计高过行高才报）、重叠、错位。每条带页码和形状名。重叠豁免和错位比较按形状名，规则见 `references/layouts.md`「审核的几何豁免」；阈值是 `review_deck.py` 里的命名常量（`OVERLAP_TOL`、`MISALIGN_TOL`、`ALIGN_SNAP`、`OVERFLOW_TOL`），取值理由写在常量旁。几何检查的测试在 `tests/test_review_geometry.py`。
- 测试在 `tests/test_review.py`（通用内容检查、真伪检查）、`tests/test_review_lead.py`（方向 C：结论 / Next 画出来、lead 和副标题、对比页两个 lead、流程说明折行）、`tests/test_team.py`（团队职责折行：生成器警告、审核规则和文档一致性）、`tests/test_review_quota.py`（红色面积超配额，配额从 SKILL.md §6.3 面积表读）、`tests/test_review_redraw.py`（正文形状被改过：按形状名删正文重画、复制同名形状要报，只挪位置改字号的细调不报）、`tests/test_table.py`（表格太高：只审文稿也报、重新渲染失败报「正文形状无法比对」）和 `tests/test_review_project.py`（项目模式、配图、目录和隔断页）：正样本是生成器的正常输出（含示例文稿），负样本用 python-pptx 把正常输出改坏或改文稿。`test_review_project.py` 的 `PROJECT_FULL` 是全版式正样本（项目模式一份、去掉 `report: project` 和 PDCA 的非项目模式一份，都要打印 `REVIEW OK`），`test_review_geometry.py` 的 `VARIANTS` 是几何正样本；两者都强制覆盖 `registered_layouts()`，新增版式没补正样本时测试失败并提示补哪个版式。新增规则时规则名放进 `[]`，测试按 `[规则]` 行首匹配。
