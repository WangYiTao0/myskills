"""process 版式测试（票 #15 实现前为占位测试，只测占位行为）。

运行：python3 skills/milwaukee-ppt/tests/test_process.py
#15 实现版式时：把 test_stub 换成真实内容检查，test_chrome 保留
（MD 里的正文按 spec #10 的字段写法写好了，实现后应仍能通过校验）。
"""
from deckcheck import (LAYOUT_INDEX, caption_bar, caption_style_problems, check,
                       finish, generate, out_of_bounds, paragraphs, placeholder,
                       tag_shape, warnings)

NAME = "process"
TITLE = "Mock Process Page"
MD = """
---
title: Mock Deck
date: 13 Oct 2026
---

# Mock Process Page
## Mock Action Title
Layout: process
Tag: Mar
1. Collect | Gather mock requests in one form
2. Review | Weekly triage of sample items
3. Ship | Publish the mock result
Mock one-line conclusion.
Next: Mock next step.
"""
IMAGES = {"img/shot.png": (1600, 900)}


def body_slide(r):
    return r.slides[1] if len(r.slides) > 1 else None


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD, images=IMAGES)
    check("process：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("process：生成了正文页", False, r.stderr)
        return
    check("process：用模板 layout 4「Process」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("process：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("process：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("process：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("process：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("process：形状在页面内、不压 banner 和页脚", not bad, bad)


def test_stub():
    """占位实现：打印一条“未实现”警告，含页标题。"""
    r = generate(MD, images=IMAGES)
    w = [x for x in warnings(r.stderr) if "未实现" in x]
    check("process（占位）：有“未实现”警告且含页标题",
          len(w) == 1 and TITLE in w[0], r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_stub()
    finish()
