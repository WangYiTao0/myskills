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
from pptx.util import Emu, Inches

from mdparse import DeckError

from .common import (BRAND_RED, add_page_chrome, add_run, fill_titles, strip_theme_style,
                     take_slot, warn)

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
INK, GRAY = "1A1A1A", "6B6B6B"
CARD_FILL = "F5F5F5"

_ITEM = re.compile(r"^[-*+]\s+(!?)\s*(.*)$")


def parse(page):
    items = []
    for line in page.lines:
        if not line:
            continue
        m = _ITEM.match(line)
        if not m:
            if line.startswith("!") and "|" in line:     # 重点条漏写列表符号，别悄悄进红条
                raise DeckError(f"页「{page.title}」的重点数据条要以列表符号开头，"
                                f"写成「- !标签 | 数字 | 一句说明」: {line}")
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


def _glyph_em(ch):
    """逐字宽（Arial，单位 em），用来定卡片几何：大数字字号、标签 / 说明行数 → 卡片高度。

    这些估算直接决定形状尺寸，按字形细分比通用口径（common.text_width_in，
    拉丁一律 0.55em）准，所以本版式保留这张表；别处的溢出警告一律用 common 的口径。"""
    if ord(ch) > 0x2E7F:
        return 1.0
    if ch in " .,:;'!|iljtfrI()[]":
        return 0.3
    if ch in "mwMW%@":
        return 0.9
    if ch.isupper():
        return 0.72
    return 0.58


def _glyph_width_in(text, pt):
    return sum(_glyph_em(ch) for ch in text) * pt / 72


def _glyph_lines(text, pt, width_in):
    return max(1, -(-_glyph_width_in(text, pt) // width_in))


def _number_size(items, inner_w_in, page_title):
    """所有数字共用一个字号：60pt 放不下最长的那个时统一缩小（整数 pt），并警告。"""
    longest = max(items, key=lambda it: _glyph_width_in(it["value"], NUMBER_PT))["value"]
    fit = int(inner_w_in / _glyph_width_in(longest, 1))   # 1pt 时的宽度 → 放得下的最大字号
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


def _text_box(slide, name, x, y, w, h, text, pt, bold, color, wrap=True):
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    add_run(p, text, pt, bold, color)
    return tb


def render(prs, page, ctx):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    left, top, width, height = take_slot(slide, SLOT_IDX)

    items = page.fields["items"]
    n = len(items)
    gap = Inches(GAP)
    card_w = (width - gap * (n - 1)) // n
    inner_w_in = Emu(card_w).inches - 2 * PAD

    number_pt = _number_size(items, inner_w_in, page.title)
    label_lines = max(_glyph_lines(it["label"], LABEL_PT, inner_w_in) for it in items)
    note_lines = max(_glyph_lines(it["note"], NOTE_PT, inner_w_in) for it in items)

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
        strip_theme_style(card)          # 去掉主题样式引用：LibreOffice 会按它补阴影
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
