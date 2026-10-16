"""SKILL.md「生成后细调」里的最小示例照抄就能跑通：md 进、pptx 出，再跑示例改成稿。

运行：python3 skills/milwaukee-ppt/tests/test_finetune_doc.py
做法：抽出 SKILL.md 里 `### 生成后细调` 一节的 ```python 代码块，把 `<skill>` 换成本 skill
目录，在放了 deck.pptx 的临时目录里运行；再检查另存的新文件改对了、原稿没动。
"""
import hashlib
import re
import shutil
import subprocess
import sys
import textwrap

from deckcheck import (EMU, SKILL, check, finish, generate, lines_with, open_pptx, review, runs)

DOC = SKILL / "SKILL.md"

MD = """
---
title: Mock Deck
date: 13 Oct 2026
---

# Mock Stats Page
Layout: stats
- A | 120 件 | Mock note
- !B | 100% | Mock note
- C | 15 秒 | Mock note
Mock one-line conclusion.
"""


def snippet():
    text = DOC.read_text(encoding="utf-8")
    section = text.split("### 生成后细调", 1)[1].split("\n## ", 1)[0]
    blocks = re.findall(r"^[ \t]*```python\n(.*?)^[ \t]*```", section, re.S | re.M)
    return textwrap.dedent(blocks[0]) if blocks else ""


def test_snippet_runs():
    code = snippet()
    check("SKILL.md 细调：有一段 python 示例", bool(code), code)
    check("SKILL.md 细调：示例约 10 来行", 0 < len(code.strip().splitlines()) <= 16,
          len(code.strip().splitlines()))
    r = generate(MD)
    check("细调示例：生成成稿", r.rc == 0, r.stderr)
    if not code or r.rc != 0:
        return
    work = r.workdir
    shutil.copy(r.path, work / "deck.pptx")
    before = hashlib.sha256((work / "deck.pptx").read_bytes()).hexdigest()
    p = subprocess.run([sys.executable, "-c", code.replace("<skill>", str(SKILL))],
                       cwd=work, capture_output=True, text=True)
    check("细调示例：照抄运行退出 0", p.returncode == 0, p.stderr)
    check("细调示例：原稿没被覆盖",
          hashlib.sha256((work / "deck.pptx").read_bytes()).hexdigest() == before)
    outs = [f for f in work.glob("*.pptx") if f.name not in ("deck.pptx", r.path.name)]
    check("细调示例：另存为一个新文件", len(outs) == 1, [f.name for f in outs])
    if len(outs) != 1:
        return
    old = {sh.name: sh for sh in r.prs.slides[1].shapes}
    new = {sh.name: sh for sh in open_pptx(outs[0]).slides[1].shapes}
    num, num0 = new["Stat Number 2"], old["Stat Number 2"]
    got = runs(num)
    check("细调示例：改的是 run 文字，字号 / 粗体 / 颜色都还在",
          got[0][1:] == runs(num0)[0][1:] and got[0][0] != runs(num0)[0][0]
          and got[1:] == runs(num0)[1:], (runs(num0), got))
    check("细调示例：位置按英寸挪动", num.top != num0.top and (num.top - num0.top) % (EMU // 100) == 0,
          (num0.top, num.top))
    added = [sh for name, sh in new.items() if name not in old]
    check("细调示例：新加的形状起了名、去掉了主题样式",
          len(added) == 1 and added[0].name and not added[0].name.startswith(("Rectangle", "Shape"))
          and added[0]._element.find(
              "{http://schemas.openxmlformats.org/presentationml/2006/main}style") is None,
          [(sh.name) for sh in added])
    r2 = review(work / "deck.md", outs[0])
    flagged = lines_with(r2.stdout, "正文形状被改过")
    check("细调示例再审：挪位置、改文字不报，只有新加的形状报「正文形状被改过」",
          len(flagged) == 1 and added and added[0].name in flagged[0]
          and "Stat Number 2" not in flagged[0], r2.stdout)


if __name__ == "__main__":
    test_snippet_runs()
    finish()
