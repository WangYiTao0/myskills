"""references/layouts.md（总览）和 references/layouts/<版式名>.md（各版式文件）里的示例照抄就能生成：
md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_layouts_doc.py
做法：总览在前、各版式文件按总览「各版式文件」清单顺序拼成全文（deckcheck.layouts_doc_text），
抽出全文里所有 ```markdown 代码块。第一个块是完整文稿格式（带 frontmatter）；
其余是各版式的片段，没有 `# ` 标题的补一个，然后拼成一份文稿生成一次。
文中引用的图片现生成纯色图。
"""
import re
import subprocess
import sys

from deckcheck import (LAYOUT_INDEX, LAYOUTS_DOC_DIR, SKILL, check, finish, generate, layout_doc,
                       layout_doc_names, layouts_doc_text, one, run_style)

_BLOCK = re.compile(r"^```markdown\n(.*?)^```", re.S | re.M)
_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_LAYOUT = re.compile(r"(?im)^layout\s*[:：]\s*(\S+)\s*$")
NOT_YET_DOCUMENTED = set()   # 已注册、文档还没写的版式；新增版式写进 layouts/<版式名>.md 前临时登记


def doc_blocks():
    return _BLOCK.findall(layouts_doc_text())


def assemble(blocks):
    parts = []
    for i, block in enumerate(blocks):
        if not re.search(r"(?m)^# ", block):
            block = f"# 示例片段 {i}\n" + block
        parts.append(block.strip("\n"))
    return "\n\n".join(parts) + "\n"


def test_doc_files_listed():
    """总览「各版式文件」清单和 references/layouts/ 下的文件一一对应。"""
    listed = layout_doc_names()
    on_disk = sorted(p.stem for p in LAYOUTS_DOC_DIR.glob("*.md"))
    check("layouts.md：「各版式文件」清单列全 layouts/ 下的文件、不重复",
          sorted(listed) == on_disk and len(set(listed)) == len(listed), (listed, on_disk))


def test_doc_examples_generate():
    blocks = doc_blocks()
    check("layouts.md：抽到示例代码块", len(blocks) >= 7, len(blocks))
    check("layouts.md：第一个块是带 frontmatter 的完整文稿",
          bool(blocks) and blocks[0].startswith("---\n"), blocks[:1])
    md = assemble(blocks)
    refs = {ref for ref in _IMG.findall(md) if not ref.startswith(("http://", "https://"))}
    r = generate(md, images={ref: (1600, 900) for ref in refs})
    check("layouts.md：示例照抄生成，退出码 0", r.rc == 0, r.stderr)
    check("layouts.md：示例没有警告", "警告" not in r.stderr, r.stderr)
    pages = len(re.findall(r"(?m)^# ", md))
    closing = 1 if re.search(r"(?m)^closing\s*:\s*\S", md) else 0
    check("layouts.md：页数 = 封面 + 示例页 + 收尾页",
          len(r.slides) == 1 + pages + closing, (len(r.slides), pages, closing))
    used = set()
    for page in re.split(r"(?m)^# ", md)[1:]:
        m = _LAYOUT.search(page)
        used.add(m.group(1).lower() if m else "evidence")
    want = set(LAYOUT_INDEX) - NOT_YET_DOCUMENTED
    check(f"layouts.md：示例覆盖全部 {len(want)} 个已写文档的版式", used == want, used)


COMMON_PAGE = """
# 证据 / EVIDENCE
## 试点两条线完成切换
Tag: Aug
PDCA: D
![](img/a.png)
两条试点线 3 周内切换到新点检表
Next: 11 月前推广到其余 4 条线
"""


def _common_row():
    m = re.search(r"(?m)^\| 各版式共用 \| (.*) \|$", layouts_doc_text())
    return m.group(1) if m else ""


def _style_row(label):
    m = re.search(rf"(?m)^\| {re.escape(label)} \| (\d+)pt (bold )?#?(\w+)? ?\|?",
                  layouts_doc_text())
    return (float(m.group(1)), bool(m.group(2))) if m else None


