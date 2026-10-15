"""timeline 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_timeline.py
检查：通用页面装饰（标题、Tag、红条、不越界）；节点数 = 条目数、等距、在槽位内；
日期在线上、标题说明在线下且文字正确；字号阶梯；槽位占位框已删；条数 / 条目格式报错；
文字估计溢出警告；banner 以外只有红条用红。
"""
import hashlib

from deckcheck import (BRAND_RED, CONTENT_SLOT_IN, DOING_AMBER, DONE_GREEN, EMU, LAYOUT_INDEX,
                       body_slide, caption_bar, caption_style_problems, center_x, center_y,
                       check, deck_error, emu_rect, fill_color, finish, generate, geometry,
                       inside, line_color, named, out_of_bounds, paragraphs, placeholder,
                       red_elements, run_style, shapes_named, slide_xmls, tag_shape, warnings)

NAME = "timeline"
TITLE = "Mock Timeline Page"
MD = """
---
month: 2026-10
author: Mock.Author
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
SLOT = emu_rect(CONTENT_SLOT_IN)


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
month: 2026-10
author: Mock.Author
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
    r = generate(deck(["!!" + SIX[0]] + SIX[1:3], title="Mock Double Key"))
    check("timeline !! 两个叹号：报错含页标题和 !!", deck_error(r, "Mock Double Key", "!!"),
          r.stderr)
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


# ---- 旧写法兼容：不写状态时与 #24 改动前的输出逐字节一致 ----------------------------

# 改动前（集成分支 d046835）生成的正文页 slide2.xml 的 sha256
LEGACY_SHA = {
    "MD": "87a0dcae31ea19eca85a4df75fc1e2f4edc2d9ef975db5d4e81373584ff4cb6c",
    "SIX": "b4663faad56844ea1ce6fe8c5d3fb69f9955a1bff35018ed69c3c4520d6da00b",
}


def test_legacy_bytes():
    """不写状态的旧写法：正文页 slide XML 与改动前逐字节一致（只用黑白灰）。"""
    for name, md in (("MD", MD), ("SIX", deck(SIX))):
        r = generate(md, images=IMAGES)
        xml = slide_xmls(r.path).get("ppt/slides/slide2.xml", b"") if r.rc == 0 else b""
        check(f"timeline 旧写法 {name}：slide XML 与改动前逐字节一致",
              hashlib.sha256(xml).hexdigest() == LEGACY_SHA[name], r.stderr)


# ---- 状态着色（spec #20 / #24）----------------------------------------------------

# 6 条：3 个关键里程碑（!）、第 5 条进行中
STATUS6 = ["Jul | Kick-off | Mock scope agreed | 完成",
           "!Aug | Form live | Mock form opened | done",
           "Aug | Codes on | One week late | 已完成",
           "!Sep | Pilot | Mock workshop switched | DONE",
           "Oct | Review | Mock data collecting | 进行中",
           "!Nov | Rollout | Mock second site | 未完成"]
STATUS6_ST = ["done", "done", "done", "done", "doing", "todo"]
STATUS6_KEY = [False, True, False, True, False, True]


def status_slide(items=STATUS6, title=TITLE):
    r = generate(deck(items, title=title))
    s = body_slide(r)
    check(f"timeline 状态 {len(items)} 条：生成了正文页", r.rc == 0 and s is not None, r.stderr)
    return r, s


def test_status_nodes():
    """每条一个节点：已完成实心绿、进行中实心琥珀、未完成白底红描边（不实心填红）。"""
    r, s = status_slide()
    if s is None:
        return
    nodes = shapes_named(s, "Milestone Node")
    check("timeline 状态：6 条 → 6 个节点", len(nodes) == 6, [n.name for n in nodes])
    if len(nodes) != 6:
        return
    want_fill = {"done": DONE_GREEN, "doing": DOING_AMBER, "todo": "FFFFFF"}
    got = [(fill_color(n), line_color(n)) for n in nodes]
    check("timeline 状态：节点填充按状态（未完成白底）",
          [g[0] for g in got] == [want_fill[st] for st in STATUS6_ST], got)
    check("timeline 状态：未完成节点红描边",
          all(g[1] == BRAND_RED for g, st in zip(got, STATUS6_ST) if st == "todo"), got)
    check("timeline 状态：整页没有实心红填充（红条除外）",
          not [sh.name for sh in s.shapes
               if sh.name != "Caption Bar" and fill_color(sh) == BRAND_RED])
    check("timeline 状态：不再画旧的黑白灰节点", not shapes_named(s, "Timeline Node"))


def test_status_emphasis():
    """关键里程碑是菱形且比普通节点大；进行中比普通节点大、带外圈和“当前”标签，日期加粗放大。"""
    r, s = status_slide()
    if s is None:
        return
    nodes = shapes_named(s, "Milestone Node")
    if len(nodes) != 6:
        check("timeline 状态：6 个节点", False, len(nodes))
        return
    geo = [geometry(n) for n in nodes]
    check("timeline 状态：关键里程碑是菱形、其余是圆",
          geo == ["diamond" if k else "ellipse" for k in STATUS6_KEY], geo)
    plain = nodes[0].width     # 第 1 条：普通、已完成
    check("timeline 状态：关键里程碑比普通节点大",
          all(n.width > plain for n, k in zip(nodes, STATUS6_KEY) if k),
          [n.width for n in nodes])
    check("timeline 状态：进行中节点比普通节点大", nodes[4].width > plain,
          (nodes[4].width, plain))
    check("timeline 状态：节点都以横线为中心",
          len({n.top + n.height // 2 for n in nodes}) == 1)
    ring = [sh for sh in s.shapes if sh.name == "Current Ring"]
    check("timeline 状态：进行中带一个外圈（琥珀描边、比节点大、同心）",
          len(ring) == 1 and line_color(ring[0]) == DOING_AMBER
          and ring[0].width > nodes[4].width
          and abs(center_x(ring[0]) - center_x(nodes[4])) <= 2, [sh.name for sh in ring])
    tag = [sh for sh in s.shapes if sh.name == "Current Tag"]
    check("timeline 状态：一个“当前”标签，在进行中节点正上方、日期之上",
          len(tag) == 1 and tag[0].text_frame.text == "当前"
          and abs(center_x(tag[0]) - center_x(nodes[4])) <= 2
          and tag[0].top + tag[0].height <= shapes_named(s, "Milestone Date")[4].top,
          [(sh.name, sh.text_frame.text) for sh in tag])
    dates = shapes_named(s, "Milestone Date")
    check("timeline 状态：日期 6 个、文字去掉了 !",
          [d.text_frame.text for d in dates] == ["Jul", "Aug", "Aug", "Sep", "Oct", "Nov"],
          [d.text_frame.text for d in dates])
    if len(dates) == 6:
        cur, other = run_style(dates[4]), run_style(dates[0])
        check("timeline 状态：进行中日期加粗、近黑、比普通日期大",
              cur[1] and cur[2] == "1A1A1A" and cur[0] > other[0], (cur, other))
    r, s = status_slide([x.replace("进行中", "未完成") for x in STATUS6])
    if s is not None:
        check("timeline 没有进行中：不画外圈和“当前”标签",
              not [sh.name for sh in s.shapes if sh.name.startswith("Current")])


def dash(shape):
    el = shape._element.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}"
                             "prstDash")
    return el.get("val") if el is not None else None


def test_status_lines():
    """已完成的那段线绿色实线（首节点 → 进行中），后面灰色虚线；已完成节点上有白色对勾。"""
    r, s = status_slide()
    if s is None:
        return
    nodes = shapes_named(s, "Milestone Node")
    prog, rest = named(s, "Progress Line"), named(s, "Remaining Line")
    check("timeline 状态：一条绿色进度线、一条剩余虚线", len(prog) == len(rest) == 1,
          (len(prog), len(rest)))
    if len(prog) == len(rest) == 1 and len(nodes) == 6:
        p, q = prog[0], rest[0]
        check("timeline 状态：进度线绿色实线，从首节点到进行中节点",
              line_color(p) == DONE_GREEN and dash(p) is None
              and abs(p.left - center_x(nodes[0])) <= 2
              and abs(p.left + p.width - center_x(nodes[4])) <= 2,
              (line_color(p), dash(p)))
        check("timeline 状态：剩余线灰色虚线，从进行中节点到末节点",
              line_color(q) == "BFBFBF" and dash(q) not in (None, "solid")
              and abs(q.left - center_x(nodes[4])) <= 2
              and abs(q.left + q.width - center_x(nodes[5])) <= 2,
              (line_color(q), dash(q)))
        check("timeline 状态：线在节点下层",
              list(s.shapes).index(q) < list(s.shapes).index(nodes[0]))
    marks = shapes_named(s, "Milestone Check")
    check("timeline 状态：4 个已完成节点各有白色对勾",
          len(marks) == 4 and all(line_color(m) == "FFFFFF" for m in marks),
          [m.name for m in marks])
    check("timeline 状态：对勾编号对应节点、落在节点内",
          [m.name for m in marks] == [f"Milestone Check {i}" for i in (1, 2, 3, 4)]
          and all(nodes[i].left <= m.left and m.left + m.width <= nodes[i].left + nodes[i].width
                  for i, m in enumerate(marks)), [m.name for m in marks])
    # 全部完成：整条绿线，没有虚线；全部未完成：整条虚线，没有绿线
    for label, st, want in (("全部完成", "完成", (1, 0)), ("全部未完成", "未完成", (0, 1))):
        items = [x.rsplit("|", 1)[0] + "| " + st for x in STATUS6]
        r, s = status_slide(items)
        if s is not None:
            got = (len(named(s, "Progress Line")), len(named(s, "Remaining Line")))
            check(f"timeline {label}：进度线 / 剩余线 = {want}", got == want, got)


def test_status_text_and_legend():
    """标题 + 说明在节点下方居中；右上角图例 4 项；所有形状在槽位内、不越界。"""
    r, s = status_slide()
    if s is None:
        return
    nodes = shapes_named(s, "Milestone Node")
    bodies = shapes_named(s, "Milestone Text")
    want = [[x.split("|")[1].strip(), x.split("|")[2].strip()] for x in STATUS6]
    check("timeline 状态：标题 + 说明文字正确", [paragraphs(b) for b in bodies] == want,
          [paragraphs(b) for b in bodies])
    if len(bodies) == len(nodes) == 6:
        ring = named(s, "Current Ring")
        lowest = max(sh.top + sh.height for sh in nodes + ring)
        check("timeline 状态：正文在所有节点和外圈下方、与节点居中",
              all(b.top >= lowest and abs(center_x(b) - center_x(nd)) <= 2
                  for b, nd in zip(bodies, nodes)))
        title_pt = [run_style(b, 0) for b in bodies]
        check("timeline 状态：未完成的标题灰色，其余近黑",
              [t[2] for t in title_pt] == ["6B6B6B" if st == "todo" else "1A1A1A"
                                            for st in STATUS6_ST], title_pt)
        check("timeline 状态：关键里程碑 / 进行中的标题比普通的大",
              all(title_pt[i][0] > title_pt[0][0] for i in (1, 3, 4, 5)), title_pt)
    icons, labels = shapes_named(s, "Legend Icon"), shapes_named(s, "Legend Label")
    check("timeline 状态：图例 4 项文字",
          [l.text_frame.text for l in labels] == ["已完成", "进行中", "未完成", "关键里程碑"],
          [l.text_frame.text for l in labels])
    if len(icons) == 4:
        check("timeline 状态：图例图标按状态着色、关键里程碑是菱形",
              [(geometry(i), fill_color(i)) for i in icons] ==
              [("ellipse", DONE_GREEN), ("ellipse", DOING_AMBER), ("ellipse", "FFFFFF"),
               ("diamond", "1A1A1A")] and line_color(icons[2]) == BRAND_RED,
              [(geometry(i), fill_color(i), line_color(i)) for i in icons])
        checks = [sh for sh in s.shapes if sh.name.startswith("Legend Check")]
        check("timeline 状态：图例对勾带编号 Legend Check 1、在已完成图标中心",
              [c.name for c in checks] == ["Legend Check 1"]
              and abs(center_x(checks[0]) - center_x(icons[0])) < 0.05 * EMU,
              [c.name for c in checks])
    else:
        check("timeline 状态：图例 4 个图标", False, len(icons))
    if icons and labels:
        top_of_body = min(sh.top for sh in named(s, "Current Tag") + shapes_named(s, "Milestone Date"))
        check("timeline 状态：图例在右上角、在“当前”标签和日期之上",
              max(sh.top + sh.height for sh in icons + labels) <= top_of_body
              and labels[-1].left + labels[-1].width > emu_rect(CONTENT_SLOT_IN)[0]
              + emu_rect(CONTENT_SLOT_IN)[2] * 0.8)
    body = [sh for sh in s.shapes if not sh.is_placeholder
            and sh.name not in ("Caption Bar", "Month Tag")]
    check("timeline 状态：内容形状都在槽位内",
          body and all(inside(sh, CONTENT_SLOT_IN) for sh in body),
          [sh.name for sh in body if not inside(sh, CONTENT_SLOT_IN)])
    check("timeline 状态：不越界、不压 banner 和页脚", not out_of_bounds(r.prs, [s]),
          out_of_bounds(r.prs, [s]))
    check("timeline 状态：空的槽位占位框已删掉", placeholder(s, 19) is None)


def test_status_errors():
    """多个进行中、状态值写错、只有部分写了状态：非零退出，信息含页标题。"""
    two = STATUS6[:3] + [STATUS6[3].replace("DONE", "进行中")] + STATUS6[4:]
    r = generate(deck(two, title="Mock Two Doing"))
    check("timeline 两个进行中：报错含页标题", deck_error(r, "Mock Two Doing", "进行中"),
          r.stderr)
    bad = STATUS6[:2] + ["Aug | Codes on | One week late | finished"] + STATUS6[3:]
    r = generate(deck(bad, title="Mock Bad Status"))
    check("timeline 状态值写错：报错含页标题和原值",
          deck_error(r, "Mock Bad Status", "finished"), r.stderr)
    part = STATUS6[:2] + ["Aug | Codes on | One week late"] + STATUS6[3:]
    r = generate(deck(part, title="Mock Partial"))
    check("timeline 部分写了状态：报错含页标题和没写的条号",
          deck_error(r, "Mock Partial", "3"), r.stderr)


def test_status_red():
    """状态色只在状态元素上：用红的只有未完成节点、图例“未完成”图标和底部红条，且都不实心填红。"""
    r, s = status_slide()
    if s is None:
        return
    reds = sorted(red_elements(s))
    check("timeline 状态：红色只出现在未完成节点和图例“未完成”图标上",
          reds == ["Legend Icon 3", "Milestone Node 6"], reds)
    greens = sorted(sh.name for sh in s.shapes
                    if DONE_GREEN in {fill_color(sh), line_color(sh)})
    check("timeline 状态：绿色只在已完成节点、进度线、图例“已完成”图标上",
          greens == sorted(["Legend Icon 1", "Progress Line"]
                           + [f"Milestone Node {i}" for i in (1, 2, 3, 4)]), greens)
    ambers = sorted(sh.name for sh in s.shapes
                    if DOING_AMBER in {fill_color(sh), line_color(sh)})
    check("timeline 状态：琥珀只在进行中节点、外圈、图例“进行中”图标上",
          ambers == ["Current Ring", "Legend Icon 2", "Milestone Node 5"], ambers)


def test_key_without_status():
    """不写状态但标了 !：照黑白灰画，关键里程碑是放大的深灰菱形；其余节点与旧写法相同。"""
    items = ["Jan | Kick-off | Mock scope agreed", "!Mar | Pilot | Two sample teams",
             "Jun | Rollout | Mock release"]
    r = generate(deck(items))
    s = body_slide(r)
    if s is None:
        check("timeline 旧写法带 !：生成了正文页", False, r.stderr)
        return
    nodes = shapes_named(s, "Timeline Node")
    check("timeline 旧写法带 !：第 2 个节点是放大的菱形、其余是圆",
          [geometry(n) for n in nodes] == ["ellipse", "diamond", "ellipse"]
          and nodes[1].width > nodes[0].width, [geometry(n) for n in nodes])
    check("timeline 旧写法带 !：日期去掉了 !",
          shapes_named(s, "Timeline Date")[1].text_frame.text == "Mar")
    check("timeline 旧写法带 !：没有图例和状态色", not shapes_named(s, "Legend Icon")
          and red_elements(s) == [])


def overlap(a, b):
    return (a.left < b.left + b.width and b.left < a.left + a.width
            and a.top < b.top + b.height and b.top < a.top + a.height)


def test_legend_with_tag():
    """写了 Tag 时右上角有月份标识：图例让到它下方，不重叠，仍在“当前”标签之上。"""
    md = deck(STATUS6).replace("Layout: timeline", "Layout: timeline\nTag: Oct")
    r = generate(md)
    s = body_slide(r)
    if s is None:
        check("timeline 状态 + Tag：生成了正文页", False, r.stderr)
        return
    tag = tag_shape(s)
    legend = shapes_named(s, "Legend Icon") + shapes_named(s, "Legend Label")
    check("timeline 状态 + Tag：图例不压月份标识",
          tag is not None and legend and not any(overlap(tag, x) for x in legend),
          [x.name for x in legend if tag is not None and overlap(tag, x)])
    cur = named(s, "Current Tag")
    check("timeline 状态 + Tag：图例仍在“当前”标签之上",
          cur and max(x.top + x.height for x in legend) <= cur[0].top)


if __name__ == "__main__":
    test_chrome()
    test_nodes()
    test_text_positions()
    test_errors()
    test_overflow_warning()
    test_red_discipline()
    test_legacy_bytes()
    test_status_nodes()
    test_status_emphasis()
    test_status_lines()
    test_status_text_and_legend()
    test_status_errors()
    test_status_red()
    test_key_without_status()
    test_legend_with_tag()
    finish()
