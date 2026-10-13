"""stats 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_stats.py
"""
from deckcheck import (LAYOUT_INDEX, caption_bar, caption_style_problems, check,
                       finish, generate, out_of_bounds, paragraphs, placeholder,
                       red_elements, tag_shape, warnings)

NAME = "stats"
TITLE = "Mock Stats Page"
MD = """
---
title: Mock Deck
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


def body_slide(r):
    return r.slides[1] if len(r.slides) > 1 else None


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


EMU = 914400
# 模板 layout 5 槽位 idx 18「Stats Area」（#13 定稿，英寸）
SLOT_L, SLOT_T, SLOT_W, SLOT_H = 0.56, 1.30, 12.21, 4.30


def shapes_named(slide, prefix):
    """按名字前缀取形状（如 "Stat Card"），按序号排好。"""
    found = [sh for sh in slide.shapes if sh.name.startswith(prefix + " ")]
    return sorted(found, key=lambda sh: int(sh.name.rsplit(" ", 1)[1]))


def stats_md(items, title=TITLE):
    body = "\n".join(items)
    return f"""
---
title: Mock Deck
date: 13 Oct 2026
---

# {title}
## Mock Action Title
Layout: stats
{body}
Mock conclusion.
"""


def run_style(shape):
    """文本框里所有 run 的 (字号pt, 加粗, 颜色)；集合，便于断言“全部一致”。"""
    out = set()
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            f = run.font
            color = str(f.color.rgb) if f.color and f.color.type is not None else None
            out.add((f.size.pt if f.size else None, bool(f.bold), color))
    return out


def test_card_text_hierarchy():
    """每张卡：小标签在上、大数字居中、说明在下，都在卡内；层级靠字号、字重和灰阶。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    if s is None:
        check("stats：生成了正文页", False, r.stderr)
        return
    cards = shapes_named(s, "Stat Card")
    labels = shapes_named(s, "Stat Label")
    numbers = shapes_named(s, "Stat Number")
    notes = shapes_named(s, "Stat Note")
    check("stats：每张卡都有标签 / 数字 / 说明",
          len(cards) == len(labels) == len(numbers) == len(notes) == 3,
          (len(cards), len(labels), len(numbers), len(notes)))
    if not len(cards) == len(labels) == len(numbers) == len(notes) == 3:
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

    def within(inner, outer):
        return (inner.left >= outer.left and inner.top >= outer.top
                and inner.left + inner.width <= outer.left + outer.width
                and inner.top + inner.height <= outer.top + outer.height)

    check("stats：标签、数字、说明都在各自的卡里",
          all(within(x, c) for c, trio in zip(cards, zip(labels, numbers, notes))
              for x in trio))
    check("stats：自上而下是标签 → 数字 → 说明",
          all(lb.top + lb.height <= nb.top and nb.top + nb.height <= nt.top
              for lb, nb, nt in zip(labels, numbers, notes)))
    check("stats：标签 12pt 加粗 #6B6B6B",
          all(run_style(x) == {(12.0, True, "6B6B6B")} for x in labels),
          [run_style(x) for x in labels])
    check("stats：说明 14pt 不加粗 #6B6B6B",
          all(run_style(x) == {(14.0, False, "6B6B6B")} for x in notes),
          [run_style(x) for x in notes])
    sizes = {st[0] for x in numbers for st in run_style(x)}
    check("stats：大数字 60pt 加粗（数字都放得下时）",
          sizes == {60.0} and all(st[1] for x in numbers for st in run_style(x)),
          [run_style(x) for x in numbers])
    P_STYLE = "{http://schemas.openxmlformats.org/presentationml/2006/main}style"
    check("stats：卡片扁平（浅灰底、无描边、不引用主题样式，渲染器不会补阴影）",
          all(c._element.find(P_STYLE) is None and str(c.fill.fore_color.rgb) == "F5F5F5"
              and c.line.fill.type is not None for c in cards),
          [c.name for c in cards if c._element.find(P_STYLE) is not None])
    check("stats：没有字号警告", not warnings(r.stderr), r.stderr)