def test_common_shape_names():
    """形状命名约定表「各版式共用」一行的名字，生成器真的会画（通用 / 项目模式 + 月报模式）。"""
    names = [n for n in re.findall(r"`([^`]+)`", _common_row()) if not n.endswith(":")]
    check("layouts.md：形状命名表有「各版式共用」一行，列出 lead / Next 的形状",
          {"Lead", "Lead Accent", "Next Rule", "Next Line"} <= set(names), names)
    drawn = set()
    for head in ("---\ntitle: Mock Deck\nreport: project\n---\n",
                 "---\nmonth: 2026-08\nauthor: Mock.Author\n---\n"):
        md = head + (COMMON_PAGE if "report" in head else COMMON_PAGE.replace("PDCA: D\n", ""))
        r = generate(md, images={"img/a.png": (1600, 900)})
        if r.rc != 0:
            check("layouts.md：共用形状探测文稿生成", False, r.stderr)
            return
        drawn |= {sh.name for sh in r.slides[1].shapes}
    want = {n.replace(" N", " 1") for n in names}
    check("layouts.md：「各版式共用」的形状名生成器都会画", want <= drawn, sorted(want - drawn))
    r = generate("---\ntitle: Mock Deck\n---\n" + COMMON_PAGE.replace("PDCA: D\n", ""),
                 images={"img/a.png": (1600, 900)})
    s = r.slides[1] if r.rc == 0 else None
    for label, shape in (("lead（通用 / 项目模式）", "Lead"), ("Next 行（通用 / 项目模式）", "Next Line")):
        doc = _style_row(label)
        got = run_style(one(s, shape))[:2] if s is not None and one(s, shape) else None
        check(f"layouts.md：{label} 的字号、粗体和生成器一致", doc is not None and doc == got,
              (doc, got))


PROCESS_PAGE = """---
title: Mock Deck
---

# 新流程 / PROCESS
## 排班改为系统分配
Layout: process
1. 登记 | 交班时登记电量
2. 排队 | 系统按电量排序
3. 充电 | 到点去充电位
三步完成排班，司机不再凭经验排队
"""


def _full_style_row(label):
    """样式表里 label 一行开头的「NNpt [bold ]#RRGGBB」→ (字号, 粗体, 颜色)；没有返回 None。"""
    m = re.search(rf"(?m)^\| {re.escape(label)} \| (\d+)pt (bold )?#(\w{{6}})",
                  layouts_doc_text())
    return (float(m.group(1)), bool(m.group(2)), m.group(3).upper()) if m else None


def _table_row(label):
    m = re.search(rf"(?m)^\| {re.escape(label)} \| (.*) \|$", layouts_doc_text())
    return m.group(1) if m else ""


def test_process_general_mode():
    """process 方向 C：形状命名表的名字生成器都会画；步骤名 / 说明 / 编号的字号、颜色和代码一致。"""
    names = re.findall(r"`([^`]+)`", _table_row("process（通用 / 项目模式）"))
    check("layouts.md：形状命名表有 process（通用 / 项目模式）一行，列出编号圆、连接线、标题和说明",
          {"Process Mark N", "Process Line N", "Process Title N", "Process Desc N"} <= set(names),
          names)
    r = generate(PROCESS_PAGE)
    s = r.slides[1] if r.rc == 0 else None
    drawn = {sh.name for sh in s.shapes} if s is not None else set()
    want = {n.replace(" N", " 1") for n in names}
    check("layouts.md：process（通用 / 项目模式）的形状名生成器都会画", want and want <= drawn,
          sorted(want - drawn))
    for label, shape in (("流程编号（通用 / 项目模式）", "Process Mark 1"),
                         ("流程步骤名（通用 / 项目模式）", "Process Title 1"),
                         ("流程说明（通用 / 项目模式）", "Process Desc 1")):
        doc = _full_style_row(label)
        got = run_style(one(s, shape)) if s is not None and one(s, shape) else None
        check(f"layouts.md：{label} 的字号、粗体、颜色和生成器一致",
              doc is not None and doc == got, (doc, got))


TEAM_PAGE = """---
title: Mock Deck
---

# 项目团队 / TEAM
## 两人小组，现场和数据分开负责
Layout: team
- 周航 | 现场推进 | 贴码和巡检
- 陈雨 | 数据复盘 | 每周出周报
分工按现场和数据两条线，周会对齐
"""


def test_team_general_mode():
    """team 方向 C：形状命名表的名字生成器都会画、不画卡片；头像首字 / 姓名 / 角色 / 职责的
    字号（最大一档）、粗体、颜色和代码一致；inspect 标记形状生成器会画、inspect 认得出。"""
    names = re.findall(r"`([^`]+)`", _table_row("team（通用 / 项目模式）"))
    check("layouts.md：形状命名表有 team（通用 / 项目模式）一行，列出头像、姓名、角色、短线、职责",
          {"Member Avatar N", "Member Name N", "Member Role N", "Member Rule N",
           "Member Duty N"} <= set(names), names)
    r = generate(TEAM_PAGE)
    s = r.slides[1] if r.rc == 0 else None
    drawn = {sh.name for sh in s.shapes} if s is not None else set()
    want = {re.sub(r" N$", " 1", n) for n in names}
    check("layouts.md：team（通用 / 项目模式）的形状名生成器都会画、没有卡片",
          want and want <= drawn and "Member Card 1" not in drawn, sorted(want - drawn))
    for label, shape in (("团队头像首字（通用 / 项目模式）", "Member Avatar 1"),
                         ("团队姓名（通用 / 项目模式）", "Member Name 1"),
                         ("团队角色（通用 / 项目模式）", "Member Role 1"),
                         ("团队职责（通用 / 项目模式）", "Member Duty 1")):
        doc = _full_style_row(label)
        got = run_style(one(s, shape)) if s is not None and one(s, shape) else None
        check(f"layouts.md：{label} 的字号、粗体、颜色和生成器一致",
              doc is not None and doc == got, (doc, got))
    m = re.search(r"inspect 靠 `([^`]+)` 认出 team", layout_doc("team"))
    mark = m.group(1) if m else None
    check("layouts/team.md：写的 inspect 标记形状生成器会画", mark is not None and mark in drawn,
          (mark, sorted(drawn)))
    out = subprocess.run([sys.executable, str(SKILL / "scripts" / "inspect_ppt.py"), str(r.path)],
                         capture_output=True, text=True).stdout if r.rc == 0 else ""
    check("layouts/team.md：生成的 team 页 inspect 认作 team",
          re.search(r"(?m)^== 第 2 页 .*\| 版式: team$", out) is not None, out[:600])


