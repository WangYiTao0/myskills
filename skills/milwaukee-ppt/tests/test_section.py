"""section（隔断页）版式测试：md 进、pptx 出。文稿全部虚构。

运行：python3 skills/milwaukee-ppt/tests/test_section.py
形状名约定：Section Number（章节编号）、Section Rule（编号和名字之间的竖线）、
Section Name（中文名）、Section English（英文名）。
"""
from deckcheck import (CONTENT_SLOT_IN, LAYOUT_INDEX, body_slide, caption_bar, check,
                       deck_error, finish, generate, inside, one, out_of_bounds, placeholder,
                       red_elements, review, run_style, tag_shape, warnings)

TITLE = "试点推进 / PILOT"


def section_md(body, title=TITLE, extra=""):
    return f"""
---
title: 虚构项目汇报
date: 13 Oct 2026
---

# {title}
## 试点 4 周，借还记录全部可追溯
Layout: section
{extra}{body}
"""


MD = section_md("02 | 试点推进 | PILOT", extra="Tag: Oct\n")
PARTS = ["Section Number", "Section Rule", "Section Name", "Section English"]


def test_render():
    """正常渲染：模板 layout 0，标题进 idx 0/10，四个形状按名字出现、文字对、落在正文区。"""
    r = generate(MD)
    check("section：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    if s is None:
        check("section：生成了正文页", False, r.stderr)
        return
    check("section：用模板 layout 0",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX["section"]], s.slide_layout.name)
    check("section：主标题在 idx 0、副标题在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "试点 4 周，借还记录全部可追溯",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    shapes = {name: one(s, name) for name in PARTS}
    check("section：四个形状各一个", all(shapes.values()), shapes)
    if not all(shapes.values()):
        return
    check("section：文字 = 编号 / 中文名 / 英文名",
          [shapes[n].text_frame.text for n in ("Section Number", "Section Name",
                                               "Section English")]
          == ["02", "试点推进", "PILOT"])
    check("section：四个形状都在正文区（内容区 1.30–5.60\"）里",
          all(inside(sh, CONTENT_SLOT_IN) for sh in shapes.values()),
          [(sh.name, sh.left, sh.top, sh.width, sh.height) for sh in shapes.values()])
    num, name, eng = (shapes[n] for n in ("Section Number", "Section Name", "Section English"))
    check("section：编号在左、名字在右，中文名在英文名上面",
          num.left + num.width <= shapes["Section Rule"].left <= name.left
          and name.left == eng.left and name.top < eng.top)
    check("section：编号字号最大、加粗",
          run_style(num)[0] > run_style(name)[0] > run_style(eng)[0] and run_style(num)[1],
          [run_style(x) for x in (num, name, eng)])
    check("section：Tag 照常显示", tag_shape(s) is not None
          and tag_shape(s).text_frame.text == "Oct 2026")
    check("section：没有底部红条", caption_bar(s) is None)
    check("section：红色纪律——banner 以外不用红", red_elements(s) == [], red_elements(s))
    bad = out_of_bounds(r.prs, [s])
    check("section：不越界、不压 banner 和页脚", not bad, bad)


def test_capacity_max_fits():
    """容量上限（编号 3 字、中文名 12 字、英文名 40 字）照常生成，不越界、文字框在正文区里。"""
    r = generate(section_md("A.1 | 试点车间借还流程线上化 | " + "W" * 40))
    check("section 上限：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    if s is None:
        return
    check("section 上限：形状都在正文区里",
          all(inside(one(s, n), CONTENT_SLOT_IN) for n in PARTS if one(s, n)),
          [(n, one(s, n) and inside(one(s, n), CONTENT_SLOT_IN)) for n in PARTS])
    check("section 上限：不越界", not out_of_bounds(r.prs, [s]), out_of_bounds(r.prs, [s]))


def test_capacity_errors():
    """缺行、多行、缺段、空段、超字数、写了结论或 Next：报错退出，信息带页标题。"""
    bad = {
        "没写编号行": section_md(""),
        "两行": section_md("01 | 准备 | PREP\n02 | 试点推进 | PILOT"),
        "只有两段": section_md("02 | 试点推进"),
        "编号为空": section_md(" | 试点推进 | PILOT"),
        "英文名为空": section_md("02 | 试点推进 | "),
        "编号超 3 字": section_md("0002 | 试点推进 | PILOT"),
        "中文名超 12 字": section_md("02 | 试点车间借还流程全部线上化 | PILOT"),
        "英文名超 40 字": section_md("02 | 试点推进 | " + "W" * 41),
        "写了结论行": section_md("02 | 试点推进 | PILOT\n试点 4 周记录全部可追溯"),
        "写了 Next": section_md("02 | 试点推进 | PILOT\nNext: 11 月推广"),
    }
    for case, md in bad.items():
        r = generate(md)
        check(f"section：{case} → 报错且带页标题", deck_error(r, TITLE), (r.rc, r.stderr))


def test_review():
    """审核：隔断页正常稿 REVIEW OK（隔断页没有红条，不报缺结论行）；
    副标题照样要写成一句结论，目录式副标题仍然报。"""
    r = generate(MD)
    check("section 审核：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    out = review(r.workdir / "deck.md", r.path)
    check("section 审核：正常稿 REVIEW OK",
          out.returncode == 0 and out.stdout.strip() == "REVIEW OK", out.stdout + out.stderr)
    r = generate(MD.replace("## 试点 4 周，借还记录全部可追溯", "## 试点推进"))
    out = review(r.workdir / "deck.md", r.path)
    check("section 审核：目录式副标题照样报",
          any(line.startswith("[目录式副标题]") for line in out.stdout.splitlines())
          and "[缺结论行]" not in out.stdout, out.stdout)


if __name__ == "__main__":
    test_render()
    test_review()
    test_capacity_max_fits()
    test_capacity_errors()
    finish()
