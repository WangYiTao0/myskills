"""table（表格页）版式测试：md 进、pptx 出。文稿全部虚构。

运行：python3 skills/milwaukee-ppt/tests/test_table.py
形状名约定：Data Table（原生表格，graphicFrame；第一行是表头）、Table Key Bar（`!` 行左侧的红竖条，
只在标了 `!` 时有）。
"""
from deckcheck import (A, EMU, CONTENT_SLOT_IN, LAYOUT_INDEX, RED_COLORS, body_slide, caption_bar,
                       check, deck_error, finish, generate, inside, one, out_of_bounds,
                       placeholder, red_elements, review, tag_shape, warnings)

TITLE = "充电等待 / WAITING"
SUBTITLE = "B 仓等待最长，排班先从 B 仓调"

HEADER = ["仓库", "叉车数", "平均等待", "高峰时段"]
ROWS = [["A 仓", "12 台", "18 分钟", "8:00–9:00"],
        ["!B 仓", "20 台", "35 分钟", "13:00–14:00"],
        ["C 仓", "9 台", "12 分钟", "8:00–9:00"]]
CONCLUSION = "B 仓高峰等待 35 分钟，是 A 仓的两倍"


def table_lines(header, rows, sep=True):
    out = ["| " + " | ".join(header) + " |"]
    if sep:
        out.append("| " + " | ".join("---" for _ in header) + " |")
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def table_md(body, title=TITLE, extra=""):
    return f"""
---
month: 2026-10
author: Mock.Author
date: 14 Oct 2026
---

# {title}
## {SUBTITLE}
Layout: table
{extra}{body}
"""


MD = table_md(table_lines(HEADER, ROWS) + "\n" + CONCLUSION, extra="Tag: Oct\n")


def cell_texts(frame):
    tbl = frame.table
    return [[tbl.cell(r, c).text_frame.text for c in range(len(tbl.columns))]
            for r in range(len(tbl.rows))]


def cell_style(frame, r, c):
    """(字号, 粗体, 颜色)，取单元格第一段第一个 run。"""
    run = frame.table.cell(r, c).text_frame.paragraphs[0].runs[0]
    color = str(run.font.color.rgb) if run.font.color and run.font.color.type else None
    return run.font.size.pt, bool(run.font.bold), color


def table_reds(frame):
    vals = {e.get("val", "").upper() for e in frame._element.iter(f"{A}srgbClr")}
    return vals & RED_COLORS