NUMBERS_DECK = """---
title: Mock Deck
---

# 试点数据 / KEY RESULTS
## 记录完整率达到 100%
Layout: stats
- 试点工具 | 120 件 | 覆盖试点车间
  - 电动工具 86 件
- !记录完整率 | 100% | 改前约 70%
口径：系统导出
试点 4 周记录完整率 100%

# 试点结论 / FINDINGS
## 两项指标都达到推广条件
Layout: stats-side
- 试点工具 | 120 件 | 覆盖试点车间
- !记录完整率 | 100% | 改前约 70%
> 记录完整率达到 100%
记录完整率和登记用时都达到推广条件

# 里程碑 / MILESTONES
## 试点按计划推进
Layout: timeline
- 07 Jul | 立项 | 确定范围
- 04 Aug | 上线 | 开放试用
- 15 Sep | 试点 | 切换扫码
贴码晚一周未影响试点开始

# 充电等待 / WAITING
## B 仓等待最长
Layout: table
| 仓库 | 叉车数 |
| --- | --- |
| A 仓 | 12 台 |
| !B 仓 | 20 台 |
B 仓高峰等待 35 分钟
"""


def _cell_style(frame, r, c):
    run = frame.table.cell(r, c).text_frame.paragraphs[0].runs[0]
    return run.font.size.pt, bool(run.font.bold), str(run.font.color.rgb)


def test_numbers_general_mode():
    """stats / stats-side / timeline / table 方向 C：样式表里「（通用 / 项目模式）」各行的
    字号、粗体、颜色和生成器一致（取每行写的第一个值，即最大一档）。"""
    r = generate(NUMBERS_DECK)
    if r.rc != 0:
        check("layouts.md：数字类版式探测文稿生成", False, r.stderr)
        return
    stats, side, tl, table = r.slides[1:5]
    rows = [
        ("stats 大数字（通用 / 项目模式）", run_style(one(stats, "Stat Number 1"))),
        ("stats 标签（通用 / 项目模式）", run_style(one(stats, "Stat Label 1"))),
        ("stats 说明 / 解读（通用 / 项目模式）", run_style(one(stats, "Stat Note 1"))),
        ("stats 说明 / 解读（通用 / 项目模式）", run_style(one(stats, "Stat Points 1"))),
        ("stats-side 大数字（通用 / 项目模式）", run_style(one(side, "Side Number 1"))),
        ("stats-side 标签（通用 / 项目模式）", run_style(one(side, "Side Text 1"))),
        ("stats-side 说明（通用 / 项目模式）", run_style(one(side, "Side Text 1"), 1)),
        ("stats-side 结论区小标题（通用 / 项目模式）", run_style(one(side, "Side Conclusion Title"))),
        ("stats-side 结论要点（通用 / 项目模式）", run_style(one(side, "Side Points"))),
        ("时间线日期（通用 / 项目模式）", run_style(one(tl, "Timeline Date 1"))),
        ("时间线标题（通用 / 项目模式）", run_style(one(tl, "Timeline Text 1"))),
        ("时间线说明（通用 / 项目模式）", run_style(one(tl, "Timeline Text 1"), 1)),
        ("表格（通用 / 项目模式）", _cell_style(one(table, "Data Table"), 1, 0)),
    ]
    for label, got in rows:
        doc = _full_style_row(label)
        check(f"layouts.md：{label} 的字号、粗体、颜色和生成器一致",
              doc is not None and doc == got, (doc, got))


if __name__ == "__main__":
    test_doc_files_listed()
    test_doc_examples_generate()
    test_common_shape_names()
    test_process_general_mode()
    test_team_general_mode()
    test_numbers_general_mode()
    finish()
