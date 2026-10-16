"""milwaukee-ppt 生成器整份文稿级测试：封面 / 收尾 / 月报回归 / 通用模式 / Layout 分派 / 报错。

各版式自己的内容检查放在 test_<版式>.py。只走“md 进、pptx 出”这一个切入点。
纯 Python 脚本，不用 pytest：python3 skills/milwaukee-ppt/tests/test_generate.py
测试图片用 Pillow 现生成纯色图；文稿内容全部虚构。
"""
import hashlib
import shutil
import tempfile
from pathlib import Path

from deckcheck import (CAPTION_BOTTOM, CAPTION_MIN_CY, EMU, SKILL,
                       TEMPLATE, caption_bar, caption_style_problems,
                       check, finish, generate, make_image, open_pptx,
                       out_of_bounds, paragraphs, slide_parts, slide_xmls, tag_texts, texts)


def run(md_text, workdir, out_name="out.pptx", use_o=True):
    r = generate(md_text, workdir, out_name=out_name, use_o=use_o)
    return r.rc, r.stdout, r.stderr, r.prs

# 虚构的旧格式月报（与原月报 md 写法一致，不改一字）
MONTHLY_MD = """
---
month: 2026-03
author: Alex.Sample
date: 9 Apr
---

<!-- 注释不会进入 PPT -->

# Sample Dashboard Program
## Build a Reusable Dashboard Model
![](img/wide.png)
Standard dashboard workflow drafted and shared with two pilot teams.
Next: Roll the workflow out to the remaining pilot teams.

# Mock Tooling Review
## First Draft Review
![](img/wide.png)
![](img/tall.png)
Tag: Mar
First-draft review finished with sample stakeholders.
下一步：整理反馈并进入正式开发。

# Demo Knowledge Page
![](img/wide.png)
![](img/tall.png)
![](img/square.png)
Tag: Dec 2025
Demo pages live; usage tracking enabled.
"""


# master（e282570，spec #20 之前）生成的月报各页 slide XML 的 sha256：月报模式输出逐字节不变
MONTHLY_SHA = {
    "ppt/slides/slide1.xml": "43ca9a136863becb59a2fa62626f02d164562d73d271987f5a2cbd8cba1cce18",
    "ppt/slides/slide2.xml": "8297b0099acca23a38f66b67321a6531ea0074a74f7c28a694404363a123852d",
    "ppt/slides/slide3.xml": "db33c0fbbac2b9e2cb367187f816177008c19fc4b2a65e35867621ec84dfcc2e",
    "ppt/slides/slide4.xml": "998adce441bae648cf59df78099275c22b821f8ad7fd678a87ea224765f63ccd",
    "ppt/slides/slide5.xml": "c89c199746d67277afa243eb1dacce8f26093c0b3b40e070e0d1a869532e1f46",
}


