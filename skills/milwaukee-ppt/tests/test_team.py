"""team（团队页）版式测试：md 进、pptx 出。文稿全部虚构。

运行：python3 skills/milwaukee-ppt/tests/test_team.py
形状名约定（N 从 1 起，与成员顺序一致）：Member Card N（卡片底）、Member Name N（姓名）、
Member Role N（角色）、Member Rule N（角色和职责之间的细线）、Member Duty N（职责）。
"""
from deckcheck import (CONTENT_SLOT_IN, EMU, INK, LAYOUT_INDEX, body_slide, bottom, caption_bar,
                       center_x, check, deck_error, fill_color, finish, generate, geometry, inside,
                       inside_shape, line_color, one, out_of_bounds, paragraphs, placeholder,
                       red_elements, review, run_style, run_styles, shapes_named, tag_shape,
                       warnings)

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


# ---- 方向 C（通用 / 项目汇报模式）：姓名首字圆形头像，不画卡片 ----

def general_md(members, title=TITLE, lead=CONCLUSION, next_line="Next: 9 月加入 A 仓班组长",
               extra=""):
    return f"""
---
title: Mock Deck
date: 14 Oct 2026
---

# {title}
## {SUBTITLE}
Layout: team
{extra}{lines(members)}
{lead}
{next_line}
"""


C_ROLES = ["Member Avatar", "Member Name", "Member Role", "Member Rule", "Member Duty"]
WHITE, MUTED, NEAR_BLACK, GRAY_LINE = "FFFFFF", "6B6B6B", "333333", "BFBFBF"


def body_bounds(s):
    """C 模式正文区上下沿（英寸）：lead 下沿 +0.19"，Next 细线上方 0.10"（没有 Next 时 6.95"）。"""
    lead, rule = one(s, "Lead"), one(s, "Next Rule")
    top = bottom(lead) / EMU + 0.19 if lead else 1.30
    low = rule.top / EMU - 0.10 if rule else 6.95
    return top, low


def check_avatars(s, members, label):
    """C 模式 N 人：不画卡片；每人头像（黑底圆、白色粗体姓名首字）+ 姓名 / 角色 / 短线 / 职责，
    自上而下居中在头像下；整组在正文区里、不越出。"""
    names = [sh.name for sh in s.shapes]
    check(f"{label}：不画卡片", not shapes_named(s, "Member Card"), names)
    got = {r: shapes_named(s, r) for r in C_ROLES}
    n = len(members)
    check(f"{label}：五类形状各 {n} 个", all(len(v) == n for v in got.values()),
          {r: len(v) for r, v in got.items()})
    if not all(len(v) == n for v in got.values()):
        return
    top, low = body_bounds(s)
    for i, (name, role, duty) in enumerate(members):
        av, nm, rl, rule, dt = (got[r][i] for r in C_ROLES)
        check(f"{label}：第 {i + 1} 人头像是黑底正圆、白色粗体姓名首字",
              geometry(av) == "ellipse" and fill_color(av) == INK and av.width == av.height
              and av.text_frame.text == name[0]
              and {(b, c) for _, b, c in run_styles(av)} == {(True, WHITE)},
              (geometry(av), fill_color(av), av.text_frame.text, run_styles(av)))
        check(f"{label}：第 {i + 1} 人文字 = 姓名 / 角色 / 职责",
              [paragraphs(x) for x in (nm, rl, dt)] == [[name], [role], [duty]],
              [paragraphs(x) for x in (nm, rl, dt)])
        check(f"{label}：第 {i + 1} 人自上而下 头像 → 姓名 → 角色 → 短线 → 职责，都居中对齐头像",
              bottom(av) <= nm.top and bottom(nm) <= rl.top and bottom(rl) <= rule.top
              and rule.top <= dt.top and rule.height == 0
              and all(abs(center_x(x) - center_x(av)) <= 2 for x in (nm, rl, rule, dt))
              and all(x.text_frame.paragraphs[0].alignment == 2 for x in (nm, rl, dt)),
              [(x.name, x.top / EMU, center_x(x) / EMU) for x in (av, nm, rl, rule, dt)])
        check(f"{label}：第 {i + 1} 人短线灰色、比文字框窄",
              line_color(rule) == GRAY_LINE and rule.width < nm.width, line_color(rule))
        n_pt, n_b, n_c = run_style(nm)
        r_pt, r_b, r_c = run_style(rl)
        d_pt, d_b, d_c = run_style(dt)
        check(f"{label}：第 {i + 1} 人姓名粗体近黑最大、角色灰、职责 #333333",
              n_b and n_c == INK and r_c == MUTED and not r_b and d_c == NEAR_BLACK and not d_b
              and n_pt > r_pt and n_pt > d_pt,
              (run_style(nm), run_style(rl), run_style(dt)))
        check(f"{label}：第 {i + 1} 人形状都在正文区里",
              all(x.top / EMU >= top - 0.01 and bottom(x) / EMU <= low + 0.01
                  and x.left >= 0.56 * EMU - 2 and x.left + x.width <= (0.56 + 12.2) * EMU + 2
                  for x in (av, nm, rl, rule, dt)),
              [(x.name, x.top / EMU, bottom(x) / EMU) for x in (av, nm, rl, rule, dt)])


