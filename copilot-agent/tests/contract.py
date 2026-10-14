"""Copilot agent 合同检查的公共部分：各票的 test_*.py 都 `from contract import *` 后使用。

只检查对外承诺：字符数、版式名集合、示例能否生成、有没有私人路径；不检查措辞和段落顺序。

- AGENT / REPO / SKILL           本文件夹、仓库根、milwaukee-ppt skill 目录
- char_count(text)               Unicode 字符数（中文、英文、标点、换行都算 1）
- registered_layouts()           生成器注册的版式名集合（直接读生成器的注册表，不硬编码）
- layout_mentions(text)          文中所有 `Layout: 名字` 里的名字集合
- md_blocks(text)                文中所有 ```markdown 代码块
- generate_md(md)                一份完整文稿交给现有生成器（图片现生成占位图）→ deckcheck.Result
- page_count(md)                 文稿页数（`# ` 行数）
- generate_blocks(blocks)        按文稿分组交给现有生成器 → [(文稿, deckcheck.Result)]
                                 （带 frontmatter 的块开一份新文稿，其后的片段拼进这份）
- sections(text)                代码块以外的 `## ` 小节：[(标题, 正文)]
- missing_refs(text)            文中提到的文件名（.md / .pptx 等）在文件夹或 skill 里找不到的
- private_hits(root)             文件夹内文本文件里的私人路径：[(相对路径, 行号, 命中文字)]
- check / finish                 沿用 milwaukee-ppt tests 的汇总写法
"""
import re
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent
REPO = AGENT.parent
SKILL = REPO / "skills" / "milwaukee-ppt"

sys.path[:0] = [str(SKILL / "scripts"), str(SKILL / "tests")]

from deckcheck import check, finish, generate  # noqa: E402,F401
from layouts import REGISTRY  # noqa: E402

_BLOCK = re.compile(r"^```markdown\n(.*?)^```", re.S | re.M)
_LAYOUT = re.compile(r"(?i)\bLayout\s*[:：]\s*([A-Za-z][\w-]*)")
_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

# 私人路径：用户目录、Windows 盘符路径、~ 开头的家目录、file 协议链接、macOS 临时目录。
# 写法刻意避免字面上命中自己（如用 (?:Users|home) 而不是直接写出路径）。
_PRIVATE = re.compile(
    r"/(?:Users|home|root)/\w"
    r"|\b[A-Za-z]:[\\/](?:Users|Documents|OneDrive)"
    r"|(?<![\w.])~[/\\]"
    r"|file:/{2,3}"
    r"|/(?:private|var/folders)/"
)
_TEXT_SUFFIXES = {".md", ".py", ".txt", ".json", ".yml", ".yaml", ".csv"}


def char_count(text):
    return len(text)


def registered_layouts():
    return set(REGISTRY)


def layout_mentions(text):
    return {m.lower() for m in _LAYOUT.findall(text)}


def md_blocks(text):
    return _BLOCK.findall(text)


def assemble(blocks):
    """带 frontmatter 的块各开一份文稿，其后的片段拼进去；没有 `# ` 标题的片段补一个。"""
    decks = []
    for i, block in enumerate(blocks):
        if block.startswith("---\n") or not decks:
            decks.append([])
        if not re.search(r"(?m)^# ", block):
            block = f"# 示例片段 {i}\n" + block
        decks[-1].append(block.strip("\n"))
    return ["\n\n".join(parts) + "\n" for parts in decks]


def generate_md(md):
    """一份完整文稿交给生成器；文中引用的相对路径图片现生成纯色图。"""
    refs = {ref for ref in _IMG.findall(md) if not ref.startswith(("http://", "https://"))}
    return generate(md, images={ref: (1600, 900) for ref in refs})


def generate_blocks(blocks):
    return [(md, generate_md(md)) for md in assemble(blocks)]


def sections(text):
    """代码块以外的 `## ` 小节（代码块里的 `## ` 是示例的副标题，不算）。"""
    found, fenced = [], False
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            found.append([line[3:].strip(), ""])
        elif found:
            found[-1][1] += line
    return [tuple(s) for s in found]


_REF = re.compile(r"[\w.-]+\.(?:md|txt|pptx|docx|pdf)\b")
_REF_ROOTS = [AGENT, SKILL / "assets", SKILL / "examples"]


def missing_refs(text):
    """文中提到的文件名，在本文件夹或 skill 的 assets / examples 里找不到的。"""
    missing = []
    for name in sorted(set(_REF.findall(text))):
        if not any(next(root.rglob(name), None) for root in _REF_ROOTS):
            missing.append(name)
    return missing


def page_count(md):
    return len(re.findall(r"(?m)^# ", md))


def private_hits(root=AGENT):
    hits = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in _TEXT_SUFFIXES or "__pycache__" in path.parts:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in _PRIVATE.finditer(line):
                hits.append((str(path.relative_to(root)), n, m.group(0)))
    return hits


def test_no_private_paths():
    """所有票共用：文件夹内文本文件不含私人路径。"""
    hits = private_hits()
    check("文件夹内没有绝对路径 / 用户目录路径", not hits, hits)
