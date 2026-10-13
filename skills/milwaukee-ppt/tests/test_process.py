"""process 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_process.py
卡片形状名约定：Process Card N（卡片，内含步骤名 + 说明）、Process Number N（序号圆）。
"""
import re

from deckcheck import (CONTENT_SLOT_IN, EMU, LAYOUT_INDEX, body_slide, caption_bar,
                       caption_style_problems, check, finish, generate, out_of_bounds,
                       paragraphs, placeholder, red_elements, shapes_named, tag_shape,
                       warnings)

NAME = "process"
TITLE = "Mock Process Page"
MD = """
---
title: Mock Deck
date: 13 Oct 2026
---

# Mock Process Page
## Mock Action Title
Layout: process
Tag: Mar
1. Collect | Gather mock requests in one form
2. Review | Weekly triage of sample items
3. Ship | Publish the mock result
Mock one-line conclusion.
Next: Mock next step.
"""
IMAGES = {"img/shot.png": (1600, 900)}


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD, images=IMAGES)
    check("process：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("process：生成了正文页", False, r.stderr)
        return
    check("process：用模板 layout 4「Process」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("process：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("process：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("process：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("process：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("process：形状在页面内、不压 banner 和页脚", not bad, bad)


def steps_md(steps, title=TITLE):
    body = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, start=1))
    return f"""
---
title: Mock Deck
date: 13 Oct 2026
---

# {title}
## Mock Action Title
Layout: process
{body}
Mock one-line conclusion.
"""


def test_cards_text():
    """每张卡片里是步骤名 + 说明，序号圆从 1 开始连续。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    cards = shapes_named(s, "Process Card") if s else []
    check("process：3 步 → 3 张卡片", len(cards) == 3, [c.name for c in cards])
    check("process：卡片文字 = 步骤名 + 说明",
          [paragraphs(c) for c in cards] == [
              ["Collect", "Gather mock requests in one form"],
              ["Review", "Weekly triage of sample items"],
              ["Ship", "Publish the mock result"]],
          [paragraphs(c) for c in cards])
    nums = shapes_named(s, "Process Number") if s else []
    check("process：序号圆 1、2、3",
          [n.text_frame.text for n in nums] == ["1", "2", "3"],
          [n.text_frame.text for n in nums])


SLOT = CONTENT_SLOT_IN     # 槽位 idx 17「Process Area」
FIVE = ["Plan | Mock plan", "Build | Mock build", "Test | Mock test",
        "Ship | Mock ship", "Learn | Mock learn"]


def close(a, b, tol=0.02):
    return abs(a - b) <= tol


def test_geometry():
    """3 步和 5 步：卡片等宽、间距 0.3"、都在槽位内；序号圆 0.5"、圆心压在卡片上沿。"""
    l, t, w, h = (v * EMU for v in SLOT)
    for steps in (["A | a", "B | b", "C | c"], FIVE):
        n = len(steps)
        r = generate(steps_md(steps))
        s = body_slide(r)
        cards = shapes_named(s, "Process Card") if s else []
        nums = shapes_named(s, "Process Number") if s else []
        check(f"process {n} 步：{n} 张卡片、{n} 个序号圆",
              len(cards) == n and len(nums) == n, (len(cards), len(nums)))
        if len(cards) != n or len(nums) != n:
            continue
        widths = {c.width for c in cards}
        check(f"process {n} 步：卡片等宽", max(widths) - min(widths) <= 1, widths)
        gaps = [(b.left - (a.left + a.width)) / EMU for a, b in zip(cards, cards[1:])]
        check(f"process {n} 步：卡片间距都是 0.3\"",
              all(close(g, 0.3) for g in gaps), gaps)
        inside = all(c.left >= l - 1 and c.left + c.width <= l + w + 1
                     and c.top >= t - 1 and c.top + c.height <= t + h + 1
                     for c in cards + nums)
        check(f"process {n} 步：卡片和序号圆都在槽位矩形内", inside,
              [(x.name, x.left / EMU, x.top / EMU) for x in cards + nums])
        check(f"process {n} 步：卡片铺满槽位宽度",
              close(cards[0].left / EMU, SLOT[0])
              and close((cards[-1].left + cards[-1].width) / EMU, SLOT[0] + SLOT[2]),
              (cards[0].left / EMU, (cards[-1].left + cards[-1].width) / EMU))
        check(f"process {n} 步：序号圆直径 0.5\"、圆心在卡片上沿、落在卡片左右之内",
              all(close(c.width / EMU, 0.5) and close(c.height / EMU, 0.5)
                  and close((c.top + c.height / 2) / EMU, k.top / EMU)
                  and k.left <= c.left and c.left + c.width <= k.left + k.width
                  for c, k in zip(nums, cards)),
              [(c.top / EMU, k.top / EMU) for c, k in zip(nums, cards)])
        check(f"process {n} 步：序号 1..{n}",
              [x.text_frame.text for x in nums] == [str(i) for i in range(1, n + 1)])
        bad = out_of_bounds(r.prs, [s])
        check(f"process {n} 步：不越界", not bad, bad)


def test_slot_cleared_and_colors():
    """槽位占位框画完就删；banner 以外只有红条用红；没有箭头 / 连接线；全是原生形状。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    check("process：空的槽位占位框 idx 17 已删", placeholder(s, 17) is None)
    check("process：只有底部红条用红", red_elements(s) == ["Caption Bar"],
          red_elements(s))
    xml = s._element.xml
    geoms = re.findall(r'prstGeom prst="(\w+)"', xml)
    check("process：没有箭头和连接线",
          "p:cxnSp" not in xml and not [g for g in geoms if "arrow" in g.lower()
                                        or "chevron" in g.lower()], geoms)
    check("process：没有图片（卡片都是原生形状）", "p:pic" not in xml)


def test_step_count_errors():
    """少于 3 步或多于 5 步：非零退出，错误信息含页标题。"""
    for steps in (["A | a", "B | b"], FIVE + ["Extra | extra"]):
        r = generate(steps_md(steps, title="Bad Count Page"))
        check(f"process：{len(steps)} 步报错退出且含页标题",
              r.rc != 0 and "Bad Count Page" in r.stderr, (r.rc, r.stderr))


def test_overflow_warning():
    """说明估计会溢出卡片时警告（含页标题），不中止；正常长度不警告。"""
    long = "Mock words " * 120
    r = generate(steps_md(FIVE[:2] + [f"Long | {long}"], title="Overflow Page"))
    w = [x for x in warnings(r.stderr) if "Overflow Page" in x and "溢出" in x]
    check("process：长说明有溢出警告且含页标题", r.rc == 0 and len(w) == 1, r.stderr)
    r = generate(MD, images=IMAGES)
    check("process：正常说明没有警告", not warnings(r.stderr), r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_cards_text()
    test_geometry()
    test_slot_cleared_and_colors()
    test_step_count_errors()
    test_overflow_warning()
    finish()
