"""审核脚本 review_deck.py：项目汇报模式检查、配图检查、全版式正样本。

运行：python3 skills/milwaukee-ppt/tests/test_review_project.py
做法：生成器按文稿出 pptx，再跑审核脚本，只看它的输出与退出码（md + pptx 进、问题清单出）。
文稿内容全部虚构。
"""
import re

from deckcheck import (check, finish, generate, layouts_in, lines_with, registered_layouts,
                       review, reviewed)

IMAGES = {"img/site.png": (1600, 900), "img/before.png": (1600, 900),
          "img/after.png": (1600, 900), "img/screen.png": (1600, 900)}

# 全版式正样本（项目模式）：§1 八节按顺序、各节 PDCA 对应、团队页不带 PDCA；
# 目录页、隔断页是导航页，不计页数、不要求 PDCA。注册表每个版式至少一页。
PROJECT_FULL = """\
---
title: 仓库叉车充电排班优化 项目汇报
author: 虚构改进小组
date: 02 Sep 2026
report: project
---

# 目录 / AGENDA
## 分八部分汇报，成果集中在第六部分
Layout: agenda
01 | 项目背景 | BACKGROUND
02 | 项目目标 | TARGET
03 | 项目范围 | SCOPE
04 | 项目应用场景 | USE CASES
05 | 项目节点 | MILESTONE
06 | 项目行动与成果 | OUTCOMES
07 | 项目团队 | TEAM
08 | 持续优化与经验沉淀 | LESSONS

# 项目背景 / BACKGROUND
## 早班交接时充电位排队超过 20 分钟
PDCA: P
![](img/site.png)
早班交接时 6 台叉车同时排队充电

# 项目目标 / TARGET
## 高峰排队降到 3 台以内
Layout: stats
PDCA: P
- 高峰排队 | 3 台以内 | 改前 6 台
- !平均等待 | 10 分钟以内 | 改前约 22 分钟
口径：B 仓早班交接时段
两项目标都按系统记录核对

# 项目范围 / SCOPE
## 先做 B 仓 18 台叉车，不含 A 仓
Layout: table
PDCA: P
| 项目 | 包含 | 不包含 |
| --- | --- | --- |
| 仓库 | B 仓 | A 仓 |
| 车辆 | 18 台电动叉车 | 内燃叉车 |
范围按 B 仓现有车辆划定

# 项目应用场景 / USE CASES
## 司机在手持终端上查看充电时段
Layout: image-text
PDCA: P
![](img/screen.png)
- 显示下一个充电时段和充电位编号
- 提前 5 分钟提醒
终端在 B 仓全部叉车上安装

# 项目节点 / MILESTONE
## 6 月立项，8 月完成试运行
Layout: timeline
PDCA: D
- Jun | 立项 | 确定试点仓库 | 完成
- !Jul | 上线 | 排班功能上线 | 完成
- Aug | 试运行 | B 仓试运行 | 完成
试运行 8 月底结束

# 项目行动与成果 / OUTCOMES
## 排班改为系统分配，高峰排队降到 2 台
Layout: section
06 | 项目行动与成果 | OUTCOMES

# 排班流程 / PROCESS
## 排班改为系统分配，三步完成
Layout: process
PDCA: D
1. 登记电量 | 交班时登记剩余电量
2. 系统排队 | 按电量自动排序
3. 按时充电 | 到点去指定充电位
三步流程在 B 仓运行 3 周

# 排队对比 / BEFORE-AFTER
## 排队改为系统分配，高峰不再扎堆
Layout: before-after
PDCA: D
同一仓库、同一批叉车，改前改后各统计 3 周

### Before: 凭经验排队
![](img/before.png)
Caption: 司机凭经验到充电区排队

### After: 系统分配
![](img/after.png)
Caption: 系统按剩余电量分配充电时段

高峰排队从 6 台降到 2 台

# 试运行结论 / FINDINGS
## 试运行 3 周，两项指标都达到目标
Layout: stats-side
PDCA: C
- 高峰排队 | 2 台 | 目标 3 台以内
- !平均等待 | 约 6 分钟 | 目标 10 分钟以内
### 结论
> 系统分配消除了交接时段扎堆
> 等待时间下降来自错峰充电
口径：B 仓 8 月 3 周系统记录
两项指标都达到目标

# 项目团队 / TEAM
## 三人小组，现场推进和数据复盘分开负责
Layout: team
- 王一 | 项目负责人 | 排班规则制定、试运行推进
- 李二 | 现场协调 | 每日巡检、问题登记
- 张三 | 数据复盘 | 系统数据导出、周报汇总
分工按现场和数据两条线，周会对齐一次

# 持续优化与经验沉淀 / LESSONS
## 上线后迭代三版，提醒改为提前 5 分钟
Layout: timeline-phase
PDCA: A
- Aug | 第一版 | 提前 10 分钟提醒 | 完成
- Sep | 第二版 | 改为提前 5 分钟 | 完成
- Oct | 第三版 | 按电量分档排队 | 完成
三次迭代都已在 B 仓上线
"""