def test_monthly_regression():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "img").mkdir()
        make_image(Path(tmp) / "img" / "wide.png", (1600, 900), (120, 120, 120))
        make_image(Path(tmp) / "img" / "tall.png", (600, 1200), (180, 180, 180))
        make_image(Path(tmp) / "img" / "square.png", (800, 800), (60, 60, 60))
        rc, _, err, prs = run(MONTHLY_MD, tmp)
        check("月报：退出码 0", rc == 0, err)
        out = Path(tmp) / "out.pptx"
        got = ({n: hashlib.sha256(x).hexdigest() for n, x in slide_xmls(out).items()}
               if out.exists() else {})
        check("月报：各页 slide XML 与 master 逐字节一致", got == MONTHLY_SHA,
              sorted(n for n in set(got) | set(MONTHLY_SHA) if got.get(n) != MONTHLY_SHA.get(n)))
        if prs is None:
            check("月报：生成了 pptx", False, err)
            return
        slides = list(prs.slides)
        check("月报：页数 = 封面 + 3 页 + Thank You", len(slides) == 5,
              f"实际 {len(slides)}")

        cover = slides[0]
        check("封面用 Title Slide", cover.slide_layout.name == "Title Slide",
              cover.slide_layout.name)
        check("封面主标题", cover.placeholders[0].text == "Mar. 2026 Working Summary",
              repr(cover.placeholders[0].text))
        check("封面副标题 = date author",
              cover.placeholders[1].text == "9 Apr   Alex.Sample",
              repr(cover.placeholders[1].text))

        thanks = slides[-1]
        check("Thank You 页", thanks.slide_layout.name == "Title Slide"
              and thanks.placeholders[0].text == "Thank You",
              repr(texts(thanks)))

        body = slides[1:-1]
        check("证据页都用 layout 0", all(
            s.slide_layout == prs.slide_layouts[0] for s in body),
            [s.slide_layout.name for s in body])
        check("主标题在 idx 0（顺序与文稿一致）",
              [s.placeholders[0].text for s in body] ==
              ["Sample Dashboard Program", "Mock Tooling Review",
               "Demo Knowledge Page"],
              [s.placeholders[0].text for s in body])
        ph10 = [s.placeholders[10].text if 10 in [p.placeholder_format.idx
                for p in s.placeholders] else None for s in body]
        check("action title 在 idx 10",
              ph10[:2] == ["Build a Reusable Dashboard Model", "First Draft Review"],
              ph10)
        check("没写 ## 的页 idx 10 不填字", not ph10[2], repr(ph10[2]))
        pics = [len([sh for sh in s.shapes if sh.shape_type == 13]) for s in body]
        check("每页图数 = 文稿里的图数 (1/2/3)", pics == [1, 2, 3], pics)

        bars = [caption_bar(s) for s in body]
        check("每页都有底部红条", all(bars), [b is not None for b in bars])
        if all(bars):
            check("红条文字 = 结论 + Next（保留中文「下一步」前缀）",
                  [paragraphs(b) for b in bars] == [
                      ["Standard dashboard workflow drafted and shared with two pilot teams.",
                       "Next: Roll the workflow out to the remaining pilot teams."],
                      ["First-draft review finished with sample stakeholders.",
                       "下一步：整理反馈并进入正式开发。"],
                      ["Demo pages live; usage tracking enabled."]],
                  [paragraphs(b) for b in bars])
            for i, b in enumerate(bars):
                problems = caption_style_problems(b)
                check(f"红条样式与月报一致（第 {i + 1} 页）", not problems, problems)

        tags = [tag_texts(s) for s in body]
        check("Tag：不写不显示；写月份补年份；含年份原样",
              tags == [[], ["Mar 2026"], ["Dec 2025"]], tags)
        badge = [sh for sh in body[1].shapes
                 if sh.has_text_frame and sh.text_frame.text == "Mar 2026"]
        if badge:
            run_ = badge[0].text_frame.paragraphs[0].runs[0]
            check("Tag 是正文区右上的灰字 11pt",
                  str(run_.font.color.rgb) == "6E6E74" and run_.font.size.pt == 11
                  and badge[0].top >= EMU and badge[0].left > 9 * EMU,
                  (run_.font.color.rgb, run_.font.size, badge[0].top, badge[0].left))

        bad = out_of_bounds(prs, list(enumerate(body, start=2)))
        check("所有形状在页面内、不压 banner 和页脚", not bad, bad)
        sample_texts = {t for sl in open_pptx(TEMPLATE).slides
                        for t in texts(sl) if t.strip()}
        leftover = [t for sl in slides for t in texts(sl) if t in sample_texts]
        check("没有残留模板样例页（样例文字不出现）", not leftover, leftover)
        parts = slide_parts(Path(tmp) / "out.pptx")
        check("包里的 slide 部件数 = 页数（样例页部件已删）",
              len(parts) == len(slides), parts)


