"""milwaukee-ppt 生成器整份文稿级测试：封面 / 收尾 / 月报回归 / 通用模式 / Layout 分派 / 报错。

各版式自己的内容检查放在 test_<版式>.py。只走“md 进、pptx 出”这一个切入点。
纯 Python 脚本，不用 pytest：python3 skills/milwaukee-ppt/tests/test_generate.py
测试图片用 Pillow 现生成纯色图；文稿内容全部虚构。
"""
import hashlib
import tempfile
from pathlib import Path

from deckcheck import (CAPTION_BOTTOM, CAPTION_MIN_CY, EMU,
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
    test_errors()
    test_default_output_name()
    test_caption_grows_upward()
    test_general_mode()
    test_unknown_layout()
    finish()


if __name__ == "__main__":
    main()
