"""agenda（Agenda 目录页）版式测试：md 进、pptx 出。文稿全部虚构。

运行：python3 skills/milwaukee-ppt/tests/test_agenda.py
形状名约定（N 从 1 起，与条目顺序一致）：Agenda Number N（章节编号）、Agenda Rule N（编号和
名字之间的竖线）、Agenda Name N（中文名）、Agenda English N（英文名）。
"""
from deckcheck import (CONTENT_SLOT_IN, LAYOUT_INDEX, body_slide, caption_bar, check,
                       deck_error, finish, generate, inside, one, out_of_bounds, placeholder,
                       red_elements, review, run_style, tag_shape, warnings)

TITLE = "目录 / AGENDA"
SUBTITLE = "四个部分：从目标到下一步，试点数据放在第三部分"

ITEMS = [("01", "项目目标", "TARGET"), ("02", "实施范围", "SCOPE"),
         ("03", "试点推进", "PILOT"), ("04", "下一步", "NEXT STEPS")]
EIGHT = ITEMS + [("05", "使用场景", "USE CASES"), ("06", "数据看板", "DASHBOARD"),
                 ("07", "风险", "RISKS"), ("08", "团队", "TEAM")]
ROLES = ["Agenda Number", "Agenda Rule", "Agenda Name", "Agenda English"]


def lines(items):
    return "\n".join(" | ".join(it) for it in items)


def agenda_md(body, title=TITLE, extra=""):
    return f"""
---
title: 虚构项目汇报
date: 13 Oct 2026
---

# {title}
## {SUBTITLE}
Layout: agenda
{extra}{body}
"""


MD = agenda_md(lines(ITEMS), extra="Tag: Oct\n")


def check_items(s, items, label):
    """N 条：四类形状各一个、文字对、落在正文区、编号在左名字在右、编号字号最大。"""
    for n, (num, name, eng) in enumerate(items, 1):
        shapes = {role: one(s, f"{role} {n}") for role in ROLES}
        if not all(shapes.values()):
            check(f"{label}：第 {n} 条四个形状各一个", False, shapes)
            continue
        nb, rule, nm, en = (shapes[r] for r in ROLES)
        texts = [x.text_frame.text for x in (nb, nm, en)]
        check(f"{label}：第 {n} 条文字 = 编号 / 中文名 / 英文名", texts == [num, name, eng], texts)
        check(f"{label}：第 {n} 条形状都在正文区里",
              all(inside(sh, CONTENT_SLOT_IN) for sh in shapes.values()),
              [(sh.name, sh.left, sh.top, sh.width, sh.height) for sh in shapes.values()])
        check(f"{label}：第 {n} 条编号在左、名字在右，中文名在英文名上面",
              nb.left + nb.width <= rule.left <= nm.left and nm.left == en.left
              and nm.top < en.top)
        check(f"{label}：第 {n} 条编号字号最大、加粗",
              run_style(nb)[0] > run_style(nm)[0] > run_style(en)[0] and run_style(nb)[1],
              [run_style(x) for x in (nb, nm, en)])
    check(f"{label}：没有多出的第 {len(items) + 1} 条",
          not any(one(s, f"{role} {len(items) + 1}") for role in ROLES))


def test_render():
    """正常渲染：模板 layout 0，标题进 idx 0/10，每条四个形状按名字出现，单列从上到下排。"""
    r = generate(MD)
    check("agenda：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    if s is None:
        check("agenda：生成了正文页", False, r.stderr)
        return
    check("agenda：用模板 layout 0",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX["agenda"]], s.slide_layout.name)
    check("agenda：主标题在 idx 0、副标题在 idx 10",
          placeholder(s, 0).text == TITLE and placeholder(s, 10).text == SUBTITLE,
          (placeholder(s, 0).text, placeholder(s, 10).text))
    check_items(s, ITEMS, "agenda")
    nums = [one(s, f"Agenda Number {n}") for n in range(1, 5)]
    if all(nums):
        check("agenda：4 条单列，左沿对齐、从上到下",
              len({x.left for x in nums}) == 1
              and all(a.top < b.top for a, b in zip(nums, nums[1:])))
    check("agenda：Tag 照常显示", tag_shape(s) is not None
          and tag_shape(s).text_frame.text == "Oct 2026")
    check("agenda：没有底部红条", caption_bar(s) is None)
    check("agenda：红色纪律——banner 以外不用红", red_elements(s) == [], red_elements(s))
    bad = out_of_bounds(r.prs, [s])
    check("agenda：不越界、不压 banner 和页脚", not bad, bad)


