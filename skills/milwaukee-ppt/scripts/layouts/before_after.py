"""before-after 版式：模板 layout 3「Before / After」，槽位约定见 references/before-after.md。

文稿写法：
    第一个 ### 之前的普通文字      → lead（正文顶部一行粗体）
    ### Before[: 自定义标题]        → 改前小节；标题默认 BEFORE（idx 11）
        一张图 ![](...) 或一段短文  → 内容区 idx 13
        Caption: 一句说明           → idx 15
    ### After[: 自定义标题]         → 改后小节，同上（idx 12 / 14 / 16）
    最后一个小节之后的普通文字      → 底部结论条（Next 也进结论条）
小节在 Caption: 行或空行处结束；两个小节之间不能有普通文字。

底部结论条：caption 之下单行品牌红条（白字 24pt），不用证据页那种向上长高的红条。
有 Next 时作为第二行、结论条顶边不动向下长，最低到页脚之上；超过两行或单项超过一行就警告。
图片 / 短文为空的内容槽和没写的 caption 槽都删掉，编辑视图里不留提示文字。

字段：fields = {"lead": str, "before": Side, "after": Side}，
Side = {"title", "image", "text": [段落], "caption"}。
"""
import re

from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from mdparse import DeckError

from .common import (IMG_LEFT, IMG_W, add_month_tag, caption_lines, fill_titles,
                     load_image, warn)

NAME = "before-after"
LAYOUT_INDEX = 3

SIDES = ("before", "after")
SLOTS = {"before": {"title": 11, "content": 13, "caption": 15},
         "after": {"title": 12, "content": 14, "caption": 16}}

# 正文 lead：模板样例页「Lead」文本框的位置与样式（英寸）。写了 Tag 时右端让到月份标识左侧。
LEAD_LEFT, LEAD_TOP, LEAD_W, LEAD_H = 0.56, 1.30, 11.90, 0.42
TAG_LEFT = IMG_LEFT + IMG_W - 1.7          # common.add_month_tag 的文本框左缘
LEAD_PT = 20
CAPTION_PT = 16                            # 模板 caption 槽：16pt bold、槽内换行、最多两行
CAPTION_MAX_LINES = 2
CAPTION_INSET = 0.06 * 2                   # 槽的左右内边距（英寸）
CONTENT_PT = 18                            # 模板内容槽：18pt、居中
LINE_SPACING = 1.2

# 底部结论条（英寸）：在 caption 槽（5.57–6.15"）之下、页脚（7.25"）之上。
# 品牌红底、白字 24pt、单行；有 Next 时第二行，顶边不动向下长，底边不超过 BAR_MAX_BOTTOM。
BAR_LEFT, BAR_TOP, BAR_W, BAR_MIN_H = 0.56, 6.43, 12.21, 0.55
BAR_MAX_BOTTOM = 7.22
BAR_PT = 24
BAR_LINE_H = 0.36                          # 24pt 单倍行距的一行（英寸，含字体行高余量）
BAR_INSET_X, BAR_INSET_Y = 0.1, 0.03
BAR_MAX_LINES = 2
BRAND_RED = RGBColor(0xDB, 0x01, 0x1C)

_IMG = re.compile(r"^!\[[^\]]*\]\(([^)]+)\)$")
_SECTION = re.compile(r"^###\s+(\S+?)\s*(?:[:：]\s*(.*))?$")
_CAPTION = re.compile(r"(?i)^caption\s*[:：]\s*(.*)$")


def parse(page):
    def err(msg):
        raise DeckError(f"页「{page.title}」{msg}")

    lead, pending, sides = [], [], {}
    cur, open_ = None, False          # 当前小节；它是否还在收内容
    for line in page.lines:
        sec = _SECTION.match(line) if line.startswith("###") else None
        if sec:
            key = sec.group(1).lower()
            if key not in SIDES:
                err(f"的小节只能是 ### Before / ### After, 实际: {line!r}")
            if key in sides:
                err(f"有两个 ### {sec.group(1)} 小节")
            if pending:
                err(f"的两个小节之间有普通文字: {pending[0]!r}")
            cur = sides[key] = {"title": (sec.group(2) or "").strip() or key.upper(),
                                "image": None, "text": [], "caption": ""}
            open_ = True
            continue
        if cur is None:               # 第一个小节之前：lead
            if line:
                lead.append(line)
            continue
        if not open_:                 # 小节已结束：结论候选
            if line:
                pending.append(line)
            continue
        if not line:
            open_ = bool(not cur["image"] and not cur["text"])   # 内容前的空行不结束小节
            continue
        cap = _CAPTION.match(line)
        if cap:
            cur["caption"] = cap.group(1).strip()
            open_ = False
            continue
        img = _IMG.match(line)
        if img:
            if cur["image"] or cur["text"]:
                err("的每个小节只能放一张图或一段短文")
            cur["image"] = img.group(1).strip()
        else:
            if cur["image"]:
                err("的每个小节只能放一张图或一段短文")
            cur["text"].append(line)

    for key in SIDES:
        if key not in sides:
            err(f"缺少 ### {key.capitalize()} 小节")
        if not sides[key]["image"] and not sides[key]["text"]:
            err(f"的 ### {key.capitalize()} 小节没有内容（一张图或一段短文）")
    page.conclusion.extend(pending)
    page.fields = {"lead": " ".join(lead), **sides}