def plain_full():
    """非项目模式的全版式正样本：同一批页，去掉 report: project 和各页 PDCA。"""
    md = PROJECT_FULL.replace("report: project\n", "", 1)
    return re.sub(r"^PDCA: .*\n", "", md, flags=re.M)


def test_full_samples_cover_every_layout():
    """新版式登记进注册表后，必须在两份全版式正样本里各补一页，否则这里失败。"""
    want = set(registered_layouts())
    for label, md in (("项目模式", PROJECT_FULL), ("非项目模式", plain_full())):
        missing = sorted(want - layouts_in(md))
        check(f"全版式正样本（{label}）覆盖注册表全部版式", not missing,
              f"缺 {' / '.join(missing)}：在 tests/test_review_project.py 的 PROJECT_FULL 补一页")


def test_full_samples_pass():
    for label, md in (("项目模式", PROJECT_FULL), ("非项目模式", plain_full())):
        r = reviewed(md, IMAGES)
        check(f"全版式正样本（{label}）：只打印 REVIEW OK", r.stdout.strip() == "REVIEW OK",
              r.stdout + r.stderr)


def split(md):
    """文稿 → (frontmatter 部分, {英文名: 页文字})，页文字以「# 」开头、按原顺序。"""
    head, *pages = re.split(r"^(?=# )", md, flags=re.M)
    return head, {p.split("\n", 1)[0].split("/")[-1].strip(): p for p in pages}


def join(head, pages, order=None):
    return head + "".join(pages[k] for k in (order or pages))


def test_chapter_order():
    head, pages = split(PROJECT_FULL)
    order = list(pages)
    i, j = order.index("BACKGROUND"), order.index("TARGET")
    order[i], order[j] = order[j], order[i]
    out = reviewed(join(head, pages, order), IMAGES).stdout
    lines = lines_with(out, "章节顺序")
    check("项目模式章节乱序：报出「章节顺序」，指明排错的页",
          any("BACKGROUND" in line and " → " in line for line in lines), out)


def edited(key, old, new):
    """PROJECT_FULL 里英文名为 key 的那页把 old 换成 new。"""
    head, pages = split(PROJECT_FULL)
    assert old in pages[key], (key, old)
    pages[key] = pages[key].replace(old, new, 1)
    return join(head, pages)


def test_missing_pdca():
    out = reviewed(edited("TARGET", "PDCA: P\n", ""), IMAGES).stdout
    check("项目模式缺 PDCA：报出「缺 PDCA」，指明页",
          any("TARGET" in line for line in lines_with(out, "缺 PDCA")), out)
    check("项目模式缺 PDCA：团队页、目录页、隔断页不报缺 PDCA",
          not any(k in line for line in lines_with(out, "缺 PDCA")
                  for k in ("TEAM", "AGENDA", "OUTCOMES")), out)


def test_team_page_with_pdca():
    out = reviewed(edited("TEAM", "Layout: team\n", "Layout: team\nPDCA: D\n"), IMAGES).stdout
    check("项目模式团队页带 PDCA：报出「团队页带 PDCA」",
          any("TEAM" in line for line in lines_with(out, "团队页带 PDCA")), out)


def test_pdca_mismatch():
    out = reviewed(edited("BACKGROUND", "PDCA: P", "PDCA: D"), IMAGES).stdout
    check("项目背景标 D：报出「PDCA 和章节不符」，说明该节应标 P",
          any("BACKGROUND" in line and "P" in line
              for line in lines_with(out, "PDCA 和章节不符")), out)
    out = reviewed(edited("BEFORE-AFTER", "PDCA: D", "PDCA: D/C"), IMAGES).stdout
    check("第 06 节一页标 D/C：报出「PDCA 和章节不符」（一页只放一个）",
          any("BEFORE-AFTER" in line for line in lines_with(out, "PDCA 和章节不符")), out)
    out = reviewed(edited("FINDINGS", "PDCA: C", "PDCA: D"), IMAGES).stdout
    check("第 06 节的子页标 D 或 C 都不报",
          not lines_with(out, "PDCA 和章节不符"), out)


def test_missing_chapter():
    head, pages = split(PROJECT_FULL)
    del pages["SCOPE"]
    out = reviewed(join(head, pages), IMAGES).stdout
    check("项目模式少一节：报出「缺章节」并点名 SCOPE",
          any("SCOPE" in line for line in lines_with(out, "缺章节")), out)


TARGET_AS_PROCESS = ("Layout: stats\nPDCA: P\n- 高峰排队 | 3 台以内 | 改前 6 台\n"
                     "- !平均等待 | 10 分钟以内 | 改前约 22 分钟\n口径：B 仓早班交接时段\n",
                     "Layout: process\nPDCA: P\n1. 定目标 | 高峰排队 3 台以内\n"
                     "2. 定口径 | 早班交接时段\n3. 定节奏 | 每周复核一次\n")


def test_misfit_only_in_project_mode():
    out = reviewed(edited("TARGET", *TARGET_AS_PROCESS), IMAGES).stdout
    check("项目模式目标页用 process：报出「章节和版式不配」",
          any("TARGET" in line for line in lines_with(out, "章节和版式不配")), out)