def test_general_mode_avatars():
    """C 模式 4 人：一行头像，同一水平线、等大；整组在正文区里水平、垂直居中；只有 lead 竖线用红；
    正常稿没有警告。"""
    r = generate(general_md(MEMBERS))
    check("C team：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
    s = body_slide(r)
    if s is None:
        return
    check_avatars(s, MEMBERS, "C team 4 人")
    avs = shapes_named(s, "Member Avatar")
    if len(avs) == 4:
        check("C team 4 人：头像同一水平线、等大、从左到右",
              len({a.top for a in avs}) == 1 and len({a.width for a in avs}) == 1
              and all(a.left < b.left for a, b in zip(avs, avs[1:])))
        top, low = body_bounds(s)
        grp_top = min(a.top for a in avs) / EMU
        grp_bot = max(bottom(d) for d in shapes_named(s, "Member Duty")) / EMU
        check("C team 4 人：整组垂直居中",
              abs((grp_top - top) - (low - grp_bot)) <= 0.05, (top, grp_top, grp_bot, low))
        mid = (center_x(avs[0]) + center_x(avs[-1])) / 2 / EMU
        check("C team 4 人：整组水平居中", abs(mid - (0.56 + 6.1)) <= 0.02, mid)
    check("C team：banner 以外只有 lead 竖线用红", red_elements(s) == ["Lead Accent"],
          red_elements(s))


# lead 写到两行（正文区最矮的正常情况：两行 lead + Next）
LONG_LEAD = "分工按现场推进、数据复盘、系统支持三条线，周会对齐一次进度和问题，月底统一复盘各条线的结果和下月计划"


def test_general_mode_capacity():
    """C 模式 2 / 5 / 8 人和 8 人每段写满（两行 lead + Next）：都正确排布、没有警告、不越界；
    5 人以上两行（第一行一半向上取整），每行头像同一水平线、各自水平居中，两行不相压；
    几何审核不误报。"""
    for members, label in ((MEMBERS[:2], "C team 2 人"), (EIGHT[:5], "C team 5 人"),
                           (EIGHT, "C team 8 人"), (FULL, "C team 8 人写满")):
        r = generate(general_md(members, lead=LONG_LEAD))
        check(f"{label}：退出码 0、没有警告", r.rc == 0 and not warnings(r.stderr), r.stderr)
        s = body_slide(r)
        if s is None:
            continue
        lead = one(s, "Lead")
        check(f"{label}：lead 确实是两行", lead is not None and lead.height / EMU > 0.9,
              lead.height / EMU if lead is not None else None)
        check_avatars(s, members, label)
        check(f"{label}：不越界", not out_of_bounds(r.prs, [s]), out_of_bounds(r.prs, [s]))
        avs = shapes_named(s, "Member Avatar")
        if len(avs) != len(members):
            continue
        first = -(-len(members) // 2) if len(members) > 4 else len(members)
        for row in (avs[:first], avs[first:]):
            if not row:
                continue
            mid = (center_x(row[0]) + center_x(row[-1])) / 2 / EMU
            check(f"{label}：每行 {len(row)} 个头像同一水平线、水平居中",
                  len({a.top for a in row}) == 1 and abs(mid - 6.66) <= 0.02, mid)
        if len(members) > 4:
            duties = shapes_named(s, "Member Duty")
            check(f"{label}：第二行头像在第一行职责下面",
                  avs[first].top > max(bottom(d) for d in duties[:first]))
        out = review(r.workdir / "deck.md", r.path)
        geo = [x for x in out.stdout.splitlines()
               if x.startswith(("[出界]", "[重叠]", "[错位]", "[文字溢出]", "[压"))]
        check(f"{label}：几何审核不误报", not geo, out.stdout)


def test_general_mode_overflow_warning():
    """C 模式：正文区放不下（lead 写到三行 + Next，8 人每段写满）时警告，信息带页标题。"""
    lead = LONG_LEAD + "，并把问题清单同步给各车间主任和班组长确认，下月起每周五下午固定召开复盘会"
    r = generate(general_md(FULL, title="Crowded Team", lead=lead))
    check("C team：放不下时警告溢出正文区",
          r.rc == 0 and any("Crowded Team" in w and "溢出" in w for w in warnings(r.stderr)),
          r.stderr)


if __name__ == "__main__":
    test_render()
    test_review()
    test_capacity_limits()
    test_capacity_errors()
    test_general_mode_avatars()
    test_general_mode_capacity()
    test_general_mode_overflow_warning()
    finish()
