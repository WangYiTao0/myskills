"""审核脚本 review_deck.py 的几何检查：出界 / 压 banner / 压页脚 / 文字溢出 / 重叠 / 错位。

运行：python3 skills/milwaukee-ppt/tests/test_review_geometry.py
做法：生成器按文稿出 pptx（正样本），再用 python-pptx 把它改坏（负样本），
只看审核脚本的输出。文稿内容全部虚构。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from pptx.util import Emu, Inches

from deckcheck import GENERATOR, SKILL, check, finish, generate, open_pptx, review

DEMO = SKILL / "examples" / "demo" / "deck.md"
GEOMETRY_RULES = ("出界", "压 banner", "压页脚", "文字溢出", "重叠", "错位")
PX = 9525   # 96 dpi 下一个像素（EMU）

# 正样本：各版式的常见写法（写了 / 没写 Tag、状态 / 旧写法、图 / 短文、条目数上下限）
VARIANTS = """\
---
title: 仓库叉车充电排班优化 项目汇报
date: 02 Sep 2026
author: 虚构改进小组
closing: Thank You
---

# 现场证据 / EVIDENCE
## 充电位高峰时段排队超过 20 分钟
Tag: Aug
![](img/a.png)
![](img/tall.png)
![](img/b.png)
早班交接时 6 台叉车同时排队充电

# 现场照片 / PHOTO
## 充电区只有一处插座可用
![](img/a.png)

# 排班流程 / PROCESS
## 排班改为系统分配，五步完成
Layout: process
Tag: Aug
1. 登记电量 | 交班时登记剩余电量
2. 系统排队 | 按电量自动排序
3. 推送时段 | 推送充电时段到手持终端
4. 按时充电 | 到点去指定充电位
5. 复核 | 班长每周复核一次
五步流程在 B 仓试运行 3 周

# 新旧流程 / FLOW
## 交班登记一步完成
Layout: process
1. 登记 | 交班登记电量
2. 排队 | 系统排队
3. 充电 | 按时充电

# 排队对比 / BEFORE-AFTER
## 排队改为系统分配，高峰不再扎堆
Layout: before-after
Tag: Aug
同一仓库、同一批叉车，改前改后各统计 3 周

### Before
司机凭经验到充电区排队，高峰时段 6 台车同时等待

### After
系统按剩余电量分配充电时段，推送到手持终端

高峰排队从 6 台降到 2 台

# 关键数据 / KEY RESULTS
## 试运行 3 周，高峰排队降到 2 台
Layout: stats
Tag: Aug
- 高峰排队 | 2 台 | 改前 6 台
  - 早班交接时段统计
- !平均等待 | 约 6 分钟 | 改前约 22 分钟
  - 以系统记录的到位时间计
  - 不含设备故障停机
- 充电位利用率 | 85% | 改前 60%
- 叉车数 | 18 台 | B 仓全部叉车
口径：B 仓 8 月 3 周系统记录
平均等待从约 22 分钟降到约 6 分钟

# 数据概览 / OVERVIEW
## 两项指标都达到目标
Layout: stats
- 高峰排队 | 2 台 | 目标 3 台以内
- !平均等待 | 6 分钟 | 目标 10 分钟以内
两项指标都达到目标

# 试运行结论 / FINDINGS
## 排队和等待都下降，可以推广
Layout: stats-side
Tag: Aug
- 高峰排队 | 2 台 | 改前 6 台
- !平均等待 | 约 6 分钟 | 改前约 22 分钟
### 结论
> 系统分配消除了交接时段扎堆
> 等待时间下降来自错峰充电
口径：B 仓 8 月 3 周系统记录
具备推广到 A 仓的条件

# 项目节点 / MILESTONE
## 7 月立项，8 月完成试运行
Layout: timeline
Tag: Aug
- Jun | 立项 | 确定试点仓库 | 完成
- !Jul | 上线 | 排班功能上线 | 完成
- Aug | 试运行 | B 仓试运行 | 进行中
- Sep | 推广 | 推广到 A 仓 | 未完成
试运行 8 月底结束

# 节点回顾 / HISTORY
## 立项到上线用了 6 周
Layout: timeline
- Jun | 立项 | 确定试点仓库
- !Jul | 上线 | 排班功能上线
- Aug | 试运行 |
立项到上线 6 周

# 推广阶段 / PHASES
## 正在试运行，9 月推广
Layout: timeline-phase
Tag: Aug
- Jun | 立项 | 确定范围 | 完成
- Jul | 开发 | 排班功能 | 完成
- !Aug | 试运行 | B 仓 | 进行中
- Sep | 推广 | A 仓 | 未完成
- Oct | 复盘 | 汇总数据 | 未完成
- !Nov | 验收 | 正式验收 | 未完成
9 月起推广到 A 仓

