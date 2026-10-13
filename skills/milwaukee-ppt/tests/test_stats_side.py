"""stats-side 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_stats_side.py
"""
from deckcheck import (CONTENT_SLOT_IN, EMU, LAYOUT_INDEX, body_slide, caption_bar,
                       caption_style_problems, check, deck_error, fill_color, finish, generate,
                       inside, inside_shape, line_color, one, out_of_bounds, paragraphs,
                       placeholder, red_elements, run_styles, runs, shapes_named, tag_shape,
                       warnings)

NAME = "stats-side"
TITLE = "Mock Stats Side Page"
MD = """
---
title: Mock Deck
date: 13 Oct 2026
---

# Mock Stats Side Page
## Mock Action Title
Layout: stats-side
Tag: Mar
- Lead time | 5 d | Mock average per request
- !Rework | -40% | Sample reduction after the change
> Mock finding one about the numbers.
> Mock finding two about the numbers.
口径：Mock source note.
Mock one-line conclusion.
Next: Mock next step.
"""

SLOT_L, SLOT_T, SLOT_W, SLOT_H = CONTENT_SLOT_IN     # 槽位 idx 18「Stats Area」
LEFT_HALF = (SLOT_L, SLOT_T, SLOT_W / 2, SLOT_H)
RIGHT_HALF = (SLOT_L + SLOT_W / 2, SLOT_T, SLOT_W / 2, SLOT_H)


def side_md(items, points=("Mock finding.",), extra="", title=TITLE):
    body = "\n".join(list(items) + [f"> {p}" for p in points])
    return f"""
---
title: Mock Deck
date: 13 Oct 2026
---

# {title}
## Mock Action Title
Layout: stats-side
{body}
{extra}
Mock conclusion.
"""


