"""team（团队页）版式测试：md 进、pptx 出。文稿全部虚构。

运行：python3 skills/milwaukee-ppt/tests/test_team.py
形状名约定（N 从 1 起，与成员顺序一致）：Member Card N（卡片底）、Member Name N（姓名）、
Member Role N（角色）、Member Rule N（角色和职责之间的细线）、Member Duty N（职责）。
"""
from deckcheck import (CONTENT_SLOT_IN, LAYOUT_INDEX, body_slide, caption_bar, check,
                       deck_error, finish, generate, inside, inside_shape, one, out_of_bounds,
                       placeholder, red_elements, review, run_style, tag_shape, warnings)

TITLE = "项目团队 / TEAM"
SUBTITLE = "四人小组，现场推进和数据复盘分开负责"

MEMBERS = [("林晓", "项目负责人", "统筹进度，对接车间主任"),
           ("周航", "现场推进", "试点车间贴码、培训和巡检"),
           ("陈雨", "数据复盘", "每周汇总借还记录并出周报"),
           ("Alex Kim", "系统支持", "扫码小程序维护和问题处理")]
EIGHT = MEMBERS + [("王宁", "采购对接", "二维码标签和扫码枪采购"),
                   ("赵一", "质量", "抽查登记记录的完整性"),
                   ("孙悦", "培训", "编写操作手册，组织新人培训"),
                   ("Mia Lee", "IT 安全", "账号权限和数据备份")]
ROLES = ["Member Card", "Member Name", "Member Role", "Member Rule", "Member Duty"]


def lines(members):
    return "\n".join("- " + " | ".join(m) for m in members)


def team_md(body, title=TITLE, extra=""):
    return f"""
---
month: 2026-10
author: Mock.Author
date: 13 Oct 2026
---

# {title}
## {SUBTITLE}
Layout: team
{extra}{body}
"""


CONCLUSION = "分工按现场和数据两条线，周会对齐一次"
MD = team_md(lines(MEMBERS) + "\n" + CONCLUSION, extra="Tag: Oct\n")


def check_members(s, members, label):
    """N 人：五类形状各一个、文字对、在正文区里、文字在卡片里、姓名在上职责在下、姓名字号最大。"""
    for n, (name, role, duty) in enumerate(members, 1):
        shapes = {r: one(s, f"{r} {n}") for r in ROLES}
        if not all(shapes.values()):
            check(f"{label}：第 {n} 人五个形状各一个", False, shapes)
            continue
        card, nm, rl, rule, dt = (shapes[r] for r in ROLES)
        got = [x.text_frame.text for x in (nm, rl, dt)]
        check(f"{label}：第 {n} 人文字 = 姓名 / 角色 / 职责", got == [name, role, duty], got)
        check(f"{label}：第 {n} 人形状都在正文区里",
              all(inside(sh, CONTENT_SLOT_IN) for sh in shapes.values()),
              [(sh.name, sh.left, sh.top, sh.width, sh.height) for sh in shapes.values()])
        check(f"{label}：第 {n} 人文字和细线都在卡片里",
              all(inside_shape(x, card) for x in (nm, rl, rule, dt)))
        check(f"{label}：第 {n} 人自上而下 姓名 → 角色 → 细线 → 职责",
              nm.top < rl.top < rule.top < dt.top)
        check(f"{label}：第 {n} 人姓名字号最大、加粗",
              run_style(nm)[0] > run_style(rl)[0] and run_style(nm)[0] > run_style(dt)[0]
              and run_style(nm)[1], [run_style(x) for x in (nm, rl, dt)])
    check(f"{label}：没有多出的第 {len(members) + 1} 人",
          not any(one(s, f"{r} {len(members) + 1}") for r in ROLES))


def test_render():
    """正常渲染：模板 layout 0，标题进 idx 0/10，每人一张卡片，4 人一行、同高等宽；
    普通文字行进底部红条；只用黑白灰。"""
    r = generate(MD)
    check("team：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    if s is None:
        check("team：生成了正文页", False, r.stderr)
        return
    check("team：用模板 layout 0",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX["team"]], s.slide_layout.name)
    check("team：主标题在 idx 0、副标题在 idx 10",
          placeholder(s, 0).text == TITLE and placeholder(s, 10).text == SUBTITLE,
          (placeholder(s, 0).text, placeholder(s, 10).text))
    check_members(s, MEMBERS, "team")
    cards = [one(s, f"Member Card {n}") for n in range(1, 5)]
    if all(cards):
        check("team：4 人排一行，上沿对齐、从左到右、同宽同高、互不重叠",
              len({c.top for c in cards}) == 1 and len({c.width for c in cards}) == 1
              and len({c.height for c in cards}) == 1
              and all(a.left + a.width < b.left for a, b in zip(cards, cards[1:])))
    bar = caption_bar(s)
    check("team：结论进底部红条", bar is not None and bar.text_frame.text == CONCLUSION,
          bar.text_frame.text if bar is not None else None)
    check("team：Tag 照常显示", tag_shape(s) is not None
          and tag_shape(s).text_frame.text == "Oct 2026")
    check("team：红色纪律——除底部红条外不用红",
          [n for n in red_elements(s) if n != "Caption Bar"] == [], red_elements(s))
    bad = out_of_bounds(r.prs, [s])
    check("team：不越界、不压 banner 和页脚", not bad, bad)


