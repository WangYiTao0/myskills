"""timeline-phase 版式测试：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_timeline_phase.py
检查：通用页面装饰（标题、Tag、红条、不越界）；箭头段数 = 条目数、按状态着色、进行中更高；
日期在段上方、标记 / 说明在段下方；关键里程碑与普通节点标记不同；图例图形与段对应；
缺状态 / 多个进行中 / 状态写错 / 条数超限报错；文字溢出警告；红色只在未完成段和红条。
"""
from deckcheck import (BRAND_RED, CONTENT_SLOT_IN, DOING_AMBER, DOING_INK, DONE_GREEN,
                       LAYOUT_INDEX, body_slide, bottom, caption_bar, caption_style_problems,
                       center_x, center_y, check, deck_error, fill_color, finish, generate,
                       geometry, inside, line_color, out_of_bounds, paragraphs, placeholder,
                       red_elements, run_style, shapes_named, tag_shape, warnings)

NAME = "timeline-phase"
TITLE = "Mock Timeline Phase Page"
MD = """
---
month: 2026-10
author: Mock.Author
date: 13 Oct 2026
---

# Mock Timeline Phase Page
## Mock Action Title
Layout: timeline-phase
Tag: Mar
- 07 Jul | Mock kickoff | Mock scope agreed | done
- !04 Aug | Mock pilot | Mock form online | doing
- 03 Nov | Mock rollout | Mock second site | todo
Mock one-line conclusion.
Next: Mock next step.
"""

TODO_FILL = "FCE6E8"   # 未完成段：浅粉底

SIX = ["07 Jul | Mock kickoff | Mock scope agreed | done",
       "!04 Aug | Mock form | Mock form online | 完成",
       "25 Aug | Mock labels | Mock one week late | Done",
       "!15 Sep | Mock pilot | Mock site switched | done",
       "13 Oct | Mock recap | Mock data in progress | 进行中",
       "!03 Nov | Mock rollout | Mock second site | todo"]


