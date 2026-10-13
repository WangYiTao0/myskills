"""stats 版式：数据对比 / Key Results，基于模板 layout 5「Stats」。

文稿写法：2–4 条无序列表「标签 | 数字 | 一句说明」；最多一条在列表符号后加 `!`，
标为重点（只有它的数字用品牌红）。其余普通文字行进底部红条。

    - Lead time | 5 d | Mock average per request
    - !Rework | -40% | Sample reduction after the change

字段：fields["items"] = [{"label", "value", "note", "key"}...]
渲染：在槽位 idx 18 里等分画数据卡（浅灰底），卡内自上而下是小标签、大数字、一行说明；
画完删掉空的槽位占位框。
"""
import re

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from mdparse import DeckError

from .common import add_page_chrome, fill_titles, warn

NAME = "stats"
LAYOUT_INDEX = 5
SLOT_IDX = 18
MIN_ITEMS, MAX_ITEMS = 2, 4

GAP = 0.3                 # 卡片间距（英寸，#13 统一块间距）
PAD = 0.2                 # 卡片内边距
INNER_GAP = 0.1           # 卡内 标签 / 数字 / 说明 之间
LINE = 1.2                # 行高 = 字号 × 1.2

# #13 字号阶梯
LABEL_PT, NUMBER_PT, NOTE_PT = 12, 60, 14
NUMBER_MIN_PT = 28        # 数字长时统一缩小，最低到这里（说明字号的 2 倍）
INK, GRAY, BRAND_RED = "1A1A1A", "6B6B6B", "DB011C"
CARD_FILL = "F5F5F5"
LATIN, EAST_ASIAN = "Arial", "PingFang SC"

_ITEM = re.compile(r"^[-*+]\s+(!?)\s*(.*)$")


def parse(page):
    items = []
    for line in page.lines:
        if not line:
            continue
        m = _ITEM.match(line)
        if not m:
            page.conclusion.append(line)
            continue
        parts = [x.strip() for x in m.group(2).split("|")]
        if len(parts) != 3 or not all(parts):
            raise DeckError(f"页「{page.title}」的数据条目要写成「标签 | 数字 | 一句说明」: "
                            f"{line}")
        items.append({"label": parts[0], "value": parts[1], "note": parts[2],
                      "key": bool(m.group(1))})
    if not MIN_ITEMS <= len(items) <= MAX_ITEMS:
        raise DeckError(f"页「{page.title}」的数据条目要 {MIN_ITEMS}–{MAX_ITEMS} 条, "
                        f"现在 {len(items)} 条")
    keys = sum(it["key"] for it in items)
    if keys > 1:
        raise DeckError(f"页「{page.title}」最多一条数据标 ! 重点, 现在 {keys} 条")
    page.fields = {"items": items}


def _char_em(ch):
    """Arial 粗体的字宽估算（单位：em），只用于判断放不放得下。"""
    if ord(ch) > 0x2E7F:
        return 1.0
    if ch in " .,:;'!|iljtfrI()[]":
        return 0.3
    if ch in "mwMW%@":
        return 0.9
    if ch.isupper():
        return 0.72
    return 0.58


def text_width_in(text, pt):
    return sum(_char_em(ch) for ch in text) * pt / 72


def lines_needed(text, pt, width_in):
    return max(1, -(-text_width_in(text, pt) // width_in))


def _number_size(items, inner_w_in, page_title):
    """所有数字共用一个字号：60pt 放不下最长的那个时统一缩小（整数 pt），并警告。"""
    longest = max(items, key=lambda it: text_width_in(it["value"], NUMBER_PT))["value"]
    fit = int(inner_w_in / text_width_in(longest, 1))   # 1pt 时的宽度 → 放得下的最大字号
    if fit >= NUMBER_PT:
        return NUMBER_PT
    size = max(fit, NUMBER_MIN_PT)
    if fit < NUMBER_MIN_PT:
        warn(f"页「{page_title}」数字「{longest}」太长, 大数字已统一缩小到 {size}pt 仍可能放不下, "
             f"建议缩短数字或减少条数")
    else:
        warn(f"页「{page_title}」数字「{longest}」在 {NUMBER_PT}pt 放不下, "
             f"大数字已统一缩小到 {size}pt")
    return size


def _slot(slide):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == SLOT_IDX:
            return ph
    return None


def _text_box(slide, name, x, y, w, h, text, pt, bold, color, wrap=True):
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    f = r.font
    f.size = Pt(pt)
    f.bold = bold
    f.name = LATIN
    f.color.rgb = RGBColor.from_string(color)
    rpr = r._r.get_or_add_rPr()
    latin = rpr.find(qn("a:latin"))
    ea = latin.makeelement(qn("a:ea"), {"typeface": EAST_ASIAN})
    latin.addnext(ea)
    return tb


def render(prs, page, ctx):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    slot = _slot(slide)
    left, top, width, height = slot.left, slot.top, slot.width, slot.height
    slot._element.getparent().remove(slot._element)

    items = page.fields["items"]
    n = len(items)
    gap = Inches(GAP)
    card_w = (width - gap * (n - 1)) // n
    inner_w_in = card_w / 914400 - 2 * PAD

    number_pt = _number_size(items, inner_w_in, page.title)
    label_lines = max(lines_needed(it["label"], LABEL_PT, inner_w_in) for it in items)
    note_lines = max(lines_needed(it["note"], NOTE_PT, inner_w_in) for it in items)

    label_h = label_lines * LABEL_PT * LINE / 72
    number_h = number_pt * LINE / 72
    note_h = note_lines * NOTE_PT * LINE / 72
    card_h = min(height, Inches(2 * PAD + label_h + number_h + note_h + 2 * INNER_GAP))
    card_y = top + (height - card_h) // 2

    for i, it in enumerate(items, start=1):
        x = left + (card_w + gap) * (i - 1)
        w = (left + width - x) if i == n else card_w   # 最后一张吃掉取整余数
        card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x), Emu(card_y),
                                      Emu(w), Emu(card_h))
        card.name = f"Stat Card {i}"
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor.from_string(CARD_FILL)
        card.line.fill.background()
        card.shadow.inherit = False
        style = card._element.find(qn("p:style"))     # 去掉主题样式引用：LibreOffice 会按它补阴影
        if style is not None:
            card._element.remove(style)
        card.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT   # add_shape 默认居中

        ix, iw = x + Inches(PAD), w - Inches(2 * PAD)
        y = card_y + Inches(PAD)
        _text_box(slide, f"Stat Label {i}", ix, y, iw, Inches(label_h),
                  it["label"], LABEL_PT, True, GRAY)
        y += Inches(label_h + INNER_GAP)
        _text_box(slide, f"Stat Number {i}", ix, y, iw, Inches(number_h),
                  it["value"], number_pt, True,
                  BRAND_RED if it["key"] else INK, wrap=False)
        y += Inches(number_h + INNER_GAP)
        _text_box(slide, f"Stat Note {i}", ix, y, iw, Inches(note_h),
                  it["note"], NOTE_PT, False, GRAY)

    add_page_chrome(slide, page, ctx)
    return slide
