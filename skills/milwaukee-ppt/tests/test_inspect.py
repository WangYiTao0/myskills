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

r = run(Path(tempfile.gettempdir()) / "no-such-file-xyz.pptx")
check("不存在的文件非零退出并报错", r.returncode != 0 and "不存在" in r.stderr, r.stderr)

bad = Path(tempfile.mkdtemp()) / "x.pptx"
bad.write_text("not a pptx")
r = run(bad)
check("非 pptx 文件非零退出并报错", r.returncode != 0 and "pptx" in r.stderr, r.stderr)

r = run()
check("缺参数非零退出", r.returncode != 0)
finish()