def page(md):
    r = generate(md)
    s = body_slide(r)
    if r.rc != 0 or s is None:
        check("stats-side：生成成功", False, r.stderr)
        return r, None
    return r, s


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD)
    check("stats-side：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("stats-side：生成了正文页", False, r.stderr)
        return
    check("stats-side：用模板 layout 5「Stats」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("stats-side：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("stats-side：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("stats-side：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("stats-side：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("stats-side：形状在页面内、不压 banner 和页脚", not bad, bad)


def test_cards():
    """卡片数 = 条目数，竖排在槽位左半；每张卡里有数字和标签 / 说明，自上而下排列。"""
    for n in (2, 3):
        items = [f"- Item {i} | {i}0 pcs | Mock note {i}" for i in range(1, n + 1)]
        r, s = page(side_md(items))
        if s is None:
            return
        cards = shapes_named(s, "Side Card")
        numbers = shapes_named(s, "Side Number")
        textb = shapes_named(s, "Side Text")
        check(f"stats-side：{n} 条 → {n} 张卡 / 数字 / 文字",
              len(cards) == len(numbers) == len(textb) == n,
              (len(cards), len(numbers), len(textb)))
        check(f"stats-side：{n} 张卡都在槽位左半",
              all(inside(c, LEFT_HALF) for c in cards), [c.name for c in cards])
        check(f"stats-side：{n} 张卡自上而下、不重叠",
              all(a.top + a.height <= b.top for a, b in zip(cards, cards[1:])))
        check(f"stats-side：{n} 张卡的数字和文字都在卡内",
              all(inside_shape(x, c) for c, pair in zip(cards, zip(numbers, textb))
                  for x in pair))
        check(f"stats-side：{n} 张卡的数字在左、文字在右",
              all(nb.left + nb.width <= tb.left for nb, tb in zip(numbers, textb)))
        check(f"stats-side：{n} 张卡的文字 = 标签 + 说明",
              [paragraphs(t) for t in textb] ==
              [[f"Item {i}", f"Mock note {i}"] for i in range(1, n + 1)],
              [paragraphs(t) for t in textb])


A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def autonum(paragraph):
    """段落的自动编号类型（a:buAutoNum type），没有为 None。"""
    pPr = paragraph._p.find(f"{A}pPr")
    el = pPr.find(f"{A}buAutoNum") if pPr is not None else None
    return el.get("type") if el is not None else None


def test_conclusion_area():
    """结论区在槽位右半：小标题 → 分隔线 → 编号要点 → 口径贴底，要点按出现顺序自动编号。"""
    r, s = page(MD)
    if s is None:
        return
    title, rule = one(s, "Side Conclusion Title"), one(s, "Side Conclusion Rule")
    pts, src = one(s, "Side Points"), one(s, "Stat Source")
    check("stats-side：结论区四个形状各一个",
          None not in (title, rule, pts, src), [sh.name for sh in s.shapes])
    if None in (title, rule, pts, src):
        return
    check("stats-side：结论区都在槽位右半",
          all(inside(x, RIGHT_HALF) for x in (title, rule, pts, src)),
          [x.name for x in (title, rule, pts, src) if not inside(x, RIGHT_HALF)])
    check("stats-side：小标题默认「结论」，18pt 加粗深色",
          title.text_frame.text == "结论" and run_styles(title) == {(18.0, True, "1A1A1A")},
          (title.text_frame.text, run_styles(title)))
    check("stats-side：要点文字（去掉 > ）",
          paragraphs(pts) == ["Mock finding one about the numbers.",
                              "Mock finding two about the numbers."], paragraphs(pts))
    check("stats-side：每条要点都自动编号（1、2…）",
          [autonum(p) for p in pts.text_frame.paragraphs] == ["arabicPlain"] * 2,
          [autonum(p) for p in pts.text_frame.paragraphs])
    check("stats-side：要点 16pt 不加粗深色",
          run_styles(pts) == {(16.0, False, "1A1A1A")}, run_styles(pts))
    check("stats-side：口径原文、12pt 灰色",
          src.text_frame.text == "口径：Mock source note."
          and run_styles(src) == {(12.0, False, "6B6B6B")}, src.text_frame.text)
    check("stats-side：自上而下 小标题 → 分隔线 → 要点 → 口径",
          title.top + title.height <= rule.top and rule.top + rule.height <= pts.top
          and pts.top + pts.height <= src.top, [(x.name, x.top) for x in (title, rule, pts, src)])
    check("stats-side：口径贴槽位底",
          abs(src.top + src.height - (SLOT_T + SLOT_H) * EMU) < 0.02 * EMU)


def test_conclusion_options():
    """### 自定义小标题；Source: 也是口径；不写口径时没有 Stat Source。"""
    r, s = page(side_md(["- A | 1 | n", "- B | 2 | n"], points=["P1", "P2", "P3", "P4"],
                        extra="### 试点结论\nSource: Mock export."))
    if s is None:
        return
    title, pts, src = one(s, "Side Conclusion Title"), one(s, "Side Points"), one(s, "Stat Source")
    check("stats-side：### 自定义小标题", title and title.text_frame.text == "试点结论",
          title and title.text_frame.text)
    check("stats-side：4 条要点", pts and paragraphs(pts) == ["P1", "P2", "P3", "P4"],
          pts and paragraphs(pts))
    check("stats-side：Source: 也算口径", src and src.text_frame.text == "Source: Mock export.")
    check("stats-side：小标题和口径不进红条",
          paragraphs(caption_bar(s)) == ["Mock conclusion."], paragraphs(caption_bar(s)))
    r, s = page(side_md(["- A | 1 | n", "- B | 2 | n"]))
    if s is None:
        return
    check("stats-side：不写口径时没有 Stat Source", one(s, "Stat Source") is None)


def test_red_and_units():
    """红色只在重点卡的竖条、重点数字和底部红条；单位拆成 28pt 灰色 run，同一段。"""
    r, s = page(MD)
    if s is None:
        return
    red = sorted(red_elements(s))
    check("stats-side：红色只在 Side Accent 2 / Side Number 2 / 红条",
          red == ["Caption Bar", "Side Accent 2", "Side Number 2"], red)
    accents = [sh for sh in s.shapes if sh.name.startswith("Side Accent")]
    card2 = shapes_named(s, "Side Card")[1]
    check("stats-side：重点卡竖条贴卡片左边、与卡同高、品牌红",
          len(accents) == 1 and accents[0].left == card2.left and accents[0].top == card2.top
          and accents[0].height == card2.height and fill_color(accents[0]) == "DB011C"
          and accents[0].width < 0.1 * EMU, [a.name for a in accents])
    nums = shapes_named(s, "Side Number")
    check("stats-side：普通数字 60pt 加粗深色 + 单位 28pt 灰色",
          runs(nums[0]) == [("5", 60.0, True, "1A1A1A"), (" d", 28.0, False, "6B6B6B")],
          runs(nums[0]))
    check("stats-side：重点数字 60pt 加粗品牌红，% 紧贴、灰色",
          runs(nums[1]) == [("-40", 60.0, True, "DB011C"), ("%", 28.0, False, "6B6B6B")],
          runs(nums[1]))
    check("stats-side：卡片浅灰底、无描边",
          all(fill_color(c) == "F5F5F5" and line_color(c) is None
              for c in shapes_named(s, "Side Card")))

    r, s = page(side_md(["- A | 1 | n", "- B | 2 | n"]))
    if s is None:
        return
    check("stats-side：没有 ! 时除红条外没有红色",
          red_elements(s) == ["Caption Bar"], red_elements(s))


def test_errors():
    """文稿写错时报错退出，信息含页标题。"""
    ok2 = ["- A | 1 | n", "- B | 2 | n"]
    cases = [
        ("1 张卡", side_md(["- A | 1 | n"]), ("2–3",)),
        ("4 张卡", side_md(ok2 + ["- C | 3 | n", "- D | 4 | n"]), ("2–3", "4")),
        ("没有结论要点", side_md(ok2, points=()), ("> ",)),
        ("5 条结论要点", side_md(ok2, points=["P1", "P2", "P3", "P4", "P5"]), ("4", "5")),
        ("两个 !", side_md(["- !A | 1 | n", "- !B | 2 | n"]), ("!",)),
        ("!! 两个叹号", side_md(["- !!A | 1 | n", "- B | 2 | n"]), ("!!",)),
        ("条目缺字段", side_md(["- A | 1", "- B | 2 | n"]), ("标签 | 数字 | 一句说明",)),
        ("重点条漏写列表符号", side_md(["!A | 1 | n", "- B | 2 | n"]), ("- !",)),
        ("卡片下缩进解读", side_md(ok2[:1] + ["  - Mock reading"] + ok2[1:]), ("解读",)),
        ("两行口径", side_md(ok2, extra="口径：A\nSource: B"), ("口径",)),
        ("两个小标题", side_md(ok2, extra="### A\n### B"), ("###",)),
    ]
    for name, md, needles in cases:
        r = generate(md)
        check(f"stats-side：{name} → 报错含页标题", deck_error(r, TITLE, *needles),
              (r.rc, r.stderr.strip()[-200:]))


def test_overflow_warnings():
    """文字估计放不下时警告（含页标题）、照常生成；正常文稿没有警告。"""
    r = generate(MD)
    check("stats-side：正常文稿没有警告", not warnings(r.stderr), r.stderr)
    ok2 = ["- A | 1 | n", "- B | 2 | n"]
    long_text = "这是一条很长的模拟说明文字" * 6
    cases = [
        ("结论要点太长", side_md(ok2, points=[long_text] * 4), "结论要点"),
        ("卡片说明太长", side_md(["- A | 1 | " + long_text * 2, "- B | 2 | n"]), "说明"),
        ("口径太长", side_md(ok2, extra="口径：" + long_text), "口径"),
    ]
    for name, md, needle in cases:
        r = generate(md)
        w = [x for x in warnings(r.stderr) if TITLE in x and needle in x]
        check(f"stats-side：{name} → 警告含页标题、照常生成", r.rc == 0 and w, r.stderr)

    r, s = page(side_md(["- A | 1,234,567 pcs | n", "- B | 2 | n"]))
    if s is None:
        return
    sizes = {st[1] for nb in shapes_named(s, "Side Number") for st in runs(nb)[:1]}
    check("stats-side：数字太长 → 所有大数字统一缩小并警告",
          len(sizes) == 1 and sizes.pop() < 60
          and any(TITLE in x and "缩小" in x for x in warnings(r.stderr)), r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_cards()
    test_conclusion_area()
    test_conclusion_options()
    test_red_and_units()
    test_errors()
    test_overflow_warnings()
    finish()