# 终端界面 / TERMINAL
## 手持终端直接显示充电时段
Layout: image-text
Tag: Aug
![](img/tall.png)
- 显示下一个充电时段和充电位编号
- 提前 5 分钟提醒
终端已在 B 仓全部叉车上安装
"""
IMAGES = {"img/a.png": (1600, 900), "img/b.png": (1200, 900), "img/tall.png": (900, 1600)}


def geometry_lines(out):
    return [line for line in out.splitlines()
            if any(line.startswith(f"[{rule}]") for rule in GEOMETRY_RULES)]


def variants():
    """→ (文稿路径, pptx 路径)。"""
    r = generate(VARIANTS, images=IMAGES)
    if r.rc != 0:
        raise RuntimeError(r.stderr)
    return r.workdir / "deck.md", r.path


def demo():
    out = Path(tempfile.mkdtemp(prefix="mppt-geom-")) / "demo.pptx"
    g = subprocess.run([sys.executable, str(GENERATOR), str(DEMO), "-o", str(out)],
                       capture_output=True, text=True)
    if g.returncode != 0:
        raise RuntimeError(g.stderr)
    return DEMO, out


def shape(prs, page, name):
    """第 page 页（从 1 起，含封面）名为 name 的形状。"""
    found = [sh for sh in prs.slides[page - 1].shapes if sh.name == name]
    assert len(found) == 1, (page, name, [sh.name for sh in prs.slides[page - 1].shapes])
    return found[0]


def broken(pptx, change):
    """生成器输出另存一份，用 change(prs) 改坏 → 新路径。"""
    prs = open_pptx(pptx)
    change(prs)
    out = Path(tempfile.mkdtemp(prefix="mppt-geom-bad-")) / "bad.pptx"
    prs.save(str(out))
    return out


def reported(md, pptx, rule, page, name):
    """审核输出里「[rule]」开头、带第 page 页和形状名的行。"""
    r = review(md, pptx)
    return [line for line in r.stdout.splitlines()
            if line.startswith(f"[{rule}]") and f"第 {page} 页" in line
            and f"「{name}」" in line and " → " in line], r.stdout


def test_normal_decks_have_no_geometry_issues():
    for label, (md, pptx) in (("示例文稿", demo()), ("各版式写法", variants())):
        r = review(md, pptx)
        check(f"{label}：没有几何问题", not geometry_lines(r.stdout), geometry_lines(r.stdout))


def expect(label, md, pptx, change, rule, page, name):
    lines, out = reported(md, broken(pptx, change), rule, page, name)
    check(f"{label}：报出「{rule}」，带第 {page} 页和形状「{name}」", bool(lines), out)


def test_out_of_page():
    md, pptx = demo()

    def move_right(prs):
        sh = shape(prs, 3, "Process Card 4")
        sh.left = prs.slide_width - sh.width // 2

    def move_up(prs):
        shape(prs, 5, "Stat Label 2").top = Inches(0.5)

    def move_down(prs):
        sh = shape(prs, 7, "Milestone Text 3")
        sh.top = Inches(7.4) - sh.height

    expect("形状挪出页面右边", md, pptx, move_right, "出界", 3, "Process Card 4")
    expect("形状挪进 banner", md, pptx, move_up, "压 banner", 5, "Stat Label 2")
    expect("形状挪进页脚", md, pptx, move_down, "压页脚", 7, "Milestone Text 3")


def test_overlap():
    md, pptx = demo()

    def push_left(prs):
        card = shape(prs, 3, "Process Card 2")
        card.left -= Inches(0.8)

    lines, out = reported(md, broken(pptx, push_left), "重叠", 3, "Process Card 2")
    check("两个形状互压：报出「重叠」，带第 3 页和形状名",
          any("Process Card 1" in line for line in lines), out)


def test_misaligned():
    md, pptx = demo()

    def nudge_down(prs):
        shape(prs, 3, "Process Card 3").top += 3 * PX

    def nudge_left(prs):
        shape(prs, 6, "Side Card 2").left -= 2 * PX

    expect("同一行的卡片下移 3 像素", md, pptx, nudge_down, "错位", 3, "Process Card 3")
    expect("同一列的卡片左移 2 像素", md, pptx, nudge_left, "错位", 6, "Side Card 2")


def stuff(sh, times=8):
    """把形状每一段的文字重复 times 遍，字号、样式不变。"""
    for para in sh.text_frame.paragraphs:
        for run in para.runs:
            run.text = run.text * times


def test_text_overflow():
    md, pptx = demo()
    expect("数据解读塞满", md, pptx, lambda prs: stuff(shape(prs, 5, "Stat Points 2")),
           "文字溢出", 5, "Stat Points 2")
    expect("流程卡片说明塞满", md, pptx, lambda prs: stuff(shape(prs, 3, "Process Card 1")),
           "文字溢出", 3, "Process Card 1")
    expect("红条塞满", md, pptx, lambda prs: stuff(shape(prs, 2, "Caption Bar")),
           "文字溢出", 2, "Caption Bar")


if __name__ == "__main__":
    test_normal_decks_have_no_geometry_issues()
    test_out_of_page()
    test_overlap()
    test_misaligned()
    test_text_overflow()
    finish()