# 月报全版式逐字节回归：12 种版式各一页（月报模式）。上面的 MONTHLY_SHA 只覆盖 evidence，
# #49 曾把月报 process 说明字号改大而测试全绿；这里把其余版式的月报输出也钉住。
# 图用 examples/demo/img 里的示例图；内容取自示例文稿。
MONTHLY_ALL_MD = """
---
month: 2026-09
author: Alex.Sample
date: 13 Oct
---

# 目录 / AGENDA
## 分三部分汇报，试点数据集中在第二部分
Layout: agenda
01 | 背景与方案 | BACKGROUND
02 | 试点结果 | RESULTS
03 | 推进安排 | ROLLOUT

# 背景与方案 / BACKGROUND
## 先看纸质登记的问题，再看扫码流程
Layout: section
01 | 背景与方案 | BACKGROUND

# 项目背景 / BACKGROUND
## 纸质登记让借还记录难以追溯
Tag: Sep
![](img/paper-log.png)
![](img/online-form.png)
抽查 3 个月的登记本，约三成借出记录没有归还登记
Next: 10 月底前完成全部工具贴码

# 新流程 / PROCESS
## 借还改为扫码登记，四步完成
Layout: process
1. 贴码 | 每件工具贴唯一二维码
2. 扫码借出 | 扫码自动带出工具信息
3. 到期提醒 | 到期前一天推送提醒
4. 扫码归还 | 归还时扫码，自动入库
新流程已在试点车间运行 4 周

# 借还登记 / BEFORE-AFTER
## 登记从手写改为扫码，记录自动留存
Layout: before-after

### Before: 纸质登记
![](img/paper-log.png)
Caption: 借出时手写登记，归还靠自觉补记

### After: 扫码登记
![](img/online-form.png)
Caption: 扫码自动带出工具信息，归还时扫码登记

试点 4 周内借还记录全部可追溯
Next: 11 月起推广到第二个车间

# 关键数据 / KEY RESULTS
## 试点 4 周，借还记录全部可追溯
Layout: stats
- 试点工具 | 120 件 | 覆盖试点车间全部手持工具
  - 电动工具 86 件、量具 34 件
- !记录完整率 | 100% | 改前约 70%，抽查口径相同
  - 4 周借还 1,240 次，全部有归还记录
- 单次登记用时 | 15 秒 | 改前手写约 1 分钟
口径：改前取 6–8 月登记本抽查，改后取系统导出
试点 4 周借还记录完整率 100%

# 试点结论 / FINDINGS
## 记录完整率达到 100%，具备推广条件
Layout: stats-side
- 试点工具 | 120 件 | 覆盖试点车间全部手持工具
- !记录完整率 | 100% | 改前约 70%
- 单次登记用时 | 15 秒 | 改前手写约 1 分钟
### 试点结论
> 记录完整率达到 100%，抽查不再缺页
> 逾期提醒起作用，逾期件数明显下降
口径：改前取 6–8 月登记本抽查，改后取系统导出
Next: 11 月起推广到第二个车间

# 车间对比 / WORKSHOPS
## 机加车间逾期最多，推广时先补提醒
Layout: table
| 车间 | 试点工具 | 4 周借还 | 逾期件数 |
| --- | --- | --- | --- |
| 装配车间 | 52 件 | 560 次 | 3 件 |
| !机加车间 | 48 件 | 520 次 | 11 件 |
| 总装车间 | 20 件 | 160 次 | 1 件 |
机加车间逾期 11 件，占三个车间逾期总数的七成以上

# 项目节点 / MILESTONE
## 软件按计划上线，贴码比计划晚一周
Layout: timeline
- 07 Jul | 立项 | 确定车间与工具范围 | 完成
- !04 Aug | 表单上线 | 扫码表单开放试用 | 完成
- 25 Aug | 贴码完成 | 比计划晚一周 | 完成
- !15 Sep | 试点开始 | 切换为扫码登记 | 完成
- 13 Oct | 试点复盘 | 4 周数据汇总中 | 进行中
- !03 Nov | 推广二车间 | 二车间切换扫码 | 未完成
试点复盘 10 月内完成

# 推广阶段 / ROLLOUT
## 试点阶段已完成，正在复盘
Layout: timeline-phase
- Jul | 立项 | 确定车间与工具范围 | 完成
- Aug | 准备 | 表单上线、全部贴码 | 完成
- !Sep | 试点 | 试点车间切换扫码 | 完成
- Oct | 复盘 | 4 周数据汇总中 | 进行中
- !Nov | 推广 | 第二个车间切换扫码 | 未完成
复盘结论 10 月底前提交

# 项目团队 / TEAM
## 四人小组，现场推进和数据复盘分开负责
Layout: team
- 林晓 | 项目负责人 | 统筹进度和车间对接
- 周航 | 现场推进 | 试点车间贴码和巡检
- 陈雨 | 数据复盘 | 汇总借还记录出周报
- 吴凡 | 系统支持 | 扫码表单维护
分工按现场和数据两条线，周会对齐一次

# 借还看板 / DASHBOARD
## 看板一眼看出逾期未还的工具
Layout: image-text
![](img/dashboard.png)
- 按车间显示在借、逾期、闲置数量
- 逾期数量单独标红，点开可见借用人
- 每天早班前自动刷新
看板已在试点车间晨会使用
"""

