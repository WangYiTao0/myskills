"""审查脚本 review_deck.py：生成后机械检查文稿和 pptx，报出 Copilot 实测里出现过的问题。

运行：python3 copilot-agent/tests/test_review.py
做法：先构建技能包、解到临时目录，再按 SKILL.md 的写法运行 scripts/review_deck.py，
和 Copilot 沙箱里的执行方式一致。
"""
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from pathlib import Path

from contract import AGENT, check, finish, test_no_private_paths

sys.path.insert(0, str(AGENT))
import build_skill  # noqa: E402

T2 = AGENT / "runs" / "t2-skill-pptx"

GOOD = """\
---
title: 来料检验记录电子化 项目汇报
---

# 项目背景 / BACKGROUND
## 查一批次的检验结论要翻纸质单
Layout: before-after
A 车间同一批检验员，改前改后的工作方式

### Before: 纸质检验单
手写纸质检验单，下班前录入 Excel，每周五手工汇总周报

### After: 电子检验单
平板填写并拍照上传，提交即入库，每周一自动生成周报

检验单提交即入库，供应商质量周报改为自动生成

# 新流程 / PROCESS
## 检验记录三步完成，提交即入库
Layout: process
1. 平板填写 | 现场填写电子检验单
2. 拍照上传 | 不良品照片随单上传
3. 自动出周报 | 每周一生成质量周报
A 车间检验员 5 月起全部使用新流程

# 关键数据 / KEY RESULTS
## 试点 8 周，检验单全部电子化
Layout: stats
- 电子检验单 | 2,360 张 | 试点 8 周全部电子化
- !单张录入用时 | 约 1.5 分钟 | 改前约 4 分钟
口径：A 车间试点 8 周
单张录入用时从约 4 分钟降到约 1.5 分钟

# 项目节点 / MILESTONE
## 3 月立项，6 月完成 8 周试点复盘
Layout: timeline
- Mar | 立项 | 确定 A 车间试点 | 完成
- Apr | 试用上线 | 电子检验单开放试用 | 完成
- !May | 全员切换 | A 车间检验员全部切换 | 完成
- Jun | 试点复盘 | 完成 8 周试点复盘 | 完成
试点复盘 6 月完成
"""

BAD = """\
---
title: 来料检验记录电子化 项目汇报
---

# 项目目标 / TARGET
## 项目目标
Layout: process
1. 平板填写 | 现场填写电子检验单
2. 拍照上传 | 不良品照片随单上传
3. 自动出周报 | 每周一生成质量周报

# 应用场景 / USE CASES
## 检验流程全面赋能，效率大幅提升
Layout: process
1. 平板填写 | 检验员填写
2. 拍照上传 | 照片上传
3. 提交入库 | 直接入库
检验流程已切换

# 关键数据 / KEY RESULTS
## 试点 8 周，检验单全部电子化
Layout: stats
- 电子检验单 | 2,360 张 | 试点期间全部电子化
- 周报生成方式 | 自动生成 | 替代每周五人工汇总
- 不良率 | [数据缺失] | 仍在核对
检验单全部电子化

# 项目节点 / MILESTONE
## 3 月立项，6 月完成 8 周试点复盘
Layout: timeline
- !Mar | 立项 | 确定试点 | 完成
- !Apr | 试用上线 | 开放试用 | 完成
- !May | 全员切换 | 全部切换 | 完成
试点复盘 6 月完成
"""


def package():
    work = Path(tempfile.mkdtemp(prefix="skill-review-"))
    with zipfile.ZipFile(build_skill.build(work / "skill.zip")) as z:
        z.extractall(work)
    return work


def review(work, md, pptx=None):
    deck = work / "deck.md"
    deck.write_text(textwrap.dedent(md), encoding="utf-8")
    if pptx is None:
        pptx = work / "deck.pptx"
        subprocess.run([sys.executable, "scripts/generate_ppt.py", str(deck), "-o", str(pptx)],
                       cwd=work, check=True, capture_output=True)
    r = subprocess.run([sys.executable, "scripts/review_deck.py", str(deck), str(pptx)],
                       cwd=work, capture_output=True, text=True)
    return r


def test_good_deck_passes():
    work = package()
    r = review(work, GOOD)
    check("合格文稿：退出码 0", r.returncode == 0, r.stderr)
    check("合格文稿：报 REVIEW OK", r.stdout.strip().endswith("REVIEW OK"), r.stdout)


def test_bad_deck_flags():
    r = review(package(), BAD)
    out = r.stdout
    check("问题文稿：退出码仍为 0（审查只报告）", r.returncode == 0, r.stderr)
    check("问题文稿：不报 REVIEW OK", "REVIEW OK" not in out, out)
    expect = {
        "相邻两页版式相同": "页「应用场景 / USE CASES」",
        "目录式副标题": "页「项目目标 / TARGET」",
        "缺结论行": "页「项目目标 / TARGET」",
        "章节和版式不配": "页「项目目标 / TARGET」",
        "内容重复": "页「应用场景 / USE CASES」",
        "数字卡不是数字": "自动生成",
        "数据缺失": "[数据缺失]",
        "用词": "赋能",
        "关键标记过多": "页「项目节点 / MILESTONE」",
    }
    for rule, needle in expect.items():
        lines = [line for line in out.splitlines() if rule in line]
        check(f"报出「{rule}」并指明位置", any(needle in line for line in lines), lines or out)


def test_hand_drawn_pptx():
    work = package()
    good = review(work, GOOD)
    check("生成脚本做的 pptx：不报手工绘制", "不是生成脚本" not in good.stdout, good.stdout)
    hand = T2 / "02-改一页.pptx"
    r = review(work, GOOD, pptx=hand)
    check("Copilot 自己画的 pptx（t2 实测第 2 份）：报出不是生成脚本做的",
          "不是生成脚本" in r.stdout, r.stdout)


if __name__ == "__main__":
    test_good_deck_passes()
    test_bad_deck_flags()
    test_hand_drawn_pptx()
    test_no_private_paths()
    finish()
