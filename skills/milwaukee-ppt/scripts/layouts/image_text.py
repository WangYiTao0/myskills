"""image-text 版式：左图右文，基于模板 layout 7「Image + Text」。

字段：一张图 `![](...)` + 若干条无序列表要点（建议 ≤5）；其余普通文字行进红条结论。
- 图放进 idx 20 图框的矩形里：按比例完整显示、不裁切、居中；图框占位框本身删掉，不留提示文字。
- 要点写进 idx 21 文字槽位，样式沿用槽位自带的（16pt、灰色圆点、段后间距）。
"""
import re

from mdparse import DeckError

from .common import (add_page_chrome, fill_titles, fit_picture, load_image, remove_shape,
                     slot, take_slot, warn)

NAME = "image-text"
LAYOUT_INDEX = 7
IMAGE_FRAME_IDX = 20
TEXT_AREA_IDX = 21
MAX_POINTS = 5            # 建议上限，超过只警告

_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_BULLET = re.compile(r"^[-*+]\s+(.*)$")


def parse(page):
    images, points = [], []
    for line in page.lines:
        if not line:
            continue
        m = _IMG.match(line)
        if m:
            images.append(m.group(1).strip())
            continue
        m = _BULLET.match(line)
        if m:
            points.append(m.group(1).strip())
        else:
            page.conclusion.append(line)
    if not images:
        raise DeckError(f"页「{page.title}」(image-text) 没有图, 需要一行 ![](图片路径)")
    if len(images) > 1:
        warn(f"页「{page.title}」(image-text) 有 {len(images)} 张图, 只用第一张")
    if len(points) > MAX_POINTS:
        warn(f"页「{page.title}」(image-text) 有 {len(points)} 条要点, "
             f"建议不超过 {MAX_POINTS} 条, 请检查右侧文字是否溢出")
    page.fields = {"image": images[0], "points": points}


def _place_image(slide, ref, ctx, page_title):
    """删掉图框占位框，在它的矩形里等比缩放、居中放图。"""
    rect = take_slot(slide, IMAGE_FRAME_IDX)
    pic = fit_picture(slide, load_image(ref, ctx, page_title), *rect)
    pic.name = "Image"
    return pic


def _fill_points(slide, points):
    """每条要点一段，只写文字，字号/颜色/圆点/段距全部继承槽位的 lstStyle。

    没有要点时删掉槽位，免得 PowerPoint 里露出提示文字。"""
    area = slot(slide, TEXT_AREA_IDX)
    if not points:
        remove_shape(area)
        return
    tf = area.text_frame
    tf.text = points[0]
    for text in points[1:]:
        tf.add_paragraph().text = text


def render(prs, page, ctx):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    _place_image(slide, page.fields["image"], ctx, page.title)
    _fill_points(slide, page.fields["points"])
    add_page_chrome(slide, page, ctx)
    return slide
