"""references/layouts.md 里的示例照抄就能生成：md 进、pptx 出。

运行：python3 skills/milwaukee-ppt/tests/test_layouts_doc.py
做法：抽出文档里所有 ```markdown 代码块。第一个块是完整文稿格式（带 frontmatter）；
其余是各版式的片段，没有 `# ` 标题的补一个，然后拼成一份文稿生成一次。
文中引用的图片现生成纯色图。
"""
import re

from deckcheck import LAYOUT_INDEX, SKILL, check, finish, generate

DOC = SKILL / "references" / "layouts.md"
_BLOCK = re.compile(r"^```markdown\n(.*?)^```", re.S | re.M)
_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_LAYOUT = re.compile(r"(?im)^layout\s*[:：]\s*(\S+)\s*$")
# 已注册、文档还没写的版式（spec #20 的文档票 #27 补上后清空）
NOT_YET_DOCUMENTED = {"stats-side", "timeline-phase"}


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


if __name__ == "__main__":
    test_doc_examples_generate()
    finish()