def deck(items, title=TITLE, extra=""):
    """一页 timeline-phase 的文稿；items 是列表行的正文（不含 "- "）。"""
    body = "\n".join(f"- {x}" for x in items)
    return f"""
---
month: 2026-10
author: Mock.Author
date: 13 Oct 2026
---

# {title}
Layout: timeline-phase
{body}
{extra}
"""


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD)
    check("timeline-phase：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("timeline-phase：生成了正文页", False, r.stderr)
        return
    check("timeline-phase：用模板 layout 6「Timeline」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("timeline-phase：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("timeline-phase：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("timeline-phase：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("timeline-phase：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("timeline-phase：形状在页面内、不压 banner 和页脚", not bad, bad)
    check("timeline-phase：没有“未实现”警告", "未实现" not in r.stderr, r.stderr)
    check("timeline-phase：空的槽位占位框（idx 19）已删掉", placeholder(s, 19) is None)


def test_segments():
    """箭头段数 = 条目数；首段 homePlate、其余 chevron；按状态着色；进行中更高；段内是标题。"""
    for items in (SIX[:3], SIX):
        n = len(items)
        r = generate(deck(items))
        s = body_slide(r)
        if s is None:
            check(f"timeline-phase {n} 条：生成了正文页", False, r.stderr)
            continue
        segs = shapes_named(s, "Phase Segment")
        check(f"timeline-phase {n} 条：{n} 个箭头段", len(segs) == n, [x.name for x in segs])
        if len(segs) != n:
            continue
        check(f"timeline-phase {n} 条：首段 homePlate、其余 chevron",
              [geometry(x) for x in segs] == ["homePlate"] + ["chevron"] * (n - 1),
              [geometry(x) for x in segs])
        titles = [x.split("|")[1].strip() for x in items]
        check(f"timeline-phase {n} 条：段上文字是标题",
              [x.text_frame.text for x in segs] == titles,
              [x.text_frame.text for x in segs])
        check(f"timeline-phase {n} 条：段从左到右排列、同一中线",
              all(a.left + a.width <= b.left for a, b in zip(segs, segs[1:]))
              and len({center_y(x) for x in segs}) == 1,
              [(x.left, center_y(x)) for x in segs])
        check(f"timeline-phase {n} 条：段都在槽位内",
              all(inside(x, CONTENT_SLOT_IN) for x in segs))

    r = generate(deck(SIX))
    s = body_slide(r)
    segs = shapes_named(s, "Phase Segment") if s is not None else []
    if len(segs) != 6:
        check("timeline-phase：6 段可查颜色", False, r.stderr)
        return
    done, doing, todo = segs[0], segs[4], segs[5]
    check("timeline-phase：已完成段绿底、无描边、白字",
          all(fill_color(x) == DONE_GREEN and line_color(x) is None
              and run_style(x)[2] == "FFFFFF" for x in segs[:4]),
          [(fill_color(x), line_color(x), run_style(x)) for x in segs[:4]])
    check("timeline-phase：进行中段琥珀底、深色字",
          fill_color(doing) == DOING_AMBER and run_style(doing)[2] == DOING_INK,
          (fill_color(doing), run_style(doing)))
    check("timeline-phase：未完成段浅粉底 + 红描边 + 红字，不整块填红",
          fill_color(todo) == TODO_FILL and line_color(todo) == BRAND_RED
          and run_style(todo)[2] == BRAND_RED,
          (fill_color(todo), line_color(todo), run_style(todo)))
    check("timeline-phase：进行中那段更高，其余段一样高",
          doing.height > done.height and len({x.height for x in segs if x is not doing}) == 1,
          [x.height for x in segs])
    check("timeline-phase：进行中段标题字号更大",
          run_style(doing)[0] > run_style(done)[0], (run_style(doing), run_style(done)))


def test_dates_markers_texts():
    """日期在段上方；标记在段下方、细线连接；关键里程碑大黑菱形 + “关键里程碑”，
    普通节点灰色小圆点；说明在最下面；同一条的日期 / 标记 / 说明竖直对齐。"""
    r = generate(deck(SIX))
    s = body_slide(r)
    if s is None:
        check("timeline-phase：生成了正文页", False, r.stderr)
        return
    segs = shapes_named(s, "Phase Segment")
    dates = shapes_named(s, "Phase Date")
    stems = shapes_named(s, "Phase Stem")
    marks = shapes_named(s, "Phase Marker")
    texts = shapes_named(s, "Phase Text")
    labels = shapes_named(s, "Phase Key Label")
    check("timeline-phase：段 / 日期 / 细线 / 标记 / 说明各 6 个",
          [len(x) for x in (segs, dates, stems, marks, texts)] == [6] * 5,
          [len(x) for x in (segs, dates, stems, marks, texts)])
    if [len(x) for x in (segs, dates, stems, marks, texts)] != [6] * 5:
        return
    want = [[y.strip() for y in x.lstrip("!").split("|")] for x in SIX]
    check("timeline-phase：日期文字正确",
          [d.text_frame.text for d in dates] == [w[0] for w in want],
          [d.text_frame.text for d in dates])
    check("timeline-phase：说明文字正确",
          [t.text_frame.text for t in texts] == [w[2] for w in want],
          [t.text_frame.text for t in texts])
    seg_top = min(x.top for x in segs)
    seg_bottom = max(bottom(x) for x in segs)
    check("timeline-phase：日期整个在段上方", all(bottom(d) <= seg_top for d in dates))
    check("timeline-phase：标记在段下方，说明在标记下方",
          all(m.top >= seg_bottom for m in marks)
          and all(t.top >= bottom(m) for t, m in zip(texts, marks)))
    check("timeline-phase：细线从段底连到标记",
          all(abs(st.top - bottom(sg)) <= 2 and abs(bottom(st) - m.top) <= 2
              for st, sg, m in zip(stems, segs, marks)),
          [(st.top, bottom(sg), bottom(st), m.top) for st, sg, m in zip(stems, segs, marks)])
    aligned = all(abs(center_x(a) - center_x(m)) <= 2
                  for d, st, m, t in zip(dates, stems, marks, texts) for a in (d, st, t))
    check("timeline-phase：日期 / 细线 / 说明与标记竖直对齐", aligned)
    key = [m for m, w in zip(marks, SIX) if w.startswith("!")]
    plain = [m for m, w in zip(marks, SIX) if not w.startswith("!")]
    check("timeline-phase：关键里程碑是黑色菱形",
          all(geometry(m) == "diamond" and fill_color(m) == "1A1A1A" for m in key),
          [(geometry(m), fill_color(m)) for m in key])
    check("timeline-phase：普通节点是灰色小圆点",
          all(geometry(m) == "ellipse" and fill_color(m) == "BFBFBF" for m in plain),
          [(geometry(m), fill_color(m)) for m in plain])
    check("timeline-phase：关键里程碑标记比普通节点大",
          min(m.width for m in key) > max(m.width for m in plain))
    check("timeline-phase：关键里程碑下面标“关键里程碑”，编号对应条目",
          [x.name for x in labels] == ["Phase Key Label 2", "Phase Key Label 4",
                                       "Phase Key Label 6"]
          and all(x.text_frame.text == "关键里程碑" for x in labels),
          [(x.name, x.text_frame.text) for x in labels])
    by_n = {int(x.name.split()[-1]): x for x in labels}
    check("timeline-phase：“关键里程碑”在菱形和说明之间",
          all(by_n[n].top >= bottom(marks[n - 1]) and bottom(by_n[n]) <= texts[n - 1].top
              for n in by_n))
    check("timeline-phase：进行中日期 14pt 粗体近黑，其余 12pt 粗体灰",
          run_style(dates[4]) == (14.0, True, "1A1A1A")
          and all(run_style(d) == (12.0, True, "6B6B6B") for i, d in enumerate(dates) if i != 4),
          [run_style(d) for d in dates])
    check("timeline-phase：说明 14pt 灰", all(run_style(t) == (14.0, False, "6B6B6B")
                                               for t in texts))
    body = [sh for sh in s.shapes if sh.name.startswith("Phase")]
    check("timeline-phase：阶段条形状都在槽位内",
          all(inside(x, CONTENT_SLOT_IN) for x in body),
          [x.name for x in body if not inside(x, CONTENT_SLOT_IN)])


def test_legend():
    """图例：已完成 / 进行中 / 未完成 / 关键里程碑 四项，图形和阶段条对应（小箭头段 + 菱形），
    在槽位右上、日期上方，不压 Month Tag。"""
    r = generate(MD)
    s = body_slide(r)
    if s is None:
        check("timeline-phase：生成了正文页", False, r.stderr)
        return
    sw = shapes_named(s, "Legend Icon")
    lb = shapes_named(s, "Legend Label")
    check("timeline-phase 图例：四项文字",
          [x.text_frame.text for x in lb] == ["已完成", "进行中", "未完成", "关键里程碑"],
          [x.text_frame.text for x in lb])
    if len(sw) != 4 or len(lb) != 4:
        check("timeline-phase 图例：四个图形", False, [x.name for x in sw])
        return
    check("timeline-phase 图例：状态图形是箭头段（chevron），关键里程碑是菱形",
          [geometry(x) for x in sw] == ["chevron"] * 3 + ["diamond"],
          [geometry(x) for x in sw])
    check("timeline-phase 图例：颜色与阶段条一致",
          [(fill_color(x), line_color(x)) for x in sw] ==
          [(DONE_GREEN, None), (DOING_AMBER, None), (TODO_FILL, BRAND_RED), ("1A1A1A", None)],
          [(fill_color(x), line_color(x)) for x in sw])
    check("timeline-phase 图例：文字 12pt 灰", all(run_style(x) == (12.0, False, "6B6B6B")
                                                 for x in lb), [run_style(x) for x in lb])
    check("timeline-phase 图例：每个图形在自己的文字左边、同一行",
          all(bottom(a) > b.top and bottom(b) > a.top and a.left + a.width <= b.left
              for a, b in zip(sw, lb)))
    legend = sw + lb
    check("timeline-phase 图例：在槽位内", all(inside(x, CONTENT_SLOT_IN) for x in legend))
    dates = shapes_named(s, "Phase Date")
    check("timeline-phase 图例：在日期上方", all(bottom(x) <= min(d.top for d in dates)
                                               for x in legend))
    tag = tag_shape(s)
    check("timeline-phase 图例：不压 Month Tag",
          tag is not None and all(x.top >= bottom(tag) for x in legend),
          tag and [(x.name, x.top, bottom(tag)) for x in legend])


def test_red_discipline():
    """红色只出现在未完成段（描边 + 字）、图例里对应的未完成图形、底部红条。"""
    r = generate(MD)
    s = body_slide(r)
    reds = red_elements(s) if s is not None else ["(没有正文页)"]
    check("timeline-phase：只有未完成段、未完成图例、红条用红",
          sorted(reds) == sorted(["Phase Segment 3", "Legend Icon 3", "Caption Bar"]), reds)
    todo = shapes_named(s, "Phase Segment")[2] if s is not None else None
    check("timeline-phase：未完成段没有实心红填充",
          todo is not None and fill_color(todo) != BRAND_RED, todo and fill_color(todo))


def test_errors():
    """缺状态、“进行中”超过一个、状态写错、条数超限、条目格式错：非零退出，信息含页标题。"""
    cases = [
        ("缺状态", SIX[:2] + ["03 Nov | Mock rollout | Mock second site"], ("第 3 条",)),
        ("整页都没写状态", [x.rsplit("|", 1)[0] for x in SIX[:3]], ("每条都必须写状态",)),
        ("两个进行中", SIX[:2] + ["03 Nov | Mock a | Mock b | doing",
                                  "04 Nov | Mock c | Mock d | 进行中"], ("进行中",)),
        ("状态写错", SIX[:2] + ["03 Nov | Mock rollout | Mock second site | later"],
         ("later",)),
        ("2 条", SIX[:2], ("2",)),
        ("7 条", SIX + ["04 Dec | Mock extra | Mock | todo"], ("7",)),
        ("条目缺标题", SIX[:2] + ["03 Nov"], ("03 Nov",)),
        ("!! 两个叹号", SIX[:2] + ["!!03 Nov | Mock rollout | Mock second site | 未完成"], ("!!",)),
    ]
    for name, items, needles in cases:
        r = generate(deck(items, title="Mock Bad Phase"))
        check(f"timeline-phase {name}：报错退出，信息含页标题和 {needles}",
              deck_error(r, "Mock Bad Phase", *needles), (r.rc, r.stderr))


def test_overflow_warning():
    """标题放不进箭头段、说明估计放不下：警告（含页标题和第几条），照常生成；正常长度不警告。"""
    long_desc = "Mock description that keeps going " * 10
    long_title = "Mock very long phase title"
    items = (SIX[:4] + [f"13 Oct | {long_title} | Mock | doing",
                        f"03 Nov | Mock rollout | {long_desc.strip()} | todo"])
    r = generate(deck(items, title="Mock Long Phase"))
    w = [x for x in warnings(r.stderr) if "Mock Long Phase" in x and "溢出" in x]
    check("timeline-phase 文字过长：退出码 0", r.rc == 0, r.stderr)
    check("timeline-phase 文字过长：第 5、6 条各一条溢出警告",
          len(w) == 2 and "第 5 条" in w[0] and "第 6 条" in w[1], r.stderr)
    r = generate(deck(SIX))
    check("timeline-phase 正常长度：没有警告", not warnings(r.stderr), r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_errors()
    test_overflow_warning()
    test_segments()
    test_dates_markers_texts()
    test_legend()
    test_red_discipline()
    finish()
