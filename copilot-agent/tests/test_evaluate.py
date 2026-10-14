"""评测脚本 evaluate.py 在人工构造的样例回答上报对三种情况：能生成、版式非法、几份之间有差异。

运行：python3 copilot-agent/tests/test_evaluate.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from contract import AGENT, check, finish, test_no_private_paths

sys.path.insert(0, str(AGENT))
import evaluate  # noqa: E402

GOOD = """好的，下面是文稿：

```markdown
---
title: 样例汇报
---

# 新流程 / PROCESS
## 借还改为扫码，三步完成
Layout: process
1. 贴码 | 每件工具贴码
2. 扫码借出 | 自动带出信息
3. 扫码归还 | 记录归还时间
新流程已试运行 4 周

# 看板 / DASHBOARD
## 看板显示逾期工具
Layout: image-text
![](img/看板截图.png)
- 按车间显示在借数量
看板已在晨会使用
```

请把看板截图替换成实际图片。
"""

BAD_LAYOUT = """```markdown
---
title: 样例汇报
---

# 新流程 / PROCESS
## 借还改为扫码，三步完成
Layout: flowchart
1. 贴码 | 每件工具贴码
2. 扫码借出 | 自动带出信息
3. 扫码归还 | 记录归还时间
新流程已试运行 4 周
```
"""

# 和 GOOD 页数不同、第一页版式不同、标题不同
DRIFT = """```md
---
title: 样例汇报
---

# 新流程 / PROCESS
## 扫码借还已在试点车间运行
![](img/流程.png)
扫码借还试运行 4 周

# 看板 / DASHBOARD
## 看板显示逾期工具
Layout: image-text
![](img/看板截图.png)
- 按车间显示在借数量
看板已在晨会使用

# 关键数据 / KEY RESULTS
## 记录完整率 100%
Layout: stats
- 试点工具 | 120 件 | 全部手持工具
- !记录完整率 | 100% | 改前约 70%
完整率达到 100%
```
"""

NO_BLOCK = "抱歉，我需要更多信息才能写文稿：项目开始时间是？"


def write(tmp, files):
    for name, body in files.items():
        (tmp / name).write_text(body, encoding="utf-8")
    return [tmp / name for name in files]


def test_single_answers():
    tmp = Path(tempfile.mkdtemp(prefix="copilot-eval-"))
    good, bad, none = (evaluate.evaluate_answer(p) for p in
                       write(tmp, {"01.md": GOOD, "02.md": BAD_LAYOUT, "03.md": NO_BLOCK}))
    check("能生成的回答：报告可生成", good.generated, good.error)
    check("能生成的回答：版式合法", good.layouts_ok and not good.bad_layouts, good.bad_layouts)
    check("能生成的回答：读出每页版式", good.layouts == ["process", "image-text"], good.layouts)
    check("能生成的回答：没有警告", good.warnings == 0, good.warnings)
    check("能生成的回答：读出每页副标题",
          good.titles == ["借还改为扫码，三步完成", "看板显示逾期工具"], good.titles)
    check("版式非法的回答：报告不可生成", not bad.generated, bad.error)
    check("版式非法的回答：指出非法版式名", bad.bad_layouts == ["flowchart"], bad.bad_layouts)
    check("版式非法的回答：错误信息来自生成器", "flowchart" in bad.error, bad.error)
    check("没有文稿的回答：报告找不到文稿", not none.found and not none.generated, none)


def test_drift():
    tmp = Path(tempfile.mkdtemp(prefix="copilot-eval-"))
    same = [evaluate.evaluate_answer(p) for p in write(tmp, {"01.md": GOOD, "02.md": GOOD})]
    d = evaluate.drift(same)
    check("两份相同：页数一致", d.pages_same, d.page_counts)
    check("两份相同：版式序列一致", d.layouts_same, d.layout_seqs)
    check("两份相同：标题一致", d.titles_same, d.title_seqs)

    tmp = Path(tempfile.mkdtemp(prefix="copilot-eval-"))
    mixed = [evaluate.evaluate_answer(p) for p in write(tmp, {"01.md": GOOD, "02.md": DRIFT})]
    check("```md 代码块也能读出", mixed[1].found and mixed[1].generated, mixed[1].error)
    d = evaluate.drift(mixed)
    check("有差异：报出页数不一致", not d.pages_same and d.page_counts == [2, 3], d.page_counts)
    check("有差异：报出版式序列不一致", not d.layouts_same, d.layout_seqs)
    check("有差异：报出标题不一致", not d.titles_same, d.title_seqs)
    check("有差异：逐页列出不一致的页", 1 in d.differing_pages, d.differing_pages)


def test_cli_report():
    tmp = Path(tempfile.mkdtemp(prefix="copilot-eval-"))
    write(tmp, {"01.md": GOOD, "02.md": BAD_LAYOUT, "03.md": DRIFT, "question.md": "题目"})
    r = subprocess.run([sys.executable, str(AGENT / "evaluate.py"), str(tmp)],
                       capture_output=True, text=True)
    check("命令行：退出码 0", r.returncode == 0, r.stderr)
    out = r.stdout
    check("命令行：不把 question.md 当回答", "question.md" not in out, out)
    check("命令行：汇总生成成功率", "生成成功 2/3" in out, out)
    check("命令行：汇总版式合法率", "版式合法 2/3" in out, out)
    check("命令行：输出一致性摘要", "一致性" in out and "页数" in out, out)
    check("命令行：报告里没有临时目录路径", str(tmp) not in out, out)


if __name__ == "__main__":
    test_single_answers()
    test_drift()
    test_cli_report()
    test_no_private_paths()
    finish()
