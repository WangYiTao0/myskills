"""stats 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_stats.py
"""
from deckcheck import (CONTENT_SLOT_IN, EMU, LAYOUT_INDEX, body_slide, caption_bar,
                       caption_style_problems, check, deck_error, fill_color, finish, generate, geometry, inside,
                       out_of_bounds,
                       paragraphs, placeholder, line_color, red_elements, run_styles, runs, shapes_named,
                       tag_shape, warnings)

NAME = "stats"
TITLE = "Mock Stats Page"
MD = """
---
month: 2026-10
author: Mock.Author
date: 13 Oct 2026
---

# Mock Stats Page
## Mock Action Title
Layout: stats
Tag: Mar
- Lead time | 5 d | Mock average per request
- !Rework | -40% | Sample reduction after the change
- Coverage | 3 teams | Mock pilot scope
Mock one-line conclusion.
Next: Mock next step.
"""
IMAGES = {"img/shot.png": (1600, 900)}


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD, images=IMAGES)
    check("stats：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("stats：生成了正文页", False, r.stderr)
        return
    check("stats：用模板 layout 5「Stats」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("stats：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("stats：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("stats：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("stats：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("stats：形状在页面内、不压 banner 和页脚", not bad, bad)


SLOT_L, SLOT_T, SLOT_W, SLOT_H = CONTENT_SLOT_IN     # 槽位 idx 18「Stats Area」
P_STYLE = "{http://schemas.openxmlformats.org/presentationml/2006/main}style"


def stats_md(items, title=TITLE):
    body = "\n".join(items)
    return f"""
---
month: 2026-10
author: Mock.Author
date: 13 Oct 2026
---

# {title}
## Mock Action Title
Layout: stats
{body}
Mock conclusion.
"""


def test_column_text_hierarchy():
    """每栏自上而下：顶线、标签、大数字、说明；层级靠字号、字重和灰阶。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    if s is None:
        check("stats：生成了正文页", False, r.stderr)
        return
    rules = shapes_named(s, "Stat Rule")
    labels = shapes_named(s, "Stat Label")
    numbers = shapes_named(s, "Stat Number")
    notes = shapes_named(s, "Stat Note")
    check("stats：每栏都有顶线 / 标签 / 数字 / 说明",
          len(rules) == len(labels) == len(numbers) == len(notes) == 3,
          (len(rules), len(labels), len(numbers), len(notes)))
    if not len(rules) == len(labels) == len(numbers) == len(notes) == 3:
        return
    check("stats：标签文字（重点的 ! 不显示）",
          [x.text_frame.text for x in labels] == ["Lead time", "Rework", "Coverage"],
          [x.text_frame.text for x in labels])
    check("stats：数字文字",
          [x.text_frame.text for x in numbers] == ["5 d", "-40%", "3 teams"],
          [x.text_frame.text for x in numbers])
    check("stats：说明文字",
          [x.text_frame.text for x in notes] == ["Mock average per request",
                                                 "Sample reduction after the change",
                                                 "Mock pilot scope"],
          [x.text_frame.text for x in notes])
    check("stats：自上而下是顶线 → 标签 → 数字 → 说明",
          all(rl.top + rl.height <= lb.top and lb.top + lb.height <= nb.top
              and nb.top + nb.height <= nt.top
              for rl, lb, nb, nt in zip(rules, labels, numbers, notes)))
    check("stats：标签 16pt 加粗 #1A1A1A",
          all(run_styles(x) == {(16.0, True, "1A1A1A")} for x in labels),
          [run_styles(x) for x in labels])
    check("stats：说明 14pt 不加粗 #6B6B6B",
          all(run_styles(x) == {(14.0, False, "6B6B6B")} for x in notes),
          [run_styles(x) for x in notes])
    check("stats：没有字号警告", not warnings(r.stderr), r.stderr)


def test_number_unit_split():
    """数值 60pt 加粗，后面的单位是独立 run：28pt 灰色不加粗；数值和单位之间的空白照原文。"""
    r = generate(stats_md(["- A | 120 件 | Mock", "- !B | 100% | Mock",
                           "- C | 15 秒 | Mock", "- D | 42 | Mock"]))
    s = body_slide(r)
    if s is None:
        check("stats 单位：生成了正文页", False, r.stderr)
        return
    got = [runs(x) for x in shapes_named(s, "Stat Number")]
    check("stats 单位：数值与单位拆成两个 run，单位 28pt 灰色不加粗", got == [
        [("120", 60.0, True, "1A1A1A"), (" 件", 28.0, False, "6B6B6B")],
        [("100", 60.0, True, "DB011C"), ("%", 28.0, False, "6B6B6B")],
        [("15", 60.0, True, "1A1A1A"), (" 秒", 28.0, False, "6B6B6B")],
        [("42", 60.0, True, "1A1A1A")],
    ], got)


def test_red_discipline():
    """有一个 ! 时只有那栏的顶线和数字是品牌红，其余栏顶线深灰；没有 ! 时红条外没有红色。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    if s is None:
        check("stats：生成了正文页", False, r.stderr)
        return
    red = [x for x in red_elements(s) if x != "Caption Bar"]
    check("stats：标了 ! 的只有第 2 栏的顶线和数字是红色",
          sorted(red) == ["Stat Number 2", "Stat Rule 2"], red)
    rules = shapes_named(s, "Stat Rule")
    check("stats：重点栏顶线品牌红，其余栏顶线 #1A1A1A",
          [fill_color(x) for x in rules] == ["1A1A1A", "DB011C", "1A1A1A"],
          [fill_color(x) for x in rules])
    num2 = shapes_named(s, "Stat Number")[1:2]
    check("stats：重点数字的数值用品牌红 DB011C",
          num2 and runs(num2[0])[0][1:] == (60.0, True, "DB011C"), num2 and runs(num2[0]))

    r = generate(stats_md(["- A | 1 | Mock note", "- B | 2 | Mock note"]))
    s = body_slide(r)
    red = s is not None and [x for x in red_elements(s) if x != "Caption Bar"]
    check("stats：没有 ! 时红条外没有红色", s is not None and red == [], red)


def test_errors():
    """! 多于一个、条数不在 2–4、条目不是三段时报错退出，信息含页标题，不留半坏文件。"""
    bad_title = "Broken Stats Page"
    cases = {
        "两个 !": ["- !A | 1 | Mock", "- !B | 2 | Mock"],
        "只有 1 条": ["- A | 1 | Mock"],
        "5 条": [f"- L{i} | {i} | Mock" for i in range(5)],
        "条目只有两段": ["- A | 1", "- B | 2 | Mock"],
        "解读在第一条数据之前": ["  - Mock orphan point", "- A | 1 | Mock", "- B | 2 | Mock"],
        "口径写了两行": ["- A | 1 | Mock", "- B | 2 | Mock", "口径：Mock 1", "Source: Mock 2"],
    }
    for name, items in cases.items():
        r = generate(stats_md(items, title=bad_title))
        check(f"stats 报错（{name}）：非零退出、信息含页标题、不出文件",
              r.rc != 0 and bad_title in r.stderr and not r.path.exists(),
              (r.rc, r.stderr))
    # 某张卡的解读超过 3 条：信息含页标题和那张卡
    r = generate(stats_md(["- A | 1 | Mock", "- Busy card | 2 | Mock",
                           "  - P1", "  - P2", "  - P3", "  - P4"], title=bad_title))
    check("stats 报错（解读 4 条）：非零退出、含页标题和卡片标签、不出文件",
          deck_error(r, bad_title, "Busy card", "3") and not r.path.exists(), (r.rc, r.stderr))
    # 写了两个 !：报错，不把多出来的 ! 当成标签文字
    r = generate(stats_md(["- !!A | 1 | Mock", "- B | 2 | Mock"], title=bad_title))
    check("stats 报错（!! 两个叹号）：非零退出、含页标题和 !!",
          deck_error(r, bad_title, "!!") and not r.path.exists(), (r.rc, r.stderr))
    # 重点行漏写列表符号：不能悄悄当成红条结论
    r = generate(stats_md(["!Rework | -40% | Mock", "- B | 2 | Mock", "- C | 3 | Mock"],
                          title=bad_title))
    check("stats 报错（! 行没写列表符号）：非零退出、含页标题和原行、提示加列表符号",
          r.rc != 0 and bad_title in r.stderr and "!Rework" in r.stderr
          and "- !" in r.stderr and not r.path.exists(), (r.rc, r.stderr))


def test_long_numbers_shrink_together():
    """有数字在 60pt 放不下时，所有数字统一缩小（仍比其他字大），并给警告含页标题。"""
    long_title = "Long Number Page"
    r = generate(stats_md(["- Revenue | $12,345,678 | Mock total",
                           "- !Tickets | 42 | Mock count",
                           "- Users | 9 | Mock count",
                           "- Sites | 3 | Mock count"], title=long_title))
    s = body_slide(r)
    if s is None:
        check("stats 长数字：生成了正文页", False, r.stderr)
        return
    sizes = {st[0] for x in shapes_named(s, "Stat Number") for st in run_styles(x)}
    check("stats 长数字：所有数字字号相同", len(sizes) == 1, sizes)
    size = next(iter(sizes)) if len(sizes) == 1 else None
    check("stats 长数字：缩到 60pt 以下但仍明显大于说明（≥ 28pt）",
          size is not None and 28 <= size < 60, sizes)
    w = [x for x in warnings(r.stderr) if long_title in x and "缩小" in x]
    check("stats 长数字：有一条缩小警告且含页标题", len(w) == 1, r.stderr)
    check("stats 长数字：仍在页面内", not out_of_bounds(r.prs, [s]),
          out_of_bounds(r.prs, [s]))


def test_columns_fill_slot():
    """栏数 = 条目数，等宽、等间距，整体铺满槽位宽度；每栏顶部一条粗线；槽位占位框已清掉。"""
    for n in (2, 3, 4):
        items = [f"- Label {i} | {i}0% | Mock note {i}" for i in range(1, n + 1)]
        r = generate(stats_md(items))
        s = body_slide(r)
        if s is None:
            check(f"stats {n} 栏：生成了正文页", False, r.stderr)
            continue
        rules = shapes_named(s, "Stat Rule")
        check(f"stats {n} 栏：顶线数 = 条目数", len(rules) == n, [x.name for x in rules])
        if len(rules) != n:
            continue
        widths = {x.width for x in rules}
        check(f"stats {n} 栏：等宽", max(widths) - min(widths) <= 2, widths)
        check(f"stats {n} 栏：都在槽位内",
              all(inside(x, CONTENT_SLOT_IN) for x in s.shapes if x.name.startswith("Stat ")),
              [x.name for x in s.shapes
               if x.name.startswith("Stat ") and not inside(x, CONTENT_SLOT_IN)])
        tol = 0.01
        span = (rules[-1].left + rules[-1].width - rules[0].left) / EMU
        check(f"stats {n} 栏：铺满槽位宽度", abs(span - SLOT_W) < tol, span)
        gaps = [(b.left - a.left - a.width) / EMU for a, b in zip(rules, rules[1:])]
        check(f"stats {n} 栏：栏间距统一 0.45\"", all(abs(g - 0.45) < tol for g in gaps), gaps)
        check(f"stats {n} 栏：顶线是 0.06\" 粗的扁平矩形",
              all(abs(x.height / EMU - 0.06) < tol and geometry(x) == "rect"
                  and x._element.find(P_STYLE) is None for x in rules))
        for prefix in ("Stat Label", "Stat Number", "Stat Note"):
            boxes = shapes_named(s, prefix)
            check(f"stats {n} 栏：{prefix} 和顶线左对齐、同宽",
                  len(boxes) == n and all(b.left == rl.left and b.width == rl.width
                                          for b, rl in zip(boxes, rules)),
                  [(b.left, b.width) for b in boxes])
        check(f"stats {n} 栏：空的槽位占位框已清掉", placeholder(s, 18) is None)
        check(f"stats {n} 栏：不再画灰底卡片", not shapes_named(s, "Stat Card"))


POINTS_MD = """
---
month: 2026-10
author: Mock.Author
date: 13 Oct 2026
---

# Mock Points Page
## Mock Action Title
Layout: stats
- Pilot tools | 120 件 | Mock scope note
  - Mock point 1a
  - Mock point 1b
- !Record rate | 100% | Mock rate note
  - Mock point 2a
  - Mock point 2b
  - Mock point 2c
- Check-in time | 15 秒 | Mock time note
口径：Mock source line for the numbers above
Mock conclusion.
"""


def test_points_under_each_column():
    """卡片行下面缩进的 `- ` 是这栏的解读：说明下方一条细分隔线，再下面是带项目符号的解读。"""
    r = generate(POINTS_MD)
    s = body_slide(r)
    if s is None:
        check("stats 解读：生成了正文页", False, r.stderr)
        return
    points = shapes_named(s, "Stat Points")
    dividers = shapes_named(s, "Stat Divider")
    notes = shapes_named(s, "Stat Note")
    rules = shapes_named(s, "Stat Rule")
    check("stats 解读：每栏一个解读框，第 3 栏没写解读就不画",
          [x.name for x in points] == ["Stat Points 1", "Stat Points 2"],
          [x.name for x in points])
    check("stats 解读：每栏一条分隔线（解读区和说明分开）", len(dividers) == 3,
          [x.name for x in dividers])
    if len(points) != 2 or len(dividers) != 3:
        return
    check("stats 解读：文字一条一段，顺序不变",
          [paragraphs(x) for x in points] ==
          [["Mock point 1a", "Mock point 1b"],
           ["Mock point 2a", "Mock point 2b", "Mock point 2c"]],
          [paragraphs(x) for x in points])
    check("stats 解读：14pt 不加粗 #1A1A1A",
          all(run_styles(x) == {(14.0, False, "1A1A1A")} for x in points),
          [run_styles(x) for x in points])
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    check("stats 解读：每段带项目符号（buChar）",
          all(p._p.find(f"{A}pPr/{A}buChar") is not None
              for x in points for p in x.text_frame.paragraphs))
    check("stats 解读：说明 → 分隔线 → 解读，自上而下，和本栏左对齐",
          all(nt.top + nt.height <= dv.top and dv.top <= pt.top and pt.left == rl.left
              for nt, dv, pt, rl in zip(notes, dividers, points, rules)))
    check("stats 解读：分隔线是 #E5E5E5 细线、和本栏同宽",
          all(line_color(dv) == "E5E5E5" and dv.width == rl.width and dv.height == 0
              for dv, rl in zip(dividers, rules)),
          [(line_color(dv), dv.width, dv.height) for dv in dividers])
    check("stats 解读：子列表不进红条", paragraphs(caption_bar(s)) == ["Mock conclusion."],
          paragraphs(caption_bar(s)))
    check("stats 解读：形状不越界", not out_of_bounds(r.prs, [s]), out_of_bounds(r.prs, [s]))
    check("stats 解读：没有警告", not warnings(r.stderr), r.stderr)


def test_source_line():
    """`口径：` / `Source:` 开头的一行：灰色 12pt 小字，贴内容区底部、在解读下方，不进红条。"""
    for line in ("口径：Mock source line for the numbers above",
                 "Source: Mock source line for the numbers above"):
        r = generate(POINTS_MD.replace("口径：Mock source line for the numbers above", line))
        s = body_slide(r)
        if s is None:
            check(f"stats 口径（{line[:7]}）：生成了正文页", False, r.stderr)
            continue
        src = [x for x in s.shapes if x.name == "Stat Source"]
        check(f"stats 口径（{line[:7]}）：一个 Stat Source，原文照写", len(src) == 1
              and src[0].text_frame.text == line, [x.text_frame.text for x in src])
        if len(src) != 1:
            continue
        src = src[0]
        check(f"stats 口径（{line[:7]}）：12pt 不加粗 #6B6B6B",
              run_styles(src) == {(12.0, False, "6B6B6B")}, run_styles(src))
        bottom = (SLOT_T + SLOT_H) * EMU
        check(f"stats 口径（{line[:7]}）：底边贴内容区底部、左对齐、通栏",
              abs(src.top + src.height - bottom) < 0.01 * EMU
              and abs(src.left - SLOT_L * EMU) < 0.01 * EMU
              and abs(src.width - SLOT_W * EMU) < 0.02 * EMU,
              (src.left / EMU, src.top / EMU, src.width / EMU, src.height / EMU))
        check(f"stats 口径（{line[:7]}）：在所有解读下方",
              all(p.top + p.height <= src.top for p in shapes_named(s, "Stat Points")))
        check(f"stats 口径（{line[:7]}）：不进红条",
              paragraphs(caption_bar(s)) == ["Mock conclusion."], paragraphs(caption_bar(s)))


def test_overflow_warnings():
    """解读或口径估计放不下时给警告（含页标题），照常生成；放得下时不警告。"""
    title = "Crowded Stats Page"
    long_point = "  - " + "这是一条很长很长的模拟解读文字，用来把这一栏的解读区撑满" * 2
    items = []
    for i in range(1, 5):
        items += [f"- Label {i} | {i}0% | Mock note {i}", long_point, long_point, long_point]
    r = generate(stats_md(items + ["口径：" + "模拟口径说明文字很长" * 12], title=title))
    check("stats 溢出：照常生成", r.rc == 0 and body_slide(r) is not None, r.stderr)
    w = warnings(r.stderr)
    check("stats 溢出：解读放不下时警告，含页标题",
          any(title in x and "解读" in x for x in w), r.stderr)
    check("stats 溢出：口径超过一行时警告，含页标题",
          any(title in x and "口径" in x for x in w), r.stderr)
    s = body_slide(r)
    check("stats 溢出：形状仍在页面内", s is not None and not out_of_bounds(r.prs, [s]),
          s is not None and out_of_bounds(r.prs, [s]))


def test_legacy_without_points():
    """旧写法（没有解读、没有口径）：只画顶线 / 标签 / 数字 / 说明，不画分隔线和解读；
    这一块在槽位里垂直居中，不顶在上面留下大片空白。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    if s is None:
        check("stats 旧写法：生成了正文页", False, r.stderr)
        return
    check("stats 旧写法：没有分隔线、解读、口径",
          not shapes_named(s, "Stat Divider") and not shapes_named(s, "Stat Points")
          and not [x for x in s.shapes if x.name == "Stat Source"])
    rules, notes = shapes_named(s, "Stat Rule"), shapes_named(s, "Stat Note")
    top_gap = rules[0].top / EMU - SLOT_T
    bottom_gap = SLOT_T + SLOT_H - (notes[0].top + notes[0].height) / EMU
    check("stats 旧写法：整块在槽位内垂直居中", top_gap > 0.5 and abs(top_gap - bottom_gap) < 0.02,
          (top_gap, bottom_gap))
    check("stats 旧写法：所有栏顶线同高", len({x.top for x in rules}) == 1)


if __name__ == "__main__":
    test_chrome()
    test_columns_fill_slot()
    test_column_text_hierarchy()
    test_number_unit_split()
    test_red_discipline()
    test_errors()
    test_long_numbers_shrink_together()
    test_points_under_each_column()
    test_source_line()
    test_overflow_warnings()
    test_legacy_without_points()
    finish()