def test_render():
    """正常渲染：模板 layout 0，标题进 idx 0/10；md 表格成原生表格，第一行是表头；
    `!` 行左侧有红竖条、文字加粗，表格本身不用红；结论进红条；不越界。"""
    r = generate(MD)
    check("table：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    if s is None:
        check("table：生成了正文页", False, r.stderr)
        return
    check("table：用模板 layout 0",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX["table"]], s.slide_layout.name)
    check("table：主标题在 idx 0、副标题在 idx 10",
          placeholder(s, 0).text == TITLE and placeholder(s, 10).text == SUBTITLE,
          (placeholder(s, 0).text, placeholder(s, 10).text))
    frame = one(s, "Data Table")
    check("table：有一个原生表格 Data Table", frame is not None and frame.has_table,
          [sh.name for sh in s.shapes])
    if frame is None or not frame.has_table:
        return
    want = [HEADER] + [[c.lstrip("!") for c in row] for row in ROWS]
    check("table：单元格文字 = 文稿（表头一行 + 3 行，分隔行不进表，! 去掉）",
          cell_texts(frame) == want, cell_texts(frame))
    check("table：表头加粗、正文不加粗",
          all(cell_style(frame, 0, c)[1] for c in range(4))
          and not cell_style(frame, 1, 0)[1], [cell_style(frame, 0, 0), cell_style(frame, 1, 0)])
    check("table：! 行文字加粗、深灰",
          all(cell_style(frame, 2, c)[1:] == (True, "1A1A1A") for c in range(4)),
          [cell_style(frame, 2, c) for c in range(4)])
    check("table：列等宽", len({col.width for col in frame.table.columns}) == 1,
          [col.width for col in frame.table.columns])
    check("table：表格在正文区里", inside(frame, CONTENT_SLOT_IN),
          (frame.left, frame.top, frame.width, frame.height))
    check("table：表格行高之和 = 表格框高",
          sum(row.height for row in frame.table.rows) == frame.height)
    tag = tag_shape(s)
    check("table：写了 Tag 时表格在 Month Tag 下面",
          tag is not None and frame.top >= tag.top + tag.height, (frame.top, tag))
    bar = one(s, "Table Key Bar")
    check("table：! 行左侧有红竖条 Table Key Bar", bar is not None)
    if bar is not None:
        rows = frame.table.rows
        row_top = frame.top + rows[0].height + rows[1].height
        check("table：红竖条在表格左边、和 ! 行同高",
              bar.left + bar.width <= frame.left and bar.top == row_top
              and bar.height == rows[2].height and inside(bar, CONTENT_SLOT_IN),
              (bar.left, bar.top, bar.height, frame.left, row_top, rows[2].height))
    check("table：红色纪律——红色只在红竖条和底部红条",
          sorted(red_elements(s)) == ["Caption Bar", "Table Key Bar"], red_elements(s))
    check("table：表格不引用主题表格样式（避免带出 accent 色）",
          frame.table._tbl.tblPr.find(f"{A}tableStyleId") is None
          or frame.table._tbl.tblPr.find(f"{A}tableStyleId").text
          == "{2D5ABB26-0587-4C30-8999-92F81FD0307C}")
    bar = caption_bar(s)
    check("table：结论进底部红条", bar is not None and bar.text_frame.text == CONCLUSION,
          bar.text_frame.text if bar is not None else None)
    bad = out_of_bounds(r.prs, [s])
    check("table：不越界、不压 banner 和页脚", not bad, bad)


def test_no_key_no_red():
    """没标 `!`：没有红竖条，表格里不用红；不写分隔行也照常认表头。"""
    rows = [[c.lstrip("!") for c in row] for row in ROWS]
    r = generate(table_md(table_lines(HEADER, rows, sep=False) + "\n" + CONCLUSION))
    s = body_slide(r)
    check("table 无 !：生成成功", s is not None and r.rc == 0, r.stderr)
    if s is None:
        return
    frame = one(s, "Data Table")
    check("table 无 !：没写分隔行也是表头 + 3 行",
          frame is not None and cell_texts(frame) == [HEADER] + rows,
          cell_texts(frame) if frame is not None else None)
    check("table 无 !：没有红竖条，红色只在底部红条",
          one(s, "Table Key Bar") is None and red_elements(s) == ["Caption Bar"],
          red_elements(s))


def grid(ncols, nrows, cell="甲"):
    header = [f"列{c}" for c in range(1, ncols + 1)]
    return header, [[f"{cell}{r}{c}" for c in range(1, ncols + 1)] for r in range(1, nrows + 1)]


# 写到上限：6 列、表头以外 8 行、带 Tag；每格 2 行（6 列时每格约 18 个汉字）的行放 3 行
# （再多一行 2 行的格子就超出正文区高度），一行标 !。
FULL_CELL = "试点车间叉车充电排班调整记录"   # 14 个汉字，6 列时 2 行


def full_grid():
    header, rows = grid(6, 8)
    for r in (0, 3, 7):
        rows[r] = [f"{FULL_CELL}{c}" for c in range(1, 7)]
    rows[4][0] = "!" + rows[4][0]
    return header, rows


