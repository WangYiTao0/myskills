"""inspect_ppt.py 检查命令测试：先用生成器生成 pptx，再只看检查命令的输出与退出码。

运行：python3 skills/milwaukee-ppt/tests/test_inspect.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from deckcheck import SKILL, check, finish, generate

INSPECT = SKILL / "scripts" / "inspect_ppt.py"

MD = """
---
title: Mock Deck
---

# Evidence Page
![](img/a.png)
这是一段很长很长的结论文字，用来检查文字前三十个字的截断是否正确生效，超出部分不应出现。
"""


def run(*args):
    return subprocess.run([sys.executable, str(INSPECT), *map(str, args)],
                          capture_output=True, text=True)


res = generate(MD, images={"img/a.png": (800, 450)})
r = run(res.path)
check("生成的 pptx 检查退出 0", r.returncode == 0, r.stderr)
lines = r.stdout.splitlines()
heads = [l for l in lines if re.match(r"^== 第 \d+ 页", l)]
check("每页一个标题行，含页码与 layout 名", len(heads) >= 2 and "layout:" in heads[0],
      r.stdout)
check("输出含 Evidence Page 标题文字", "Evidence Page" in r.stdout, r.stdout)
check("输出含图片形状与类型", "PICTURE" in r.stdout, r.stdout)
check("形状行含两位小数的 L/T/W/H",
      re.search(r"L=\d+\.\d\d T=\d+\.\d\d W=\d+\.\d\d H=\d+\.\d\d", r.stdout) is not None,
      r.stdout)
check("文字只取前 30 字",
      "这是一段很长很长的结论文字，用来检查文字前三十个字的截断是否" in r.stdout
      and "超出部分不应出现" not in r.stdout, r.stdout)

# 页标题行除模板 layout 名外还给生成器版式名；共用模板 layout 的版式（stats / stats-side、
# timeline / timeline-phase、evidence / section / agenda / team / table）也要分得出来。占位框给出 idx。
LAYOUTS_MD = """
---
title: Mock Deck
date: 13 Oct 2026
closing: Thank You
---

# Mock Evidence
![](img/a.png)

# Mock Stats
Layout: stats
- A | 1 | n
- B | 2 | n

# Mock Side
Layout: stats-side
- A | 1 | n
- B | 2 | n
> Mock finding.

# Mock Timeline
Layout: timeline
- Jan | A | n
- Feb | B | n
- Mar | C | n

# Mock Status Timeline
Layout: timeline
- Jan | A | n | 完成
- Feb | B | n | 进行中
- Mar | C | n | 未完成

# Mock Phase
Layout: timeline-phase
- Jan | A | n | 完成
- Feb | B | n | 进行中
- Mar | C | n | 未完成

# Mock Steps
Layout: process
1. A | n
2. B | n
3. C | n

# Mock Section
Layout: section
02 | 试点推进 | PILOT

# Mock Agenda
Layout: agenda
01 | 项目目标 | TARGET
02 | 试点推进 | PILOT
03 | 下一步 | NEXT STEPS

# Mock Team
Layout: team
- 林晓 | 项目负责人 | 统筹进度
- 周航 | 现场推进 | 贴码和培训

# Mock Table
Layout: table
| 车间 | 工具数 |
| 一车间 | 120 件 |
| 二车间 | 80 件 |
"""
res = generate(LAYOUTS_MD, images={"img/a.png": (800, 450)})
r = run(res.path)
heads = [l for l in r.stdout.splitlines() if l.startswith("== ")]
want = ["-", "evidence", "stats", "stats-side", "timeline", "timeline", "timeline-phase",
        "process", "section", "agenda", "team", "table", "-"]
got = [re.search(r"\| 版式: (\S+)$", h).group(1) if re.search(r"\| 版式: (\S+)$", h) else None
       for h in heads]
check("页标题行：模板 layout 名之后给生成器版式名（封面 / 收尾为 -）", got == want, heads)
check("页标题行：模板 layout 名仍在", "layout: Stats |" in r.stdout, heads)
check("表格页：原生表格一行，类型 TABLE", any(l.startswith("Data Table | TABLE |")
                                          for l in r.stdout.splitlines()), r.stdout[-800:])
check("占位框给出 idx", any("PLACEHOLDER idx=0 |" in l for l in r.stdout.splitlines()),
      r.stdout[:800])
check("非占位框不带 idx", all("idx=" not in l for l in r.stdout.splitlines()
                              if l.startswith("Stat Number")), r.stdout[:800])

r = run(Path(tempfile.gettempdir()) / "no-such-file-xyz.pptx")
check("不存在的文件非零退出并报错", r.returncode != 0 and "不存在" in r.stderr, r.stderr)

bad = Path(tempfile.mkdtemp()) / "x.pptx"
bad.write_text("not a pptx")
r = run(bad)
check("非 pptx 文件非零退出并报错", r.returncode != 0 and "pptx" in r.stderr, r.stderr)

r = run()
check("缺参数非零退出", r.returncode != 0)
finish()