def test_red_discipline():
    """有一个 ! 时只有那个数字是品牌红；没有 ! 时整页（红条除外）没有红色。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    if s is None:
        check("stats：生成了正文页", False, r.stderr)
        return
    red = [x for x in red_elements(s) if x != "Caption Bar"]
    check("stats：标了 ! 的只有第 2 个数字是红色", red == ["Stat Number 2"], red)
    num2 = shapes_named(s, "Stat Number")[1:2]
    check("stats：重点数字用品牌红 DB011C",
          num2 and {st[2] for st in run_style(num2[0])} == {"DB011C"},
          num2 and run_style(num2[0]))
    others = [x for i, x in enumerate(shapes_named(s, "Stat Number")) if i != 1]
    check("stats：其余数字 #1A1A1A",
          all({st[2] for st in run_style(x)} == {"1A1A1A"} for x in others),
          [run_style(x) for x in others])

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
    }
    for name, items in cases.items():
        r = generate(stats_md(items, title=bad_title))
        check(f"stats 报错（{name}）：非零退出、信息含页标题、不出文件",
              r.rc != 0 and bad_title in r.stderr and not r.path.exists(),
              (r.rc, r.stderr))


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
    sizes = {st[0] for x in shapes_named(s, "Stat Number") for st in run_style(x)}
    check("stats 长数字：所有数字字号相同", len(sizes) == 1, sizes)
    size = next(iter(sizes)) if len(sizes) == 1 else None
    check("stats 长数字：缩到 60pt 以下但仍明显大于说明（≥ 28pt）",
          size is not None and 28 <= size < 60, sizes)
    w = [x for x in warnings(r.stderr) if long_title in x and "缩小" in x]
    check("stats 长数字：有一条缩小警告且含页标题", len(w) == 1, r.stderr)
    check("stats 长数字：仍在页面内", not out_of_bounds(r.prs, [s]),
          out_of_bounds(r.prs, [s]))


def test_cards_fill_slot():
    """卡片数 = 条目数，等宽、等间距，整体在槽位内；槽位占位框已清掉。"""
    for n in (2, 3, 4):
        items = [f"- Label {i} | {i}0% | Mock note {i}" for i in range(1, n + 1)]
        r = generate(stats_md(items))
        s = body_slide(r)
        if s is None:
            check(f"stats {n} 条：生成了正文页", False, r.stderr)
            continue
        cards = shapes_named(s, "Stat Card")
        check(f"stats {n} 条：卡片数 = 条目数", len(cards) == n, [c.name for c in cards])
        if len(cards) != n:
            continue
        widths = {c.width for c in cards}
        check(f"stats {n} 条：卡片等宽", max(widths) - min(widths) <= 2, widths)
        tol = 0.01
        inside = all(c.left >= (SLOT_L - tol) * EMU and c.top >= (SLOT_T - tol) * EMU
                     and c.left + c.width <= (SLOT_L + SLOT_W + tol) * EMU
                     and c.top + c.height <= (SLOT_T + SLOT_H + tol) * EMU
                     for c in cards)
        check(f"stats {n} 条：卡片都在槽位内", inside,
              [(c.left / EMU, c.top / EMU, c.width / EMU, c.height / EMU) for c in cards])
        span = (cards[-1].left + cards[-1].width - cards[0].left) / EMU
        check(f"stats {n} 条：卡片铺满槽位宽度", abs(span - SLOT_W) < tol, span)
        gaps = [(b.left - a.left - a.width) / EMU for a, b in zip(cards, cards[1:])]
        check(f"stats {n} 条：卡片间距统一 0.3\"",
              all(abs(g - 0.3) < tol for g in gaps), gaps)
        check(f"stats {n} 条：空的槽位占位框已清掉", placeholder(s, 18) is None)
        check(f"stats {n} 条：没有“未实现”警告",
              not [w for w in warnings(r.stderr) if "未实现" in w], r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_cards_fill_slot()
    test_card_text_hierarchy()
    test_red_discipline()
    test_errors()
    test_long_numbers_shrink_together()
    finish()
