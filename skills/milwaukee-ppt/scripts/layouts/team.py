"""team 版式（团队页）：模板 layout 0「Blank Slide」，列出成员、角色和分工。本期不带头像。

文稿写法：2–8 行无序列表「- 姓名 | 角色 | 职责」，一人一行，三段都必填，如
`- 周航 | 现场推进 | 试点车间贴码、培训和巡检`；其余普通文字行进底部红条（分工结论），
Next: 照常可用。没写列表符号的「姓名 | 角色 | 职责」行报错（免得悄悄进红条）；
团队页不标重点（`!`）、不写子列表。

排版：每人一张卡片（#F5F5F5 底 + #E5E5E5 细描边），卡片宽固定为一行 4 张时的宽度：
2–4 人排一行，5–8 人排两行（第一行 = 总数一半向上取整，第二行从同一左沿排起）；
整组在正文区（1.30–5.60"）里水平、垂直居中。卡片里自上而下：姓名（20pt bold #1A1A1A）、
角色（14pt #6B6B6B）、一条 #BFBFBF 细线、职责（12pt #1A1A1A，最多 3 行）。
只用黑白灰，banner 和底部红条以外不用红。和 evidence、section、agenda 共用模板 layout 0，
inspect 靠 MARK_SHAPE 区分。
"""
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt

from mdparse import DeckError

from .common import (IMG_H, IMG_LEFT, IMG_TOP, IMG_W, INK, LINE_SPACING, LIST_ITEM, MUTED, RULE,
                     add_line, add_page_chrome, add_run, add_shape, add_textbox, fill_titles,
                     text_lines, text_width_in)

NAME = "team"
LAYOUT_INDEX = 0
MARK_SHAPE = "Member Card 1"

MIN_MEMBERS, MAX_MEMBERS = 2, 8
ROW_MAX = 4                     # 一行最多 4 张卡片

NAME_PT, ROLE_PT, DUTY_PT = 20, 14, 12
MAX_DUTY_LINES = 3
CARD_FILL, CARD_LINE = "F5F5F5", "E5E5E5"

# 几何（英寸）
GAP = 0.3                       # 卡片之间（横、竖）
CARD_W = (IMG_W - GAP * (ROW_MAX - 1)) / ROW_MAX
PAD = 0.2                       # 卡片内边距
TEXT_W = CARD_W - 2 * PAD
NAME_H = NAME_PT * LINE_SPACING / 72
ROLE_H = ROLE_PT * LINE_SPACING / 72
DUTY_H = MAX_DUTY_LINES * DUTY_PT * LINE_SPACING / 72
ROLE_GAP = 0.04                 # 姓名 → 角色
RULE_GAP = 0.12                 # 角色 → 细线 → 职责
CARD_H = PAD + NAME_H + ROLE_GAP + ROLE_H + 2 * RULE_GAP + DUTY_H + PAD   # ≈ 1.90"


def _fail(page, msg):
    raise DeckError(f"页「{page.title}」{msg}")


def parse(page):
    members = []
    for i, line in enumerate(page.lines):
        if not line:
            continue
        m = LIST_ITEM.match(line)
        if m and page.indents[i] > 0:
            _fail(page, f"团队页不写子列表，职责写在成员行的第三段: {line!r}")
        if not m:
            if "|" in line:
                _fail(page, f"团队页成员行要以列表符号开头，写成「- 姓名 | 角色 | 职责」: {line!r}")
            page.conclusion.append(line)
            continue
        body = m.group(1)
        if body.startswith("!"):
            _fail(page, f"团队页不标重点，去掉 !: {line!r}")
        parts = [p.strip() for p in body.split("|")]
        if len(parts) != 3:
            _fail(page, f"团队页成员行写成「- 姓名 | 角色 | 职责」，这一行不对: {line!r}")
        members.append(parts)
    if not MIN_MEMBERS <= len(members) <= MAX_MEMBERS:
        _fail(page, f"团队页须 {MIN_MEMBERS}–{MAX_MEMBERS} 行「- 姓名 | 角色 | 职责」，"
                    f"现在 {len(members)} 行")
    for name, role, duty in members:
        for label, value in (("姓名", name), ("角色", role), ("职责", duty)):
            if not value:
                _fail(page, f"团队页「{name} | {role} | {duty}」的{label}为空")
        for label, value, pt, hint in (("姓名", name, NAME_PT, "约 8 个汉字"),
                                       ("角色", role, ROLE_PT, "约 12 个汉字")):
            if text_width_in(value, pt) > TEXT_W:
                _fail(page, f"团队页的{label}「{value}」一行放不下，最多{hint}")
        if text_lines(duty, DUTY_PT, TEXT_W) > MAX_DUTY_LINES:
            _fail(page, f"团队页「{name}」的职责「{duty}」超过 {MAX_DUTY_LINES} 行，"
                        f"最多约 40 个汉字；写一句分工就够")
    page.fields = {"members": [{"name": n, "role": r, "duty": d} for n, r, d in members]}


def render(prs, page, ctx):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    members = page.fields["members"]
    per_row = len(members) if len(members) <= ROW_MAX else (len(members) + 1) // 2
    rows = -(-len(members) // per_row)
    group_w = per_row * CARD_W + (per_row - 1) * GAP
    group_h = rows * CARD_H + (rows - 1) * GAP
    left0 = IMG_LEFT + (IMG_W - group_w) / 2
    top0 = IMG_TOP + (IMG_H - group_h) / 2
    for i, mb in enumerate(members):
        n = i + 1
        row, col = divmod(i, per_row)
        x = left0 + col * (CARD_W + GAP)
        y = top0 + row * (CARD_H + GAP)
        add_shape(slide, MSO_SHAPE.RECTANGLE, f"Member Card {n}", Inches(x), Inches(y),
                  Inches(CARD_W), Inches(CARD_H), CARD_FILL, CARD_LINE, 0.75)
        tx, tw = Inches(x + PAD), Inches(TEXT_W)
        top = y + PAD
        tf = add_textbox(slide, f"Member Name {n}", tx, Inches(top), tw, Inches(NAME_H),
                         anchor=MSO_ANCHOR.BOTTOM, wrap=False)
        add_run(tf.paragraphs[0], mb["name"], NAME_PT, True, INK)
        top += NAME_H + ROLE_GAP
        tf = add_textbox(slide, f"Member Role {n}", tx, Inches(top), tw, Inches(ROLE_H),
                         wrap=False)
        add_run(tf.paragraphs[0], mb["role"], ROLE_PT, False, MUTED)
        top += ROLE_H + RULE_GAP
        add_line(slide, f"Member Rule {n}", tx, Inches(top), tx + tw, Inches(top), RULE, 0.75)
        top += RULE_GAP
        tf = add_textbox(slide, f"Member Duty {n}", tx, Inches(top), tw, Inches(DUTY_H))
        add_run(tf.paragraphs[0], mb["duty"], DUTY_PT, False, INK)
    add_page_chrome(slide, page, ctx)
    return slide
