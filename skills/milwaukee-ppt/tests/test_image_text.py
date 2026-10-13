"""image-text 版式测试：左图右文。

运行：python3 skills/milwaukee-ppt/tests/test_image_text.py
"""
from deckcheck import (EMU, IMAGE_FRAME_IN, LAYOUT_INDEX, body_slide, caption_bar,
                       caption_style_problems, check, emu_rect, finish, generate,
                       out_of_bounds, paragraphs, pictures, placeholder, tag_shape,
                       warnings)

NAME = "image-text"
TITLE = "Mock Image + Text Page"
MD = """
---
title: Mock Deck
date: 13 Oct 2026
---

# Mock Image + Text Page
## Mock Action Title
Layout: image-text
Tag: Mar
![](img/shot.png)
- Point one about the mock screenshot
- Point two about the mock screenshot
Mock one-line conclusion.
Next: Mock next step.
"""
IMAGES = {"img/shot.png": (1600, 900)}


def test_chrome():
    """所有版式通用：用模板对应 layout、标题进 idx 0/10、Tag 和底部红条、不越界。"""
    r = generate(MD, images=IMAGES)
    check("image-text：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("image-text：生成了正文页", False, r.stderr)
        return
    check("image-text：用模板 layout 7「Image + Text」",
          s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX[NAME]],
          s.slide_layout.name)
    check("image-text：主标题在 idx 0、action title 在 idx 10",
          placeholder(s, 0).text == TITLE
          and placeholder(s, 10).text == "Mock Action Title",
          (placeholder(s, 0).text, placeholder(s, 10).text))
    bar = caption_bar(s)
    check("image-text：底部红条 = 结论 + Next",
          bar is not None and paragraphs(bar) ==
          ["Mock one-line conclusion.", "Next: Mock next step."],
          bar and paragraphs(bar))
    if bar is not None:
        problems = caption_style_problems(bar)
        check("image-text：红条样式与月报一致", not problems, problems)
    tag = tag_shape(s)
    check("image-text：Tag 补年份显示", tag is not None and tag.text_frame.text == "Mar 2026",
          tag and tag.text_frame.text)
    bad = out_of_bounds(r.prs, [s])
    check("image-text：形状在页面内、不压 banner 和页脚", not bad, bad)


def check_fitted(label, slide, src_w, src_h):
    """图在图框内完整显示：比例不变、贴住一边、两个方向居中。"""
    pics = pictures(slide)
    if len(pics) != 1:
        check(f"{label}：页上正好一张图", False, len(pics))
        return
    pic = pics[0]
    fl, ft, fw, fh = emu_rect(IMAGE_FRAME_IN)
    tol = EMU // 100
    inside = (pic.left >= fl - tol and pic.top >= ft - tol
              and pic.left + pic.width <= fl + fw + tol
              and pic.top + pic.height <= ft + fh + tol)
    check(f"{label}：图在图框内", inside,
          (pic.left, pic.top, pic.width, pic.height))
    ratio = (pic.width / pic.height) / (src_w / src_h)
    check(f"{label}：比例不变", abs(ratio - 1) < 0.01, ratio)
    fills = (abs(pic.width - fw) <= tol) or (abs(pic.height - fh) <= tol)
    check(f"{label}：撑满图框的一边（不留多余空白）", fills,
          (pic.width, pic.height, fw, fh))
    cx = pic.left + pic.width / 2 - (fl + fw / 2)
    cy = pic.top + pic.height / 2 - (ft + fh / 2)
    check(f"{label}：在图框内居中", abs(cx) <= tol and abs(cy) <= tol, (cx, cy))
    crop = (pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom)
    check(f"{label}：不裁切", all(c == 0 for c in crop), crop)


def test_landscape_image():
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    if s is None:
        check("image-text 横图：生成了正文页", False, r.stderr)
        return
    check_fitted("image-text 横图", s, 1600, 900)


def test_portrait_image():
    r = generate(MD.replace("img/shot.png", "img/tall.png"),
                 images={"img/tall.png": (900, 1600)})
    check("image-text 竖图：退出码 0", r.rc == 0, r.stderr)
    s = body_slide(r)
    if s is None:
        check("image-text 竖图：生成了正文页", False, r.stderr)
        return
    check_fitted("image-text 竖图", s, 900, 1600)


