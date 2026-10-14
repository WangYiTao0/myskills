"""助手指令（instructions.md，整份粘进 Agent Builder 的 Instructions）守住合同。

运行：python3 copilot-agent/tests/test_instructions.py
"""
from contract import (AGENT, char_count, check, finish, generate_blocks, layout_mentions,
                      md_blocks, missing_refs, page_count, private_hits, registered_layouts,
                      test_no_private_paths)

INSTRUCTIONS = AGENT / "instructions.md"
LIMIT = 8000          # Agent Builder Instructions 上限
MARGIN = 400          # 留给后续小改的余量
# report-voice 核心规则抽查：五类挡下的表达各取一个代表词，外加缺数据占位
VOICE_KEYWORDS = ["赋能", "令人兴奋", "大幅", "彻底解决", "贬", "[数据缺失]"]


def text():
    return INSTRUCTIONS.read_text(encoding="utf-8") if INSTRUCTIONS.exists() else ""


def test_length():
    n = char_count(text())
    check("指令文件存在", INSTRUCTIONS.exists(), INSTRUCTIONS.name)
    check(f"指令 ≤ {LIMIT} 字符", 0 < n <= LIMIT, n)
    check(f"指令留 {MARGIN} 字符余量（≤ {LIMIT - MARGIN}）", 0 < n <= LIMIT - MARGIN, n)


def test_layout_set():
    want, got = registered_layouts(), layout_mentions(text())
    check("指令里的版式名集合 = 生成器注册的版式集合", got == want,
          f"多 {sorted(got - want)}，少 {sorted(want - got)}")


def test_report_voice():
    missing = [k for k in VOICE_KEYWORDS if k not in text()]
    check("指令含 report-voice 核心规则", not missing, missing)


def test_examples_generate():
    blocks = md_blocks(text())
    check("指令里有示例 md 代码块", bool(blocks), len(blocks))
    check("第一个示例是带 frontmatter 的完整文稿", bool(blocks) and blocks[0].startswith("---\n"))
    if not blocks:
        return
    for md, r in generate_blocks(blocks):
        check("示例照抄生成，退出码 0", r.rc == 0, r.stderr)
        check("示例每个 Layout 都被识别", layout_mentions(md) <= registered_layouts(),
              layout_mentions(md) - registered_layouts())
        check("示例页数都生成出来", len(r.slides) >= 1 + page_count(md),
              (len(r.slides), page_count(md)))


def test_refs():
    check("指令提到的文件都真实存在", not missing_refs(text()), missing_refs(text()))


if __name__ == "__main__":
    test_length()
    test_layout_set()
    test_report_voice()
    test_examples_generate()
    test_refs()
    test_no_private_paths()
    finish()