def test_plain_mode_skips_project_rules():
    head, pages = split(plain_full())
    pages["TARGET"] = pages["TARGET"].replace(*(t.replace("PDCA: P\n", "")
                                                for t in TARGET_AS_PROCESS))
    del pages["SCOPE"]
    order = list(pages)
    i, j = order.index("BACKGROUND"), order.index("TARGET")
    order[i], order[j] = order[j], order[i]
    out = reviewed(join(head, pages, order), IMAGES).stdout
    for rule in ("章节顺序", "缺章节", "缺 PDCA", "团队页带 PDCA", "PDCA 和章节不符",
                 "章节和版式不配"):
        check(f"非项目模式（乱序、缺节、目标页用 process）：不报「{rule}」",
              not lines_with(out, rule), out)


def test_evidence_without_image():
    for label, md in (("项目模式", PROJECT_FULL), ("非项目模式", plain_full())):
        head, pages = split(md)
        pages["BACKGROUND"] = pages["BACKGROUND"].replace("![](img/site.png)\n", "")
        out = reviewed(join(head, pages), IMAGES).stdout
        check(f"{label}证据页没放图：报出「缺配图」，指明页",
              any("BACKGROUND" in line and " → " in line for line in lines_with(out, "缺配图")),
              out)


def test_image_text_without_image():
    r = generate(edited("USE CASES", "![](img/screen.png)\n", ""), images=IMAGES)
    rr = review(r.workdir / "deck.md")
    check("左图右文没放图：审核报错退出（和生成器同一条解析规则），错误含页标题",
          rr.returncode == 1 and "USE CASES" in rr.stderr, (rr.returncode, rr.stderr))


def test_image_file_missing():
    r = generate(PROJECT_FULL, images=IMAGES)
    (r.workdir / "img" / "after.png").unlink()
    out = review(r.workdir / "deck.md").stdout
    check("改前改后一侧的图片文件不在了（只审文稿）：报出「图片不存在」，带页和路径",
          any("BEFORE-AFTER" in line and "img/after.png" in line
              for line in lines_with(out, "图片不存在")), out)


def test_section_not_in_agenda():
    out = reviewed(edited("OUTCOMES", "06 | 项目行动与成果 | OUTCOMES", "06 | 行动与结果 | OUTCOMES"),
                   IMAGES).stdout
    check("隔断页章节名不在目录里：报出「目录和隔断页不一致」，指明隔断页",
          any("OUTCOMES" in line and "行动与结果" in line
              for line in lines_with(out, "目录和隔断页不一致")), out)


def test_agenda_order_in_project_mode():
    swapped = PROJECT_FULL.replace("01 | 项目背景 | BACKGROUND\n02 | 项目目标 | TARGET",
                                   "01 | 项目目标 | TARGET\n02 | 项目背景 | BACKGROUND")
    out = reviewed(swapped, IMAGES).stdout
    check("项目模式目录页顺序不对：报出「章节顺序」，指明目录页",
          any("AGENDA" in line for line in lines_with(out, "章节顺序")), out)
    out = reviewed(plain_full().replace("01 | 项目背景 | BACKGROUND\n02 | 项目目标 | TARGET",
                                        "01 | 项目目标 | TARGET\n02 | 项目背景 | BACKGROUND"),
                   IMAGES).stdout
    check("非项目模式目录页顺序随意：不报「章节顺序」", not lines_with(out, "章节顺序"), out)


def test_consecutive_sections():
    extra = ("# 项目节点 / MILESTONE\n## 6 月立项，8 月完成试运行\nLayout: section\n"
             "05 | 项目节点 | MILESTONE\n\n")
    md = plain_full().replace("# 项目行动与成果 / OUTCOMES", extra + "# 项目行动与成果 / OUTCOMES")
    out = reviewed(md, IMAGES).stdout
    check("连着两张隔断页：不报「相邻两页版式相同」", not lines_with(out, "相邻两页版式相同"), out)


def test_short_conclusion_subtitle():
    out = reviewed(edited("FINDINGS", "试运行 3 周，两项指标都达到目标", "两项指标均达标"),
                   IMAGES).stdout
    check("副标题是短结论（7 字）：不报「目录式副标题」", not lines_with(out, "目录式副标题"), out)
    out = reviewed(edited("TARGET", "高峰排队降到 3 台以内", "项目目标介绍"), IMAGES).stdout
    check("副标题是主标题加两三个字（项目目标介绍）：仍报「目录式副标题」",
          any("TARGET" in line for line in lines_with(out, "目录式副标题")), out)


if __name__ == "__main__":
    test_section_not_in_agenda()
    test_agenda_order_in_project_mode()
    test_consecutive_sections()
    test_short_conclusion_subtitle()
    test_evidence_without_image()
    test_image_text_without_image()
    test_image_file_missing()
    test_misfit_only_in_project_mode()
    test_plain_mode_skips_project_rules()
    test_chapter_order()
    test_missing_pdca()
    test_team_page_with_pdca()
    test_pdca_mismatch()
    test_missing_chapter()
    test_full_samples_cover_every_layout()
    test_full_samples_pass()
    finish()
