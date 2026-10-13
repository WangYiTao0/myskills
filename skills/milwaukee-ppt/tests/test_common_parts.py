"""共用部件测试：缩进子列表、数字拆单位、状态解析。md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_common_parts.py
做法：generate(md, probe=True) 时，生成器额外注册测试专用版式 `_probe`（tests/probe_layout.py），
它只把共用部件的结果画出来，不进正式注册表。各版式票改自己的版式时，本文件不用动。
"""
from deckcheck import (body_slide, check, deck_error, finish, generate, runs, shapes_named)

INK, GRAY = "1A1A1A", "6B6B6B"
TITLE = "Mock Probe Page"


def probe_md(body, title=TITLE):
    return f"""
---
title: Mock Deck
date: 13 Oct 2026
---

# {title}
Layout: _probe
{body}
"""


# ---- 数字拆单位 ---------------------------------------------------------------

def test_number_unit_split():
    U = lambda t: (t, 28, False, GRAY)          # 单位 / 前缀：28pt 灰色不加粗
    N = lambda t: (t, 60, True, INK)            # 大数字
    cases = [
        ("120 件", [N("120"), U(" 件")]),
        ("100%", [N("100"), U("%")]),
        ("-40%", [N("-40"), U("%")]),
        ("+15 秒", [N("+15"), U(" 秒")]),
        ("$1,240.5 k", [N("$1,240.5"), U(" k")]),
        ("5 d", [N("5"), U(" d")]),
        ("120", [N("120")]),
        # 数值和单位之间保留原文的空白，不补空格
        ("120件", [N("120"), U("件")]),
        ("15秒", [N("15"), U("秒")]),
        # 数量级后缀、+、/数字 留在大数字里
        ("24/7", [N("24/7")]),
        ("3/5", [N("3/5")]),
        ("12.3M", [N("12.3M")]),
        ("1,000+", [N("1,000+")]),
        ("5x", [N("5x")]),
        ("2.5k 次", [N("2.5k"), U(" 次")]),
        ("10Mbps", [N("10Mbps")]),
        # 前缀符号：灰色小字，和单位同字号
        ("约 120 件", [U("约 "), N("120"), U(" 件")]),
        ("约 5 天", [U("约 "), N("5"), U(" 天")]),
        ("≥95%", [U("≥"), N("95"), U("%")]),
        ("~3 h", [U("~"), N("3"), U(" h")]),
        ("+/-2%", [U("+/-"), N("2"), U("%")]),
        ("<1 s", [U("<"), N("1"), U(" s")]),
        # 不以（前缀 +）数字开头：整串大数字
        ("Q3", [N("Q3")]),
        ("N/A", [N("N/A")]),
    ]
    body = "\n".join(f"num: {v}" for v, _ in cases)
    r = generate(probe_md(body), probe=True)
    check("拆单位：退出码 0", r.rc == 0, r.stderr)
    boxes = shapes_named(body_slide(r), "Probe Number") if r.rc == 0 else []
    check("拆单位：每个数字一个文本框", len(boxes) == len(cases), len(boxes))
    for (value, want), box in zip(cases, boxes):
        got = runs(box)
        check(f"拆单位：「{value}」→ 数值大字 + 单位 28pt 灰色不加粗", got == want, got)


def test_number_unit_key_red():
    r = generate(probe_md("num: !100%"), probe=True)
    box = shapes_named(body_slide(r), "Probe Number")[0] if r.rc == 0 else None
    got = runs(box) if box is not None else r.stderr
    check("拆单位：重点数字红色，单位仍是灰色",
          got == [("100", 60, True, "DB011C"), ("%", 28, False, GRAY)], got)
    r = generate(probe_md("num: !≥95%"), probe=True)
    box = shapes_named(body_slide(r), "Probe Number")[0] if r.rc == 0 else None
    got = runs(box) if box is not None else r.stderr
    check("拆单位：重点数字红色，前缀和单位仍是灰色",
          got == [("≥", 28, False, GRAY), ("95", 60, True, "DB011C"), ("%", 28, False, GRAY)],
          got)


# ---- 缩进子列表 ---------------------------------------------------------------

def test_indented_sub_items():
    body = "\n".join([
        "- Card A | 1 | note",
        "  - Sub a1",
        "\t- Sub a2",
        "- Card B | 2 | note",
        "    * Sub b1",
        "  plain indented text",
        "-not a list item",
    ])
    r = generate(probe_md(body), probe=True)
    check("缩进：退出码 0", r.rc == 0, r.stderr)
    subs = shapes_named(body_slide(r), "Probe Sub") if r.rc == 0 else []
    got = [sh.text_frame.text for sh in subs]
    check("缩进：只有缩进的列表行算子列表项，去掉列表符号",
          got == ["Sub a1", "Sub a2", "Sub b1"], got)
    lines = shapes_named(body_slide(r), "Probe Line") if r.rc == 0 else []
    got = [sh.text_frame.text for sh in lines]
    check("缩进：page.lines 仍是去掉首尾空白的原文，缩进宽度另给（tab 算 4）",
          got == ["0|- Card A | 1 | note", "2|- Sub a1", "4|- Sub a2",
                  "0|- Card B | 2 | note", "4|* Sub b1", "2|plain indented text",
                  "0|-not a list item"], got)


# ---- 状态解析 -----------------------------------------------------------------

def statuses(r):
    return [sh.text_frame.text for sh in shapes_named(body_slide(r), "Probe Status")]


def test_status_values():
    r = generate(probe_md("status: 完成, 进行中, 未完成\nstatus: DONE, Doing, todo\n"
                          "status: done, 完成, todo"), probe=True)
    check("状态：退出码 0", r.rc == 0, r.stderr)
    got = statuses(r) if r.rc == 0 else []
    check("状态：中英文、大小写都认，统一成 done / doing / todo",
          got == ["done doing todo", "done doing todo", "done done todo"], got)


def test_status_colors():
    r = generate(probe_md("status: done, doing, todo"), probe=True)
    box = shapes_named(body_slide(r), "Probe Status")[0] if r.rc == 0 else None
    got = [c for _, _, _, c in runs(box)] if box is not None else r.stderr
    check("状态色：已完成 2E7D32、进行中 F2A900、未完成品牌红",
          got == ["2E7D32", "F2A900", "DB011C"], got)


def test_status_none_written():
    r = generate(probe_md("status: , , "), probe=True)
    check("状态：全部不写 → 旧写法（None）", r.rc == 0 and statuses(r) == ["none"],
          r.stderr or statuses(r))


def test_status_errors():
    cases = [
        ("status: done, finished, todo", "写错", "finished"),
        ("status: done, doing, doing", "进行中", "2"),
        ("status: done, , todo", "部分", None),
        ("status!: , , ", "必须", None),
        ("status!: done, , todo", "必须", None),
    ]
    for body, label, detail in cases:
        r = generate(probe_md(body), probe=True)
        ok = deck_error(r, TITLE, *([detail] if detail else []))
        check(f"状态报错（{label}）：非零退出、信息含页标题：{body}", ok, r.stderr)


if __name__ == "__main__":
    test_number_unit_split()
    test_number_unit_key_red()
    test_indented_sub_items()
    test_status_values()
    test_status_colors()
    test_status_none_written()
    test_status_errors()
    finish()
