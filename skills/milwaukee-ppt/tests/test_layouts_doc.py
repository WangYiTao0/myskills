"""references/layouts.md 里的示例照抄就能生成：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_layouts_doc.py
做法：抽出文档里所有 ```markdown 代码块。第一个块是完整文稿格式（带 frontmatter）；
其余是各版式的片段，没有 `# ` 标题的补一个，然后拼成一份文稿生成一次。
文中引用的图片现生成纯色图。
"""
import re

from deckcheck import LAYOUT_INDEX, SKILL, check, finish, generate, one, run_style

DOC = SKILL / "references" / "layouts.md"
_BLOCK = re.compile(r"^```markdown\n(.*?)^```", re.S | re.M)
_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_LAYOUT = re.compile(r"(?im)^layout\s*[:：]\s*(\S+)\s*$")
NOT_YET_DOCUMENTED = set()   # 已注册、文档还没写的版式；新增版式写进 layouts.md 前临时登记


def doc_blocks():
    return _BLOCK.findall(DOC.read_text(encoding="utf-8"))


def assemble(blocks):
    parts = []
    for i, block in enumerate(blocks):
        if not re.search(r"(?m)^# ", block):
            block = f"# 示例片段 {i}\n" + block
        parts.append(block.strip("\n"))
    return "\n\n".join(parts) + "\n"


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
    m = re.search(r"(?m)^\| 各版式共用 \| (.*) \|$", DOC.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def _style_row(label):
    m = re.search(rf"(?m)^\| {re.escape(label)} \| (\d+)pt (bold )?#?(\w+)? ?\|?",
                  DOC.read_text(encoding="utf-8"))
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
                  DOC.read_text(encoding="utf-8"))
    return (float(m.group(1)), bool(m.group(2)), m.group(3).upper()) if m else None


def _table_row(label):
    m = re.search(rf"(?m)^\| {re.escape(label)} \| (.*) \|$", DOC.read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    test_doc_examples_generate()
    test_common_shape_names()
    test_process_general_mode()
    finish()
