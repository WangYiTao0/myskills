"""timeline 版式：模板 layout 6「Timeline」，槽位 idx 19「Timeline Area」。

字段：3–6 条无序列表，每条「日期 | 标题 | 说明」→ fields["items"] = [(日期, 标题, 说明)]；
其余普通文字行进红条结论。

画法：槽位按条目数等分成列（列间距 0.3"），每列中心一个节点；一条横线连起首末节点。
日期在线上方，标题和说明在线下方，都与节点居中对齐。全部原生形状，只用黑白灰。
画完删掉空的槽位占位框。
"""
import re

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from mdparse import DeckError

from .common import (add_page_chrome, add_run, fill_titles, strip_theme_style, take_slot,
                     text_lines, warn)

NAME = "timeline"
LAYOUT_INDEX = 6
SLOT_IDX = 19
MIN_ITEMS, MAX_ITEMS = 3, 6

GAP = 0.3             # 列间距（统一块间距）
LINE_Y = 1.6          # 横线距槽位上沿（内容大致落在槽位中部，不全挤在上半）
NODE_D = 0.24         # 节点直径

DATE_H = 0.35         # 日期框高（12pt 一行）
TEXT_GAP = 0.2        # 日期 / 正文与节点之间的空隙

LINE_COLOR = (0xBF, 0xBF, 0xBF)
NODE_COLOR = (0x33, 0x33, 0x33)
INK = "1A1A1A"        # 标题
MUTED = "6B6B6B"      # 日期、说明
LINE_SPACING = 1.2    # 行高 ≈ 字号 × 1.2（估算溢出用）
DESC_SPACE_BEFORE = 6  # 说明段前（pt）

# (字号 pt, 粗体, 颜色)：#13 字号阶梯
DATE_STYLE = (12, True, MUTED)
TITLE_STYLE = (18, True, INK)
DESC_STYLE = (14, False, MUTED)

_ITEM = re.compile(r"^[-*+]\s+(.*)$")


def parse(page):
    items = []
    for line in page.lines:
        if not line:
            continue
        m = _ITEM.match(line)
        if not m:
            page.conclusion.append(line)
            continue
        parts = [x.strip() for x in m.group(1).split("|")]
        if len(parts) != 3 or not parts[0] or not parts[1]:
            raise DeckError(f"页「{page.title}」的时间线条目要写成「日期 | 标题 | 说明」: "
                            f"{line}")
        items.append(tuple(parts))
    if not MIN_ITEMS <= len(items) <= MAX_ITEMS:
        raise DeckError(f"页「{page.title}」的时间线条目有 {len(items)} 条, "
                        f"应为 {MIN_ITEMS}–{MAX_ITEMS} 条")
    page.fields = {"items": items}


def _rgb(shape_fill, rgb):
    shape_fill.solid()
    shape_fill.fore_color.rgb = RGBColor(*rgb)


def _textbox(slide, name, left, top, width, height, anchor):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Pt(0)
    tf.margin_top = tf.margin_bottom = Pt(0)
    tf.vertical_anchor = anchor
    return tf


def _overflow_warnings(page, items, col_w, date_h, body_h):
    """日期超过一行、标题 + 说明估计超出线下区域时警告（不中止）。"""
    width_in = Emu(col_w).inches

    def height_pt(text, style):
        return text_lines(text, style[0], width_in) * style[0] * LINE_SPACING

    for i, (date, title, desc) in enumerate(items, start=1):
        date_pt = height_pt(date, DATE_STYLE)
        body_pt = height_pt(title, TITLE_STYLE)
        if desc:
            body_pt += DESC_SPACE_BEFORE + height_pt(desc, DESC_STYLE)
        if date_pt > Emu(date_h).pt or body_pt > Emu(body_h).pt:
            warn(f"页「{page.title}」时间线第 {i} 条文字估计溢出, 建议精简日期 / 标题 / 说明")


def _plain(shape):
    """去掉主题样式引用、关掉继承阴影：填充和描边只用显式写的黑白灰。"""
    strip_theme_style(shape)
    shape.shadow.inherit = False
    return shape


def render(prs, page, ctx):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    left, top, width, slot_h = take_slot(slide, SLOT_IDX)   # 空槽位不留在页面上

    items = page.fields["items"]
    n = len(items)
    gap = Inches(GAP)
    col_w = (width - gap * (n - 1)) // n
    centers = [left + i * (col_w + gap) + col_w // 2 for i in range(n)]
    line_y = top + Inches(LINE_Y)

    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                      centers[0], line_y, centers[-1], line_y)
    line.name = "Timeline Line"
    line.line.color.rgb = RGBColor(*LINE_COLOR)
    line.line.width = Emu(19050)    # 1.5pt
    _plain(line)

    d = Inches(NODE_D)
    for i, cx in enumerate(centers, start=1):
        node = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - d // 2, line_y - d // 2, d, d)
        node.name = f"Timeline Node {i}"
        _rgb(node.fill, NODE_COLOR)
        node.line.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        node.line.width = Emu(25400)  # 2pt 白描边，让节点和横线之间留一圈空隙
        _plain(node)

    date_h = Inches(DATE_H)
    date_top = line_y - d // 2 - Inches(TEXT_GAP) - date_h
    body_top = line_y + d // 2 + Inches(TEXT_GAP)
    body_h = top + slot_h - body_top
    _overflow_warnings(page, items, col_w, date_h, body_h)
    for i, (cx, (date, title, desc)) in enumerate(zip(centers, items), start=1):
        x = cx - col_w // 2
        tf = _textbox(slide, f"Timeline Date {i}", x, date_top, col_w, date_h,
                      MSO_ANCHOR.BOTTOM)
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        add_run(tf.paragraphs[0], date, *DATE_STYLE)

        tf = _textbox(slide, f"Timeline Text {i}", x, body_top, col_w, body_h,
                      MSO_ANCHOR.TOP)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        add_run(p, title, *TITLE_STYLE)
        if desc:
            p = tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            p.space_before = Pt(DESC_SPACE_BEFORE)
            add_run(p, desc, *DESC_STYLE)

    add_page_chrome(slide, page, ctx)
    return slide