# 每段写满：姓名 8 个汉字、角色 12 个汉字、职责 40 个汉字（3 行）
FULL = [(f"欧阳试点{n}号成员", "试点车间现场推进负责人" + str(n),
         "负责试点车间工具贴码、借还培训、每日巡检、问题登记和周报汇总，并对接车间主任与班组长" [:39]
         + str(n)) for n in range(1, 9)]


def test_capacity_limits():
    """容量：下限 2 人、上限 8 人照常生成；每段写满也不越界、不警告。
    5 人以上排两行：第一行 = 一半向上取整，第二行从同一左沿排起，两行不重叠。"""
    for members, label in ((MEMBERS[:2], "team 2 人"), (EIGHT[:5], "team 5 人"),
                           (EIGHT, "team 8 人"), (FULL, "team 8 人写满")):
        r = generate(team_md(lines(members) + "\n" + CONCLUSION))
        check(f"{label}：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
        s = body_slide(r)
        if s is None:
            continue
        check_members(s, members, label)
        check(f"{label}：不越界", not out_of_bounds(r.prs, [s]), out_of_bounds(r.prs, [s]))
        cards = [one(s, f"Member Card {n}") for n in range(1, len(members) + 1)]
        if not all(cards):
            continue
        first = -(-len(members) // 2) if len(members) > 4 else len(members)
        row1, row2 = cards[:first], cards[first:]
        check(f"{label}：第一行 {first} 张上沿对齐",
              len({c.top for c in row1}) == 1, [c.top for c in row1])
        if row2:
            check(f"{label}：第二行在第一行下面、不重叠，左沿和第一行对齐",
                  len({c.top for c in row2}) == 1
                  and row2[0].top > row1[0].top + row1[0].height
                  and [c.left for c in row2] == [c.left for c in row1[:len(row2)]])


def test_capacity_errors():
    """人数不在 2–8、缺段、空段、姓名 / 角色一行放不下、职责超 3 行、漏写列表符号、
    标 !、写子列表：报错退出，信息带页标题。"""
    two = lines(MEMBERS[:2])
    bad = {
        "没写成员": team_md(CONCLUSION),
        "只有 1 人": team_md(lines(MEMBERS[:1])),
        "9 人": team_md(lines(EIGHT + [("钱多", "财务", "预算和报销")])),
        "某行只有两段": team_md(two + "\n- 陈雨 | 数据复盘"),
        "职责为空": team_md(two + "\n- 陈雨 | 数据复盘 | "),
        "姓名为空": team_md(two + "\n-  | 数据复盘 | 汇总借还记录"),
        "姓名超 8 个汉字": team_md(two + "\n- 欧阳试点车间九号成员 | 数据复盘 | 汇总借还记录"),
        "角色超 12 个汉字": team_md(two + "\n- 陈雨 | 试点车间数据复盘与周报负责人 | 汇总借还记录"),
        "职责超 3 行": team_md(two + "\n- 陈雨 | 数据复盘 | " + "汇总借还记录并出周报" * 5),
        "漏写列表符号": team_md(two + "\n陈雨 | 数据复盘 | 汇总借还记录"),
        "标了 !": team_md(two + "\n- !陈雨 | 数据复盘 | 汇总借还记录"),
        "写了子列表": team_md(two + "\n  - 每周五出周报"),
    }
    for case, md in bad.items():
        r = generate(md)
        check(f"team：{case} → 报错且带页标题", deck_error(r, TITLE), (r.rc, r.stderr))


def test_review():
    """审核：团队页正常稿 REVIEW OK（有分工结论，几何不误报）；没写结论照常报缺结论行。"""
    r = generate(team_md(lines(FULL) + "\n" + CONCLUSION, extra="Tag: Oct\n"))
    check("team 审核：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    out = review(r.workdir / "deck.md", r.path)
    check("team 审核：8 人写满、带 Tag 的正常稿 REVIEW OK",
          out.returncode == 0 and out.stdout.strip() == "REVIEW OK", out.stdout + out.stderr)
    r = generate(team_md(lines(MEMBERS)))
    out = review(r.workdir / "deck.md", r.path)
    check("team 审核：没写分工结论 → 报缺结论行",
          any(line.startswith("[缺结论行]") for line in out.stdout.splitlines()), out.stdout)


if __name__ == "__main__":
    test_render()
    test_review()
    test_capacity_limits()
    test_capacity_errors()
    finish()
