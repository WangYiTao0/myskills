"""before-after 版式测试（票 #14 实现前为占位测试，只测占位行为）。

运行：python3 skills/milwaukee-ppt/tests/test_before_after.py
#14 实现版式时：把 test_stub 换成真实内容检查，test_chrome 保留
（MD 里的正文按 spec #10 的字段写法写好了，实现后应仍能通过校验）。
小节与结论之间的空行是占位解析的约定（小节到空行为止），#14 可按定稿写法调整。
"""
from deckcheck import (LAYOUT_INDEX, caption_bar, caption_style_problems, check,
                       finish, generate, out_of_bounds, paragraphs, placeholder,
                       tag_shape, warnings)

NAME = "before-after"
TITLE = "Mock Before / After Page"
MD = """
---
title: Mock Deck
date: 13 Oct 2026
---

# Mock Before / After Page
## Mock Action Title
Layout: before-after
Tag: Mar
### Before
Manual copy-paste between three mock spreadsheets.
Caption: Three manual hand-offs
### After
One mock form feeds every sheet.
Caption: One automated hand-off

Mock one-line conclusion.
Next: Mock next step.
"""
IMAGES = {"img/shot.png": (1600, 900)}


def body_slide(r):
    return r.slides[1] if len(r.slides) > 1 else None


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD, images=IMAGES)
    check("before-after：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("before-after：生成了正文页", False, r.stderr)
        return
    check("before-after：用模板 layout 3「Before / After」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("before-after：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("before-after：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("before-after：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("before-after：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("before-after：形状在页面内、不压 banner 和页脚", not bad, bad)


def test_stub():
    """占位实现：打印一条“未实现”警告，含页标题。"""
    r = generate(MD, images=IMAGES)
    w = [x for x in warnings(r.stderr) if "未实现" in x]
    check("before-after（占位）：有“未实现”警告且含页标题",
          len(w) == 1 and TITLE in w[0], r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_stub()
    finish()
