"""方向 C 骨架（spec #47 / #48）：通用模式和项目汇报模式下，结论画成标题下的 lead，
`Next:` 画在页底一行；月报模式仍是底部红条（月报回归见 test_generate.py 的 MONTHLY_SHA）。

只走“md 进、pptx 出”这一个切入点。运行：python3 skills/milwaukee-ppt/tests/test_lead.py
"""
from deckcheck import (BRAND_RED, EMU, INK, bottom, caption_bar, check, fill_color, finish,
                       generate, one, paragraphs, run_styles, warnings)

GENERAL = """
---
title: Mock Deck
date: 14 Oct 2026
---
"""

EVIDENCE = GENERAL + """
# Mock Evidence Page
## Pilot covers two lines
![](img/a.png)
Two pilot lines switched to the new checklist in 3 weeks.
Next: Roll out to the remaining 4 lines by Nov.

# Mock No Next Page
## Pilot covers two lines again
![](img/a.png)
Only a conclusion here.
"""
IMG = {"img/a.png": (1600, 900)}


def test_lead_and_next():
    r = generate(EVIDENCE, images=IMG)
    check("C 模式：生成退出码 0", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    s, s2 = r.slides[1], r.slides[2]
    lead, accent = one(s, "Lead"), one(s, "Lead Accent")
    check("C 模式：有 Lead 和 Lead Accent", lead is not None and accent is not None,
          [sh.name for sh in s.shapes])
    check("C 模式：没有底部红条", caption_bar(s) is None and caption_bar(s2) is None)
    if lead is None or accent is None:
        return
    check("Lead 文字 = 结论行", paragraphs(lead) ==
          ["Two pilot lines switched to the new checklist in 3 weeks."], paragraphs(lead))
    check("Lead 是黑色粗体 22pt", run_styles(lead) == {(22.0, True, INK)}, run_styles(lead))
    check("Lead Accent 是品牌红竖线，在 Lead 左边",
          fill_color(accent) == BRAND_RED and accent.width < accent.height
          and accent.left + accent.width <= lead.left, (fill_color(accent), accent.left))
    check("Lead 在标题 banner 下、1.30\" 起", lead.top == int(1.30 * EMU), lead.top / EMU)
    rule, line = one(s, "Next Rule"), one(s, "Next Line")
    check("有 Next 的页有 Next Rule / Next Line", rule is not None and line is not None)
    if rule is not None and line is not None:
        check("Next Line 文字 = Next 前缀 + 内容",
              paragraphs(line) == ["Next: Roll out to the remaining 4 lines by Nov."],
              paragraphs(line))
        check("Next Line 黑色粗体", {(b, c) for _, b, c in run_styles(line)} == {(True, INK)},
              run_styles(line))
        check("Next Rule 在 Next Line 上方", bottom(rule) <= line.top, (rule.top, line.top))
    check("没写 Next 的页没有 Next Rule / Next Line",
          one(s2, "Next Rule") is None and one(s2, "Next Line") is None)
    check("C 模式：生成没有警告", not warnings(r.stderr), r.stderr)


# 每种内容版式一页，都写结论和 Next（导航版式 section / agenda 不画 lead，单独查）
ALL_LAYOUTS = GENERAL + """
# 证据 / EVIDENCE
## 两条线试点完成
Tag: Aug
![](img/a.png)
![](img/tall.png)
两条试点线 3 周内切换到新点检表
Next: 11 月前推广到其余 4 条线

# 流程 / PROCESS
## 排班改为系统分配
Layout: process
1. 登记 | 交班时登记剩余电量
2. 排队 | 系统按电量排序
3. 充电 | 到点去指定充电位
三步完成排班，司机不再凭经验排队
Next: 9 月推广到 A 仓

# 对比 / BEFORE-AFTER
## 排队改为系统分配
Layout: before-after

### Before
司机凭经验排队

### After
系统按电量分配时段

高峰排队从 6 台降到 2 台
Next: 9 月推广到 A 仓

# 数据 / STATS
## 高峰排队降到 2 台
Layout: stats
Tag: Aug
- 高峰排队 | 2 台 | 改前 6 台
  - 早班交接时段统计
- !平均等待 | 约 6 分钟 | 改前约 22 分钟
口径：B 仓 8 月 3 周系统记录
平均等待从约 22 分钟降到约 6 分钟
Next: 9 月复核 A 仓数据

# 结论 / FINDINGS
## 可以推广
Layout: stats-side
- 高峰排队 | 2 台 | 改前 6 台
- !平均等待 | 约 6 分钟 | 改前约 22 分钟
### 结论
> 系统分配消除了交接时段扎堆
口径：B 仓 8 月 3 周系统记录
具备推广到 A 仓的条件
Next: 9 月推广到 A 仓

# 节点 / MILESTONE
## 8 月完成试运行
Layout: timeline
- Jun | 立项 | 确定试点仓库 | 完成
- !Jul | 上线 | 排班功能上线 | 完成
- Aug | 试运行 | B 仓试运行 | 进行中
- Sep | 推广 | 推广到 A 仓 | 未完成
试运行 8 月底结束
Next: 9 月推广到 A 仓

# 旧节点 / HISTORY
## 立项到上线 6 周
Layout: timeline
- Jun | 立项 | 确定试点仓库
- !Jul | 上线 | 排班功能上线
- Aug | 试运行 |
立项到上线用了 6 周
Next: 9 月推广到 A 仓

# 阶段 / PHASES
## 正在试运行
Layout: timeline-phase
- Jun | 立项 | 确定范围 | 完成
- !Aug | 试运行 | B 仓 | 进行中
- Sep | 推广 | A 仓 | 未完成
9 月起推广到 A 仓
Next: 10 月复盘

# 终端 / TERMINAL
## 终端显示充电时段
Layout: image-text
![](img/tall.png)
- 显示下一个充电时段
- 提前 5 分钟提醒
终端已装到 B 仓全部叉车
Next: 9 月装到 A 仓

# 团队 / TEAM
## 两条线分工
Layout: team
- 周航 | 现场推进 | 试点车间贴码、培训和巡检
- 陈雨 | 数据复盘 | 周报和数据看板
分工按现场和数据两条线，周会对齐
Next: 9 月加入 A 仓班组长

# 等待 / WAITING
## B 仓等待最长
Layout: table
Tag: Aug
| 仓库 | 叉车数 | 平均等待 |
| --- | --- | --- |
| A 仓 | 12 | 18 分钟 |
| !B 仓 | 18 | 35 分钟 |
B 仓高峰等待 35 分钟，是 A 仓的两倍
Next: 9 月先调 B 仓
"""
ALL_IMAGES = {"img/a.png": (1600, 900), "img/tall.png": (900, 1600)}
CHROME = {"Lead", "Lead Accent", "Next Rule", "Next Line", "Month Tag"}
BODY_GAP_IN, NEXT_GAP_IN = 0.19, 0.10     # lead 下沿 → 正文区；正文区 → Next 细线
TOL = int(0.01 * EMU)


def body_shapes(slide):
    return [sh for sh in slide.shapes
            if sh.name not in CHROME and not (sh.is_placeholder
                                              and sh.placeholder_format.idx in (0, 10))]


def test_content_in_body_area():
    r = generate(ALL_LAYOUTS, images=ALL_IMAGES)
    check("全版式文稿：生成退出码 0", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    for s in r.slides[1:]:
        title = s.placeholders[0].text
        lead, rule = one(s, "Lead"), one(s, "Next Rule")
        if lead is None or rule is None:
            check(f"{title}：有 Lead 和 Next Rule", False, [sh.name for sh in s.shapes])
            continue
        top = bottom(lead) + int(BODY_GAP_IN * EMU)
        low = rule.top - int(NEXT_GAP_IN * EMU)
        out = [sh.name for sh in body_shapes(s)
               if sh.top < top - TOL or bottom(sh) > low + TOL
               or sh.left < int(0.56 * EMU) - TOL or sh.left + sh.width > int(12.77 * EMU) + TOL]
        check(f"{title}：正文形状都在 lead 下、Next 细线上的正文区里", not out, out)
        check(f"{title}：没有底部红条", caption_bar(s) is None)


def test_lead_avoids_tag_and_pdca():
    md = """
---
title: Mock Deck
report: project
---

# 证据 / EVIDENCE
PDCA: D/C
Tag: Aug
![](img/a.png)
写了 Tag 和 PDCA 的页，lead 要让开右上角的月份标识
"""
    r = generate(md, images=ALL_IMAGES)
    check("项目模式：生成退出码 0", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    s = r.slides[1]
    lead, tag = one(s, "Lead"), one(s, "Month Tag")
    icons = [sh for sh in s.shapes if sh.name.startswith("PDCA Icon")]
    check("项目模式：有 Lead、Month Tag 和两个 PDCA 图标",
          lead is not None and tag is not None and len(icons) == 2)
    if lead is None or tag is None:
        return
    check("lead 右端让到月份标识框左侧", lead.left + lead.width <= tag.left,
          (lead.left + lead.width, tag.left))
    check("PDCA 图标在 lead 上方（位置不变：1.02–1.30\")",
          all(ic.top == int(1.02 * EMU) and bottom(ic) <= lead.top + TOL for ic in icons),
          [(ic.top, bottom(ic)) for ic in icons])


TWO_LEADS = GENERAL + """
# 对比 / BEFORE-AFTER
## 排队改为系统分配
Layout: before-after
同一仓库、同一批叉车，改前改后各统计 3 周

### Before
司机凭经验排队

### After
系统按电量分配时段

高峰排队从 6 台降到 2 台
"""


def test_before_after_two_leads():
    r = generate(TWO_LEADS)
    check("对比页两个 lead：照样生成", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    s = r.slides[1]
    warned = [w for w in warnings(r.stderr) if "对比 / BEFORE-AFTER" in w and "###" in w]
    check("对比页两个 lead：生成器报警告（带页标题）", len(warned) == 1, r.stderr)
    leads = [paragraphs(sh) for sh in s.shapes if sh.name == "Lead"]
    check("对比页两个 lead：只画一个 Lead，文字是结论行", leads == [["高峰排队从 6 台降到 2 台"]],
          leads)
    check("对比页两个 lead：第一个 ### 前的文字不画",
          not any("改前改后各统计" in sh.text_frame.text for sh in s.shapes if sh.has_text_frame))
    one_lead = generate(TWO_LEADS.replace("同一仓库、同一批叉车，改前改后各统计 3 周\n", ""))
    check("对比页只写结论：没有警告", one_lead.rc == 0 and not warnings(one_lead.stderr),
          one_lead.stderr)


NAV = """
# 试运行 / PILOT
## 分三部分汇报
Layout: section
Tag: Aug
3.1 | 试运行 | PILOT RUN

# 目录 / AGENDA
## 分三部分汇报
Layout: agenda
1 | 背景 | BACKGROUND
2 | 试运行 | PILOT RUN
3 | 推广 | ROLLOUT
"""
MONTHLY = """
---
month: 2026-10
author: Mock.Author
---
"""


def test_nav_pages_unchanged():
    c, m = generate(GENERAL + NAV), generate(MONTHLY + NAV)
    check("导航页：两种模式都生成", c.rc == 0 and m.rc == 0, c.stderr + m.stderr)
    if c.rc or m.rc:
        return
    for n in (1, 2):
        geo = [[(sh.name, sh.left, sh.top, sh.width, sh.height) for sh in deck.slides[n].shapes]
               for deck in (c, m)]
        check(f"导航页（第 {n} 页）：C 模式不画 lead，形状和月报模式一样", geo[0] == geo[1], geo)


if __name__ == "__main__":
    test_lead_and_next()
    test_content_in_body_area()
    test_lead_avoids_tag_and_pdca()
    test_before_after_two_leads()
    test_nav_pages_unchanged()
    finish()