def _place_image(slide, slot, path):
    """图在槽矩形内等比缩放、居中；用 add_picture 画原生图片，不用 insert_picture。"""
    pic = slide.shapes.add_picture(path, slot.left, slot.top)
    scale = min(slot.width / pic.width, slot.height / pic.height)
    pic.width, pic.height = int(pic.width * scale), int(pic.height * scale)
    pic.left = slot.left + (slot.width - pic.width) // 2
    pic.top = slot.top + (slot.height - pic.height) // 2
    return pic


def text_width_in(text, pt):
    """按字宽估算单行文字宽度（英寸）：CJK / 全角 1em，其余按 0.6em（粗体 Arial 偏保守）。"""
    em = sum(1.0 if ord(ch) > 0x2E7F else 0.6 for ch in text)
    return em * pt / 72


def _lines(text, pt, avail_w):
    return max(1, -(-text_width_in(text, pt) // avail_w))


def _check_caption(page, side, slot):
    avail = slot.width / 914400 - CAPTION_INSET
    if side["caption"] and _lines(side["caption"], CAPTION_PT, avail) > CAPTION_MAX_LINES:
        warn(f"页「{page.title}」{side['title']} 的 Caption 估计超过两行, "
             f"建议精简到约 {int(avail * 72 / CAPTION_PT) * CAPTION_MAX_LINES} 个汉字以内: "
             f"{side['caption']}")


def _check_text(page, side, slot):
    avail_w = slot.width / 914400 - CAPTION_INSET
    lines = sum(_lines(t, CONTENT_PT, avail_w) for t in side["text"])
    if lines * CONTENT_PT * LINE_SPACING / 72 > slot.height / 914400:
        warn(f"页「{page.title}」{side['title']} 的短文估计溢出内容区 (约 {int(lines)} 行), "
             f"建议精简")


def _add_lead(slide, page):
    text = page.fields["lead"]
    if not text:
        return None
    right = min(LEAD_LEFT + LEAD_W, TAG_LEFT - 0.1) if page.tag else LEAD_LEFT + LEAD_W
    tb = slide.shapes.add_textbox(Inches(LEAD_LEFT), Inches(LEAD_TOP),
                                  Inches(right - LEAD_LEFT), Inches(LEAD_H))
    tb.name = "Lead"
    if text_width_in(text, LEAD_PT) > right - LEAD_LEFT - CAPTION_INSET:
        warn(f"页「{page.title}」的 lead 估计超过一行, 建议精简: {text}")
    tf = tb.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.06)
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    _set_run(p.add_run(), text, LEAD_PT, True, RGBColor(0x1A, 0x1A, 0x1A))
    return tb


def _set_run(r, text, pt, bold, rgb):
    r.text = text
    r.font.size, r.font.bold, r.font.name = Pt(pt), bold, "Arial"
    r.font.color.rgb = rgb
    rpr = r._r.get_or_add_rPr()                 # 中文字体与模板一致（latin 之后追加 ea）
    rpr.append(rpr.makeelement(qn("a:ea"), {"typeface": "PingFang SC"}))


def _add_conclusion_bar(slide, page):
    """caption 之下的单行红色结论条；有 Next 时第二行，向下长到页脚之上为止。"""
    lines = caption_lines(page)
    if not lines:
        return None
    avail = BAR_W - 2 * BAR_INSET_X
    rows = [_lines(t, BAR_PT, avail) for t in lines]
    h = max(BAR_MIN_H, sum(rows) * BAR_LINE_H + 2 * BAR_INSET_Y)
    if max(rows) > 1 or sum(rows) > BAR_MAX_LINES:
        warn(f"页「{page.title}」的结论条估计放不下 (结论和 Next 各应单行), "
             f"建议精简到约 {int(avail * 72 / BAR_PT)} 个汉字以内: {' / '.join(lines)}")
    h = min(h, BAR_MAX_BOTTOM - BAR_TOP)
    tb = slide.shapes.add_textbox(Inches(BAR_LEFT), Inches(BAR_TOP), Inches(BAR_W), Inches(h))
    tb.name = "Conclusion Bar"
    tb.fill.solid()
    tb.fill.fore_color.rgb = BRAND_RED
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(BAR_INSET_X)
    tf.margin_top = tf.margin_bottom = Inches(BAR_INSET_Y)
    for i, text in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.line_spacing = 1.0
        _set_run(p.add_run(), text, BAR_PT, False, RGBColor(0xFF, 0xFF, 0xFF))
    return tb


def _drop(shape):
    """删掉空槽位：页面上不留占位框，编辑视图里就不会出现提示文字。"""
    shape._element.getparent().remove(shape._element)


def render(prs, page, ctx):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_INDEX])
    fill_titles(slide, page)
    for key in SIDES:
        side, slots = page.fields[key], SLOTS[key]
        slide.placeholders[slots["title"]].text = side["title"]
        content = slide.placeholders[slots["content"]]
        caption = slide.placeholders[slots["caption"]]
        if side["image"]:
            _place_image(slide, content, load_image(side["image"], ctx, page.title))
            _drop(content)
        else:
            content.text = "\n".join(side["text"])
            content.text_frame.word_wrap = True        # 模板槽是不换行的，短文要在槽宽内换行
            _check_text(page, side, content)
        if side["caption"]:
            caption.text = side["caption"]
            caption.text_frame.word_wrap = True
            _check_caption(page, side, caption)
        else:
            _drop(caption)
    _add_lead(slide, page)
    add_month_tag(slide, page.tag, ctx.year)
    _add_conclusion_bar(slide, page)
    return slide