# 6c9dc2b（方向 C 之前）的生成器生成 MONTHLY_ALL_MD 的各页 slide XML sha256；
# 当前代码生成结果与之逐字节一致时写入。{部件名: (版式, sha256)}
MONTHLY_ALL_SHA = {
    "ppt/slides/slide1.xml": ("封面", "558477f9a531327cabba1a5d79e7a2e0ff646c29bd0aae1ad515e647bc3272c2"),
    "ppt/slides/slide2.xml": ("agenda", "c7c425026b535490a0cedbcec066ae34302ace6c101ec765a087f5d1730d48b7"),
    "ppt/slides/slide3.xml": ("section", "d0365c1c32e9fb4c833d0560d6c0a163409203e1b04839c555b1efb2401a9847"),
    "ppt/slides/slide4.xml": ("evidence", "88a85bdca068b81ba95f0a8e4213bc718c73803a6a4a0c161be2070f494891c7"),
    "ppt/slides/slide5.xml": ("process", "8b22bcfba59b0c89c55c471190daca1e54ba6a7d06812f6512250b158ce9de00"),
    "ppt/slides/slide6.xml": ("before-after", "ea23b91b13fef41b2c830b11ef6397f43501f1a1b9951d623882d3a9c438f113"),
    "ppt/slides/slide7.xml": ("stats", "0992ac6c19272a8559794c89885b25b2168b9491ef8e513d4c44e8ff28ae098a"),
    "ppt/slides/slide8.xml": ("stats-side", "9c11d7ed620dd796b62abab77fdfb7ae8c1bff03edc576af88d04cfd8fa76314"),
    "ppt/slides/slide9.xml": ("table", "e267be9b2b4df64fc2359dbe1536038fe3e3de97fdfd0a37a3650f8d7073dee5"),
    "ppt/slides/slide10.xml": ("timeline", "e51ead3bc26d7a868f9ea1f184827506b997dc59eb8d3ea4ff265ccb21e6f2a8"),
    "ppt/slides/slide11.xml": ("timeline-phase", "e47ff9090714948733babdc19605a5afe0e30e9d7fb0d49ae0af50645fa1459f"),
    "ppt/slides/slide12.xml": ("team", "8b03ab987b35b4d13c56ceb8cb2e99f32e92a4c3be4dbbc5c560e53ebcc7ad98"),
    "ppt/slides/slide13.xml": ("image-text", "2b90d26682aa87dba22ef53ca28eb77bd57e568cb222438171c4e2c25e3237f8"),
    "ppt/slides/slide14.xml": ("Thank You", "c89c199746d67277afa243eb1dacce8f26093c0b3b40e070e0d1a869532e1f46"),
}


def test_monthly_all_layouts_regression():
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(SKILL / "examples" / "demo" / "img", Path(tmp) / "img")
        rc, _, err, _ = run(MONTHLY_ALL_MD, tmp)
        check("月报全版式：退出码 0", rc == 0, err)
        out = Path(tmp) / "out.pptx"
        got = ({n: hashlib.sha256(x).hexdigest() for n, x in slide_xmls(out).items()}
               if out.exists() else {})
        bad = [f"{n}（{MONTHLY_ALL_SHA[n][0] if n in MONTHLY_ALL_SHA else '多出的页'}）"
               for n in sorted(set(got) | set(MONTHLY_ALL_SHA),
                               key=lambda n: int("".join(c for c in n if c.isdigit())))
               if got.get(n) != MONTHLY_ALL_SHA.get(n, (None, None))[1]]
        check("月报全版式：各页 slide XML 与 6c9dc2b 基线逐字节一致", not bad,
              "不一致的页：" + "、".join(bad))


def test_errors():
    with tempfile.TemporaryDirectory() as tmp:
        rc, _, err, prs = run("""
            ---
            month: 2026-03
            ---
            # Only Page
            Some conclusion.
            """, tmp)
        check("缺 author：非零退出", rc != 0, rc)
        check("缺 author：错误信息点名 author", "author" in err, err)
        check("缺 author：不生成文件", prs is None)

        rc, _, err, prs = run("""
            ---
            month: 2026-03
            author: Alex.Sample
            ---
            # Fine Page
            Fine.

            # Broken Image Page
            ![](img/missing.png)
            Conclusion.
            """, tmp)
        check("图片不存在：非零退出", rc != 0, rc)
        check("图片不存在：错误信息含页标题和路径",
              "Broken Image Page" in err and "img/missing.png" in err, err)
        check("图片不存在：不生成半坏的文件", prs is None)


