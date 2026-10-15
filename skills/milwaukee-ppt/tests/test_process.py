"""process 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_process.py
卡片形状名约定：Process Card N（卡片，内含步骤名 + 说明）、Process Number N（序号圆）。
"""
import re

from deckcheck import (CONTENT_SLOT_IN, EMU, INK, LAYOUT_INDEX, body_slide, bottom, caption_bar,
                       caption_style_problems, center_x, center_y, check, fill_color, finish,
                       generate, geometry, line_color, one, out_of_bounds, paragraphs,
                       placeholder, red_elements, run_styles, shapes_named, tag_shape, warnings)

NAME = "process"
TITLE = "Mock Process Page"
MD = """
---
month: 2026-10
author: Mock.Author
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
month: 2026-10
author: Mock.Author
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


# ---- 方向 C（通用 / 项目汇报模式）：编号圆 + 连接线，标题和说明居中在圆下，不画卡片 ----

def general_md(steps, title=TITLE, next_line=True):
    body = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, start=1))
    nxt = "Next: 9 月推广到 A 仓\n" if next_line else ""
    return f"""
---
title: Mock Deck
date: 14 Oct 2026
---

# {title}
## Mock Action Title
Layout: process
{body}
三步完成排班，司机不再凭经验排队
{nxt}"""


C_STEPS = ["登记 | 交班时登记剩余电量", "排队 | 系统按电量排序", "充电 | 到点去指定充电位"]
WHITE = "FFFFFF"
NEAR_BLACK = "333333"
GRAY_LINE = "BFBFBF"


def test_general_mode_marks_and_lines():
    """C 模式：N 个黑底白字编号圆、N-1 条灰色连接线，标题 24pt bold、说明 18pt 近黑居中在圆下。"""
    for steps in (C_STEPS, FIVE):
        n = len(steps)
        r = generate(general_md(steps))
        check(f"C process {n} 步：退出码 0", r.rc == 0, r.stderr)
        s = body_slide(r)
        if s is None:
            continue
        names = [sh.name for sh in s.shapes]
        check(f"C process {n} 步：不画卡片和旧序号圆",
              not shapes_named(s, "Process Card") and not shapes_named(s, "Process Number"),
              names)
        marks = shapes_named(s, "Process Mark")
        lines = shapes_named(s, "Process Line")
        titles = shapes_named(s, "Process Title")
        descs = shapes_named(s, "Process Desc")
        check(f"C process {n} 步：{n} 个编号圆、{n - 1} 条连接线、{n} 个标题和说明",
              (len(marks), len(lines), len(titles), len(descs)) == (n, n - 1, n, n), names)
        if (len(marks), len(lines), len(titles), len(descs)) != (n, n - 1, n, n):
            continue
        check(f"C process {n} 步：编号圆是黑底圆、白色粗体编号 1..{n}",
              all(geometry(m) == "ellipse" and fill_color(m) == INK
                  and m.width == m.height and m.text_frame.text == str(i)
                  and {(b, c) for _, b, c in run_styles(m)} == {(True, WHITE)}
                  for i, m in enumerate(marks, start=1)),
              [(geometry(m), fill_color(m), m.text_frame.text) for m in marks])
        check(f"C process {n} 步：编号圆等大、同一水平线",
              len({m.width for m in marks}) == 1 and len({m.top for m in marks}) == 1)
        check(f"C process {n} 步：连接线灰色、水平、夹在相邻两圆之间不相压",
              all(line_color(ln) == GRAY_LINE and ln.height == 0
                  and abs(ln.top - center_y(a)) <= 2
                  and ln.left >= a.left + a.width and ln.left + ln.width <= b.left
                  for ln, a, b in zip(lines, marks, marks[1:])),
              [(line_color(ln), ln.left / EMU, ln.top / EMU) for ln in lines])
        texts_ok = [paragraphs(t) for t in titles] == [[x.split(" | ")[0]] for x in steps] \
            and [paragraphs(d) for d in descs] == [[x.split(" | ")[1]] for x in steps]
        check(f"C process {n} 步：标题 = 步骤名、说明 = 一句说明", texts_ok,
              ([paragraphs(t) for t in titles], [paragraphs(d) for d in descs]))
        check(f"C process {n} 步：标题 24pt bold 近黑、说明 18pt 不加粗 #333333",
              all(run_styles(t) == {(24.0, True, INK)} for t in titles)
              and all(run_styles(d) == {(18.0, False, NEAR_BLACK)} for d in descs),
              (run_styles(titles[0]), run_styles(descs[0])))
        check(f"C process {n} 步：标题、说明在圆下方，水平居中对齐圆心",
              all(t.top >= bottom(m) and d.top >= bottom(t)
                  and abs(center_x(t) - center_x(m)) <= 2 and abs(center_x(d) - center_x(m)) <= 2
                  and t.text_frame.paragraphs[0].alignment == 2
                  and d.text_frame.paragraphs[0].alignment == 2
                  for m, t, d in zip(marks, titles, descs)),
              [(m.top / EMU, t.top / EMU, d.top / EMU) for m, t, d in zip(marks, titles, descs)])
        check(f"C process {n} 步：编号圆铺满正文区宽度（首末列中心在 1/2n 处）",
              abs(center_x(marks[0]) - (0.56 + 12.2 / (2 * n)) * EMU) <= 0.02 * EMU
              and abs(center_x(marks[-1]) - (0.56 + 12.2 - 12.2 / (2 * n)) * EMU) <= 0.02 * EMU,
              (center_x(marks[0]) / EMU, center_x(marks[-1]) / EMU))
        rule = one(s, "Next Rule")
        lead = one(s, "Lead")
        top_in = bottom(lead) / EMU + 0.19
        low_in = rule.top / EMU - 0.10
        grp_top = min(m.top for m in marks) / EMU
        grp_bot = max(bottom(d) for d in descs) / EMU
        check(f"C process {n} 步：整组在正文区内、垂直居中",
              grp_top >= top_in - 0.01 and grp_bot <= low_in + 0.01
              and abs((grp_top - top_in) - (low_in - grp_bot)) <= 0.05,
              (top_in, grp_top, grp_bot, low_in))
        check(f"C process {n} 步：banner 以外只有 lead 竖线用红",
              red_elements(s) == ["Lead Accent"], red_elements(s))
        check(f"C process {n} 步：正常说明没有警告", not warnings(r.stderr), r.stderr)


# 3 步时说明框约 3.67" 宽，18pt 汉字约 0.25" → 每行约 14 字
WIDOW = "每班交接时登记叉车剩余电量和位置"          # 16 字：第二行只剩 2 字
TOO_LONG = "交班时由司机在终端登记剩余电量，系统按电量和到达时间排序，再推送充电时段"  # 3 行
TWO_LINES = "交班时登记剩余电量，系统按电量自动排序"     # 19 字：两行，末行 5 字


def test_general_mode_wrap_warning():
    """C 模式：说明超过两行或末行只剩 ≤2 字时警告（含页标题和步骤名）；正常两行不警告。"""
    for label, desc, want in (("末行只剩两字", WIDOW, True), ("超过两行", TOO_LONG, True),
                              ("正常两行", TWO_LINES, False)):
        steps = [f"登记 | {desc}", "排队 | 系统按电量排序", "充电 | 到点去指定充电位"]
        r = generate(general_md(steps, title="Wrap Page"))
        w = [x for x in warnings(r.stderr) if "Wrap Page" in x and "折行" in x and "登记" in x]
        check(f"C process：{label}{'有' if want else '没有'}折行警告",
              r.rc == 0 and len(w) == (1 if want else 0), r.stderr)


def test_monthly_no_wrap_warning():
    """月报模式不变：同样的说明不报折行警告（卡片画法另有溢出警告口径）。"""
    r = generate(steps_md([f"登记 | {WIDOW}", "排队 | 系统按电量排序", "充电 | 到点去指定充电位"]))
    check("月报 process：不报折行警告", not [x for x in warnings(r.stderr) if "折行" in x], r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_cards_text()
    test_geometry()
    test_slot_cleared_and_colors()
    test_step_count_errors()
    test_overflow_warning()
    test_general_mode_marks_and_lines()
    test_general_mode_wrap_warning()
    test_monthly_no_wrap_warning()
    finish()
