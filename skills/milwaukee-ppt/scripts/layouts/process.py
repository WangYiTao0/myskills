"""process 版式：模板 layout 4「Process」，3–5 步等宽卡片 + 序号圆，不画箭头。

文稿写法：3–5 条有序列表，每条「步骤名 | 一句说明」（说明可省略）；
其余普通文字行是结论（月报进底部红条，通用 / 项目模式画成标题下的 lead）。

排版（#13 定稿）：在槽位 idx 17 的矩形内按步数等分，卡片间距 0.3"、内边距 0.2"；
序号圆直径 0.5"、#333333 底、白字 16pt bold，圆心压在卡片上沿；
卡片 #F5F5F5 底 + #E5E5E5 细描边；步骤名 18pt bold #1A1A1A，说明 14pt #6B6B6B。
只用黑白灰。画完删掉空的槽位占位框，免得编辑视图里显示提示文字。
以上是月报模式（逐字节不变）。

通用 / 项目汇报模式（方向 C，#49）：不画卡片。正文区（common.body_area）按步数等分成列，
每列一个黑底白字编号圆（Process Mark N，直径 1.1"，40pt bold），相邻两圆之间一条灰色连接线
（Process Line N，#BFBFBF 2.25pt，两端离圆 0.12"）；圆下居中放步骤名（Process Title N，24pt bold
#1A1A1A）和说明（Process Desc N，18pt #333333）。整组在正文区里垂直居中。
说明折行难看（超过 DESC_MAX_LINES 行，或末行只剩 ≤ common.WIDOW_CHARS 个字）时警告；
审核脚本用同一个 desc_wrap_problem 报「流程说明折行」。
"""
import re

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from mdparse import DeckError

from .common import (DESC_INK, IMG_W, INK as C_INK, LINE_SPACING as C_LINE_SPACING, RULE,
                     add_line, add_page_chrome, add_run, add_shape, add_textbox, body_area, fill_titles,
                     strip_theme_style, fit_body, take_slot, text_lines, text_width_in, warn,
                     wrap_lines, wrap_problem)

NAME = "process"
LAYOUT_INDEX = 4
SLOT_IDX = 17
MIN_STEPS, MAX_STEPS = 3, 5

GAP = Inches(0.3)
PAD = Inches(0.2)
CIRCLE = Inches(0.5)
MIN_CARD_H = Inches(2.0)    # 内容少时卡片也不低于这个高度，免得显得单薄

NAME_PT, DESC_PT, NUM_PT = 18, 14, 16
INK, MUTED, WHITE = "1A1A1A", "6B6B6B", "FFFFFF"
CARD_FILL, CARD_LINE, CIRCLE_FILL = (
    RGBColor(0xF5, 0xF5, 0xF5), RGBColor(0xE5, 0xE5, 0xE5), RGBColor(0x33, 0x33, 0x33))
LINE_SPACING = 1.2          # 行高 ≈ 字号 × 1.2（估算溢出用）
NAME_SPACE_AFTER = Pt(6)

# 方向 C（英寸 / pt）
MARK_D = 1.1                # 编号圆直径
MARK_PT = 40
LINE_PT = 2.25              # 连接线
LINE_INSET = 0.12           # 连接线两端离圆
TITLE_GAP = 0.35            # 圆下沿 → 步骤名
TITLE_PT = 24
TITLE_PAD = 0.15            # 步骤名框比列宽左右各窄
DESC_GAP = 0.12             # 步骤名 → 说明
C_DESC_PT = 18              # 方向 C 说明字号（月报卡片说明仍用 DESC_PT = 14）
DESC_PAD = 0.2              # 说明框比列宽左右各窄
DESC_MAX_LINES = 2          # 说明最多几行

_STEP = re.compile(r"^\d+[.)、]\s*(.+)$")


def parse(page):
    steps = []
    for line in page.lines:
        if not line:
            continue
        m = _STEP.match(line)
        if m:
            name, _, desc = m.group(1).partition("|")
            steps.append((name.strip(), desc.strip()))
        else:
            page.conclusion.append(line)
    if not MIN_STEPS <= len(steps) <= MAX_STEPS:
        raise DeckError(f"页「{page.title}」流程步骤须 {MIN_STEPS}–{MAX_STEPS} 条"
                        f"（有序列表「1. 步骤名 | 说明」），现在 {len(steps)} 条")
    page.fields = {"steps": steps}