def test_default_output_name():
    with tempfile.TemporaryDirectory() as tmp:
        rc, out, err, _ = run("""
            ---
            month: 2026-11
            author: Alex.Sample
            ---
            # Page
            Conclusion.
            """, tmp, use_o=False)
        expected = Path(tmp) / "Monthly Working Summary_Alex.Sample_Nov_2026.pptx"
        check("不写 -o：按 frontmatter 推导文件名（放在文稿旁）",
              rc == 0 and expected.exists(),
              (rc, err, sorted(p.name for p in Path(tmp).iterdir())))


def test_caption_grows_upward():
    long = " ".join(["This sample sentence is deliberately long."] * 8)
    with tempfile.TemporaryDirectory() as tmp:
        rc, _, err, prs = run(f"""
            ---
            month: 2026-03
            author: Alex.Sample
            ---
            # Short
            Short conclusion.

            # Long
            {long}
            Next: {long}
            """, tmp)
        if prs is None:
            check("长红条：生成成功", False, err)
            return
        short_bar, long_bar = (caption_bar(s) for s in list(prs.slides)[1:3])
        check("短红条 = 原版高度", short_bar.height == CAPTION_MIN_CY, short_bar.height)
        check("长红条向上加高、底边不动",
              long_bar.height > CAPTION_MIN_CY
              and long_bar.top + long_bar.height == CAPTION_BOTTOM,
              (long_bar.top, long_bar.height))


GENERAL_MD = """
---
title: Sample Tooling Workshop
subtitle: Internal Sharing (Mock)
author: Alex.Sample
date: 17 Oct 2026
{closing}
---

# Why a Generator
## Writing Slides by Hand Is Slow
Mock conclusion for the general-mode deck.
"""


def test_general_mode():
    r = generate(GENERAL_MD.format(closing=""))
    check("通用模式：退出码 0", r.rc == 0, r.stderr)
    slides = r.slides
    check("通用模式无 closing：页数 = 封面 + 1 页（没有收尾页）", len(slides) == 2,
          [texts(s) for s in slides])
    if slides:
        cover = slides[0]
        check("通用模式封面用 Title Slide", cover.slide_layout.name == "Title Slide",
              cover.slide_layout.name)
        check("通用模式封面主标题 = title",
              cover.placeholders[0].text == "Sample Tooling Workshop",
              repr(cover.placeholders[0].text))
        check("通用模式封面副标题 = subtitle 一行 + date author 一行",
              paragraphs(cover.placeholders[1]) ==
              ["Internal Sharing (Mock)", "17 Oct 2026   Alex.Sample"],
              paragraphs(cover.placeholders[1]))

    r = generate(GENERAL_MD.format(closing="closing: Questions?"))
    slides = r.slides
    check("通用模式有 closing：最后一页是收尾页、文字 = closing",
          len(slides) == 3 and slides[-1].slide_layout.name == "Title Slide"
          and slides[-1].placeholders[0].text == "Questions?",
          (r.stderr, [texts(s) for s in slides]))

    r = generate("""
        ---
        title: Only Title
        ---
        # Page
        Conclusion.
        """)
    check("通用模式只写 title 也能生成，副标题为空",
          r.rc == 0 and r.slides and r.slides[0].placeholders[1].text == "",
          (r.stderr, [texts(s) for s in r.slides]))

    r = generate("""
        ---
        title: Sample Tooling Workshop
        ---
        # Page
        Conclusion.
        """, use_o=False)
    check("通用模式不写 -o：按 title 推导文件名",
          r.rc == 0 and (r.workdir / "Sample Tooling Workshop.pptx").exists(),
          (r.stderr, sorted(p.name for p in r.workdir.iterdir())))

    r = generate("""
        ---
        author: Alex.Sample
        ---
        # Page
        Conclusion.
        """)
    check("既没 title 也没 month：非零退出且提示两种模式",
          r.rc != 0 and "title" in r.stderr and "month" in r.stderr, r.stderr)


def test_unknown_layout():
    r = generate("""
        ---
        title: Mock Deck
        ---
        # Fine Page
        Fine.

        # Mystery Layout Page
        Layout: pie-chart
        Conclusion.
        """)
    check("未知 Layout：非零退出", r.rc != 0, r.rc)
    check("未知 Layout：错误信息含页标题和版式名",
          "Mystery Layout Page" in r.stderr and "pie-chart" in r.stderr, r.stderr)
    check("未知 Layout：不生成文件", r.prs is None)


def main():
    test_monthly_regression()
    test_monthly_all_layouts_regression()
    test_errors()
    test_default_output_name()
    test_caption_grows_upward()
    test_general_mode()
    test_unknown_layout()
    finish()


if __name__ == "__main__":
    main()