def test_frame_placeholder_cleared():
    """图框不留占位框和提示文字（PowerPoint 里看不到“图框（16:9）…”）。"""
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    check("image-text：图框占位框已清掉",
          s is not None and placeholder(s, 20) is None,
          s and placeholder(s, 20) and placeholder(s, 20).text)


def test_points_in_text_area():
    r = generate(MD, images=IMAGES)
    s = body_slide(r)
    slot = s and placeholder(s, 21)
    check("image-text：要点在 idx 21 文字槽位，条数和内容正确",
          slot is not None and paragraphs(slot) ==
          ["Point one about the mock screenshot",
           "Point two about the mock screenshot"],
          slot and paragraphs(slot))
    if slot is not None:
        runs = [r_ for p in slot.text_frame.paragraphs for r_ in p.runs]
        local = [r_.font.size for r_ in runs if r_.font.size is not None]
        check("image-text：要点沿用槽位样式（不另设字号）", not local, local)


def test_no_image_is_error():
    r = generate(MD.replace("![](img/shot.png)\n", ""))
    check("image-text：没有图时非零退出，错误含页标题",
          r.rc != 0 and TITLE in r.stderr and "图" in r.stderr, (r.rc, r.stderr))


def test_missing_image_is_error():
    r = generate(MD)                      # 不生成 img/shot.png
    check("image-text：图片不存在时非零退出，错误含页标题和路径",
          r.rc != 0 and TITLE in r.stderr and "img/shot.png" in r.stderr,
          (r.rc, r.stderr))


def test_more_than_five_points_warns():
    extra = "".join(f"- Extra point {i}\n" for i in range(3, 7))
    md = MD.replace("- Point two about the mock screenshot\n",
                    "- Point two about the mock screenshot\n" + extra)
    r = generate(md, images=IMAGES)
    check("image-text：6 条要点仍生成", r.rc == 0, r.stderr)
    w = [x for x in warnings(r.stderr) if TITLE in x and "6" in x]
    check("image-text：要点超过 5 条给警告（含页标题和条数）", len(w) == 1, r.stderr)
    s = body_slide(r)
    slot = s and placeholder(s, 21)
    check("image-text：6 条要点都写进槽位",
          slot is not None and len(paragraphs(slot)) == 6,
          slot and paragraphs(slot))


def test_five_points_no_warning():
    extra = "".join(f"- Extra point {i}\n" for i in range(3, 6))
    md = MD.replace("- Point two about the mock screenshot\n",
                    "- Point two about the mock screenshot\n" + extra)
    r = generate(md, images=IMAGES)
    check("image-text：5 条要点不警告", r.rc == 0 and not warnings(r.stderr),
          r.stderr)


def test_second_image_warns():
    md = MD.replace("![](img/shot.png)\n", "![](img/shot.png)\n![](img/b.png)\n")
    r = generate(md, images={**IMAGES, "img/b.png": (800, 800)})
    w = [x for x in warnings(r.stderr) if TITLE in x]
    s = body_slide(r)
    check("image-text：多于一张图时警告、只放第一张",
          r.rc == 0 and len(w) == 1 and s is not None and len(pictures(s)) == 1,
          r.stderr)


def test_no_points_leaves_no_prompt():
    """没写要点：文字槽位删掉，不在 PowerPoint 里露出“要点（建议…）”提示。"""
    md = MD.replace("- Point one about the mock screenshot\n", "").replace(
        "- Point two about the mock screenshot\n", "")
    r = generate(md, images=IMAGES)
    s = body_slide(r)
    check("image-text：没有要点时文字槽位已清掉",
          r.rc == 0 and s is not None and placeholder(s, 21) is None, r.stderr)


if __name__ == "__main__":
    test_chrome()
    test_landscape_image()
    test_portrait_image()
    test_frame_placeholder_cleared()
    test_points_in_text_area()
    test_no_image_is_error()
    test_missing_image_is_error()
    test_more_than_five_points_warns()
    test_five_points_no_warning()
    test_second_image_warns()
    test_no_points_leaves_no_prompt()
    finish()
