"""精简版知识文件（knowledge/ 下，上传到 Agent Builder 知识库）守住合同。

运行：python3 copilot-agent/tests/test_knowledge.py
"""
import re

from contract import (AGENT, char_count, check, finish, generate_blocks, generate_md,
                      layout_mentions,
                      md_blocks, missing_refs, page_count, registered_layouts, sections,
                      test_no_private_paths)

KNOWLEDGE = AGENT / "knowledge" / "milwaukee-ppt-layout-guide.txt"
EXAMPLE_DECK = AGENT / "knowledge" / "example-deck.txt"   # 虚构示例 deck，整份是一份文稿
INSTRUCTIONS = AGENT / "instructions.md"
LIMIT = 15000
# 版式小节的标题以版式名开头（小写英文），其余小节标题用中文
_LAYOUT_HEADING = re.compile(r"^([a-z][a-z-]*)\b")
# 生成器画出来的形状名（如 Stat Number 2、Caption Bar）、占位框编号、脚本命令
_SHAPE = re.compile(r"\b(?:Stat|Side|Milestone|Timeline|Phase|Legend|Process|Caption|Month|"
                    r"Current|Progress|Remaining) [A-Z][a-z]+\b|\b[Ii]dx\b|[Pp]laceholder")
_SCRIPT = re.compile(r"python3?\b|\.py\b|generate_ppt|inspect_ppt|soffice|pdftoppm|```(?:bash|sh)\b")
PARTS = ["适用", "写法", "反例"]


def text():
    return KNOWLEDGE.read_text(encoding="utf-8") if KNOWLEDGE.exists() else ""


def layout_sections():
    found = {}
    for heading, body in sections(text()):
        m = _LAYOUT_HEADING.match(heading)
        if m:
            found[m.group(1)] = body
    return found


def test_coverage():
    check("知识文件存在", KNOWLEDGE.exists(), KNOWLEDGE.name)
    found, want = layout_sections(), registered_layouts()
    check("版式小节 = 生成器注册的 8 个版式", set(found) == want,
          f"多 {sorted(set(found) - want)}，少 {sorted(want - set(found))}")
    for name, body in sorted(found.items()):
        missing = [p for p in PARTS if p not in body]
        check(f"{name}：有适用场景、写法、反例", not missing, missing)
        examples = [b for b in md_blocks(body) if name in layout_mentions(b)]
        check(f"{name}：有带 `Layout: {name}` 的示例", bool(examples), md_blocks(body))
    check("全文的版式名集合 = 生成器注册的版式集合", layout_mentions(text()) == want,
          layout_mentions(text()) ^ want)


def test_examples_generate():
    blocks = md_blocks(text())
    check("第一个示例是带 frontmatter 的完整文稿", bool(blocks) and blocks[0].startswith("---\n"))
    for md, r in generate_blocks(blocks):
        title = md.splitlines()[1] if md.startswith("---") else md.splitlines()[0]
        check(f"示例照抄生成，退出码 0（{title}）", r.rc == 0, r.stderr)
        check(f"示例没有警告（{title}）", "警告" not in r.stderr, r.stderr)
        check(f"示例页数都生成出来（{title}）", len(r.slides) >= 1 + page_count(md),
              (len(r.slides), page_count(md)))


def test_no_internals():
    t = text()
    check(f"知识文件 ≤ {LIMIT} 字符", 0 < char_count(t) <= LIMIT, char_count(t))
    check("不出现形状名和占位框编号", not _SHAPE.findall(t), _SHAPE.findall(t))
    check("不出现脚本命令", not _SCRIPT.findall(t), _SCRIPT.findall(t))
    check("知识文件提到的文件都真实存在", not missing_refs(t), missing_refs(t))


def test_example_deck():
    md = EXAMPLE_DECK.read_text(encoding="utf-8") if EXAMPLE_DECK.exists() else ""
    check("虚构示例 deck 存在", bool(md), EXAMPLE_DECK.name)
    if not md:
        return
    r = generate_md(md)
    check("示例 deck 照抄生成，退出码 0", r.rc == 0, r.stderr)
    check("示例 deck 没有警告", "警告" not in r.stderr, r.stderr)
    check("示例 deck 覆盖全部版式", layout_mentions(md) | {"evidence"} == registered_layouts(),
          layout_mentions(md))
    check("示例 deck 不出现形状名和脚本命令",
          not _SHAPE.findall(md) and not _SCRIPT.findall(md), _SHAPE.findall(md) + _SCRIPT.findall(md))


def test_instructions_reference():
    t = INSTRUCTIONS.read_text(encoding="utf-8")
    check("助手指令按实际文件名引用知识文件", KNOWLEDGE.name in t, KNOWLEDGE.name)


if __name__ == "__main__":
    test_coverage()
    test_examples_generate()
    test_no_internals()
    test_example_deck()
    test_instructions_reference()
    test_no_private_paths()
    finish()
