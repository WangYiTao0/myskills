"""timeline 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_timeline.py
检查：通用页面装饰（标题、Tag、红条、不越界）；节点数 = 条目数、等距、在槽位内；
日期在线上、标题说明在线下且文字正确；字号阶梯；槽位占位框已删；条数 / 条目格式报错；
文字估计溢出警告；banner 以外只有红条用红。
"""
from deckcheck import (EMU, LAYOUT_INDEX, caption_bar, caption_style_problems, check,
                       finish, generate, out_of_bounds, paragraphs, placeholder,
                       red_elements,
                       tag_shape, warnings)

NAME = "timeline"
TITLE = "Mock Timeline Page"
MD = """
---
title: Mock Deck
date: 13 Oct 2026
---

# Mock Timeline Page
## Mock Action Title
Layout: timeline
Tag: Mar
- Jan | Kick-off | Mock scope agreed
- Mar | Pilot | Two sample teams onboard
- Jun | Rollout | Mock company-wide release
Mock one-line conclusion.
Next: Mock next step.
"""
IMAGES = {"img/shot.png": (1600, 900)}


def body_slide(r):
    return r.slides[1] if len(r.slides) > 1 else None


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD, images=IMAGES)
    check("timeline：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("timeline：生成了正文页", False, r.stderr)
        return
    check("timeline：用模板 layout 6「Timeline」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("timeline：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("timeline：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("timeline：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("timeline：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("timeline：形状在页面内、不压 banner 和页脚", not bad, bad)


# 模板 layout 6 的槽位 idx 19「Timeline Area」：0.56 / 1.30 / 12.21 / 4.30 英寸
SLOT = (int(0.56 * EMU), int(1.30 * EMU), int(12.21 * EMU), int(4.30 * EMU))


def shapes_named(slide, prefix):
    """名字以 prefix 开头的形状，按名字末尾的序号排序。"""
    found = [sh for sh in slide.shapes if sh.name.startswith(prefix)]
    return sorted(found, key=lambda sh: int(sh.name.rsplit(" ", 1)[-1]))


def center_x(sh):
    return sh.left + sh.width // 2


def center_y(sh):
    return sh.top + sh.height // 2


def inside_slot(sh):
    l, t, w, h = SLOT
    return (sh.left >= l and sh.left + sh.width <= l + w
            and sh.top >= t and sh.top + sh.height <= t + h)


def test_nodes():
    """节点数 = 条目数，等距，全部在槽位内。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    if s is None:
        check("timeline：生成了正文页", False, r.stderr)
        return
    nodes = shapes_named(s, "Timeline Node")
    check("timeline：3 条 → 3 个节点", len(nodes) == 3, [n.name for n in nodes])
    xs = [center_x(n) for n in nodes]
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    check("timeline：节点等距（误差 ≤ 2 EMU）",
          len(gaps) == 2 and gaps[0] > 0 and abs(gaps[0] - gaps[1]) <= 2, gaps)
    check("timeline：节点都在同一水平线上",
          len({center_y(n) for n in nodes}) == 1, [center_y(n) for n in nodes])
    body = [sh for sh in s.shapes if sh.name.startswith("Timeline")]
    check("timeline：时间线形状都在槽位内",
          body and all(inside_slot(sh) for sh in body),
          [sh.name for sh in body if not inside_slot(sh)])


def deck(items, title=TITLE, extra=""):
    """一页 timeline 的文稿；items 是列表行的正文（不含 "- "）。"""
    body = "\n".join(f"- {x}" for x in items)
    return f"""
---
title: Mock Deck
date: 13 Oct 2026
---

# {title}
Layout: timeline
{body}
{extra}
"""


SIX = ["Jan | Kick-off | Mock scope agreed",
       "Feb | Design | Mock layouts drafted",
       "Mar | Pilot | Two sample teams onboard",
       "Apr | Review | Mock feedback collected",
       "May | Training | Mock sessions held",
       "Jun | Rollout | Mock company-wide release"]


def run_style(sh, para):
    """第 para 段第一个 run 的 (字号 pt, 粗体, 颜色 hex)。"""
    r = sh.text_frame.paragraphs[para].runs[0]
    color = str(r.font.color.rgb) if r.font.color and r.font.color.type else None
    return (r.font.size.pt if r.font.size else None, r.font.bold, color)


def test_text_positions():
    """每个节点：日期在线上方，标题 + 说明在线下方，与节点居中对齐，文字正确。"""
    for items in (SIX[:3], SIX):
        n = len(items)
        r = generate(deck(items))
        s = body_slide(r)
        if s is None:
            check(f"timeline {n} 条：生成了正文页", False, r.stderr)
            continue
        nodes = shapes_named(s, "Timeline Node")
        dates = shapes_named(s, "Timeline Date")
        bodies = shapes_named(s, "Timeline Text")
        check(f"timeline {n} 条：节点 / 日期 / 正文各 {n} 个",
              len(nodes) == len(dates) == len(bodies) == n,
              (len(nodes), len(dates), len(bodies)))
        if not len(nodes) == len(dates) == len(bodies) == n:
            continue
        line_y = center_y(nodes[0])
        want = [tuple(x.strip() for x in it.split("|")) for it in items]
        check(f"timeline {n} 条：日期文字正确",
              [d.text_frame.text for d in dates] == [w[0] for w in want],
              [d.text_frame.text for d in dates])
        check(f"timeline {n} 条：标题 + 说明文字正确（两段）",
              [paragraphs(b) for b in bodies] == [[w[1], w[2]] for w in want],
              [paragraphs(b) for b in bodies])
        check(f"timeline {n} 条：日期整个在线上方、不碰节点",
              all(d.top + d.height <= nodes[0].top for d in dates),
              [(d.top + d.height, nodes[0].top) for d in dates])
        check(f"timeline {n} 条：标题说明整个在线下方、不碰节点",
              all(b.top >= nodes[0].top + nodes[0].height for b in bodies),
              [(b.top, line_y) for b in bodies])
        check(f"timeline {n} 条：日期和正文与节点居中对齐",
              all(abs(center_x(d) - center_x(nd)) <= 2
                  and abs(center_x(b) - center_x(nd)) <= 2
                  for d, b, nd in zip(dates, bodies, nodes)))
        check(f"timeline {n} 条：所有形状在页面内、不压 banner 和页脚",
              not out_of_bounds(r.prs, [s]), out_of_bounds(r.prs, [s]))
        check(f"timeline {n} 条：时间线形状都在槽位内",
              all(inside_slot(sh) for sh in s.shapes if sh.name.startswith("Timeline")))
        check(f"timeline {n} 条：空的槽位占位框（idx 19）已删掉",
              placeholder(s, 19) is None)
        check(f"timeline {n} 条：没有“未实现”警告",
              not [w for w in warnings(r.stderr) if "未实现" in w], r.stderr)
    if not (dates and bodies):
        check("timeline：有日期和正文可查字号", False)
        return
    # 字号阶梯（#13 定稿）：日期 12pt bold #6B6B6B；标题 18pt bold #1A1A1A；说明 14pt #6B6B6B
    check("timeline：日期 12pt 粗体灰",
          run_style(dates[0], 0) == (12.0, True, "6B6B6B"), run_style(dates[0], 0))
    check("timeline：标题 18pt 粗体近黑",
          run_style(bodies[0], 0) == (18.0, True, "1A1A1A"), run_style(bodies[0], 0))
    check("timeline：说明 14pt 灰",
          run_style(bodies[0], 1)[0] == 14.0 and run_style(bodies[0], 1)[2] == "6B6B6B",
          run_style(bodies[0], 1))


def test_errors():
    """条数超出 3–6、条目没写成「日期 | 标题 | 说明」：非零退出，错误信息含页标题。"""
    for name, items in (("2 条", SIX[:2]), ("7 条", SIX + ["Jul | Extra | Mock"])):
        r = generate(deck(items, title="Mock Bad Count"))
        check(f"timeline {name}：非零退出", r.rc != 0, r.rc)
        check(f"timeline {name}：错误信息含页标题和条数",
              "Mock Bad Count" in r.stderr and str(len(items)) in r.stderr, r.stderr)
    r = generate(deck(SIX[:2] + ["Mar | Pilot only"], title="Mock Bad Item"))
    check("timeline 条目缺说明：非零退出", r.rc != 0, r.rc)
    check("timeline 条目缺说明：错误信息含页标题和该行",
          "Mock Bad Item" in r.stderr and "Pilot only" in r.stderr, r.stderr)


def test_overflow_warning():
    """说明估计放不下：警告（含页标题），但照常生成。正常长度不警告。"""
    long = "Mock description that keeps going " * 12
    items = SIX[:5] + [f"Jun | Rollout | {long.strip()}"]
    r = generate(deck(items, title="Mock Long Page"))
    w = [x for x in warnings(r.stderr) if "Mock Long Page" in x and "溢出" in x]
    check("timeline 说明过长：退出码 0", r.rc == 0, r.stderr)
    check("timeline 说明过长：有溢出警告且含页标题", len(w) == 1, r.stderr)
    r = generate(deck(SIX))
    check("timeline 正常长度：没有警告", not warnings(r.stderr), r.stderr)


def test_red_discipline():
    """banner 以外只有底部红条用红：节点、横线、文字都是黑白灰。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    reds = red_elements(s) if s is not None else ["(没有正文页)"]
    check("timeline：只有底部红条用红", reds == ["Caption Bar"], reds)


if __name__ == "__main__":
    test_chrome()
    test_nodes()
    test_text_positions()
    test_errors()
    test_overflow_warning()
    test_red_discipline()
    finish()