def test_capacity_limits():
    """容量：下限 3 条、上限 8 条照常生成；每段写满（编号 3 字、中文名 12 字、英文名 40 字）
    也不越界。5 条以上分两列（先左列、再右列），两列同行对齐、不重叠。"""
    full = [(f"{n}.1", "试点车间借还流程线上化" + str(n), "W" * 40) for n in range(1, 9)]
    for items, label in ((ITEMS[:3], "agenda 3 条"), (EIGHT, "agenda 8 条"),
                         (full, "agenda 8 条写满")):
        r = generate(agenda_md(lines(items)))
        check(f"{label}：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
        s = body_slide(r)
        if s is None:
            continue
        check_items(s, items, label)
        check(f"{label}：不越界", not out_of_bounds(r.prs, [s]), out_of_bounds(r.prs, [s]))
        if len(items) < 5:
            continue
        n1, n4, n5 = (one(s, f"Agenda Number {n}") for n in (1, 4, 5))
        right_edge = max(one(s, f"{role} {n}").left + one(s, f"{role} {n}").width
                         for n in range(1, 5) for role in ROLES if one(s, f"{role} {n}"))
        if n1 and n4 and n5:
            check(f"{label}：1–4 在左列、5–8 在右列，同行对齐、两列不重叠",
                  n1.left == n4.left and n5.left >= right_edge and n5.top == n1.top,
                  (n1.left, n4.left, n5.left, right_edge))


def test_capacity_errors():
    """条数不在 3–8、缺段、空段、超字数、编号重复、写了结论或 Next：报错退出，信息带页标题。"""
    three = lines(ITEMS[:3])
    bad = {
        "没写条目": agenda_md(""),
        "只有 2 条": agenda_md(lines(ITEMS[:2])),
        "9 条": agenda_md(lines(EIGHT + [("09", "附录", "APPENDIX")])),
        "某条只有两段": agenda_md(three + "\n04 | 下一步"),
        "编号为空": agenda_md(three + "\n | 下一步 | NEXT"),
        "英文名为空": agenda_md(three + "\n04 | 下一步 | "),
        "编号超 3 字": agenda_md(three + "\n0004 | 下一步 | NEXT"),
        "中文名超 12 字": agenda_md(three + "\n04 | 试点车间借还流程全部线上化 | NEXT"),
        "英文名超 40 字": agenda_md(three + "\n04 | 下一步 | " + "W" * 41),
        "编号重复": agenda_md(three + "\n03 | 下一步 | NEXT"),
        "写了结论行": agenda_md(lines(ITEMS) + "\n四个部分覆盖试点全过程"),
        "写了 Next": agenda_md(lines(ITEMS) + "\nNext: 11 月推广"),
    }
    for case, md in bad.items():
        r = generate(md)
        check(f"agenda：{case} → 报错且带页标题", deck_error(r, TITLE), (r.rc, r.stderr))


def test_with_section():
    """和隔断页配合：Agenda 的条目行原样抄到隔断页（同一种「编号 | 中文名 | 英文名」）。"""
    md = agenda_md(lines(ITEMS)) + """
# 试点推进 / PILOT
## 试点 4 周，借还记录全部可追溯
Layout: section
03 | 试点推进 | PILOT
"""
    r = generate(md)
    check("agenda + section：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    if r.rc != 0:
        return
    agenda, section = r.prs.slides[1], r.prs.slides[2]
    a3, sn = one(agenda, "Agenda Name 3"), one(section, "Section Name")
    check("agenda + section：目录第 3 条和隔断页章节名一致",
          a3 is not None and sn is not None and a3.text_frame.text == sn.text_frame.text)


def test_review():
    """审核：目录页正常稿 REVIEW OK（目录页没有红条，不报缺结论行）；
    副标题照样要写成一句结论，目录式副标题仍然报。"""
    r = generate(MD)
    check("agenda 审核：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    out = review(r.workdir / "deck.md", r.path)
    check("agenda 审核：正常稿 REVIEW OK",
          out.returncode == 0 and out.stdout.strip() == "REVIEW OK", out.stdout + out.stderr)
    r = generate(MD.replace(f"## {SUBTITLE}", "## 目录"))
    out = review(r.workdir / "deck.md", r.path)
    check("agenda 审核：目录式副标题照样报",
          any(line.startswith("[目录式副标题]") for line in out.stdout.splitlines())
          and "[缺结论行]" not in out.stdout, out.stdout)


if __name__ == "__main__":
    test_render()
    test_review()
    test_capacity_limits()
    test_capacity_errors()
    test_with_section()
    finish()