def render(prs, page, ctx):
    if ctx.lead:
        return _render_marks(prs, page, ctx)
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    # 方向 C 下上下沿换成正文区（common.fit_body）
    left, top, width, height = fit_body(take_slot(slide, SLOT_IDX), page, ctx)

    steps = page.fields["steps"]
    n = len(steps)
    card_w = (width - GAP * (n - 1)) // n
    max_h = height - CIRCLE // 2
    needs = [_card_height(name, desc, card_w) for name, desc in steps]
    for i, ((name, _), need) in enumerate(zip(steps, needs), start=1):
        if need > max_h:
            warn(f"页「{page.title}」第 {i} 步「{name}」的说明估计会溢出卡片, 建议精简")
    # 卡片等高：取最高的那张（不低于 MIN_CARD_H，不超槽位）；序号圆 + 卡片整组在槽位里垂直居中
    card_h = min(max_h, max(MIN_CARD_H, *needs))
    group_top = top + (height - (card_h + CIRCLE // 2)) // 2
    card_top = group_top + CIRCLE // 2
    for i, (name, desc) in enumerate(steps, start=1):
        x = left + (card_w + GAP) * (i - 1)
        _add_card(slide, i, name, desc, x, card_top, card_w, card_h)
        _add_number(slide, i, x + PAD, group_top)
    add_page_chrome(slide, page, ctx)
    return slide


def _add_card(slide, i, name, desc, x, y, w, h):
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    card.name = f"Process Card {i}"
    strip_theme_style(card)
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_FILL
    card.line.color.rgb = CARD_LINE
    card.line.width = Pt(0.75)
    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = tf.margin_bottom = PAD
    tf.margin_top = CIRCLE // 2 + PAD
    head = tf.paragraphs[0]
    head.alignment = PP_ALIGN.LEFT        # 自选图形默认居中，正文一律左对齐
    head.space_after = NAME_SPACE_AFTER
    add_run(head, name, NAME_PT, True, INK)
    if desc:
        body = tf.add_paragraph()
        body.alignment = PP_ALIGN.LEFT
        add_run(body, desc, DESC_PT, False, MUTED)


def _add_number(slide, i, x, y):
    c = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, CIRCLE, CIRCLE)
    c.name = f"Process Number {i}"
    strip_theme_style(c)
    c.fill.solid()
    c.fill.fore_color.rgb = CIRCLE_FILL
    c.line.fill.background()
    tf = c.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    add_run(tf.paragraphs[0], str(i), NUM_PT, True, WHITE)


def _card_height(name, desc, card_w):
    """估算卡片需要的高度（EMU）：上内边距（含半个序号圆）+ 文字 + 下内边距。"""
    text_w = Emu(card_w - 2 * PAD).inches
    text_pt = (text_lines(name, NAME_PT, text_w) * NAME_PT * LINE_SPACING
               + NAME_SPACE_AFTER.pt
               + text_lines(desc, DESC_PT, text_w) * DESC_PT * LINE_SPACING)
    return CIRCLE // 2 + 2 * PAD + Pt(text_pt)


# ---- 方向 C：编号圆 + 连接线 ------------------------------------------------------

def desc_width_in(n):
    """n 步时说明框的宽度（英寸）：正文区宽 12.2"（body_area 左右不随模式变）按步数等分，再左右各缩 DESC_PAD。"""
    return IMG_W / n - 2 * DESC_PAD


def desc_wrap_problem(desc, n):
    """n 步的流程页上，这句说明折行难看时返回原因（中文短句），否则 None。生成器警告和
    审核「流程说明折行」都用它。"""
    return wrap_problem(desc, C_DESC_PT, desc_width_in(n), DESC_MAX_LINES)


def _line_h(pt):
    return pt * C_LINE_SPACING / 72


def _render_marks(prs, page, ctx):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    take_slot(slide, SLOT_IDX)          # 槽位占位框只取几何，画完删掉；C 下按正文区排
    area = body_area(page, ctx)
    steps = page.fields["steps"]
    n = len(steps)
    col = area.width / n
    title_w, desc_w = col - 2 * TITLE_PAD, col - 2 * DESC_PAD
    for i, (name, desc) in enumerate(steps, start=1):
        problem = desc and desc_wrap_problem(desc, n)
        if problem:
            warn(f"页「{page.title}」第 {i} 步「{name}」的说明折行难看（{problem}）, "
                 f"建议改短或改写: {desc}")
    title_h = max(len(wrap_lines(name, TITLE_PT, title_w)) for name, _ in steps) * _line_h(TITLE_PT)
    desc_lines = max(len(wrap_lines(desc, C_DESC_PT, desc_w)) for _, desc in steps)
    desc_h = desc_lines * _line_h(C_DESC_PT)
    group_h = MARK_D + TITLE_GAP + title_h + (DESC_GAP + desc_h if desc_lines else 0)
    if group_h > area.height:
        warn(f"页「{page.title}」流程的步骤名和说明估计溢出正文区, 建议精简")
    top = area.top + max(0, (area.height - group_h) / 2)
    cy = top + MARK_D / 2
    for i in range(1, n):
        x1 = area.left + (i - 0.5) * col + MARK_D / 2 + LINE_INSET
        x2 = area.left + (i + 0.5) * col - MARK_D / 2 - LINE_INSET
        add_line(slide, f"Process Line {i}", Inches(x1), Inches(cy), Inches(x2), Inches(cy),
                 RULE, LINE_PT)
    title_top = top + MARK_D + TITLE_GAP
    desc_top = title_top + title_h + DESC_GAP
    for i, (name, desc) in enumerate(steps, start=1):
        cx = area.left + (i - 0.5) * col
        mark = add_shape(slide, MSO_SHAPE.OVAL, f"Process Mark {i}", Inches(cx - MARK_D / 2),
                         Inches(top), Inches(MARK_D), Inches(MARK_D), C_INK)
        tf = mark.text_frame
        tf.word_wrap = False
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        add_run(tf.paragraphs[0], str(i), MARK_PT, True, WHITE)
        _centered_text(slide, f"Process Title {i}", name, TITLE_PT, True, C_INK,
                       cx, title_top, title_w, title_h)
        if desc:
            _centered_text(slide, f"Process Desc {i}", desc, C_DESC_PT, False, DESC_INK,
                           cx, desc_top, desc_w, desc_h)
    add_page_chrome(slide, page, ctx)
    return slide


def _centered_text(slide, name, text, pt, bold, color, cx, top, width, height):
    tf = add_textbox(slide, name, Inches(cx - width / 2), Inches(top), Inches(width),
                     Inches(height))
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    add_run(tf.paragraphs[0], text, pt, bold, color)