def test_capacity_limits():
    """容量：2 列 / 6 列、2 行 / 8 行照常生成；写满（6 列 × 8 行、3 行两行字、带 Tag）
    不越界、不警告，表格在正文区里。"""
    cases = [(grid(2, 2), "", "2 列 2 行"), (grid(6, 2), "", "6 列 2 行"),
             (grid(2, 8), "", "2 列 8 行"), (full_grid(), "Tag: Oct\n", "6 列 8 行写满带 Tag")]
    for (header, rows), extra, label in cases:
        r = generate(table_md(table_lines(header, rows) + "\n" + CONCLUSION, extra=extra))
        check(f"table {label}：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
        s = body_slide(r)
        frame = one(s, "Data Table") if s is not None else None
        if frame is None:
            continue
        check(f"table {label}：{len(rows) + 1} 行 {len(header)} 列",
              (len(frame.table.rows), len(frame.table.columns)) == (len(rows) + 1, len(header)))
        check(f"table {label}：表格在正文区里、不越界",
              inside(frame, CONTENT_SLOT_IN) and not out_of_bounds(r.prs, [s]),
              (frame.top, frame.height, out_of_bounds(r.prs, [s])))


def test_capacity_errors():
    """列数不在 2–6、行数不在 2–8、列数不齐、表头空格、单元格超 2 行、表格太高、
    ! 超过一行 / 写在表头 / 写在非首格 / !!、漏写开头 |、写列表行、没有表格：
    报错退出，信息带页标题；容量错误提示拆页。"""
    two = table_lines(*grid(3, 2))
    header, rows = grid(6, 8)
    tall = [[f"{FULL_CELL}{c}" for c in range(1, 7)] for _ in range(4)] + rows[4:]
    bad = {
        "1 列": (table_md(table_lines(*grid(1, 3))), ()),
        "7 列": (table_md(table_lines(*grid(7, 3))), ("拆",)),
        "表头以外 1 行": (table_md(table_lines(*grid(3, 1))), ()),
        "表头以外 9 行": (table_md(table_lines(*grid(3, 9))), ("拆页",)),
        "某行列数不齐": (table_md(two + "\n| 甲 | 乙 |"), ()),
        "表头有空格": (table_md(table_lines(["仓库", "", "等待"], grid(3, 2)[1])), ()),
        "单元格超 2 行": (table_md(two + "\n| " + FULL_CELL * 3 + " | 乙 | 丙 |"), ()),
        "表格太高（4 行两行字、带 Tag）": (table_md(table_lines(header, tall), extra="Tag: Oct\n"),
                                   ("拆",)),
        "两行标 !": (table_md(two + "\n| !甲 | 乙 | 丙 |\n| !丁 | 戊 | 己 |"), ()),
        "表头标 !": (table_md(table_lines(["!仓库", "数", "等待"], grid(3, 2)[1])), ()),
        "! 写在非首格": (table_md(two + "\n| 甲 | !乙 | 丙 |"), ()),
        "写成 !!": (table_md(two + "\n| !!甲 | 乙 | 丙 |"), ()),
        "漏写开头 |": (table_md(two + "\n甲 | 乙 | 丙 |"), ()),
        "写了列表行": (table_md(two + "\n- 补充一句说明"), ()),
        "没有表格": (table_md(CONCLUSION), ()),
    }
    for case, (md, needles) in bad.items():
        r = generate(md)
        check(f"table：{case} → 报错且带页标题", deck_error(r, TITLE, *needles), (r.rc, r.stderr))


def test_review():
    """审核：写满、带 Tag、含一行 ! 的正常稿 REVIEW OK；没写结论照常报缺结论行；
    改坏单元格（塞满文字）报「文字溢出」带 Data Table。"""
    md = table_md(table_lines(*full_grid()) + "\n" + CONCLUSION, extra="Tag: Oct\n")
    r = generate(md)
    check("table 审核：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    out = review(r.workdir / "deck.md", r.path)
    check("table 审核：写满、带 Tag、含 ! 的正常稿 REVIEW OK",
          out.returncode == 0 and out.stdout.strip() == "REVIEW OK", out.stdout + out.stderr)

    from deckcheck import open_pptx
    prs = open_pptx(r.path)
    frame = one(prs.slides[1], "Data Table")
    frame.table.cell(2, 1).text_frame.paragraphs[0].runs[0].text = FULL_CELL * 4
    bad = r.workdir / "bad.pptx"
    prs.save(str(bad))
    out = review(r.workdir / "deck.md", bad)
    check("table 审核：单元格塞满 → 报文字溢出，带第 2 页和 Data Table",
          any(line.startswith("[文字溢出]") and "第 2 页" in line and "「Data Table」" in line
              for line in out.stdout.splitlines()), out.stdout)

    r = generate(table_md(table_lines(HEADER, ROWS)))
    out = review(r.workdir / "deck.md", r.path)
    check("table 审核：没写结论 → 报缺结论行",
          any(line.startswith("[缺结论行]") for line in out.stdout.splitlines()), out.stdout)


# ---- 方向 C（通用 / 项目汇报模式）：字号随行数放大、整表在正文区垂直居中 ----

def general_md(body, title=TITLE, extra="", next_line=True):
    nxt = "Next: 9 月先在 B 仓试行新排班\n" if next_line else ""
    return f"""
---
title: Mock Deck
date: 14 Oct 2026
---

# {title}
## {SUBTITLE}
Layout: table
{extra}{body}
{CONCLUSION}
{nxt}"""


def c_bounds(s):
    """C 模式正文区上下沿（EMU）：lead 下沿 + 0.19"、Next 细线上方 0.10"。"""
    lead, rule = one(s, "Lead"), one(s, "Next Rule")
    return lead.top + lead.height + int(0.19 * EMU), rule.top - int(0.10 * EMU)


def cell_pts(frame):
    tbl = frame.table
    return {run.font.size.pt for r in range(len(tbl.rows)) for c in range(len(tbl.columns))
            for p in tbl.cell(r, c).text_frame.paragraphs for run in p.runs}


def test_general_mode_few_rows():
    """C 模式行少（3 行）：全表 18pt、行高跟着字号放大；整表在正文区里垂直居中，
    下方不留大片空白；红竖条仍贴着 ! 行。"""
    r = generate(general_md(table_lines(HEADER, ROWS), extra="Tag: Oct\n"))
    check("C table 3 行：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    frame = one(s, "Data Table") if s is not None else None
    if frame is None:
        return
    check("C table 3 行：全表 18pt", cell_pts(frame) == {18.0}, cell_pts(frame))
    check("C table 3 行：行高放得下 18pt 一行（≥ 18pt × 1.25）",
          all(row.height >= 18 * 1.25 / 72 * EMU for row in frame.table.rows),
          [row.height / EMU for row in frame.table.rows])
    top, low = c_bounds(s)
    up, down = frame.top - top, low - (frame.top + frame.height)
    check("C table 3 行：整表在正文区里垂直居中", up >= 0 and down >= 0
          and abs(up - down) <= 0.02 * EMU, (up / EMU, down / EMU))
    bar = one(s, "Table Key Bar")
    rows = frame.table.rows
    check("C table 3 行：红竖条和 ! 行同高、同位置",
          bar is not None and bar.top == frame.top + rows[0].height + rows[1].height
          and bar.height == rows[2].height,
          bar is not None and (bar.top, bar.height))
    out = review(r.workdir / "deck.md", r.path)
    check("C table 3 行：审核 REVIEW OK",
          out.returncode == 0 and out.stdout.strip() == "REVIEW OK", out.stdout + out.stderr)


def test_general_mode_full():
    """C 模式写满（6 列 × 8 行、3 行两行字、Tag、lead、Next）：字号降到放得下的一档，
    不警告、在正文区里，审核不报表格 / 文字溢出。"""
    r = generate(general_md(table_lines(*full_grid()), title="Full Table", extra="Tag: Oct\n"))
    check("C table 写满：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    frame = one(s, "Data Table") if s is not None else None
    if frame is None:
        return
    top, low = c_bounds(s)
    check("C table 写满：整表在正文区里", frame.top >= top and frame.top + frame.height <= low,
          (frame.top / EMU, (frame.top + frame.height) / EMU, top / EMU, low / EMU))
    check("C table 写满：全表同一字号、14–18pt",
          len(cell_pts(frame)) == 1 and 14 <= min(cell_pts(frame)) <= 18, cell_pts(frame))
    out = review(r.workdir / "deck.md", r.path)
    check("C table 写满：审核 REVIEW OK",
          out.returncode == 0 and out.stdout.strip() == "REVIEW OK", out.stdout + out.stderr)


if __name__ == "__main__":
    test_render()
    test_no_key_no_red()
    test_capacity_limits()
    test_capacity_errors()
    test_review()
    test_general_mode_few_rows()
    test_general_mode_full()
    finish()
