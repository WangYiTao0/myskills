"""各版式共用的部件：Context、警告、图片加载、标题填充、底部红条、月份标识，
以及画原生形状的小工具（取槽位、删形状、等比放图、写带中文字体的 run、去主题样式、
估算文字宽度和行数、写“大数字 + 缩小单位”）和品牌红、字体名常量；
缩进子列表、时间线状态解析和状态色；未实现版式的占位解析 / 渲染。

版式模块只从这里 import，互相之间不 import。"""
import hashlib
import os
import re
import sys
import urllib.request
from dataclasses import dataclass

from xml.sax.saxutils import escape

from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from mdparse import DeckError

BRAND_RED = "DB011C"          # Milwaukee Red（与 banner 同色）
LATIN_FONT = "Arial"
EA_FONT = "PingFang SC"       # 中文字体（a:ea）

# 正文区几何（英寸）：banner 占顶部 1.0"，底部留给红条（各版式槽位见模板 layout 4–7）
IMG_LEFT, IMG_TOP, IMG_W, IMG_H = 0.56, 1.3, 12.2, 4.3
IMG_GAP = 0.3

# 底部红条：月报模板固定样式，逐项复刻，不要改。
# 品牌红 DB011C（与 banner 同色）+ 0.75pt 黑描边，白字 ❖（Wingdings）14pt，行距 150%，垂直居中。
# 底边固定；文字多时向上加高，但不高过图片区底缘。
CAPTION_BOTTOM = 5379048 + 1097952  # EMU，底边位置固定
CAPTION_MIN_CY = 1097952            # 原版高度 = 最小高度
CAPTION_MAX_TOP = 5121840           # 不高过正文图片区底缘
CAPTION_LINE_EMU = 266700           # 每行 14pt × 150% 行距 = 21pt
CAPTION_INSETS_EMU = 45720 * 2      # tIns + bIns
CAPTION_CHARS_PER_LINE = 105        # 14pt Arial 在 12.3in 可用宽度下的保守估计

CAPTION_SP_XML = """<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="{id}" name="Caption Bar"/>
    <p:cNvSpPr txBox="1"><a:spLocks noChangeArrowheads="1"/></p:cNvSpPr>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr bwMode="auto">
    <a:xfrm><a:off x="155575" y="{y}"/><a:ext cx="11874874" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="{red}"/></a:solidFill>
    <a:ln w="9525" cap="flat" cmpd="sng" algn="ctr">
      <a:solidFill><a:schemeClr val="tx1"/></a:solidFill>
      <a:prstDash val="solid"/><a:round/>
      <a:headEnd type="none" w="med" len="med"/><a:tailEnd type="none" w="med" len="med"/>
    </a:ln>
    <a:effectLst/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr vert="horz" wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720" numCol="1" rtlCol="0" anchor="ctr" anchorCtr="0" compatLnSpc="1"><a:prstTxWarp prst="textNoShape"><a:avLst/></a:prstTxWarp></a:bodyPr>
    <a:lstStyle>
      <a:defPPr><a:defRPr lang="en-US"/></a:defPPr>
      <a:lvl1pPr marL="342900" indent="-342900" eaLnBrk="0" hangingPunct="0">
        <a:lnSpc><a:spcPct val="150000"/></a:lnSpc>
        <a:buFont typeface="Wingdings" panose="05000000000000000000" pitchFamily="2" charset="2"/>
        <a:buChar char="v"/>
        <a:defRPr sz="1400" b="0">
          <a:solidFill><a:schemeClr val="bg1"/></a:solidFill>
          <a:ea typeface="微软雅黑" panose="020B0503020204020204" pitchFamily="34" charset="-122"/>
          <a:cs typeface="Arial" panose="020B0604020202020204" pitchFamily="34" charset="0"/>
        </a:defRPr>
      </a:lvl1pPr>
    </a:lstStyle>
  </p:txBody>
</p:sp>"""

CAPTION_P_XML = ('<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                 '<a:r><a:rPr lang="en-US" altLang="zh-CN" dirty="0"/>'
                 '<a:t>{text}</a:t></a:r></a:p>')


@dataclass
class Context:
    source_dir: str      # 文稿所在目录，相对图片路径以它为基准
    year: str            # Tag 不含年份时补上的年份


def fill_titles(slide, page):
    """主标题进 idx 0、action title 进 idx 10（所有正文版式都有这两个占位框）。"""
    slide.placeholders[0].text = page.title
    if page.action_title:
        slide.placeholders[10].text = page.action_title


def warn(msg):
    print(f"警告: {msg}", file=sys.stderr)


def url_cache_dir():
    """URL 图片的下载缓存目录（PPT 必须内嵌图片字节；缓存后可离线重复生成）。"""
    return os.environ.get("MILWAUKEE_PPT_CACHE") or os.path.join(
        os.path.expanduser("~"), ".cache", "milwaukee-ppt", "url-images")


def load_image(ref, ctx, page_title):
    """图片引用 → 本地路径。支持相对路径（相对文稿）、绝对路径、http(s) URL。"""
    if ref.startswith(("http://", "https://")):
        cache_dir = url_cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
        ext = os.path.splitext(ref.split("?")[0])[1] or ".png"
        cache = os.path.join(cache_dir, hashlib.md5(ref.encode()).hexdigest() + ext)
        if not os.path.exists(cache):
            try:
                req = urllib.request.Request(ref, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                with open(cache, "wb") as fh:
                    fh.write(data)
            except Exception as e:                      # noqa: BLE001
                raise DeckError(f"页「{page_title}」下载图片失败: {ref}\n  {e}")
        return cache
    p = ref if os.path.isabs(ref) else os.path.join(ctx.source_dir, ref)
    if not os.path.exists(p):
        raise DeckError(f"页「{page_title}」引用的图片不存在: {ref}")
    return p


def _next_shape_id(slide):
    ids = [int(e.get("id")) for e in slide.shapes._spTree.iter(qn("p:cNvPr"))
           if e.get("id")]
    return (max(ids) + 1) if ids else 100


def _caption_geometry(lines, page_title):
    """底边固定，按估算行数向上加高（CJK 宽字符按 2 计，额外半行余量防贴框）。

    这是月报红条固定的算法（几何直接决定输出），不改用下面的 text_lines，
    以保证月报模式的输出不变。"""
    rows = 0
    for text in lines:
        w = sum(2 if ord(ch) > 0x2E7F else 1 for ch in text)
        rows += max(1, -(-w // CAPTION_CHARS_PER_LINE))
    cy = max(CAPTION_MIN_CY,
             rows * CAPTION_LINE_EMU + CAPTION_INSETS_EMU + CAPTION_LINE_EMU // 2)
    y = CAPTION_BOTTOM - cy
    if y < CAPTION_MAX_TOP:
        warn(f"页「{page_title}」红条文字过多 ({rows} 行), 已顶到图片区底缘, "
             f"建议精简结论/Next")
        y = CAPTION_MAX_TOP
        cy = CAPTION_BOTTOM - y
    return y, cy


def caption_lines(page):
    """页面的一句话结论 + 可选 Next，组成红条的各行。"""
    lines = []
    conclusion = " ".join(page.conclusion).strip()
    if conclusion:
        lines.append(conclusion)
    if page.next:
        sep = "：" if page.next_label == "下一步" else ": "
        lines.append(f"{page.next_label}{sep}{page.next}")
    return lines


def add_caption_bar(slide, page):
    """有结论或 Next 时画底部红条；样式全部由 CAPTION_SP_XML 的 lstStyle 继承。"""
    lines = caption_lines(page)
    if not lines:
        return None
    y, cy = _caption_geometry(lines, page.title)
    sp = parse_xml(CAPTION_SP_XML.format(id=_next_shape_id(slide), y=y, cy=cy,
                                         red=BRAND_RED))
    tx_body = sp.find(qn("p:txBody"))
    for text in lines:
        tx_body.append(parse_xml(CAPTION_P_XML.format(text=escape(text))))
    slide.shapes._spTree.append(sp)
    return sp


def add_month_tag(slide, tag, year):
    """正文区右上角极简月份标识（无框、灰字）；只在页面写了 Tag 时显示。

    Tag 不含 4 位年份时补上文稿年份，如 "Mar" → "Mar 2026"。"""
    if not tag:
        return None
    text = tag if re.search(r"\d{4}", tag) else f"{tag} {year}"
    w, h = Inches(1.7), Inches(0.3)
    tb = slide.shapes.add_textbox(Inches(IMG_LEFT + IMG_W) - w, Inches(1.12), w, h)
    tb.name = "Month Tag"
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = Pt(0)
    tf.margin_top = tf.margin_bottom = Pt(0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(11)
    r.font.bold = False
    r.font.name = LATIN_FONT
    r.font.color.rgb = RGBColor(0x6E, 0x6E, 0x74)
    return tb


def add_page_chrome(slide, page, ctx):
    """所有版式通用的页面装饰：右上月份标识 + 底部红条（结论 / Next）。

    版式渲染函数画完自己的内容后最后调用它，红条叠在最上层。"""
    add_month_tag(slide, page.tag, ctx.year)
    add_caption_bar(slide, page)


# ---- 画原生形状的小工具 ---------------------------------------------------------

def slot(slide, idx):
    """按 idx 取占位框（槽位）；没有返回 None。按 idx 找，不按名字找。"""
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    return None


def remove_shape(shape):
    """从页面上删掉形状（空槽位画完就删，免得编辑视图里露出提示文字）。"""
    shape._element.getparent().remove(shape._element)


def take_slot(slide, idx):
    """取出槽位矩形 (left, top, width, height)（EMU）并删掉槽位占位框。"""
    ph = slot(slide, idx)
    rect = (ph.left, ph.top, ph.width, ph.height)
    remove_shape(ph)
    return rect


def strip_theme_style(shape):
    """去掉自选图形自带的主题样式引用（p:style 会带出主题阴影和 accent 色）；
    填充、描边、文字颜色全部由调用方显式给。"""
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)
    return shape


def add_run(paragraph, text, pt, bold, color):
    """追加一个 run：Arial + 中文 PingFang SC（latin 之后写 a:ea），字号、粗细、颜色显式给。

    color 是 6 位十六进制字符串，如 "1A1A1A"。"""
    r = paragraph.add_run()
    r.text = text
    f = r.font
    f.size = Pt(pt)
    f.bold = bold
    f.name = LATIN_FONT
    f.color.rgb = RGBColor.from_string(color)
    latin = r._r.get_or_add_rPr().find(qn("a:latin"))
    latin.addnext(latin.makeelement(qn("a:ea"), {"typeface": EA_FONT}))
    return r


UNIT_PT = 28                  # 数字后面的单位（件、%、秒…）：28pt 灰色、不加粗
UNIT_COLOR = "6B6B6B"

# 数值部分：可带 $ + - 前缀，数字、千分位逗号、小数点；后面的全部算单位
_NUMBER = re.compile(r"^([$+\-]*\d[\d,]*(?:\.\d+)?)\s*(.*)$")


def split_number(value):
    """「120 件」→ ("120", "件")；「-40%」→ ("-40", "%")；不以数值开头 → (原串, "")。"""
    m = _NUMBER.match(value.strip())
    return (m.group(1), m.group(2)) if m else (value.strip(), "")


def add_number(paragraph, value, pt, color, unit_pt=UNIT_PT, unit_color=UNIT_COLOR):
    """在段落里写「大数字 + 缩小单位」：数值部分 pt 号加粗、color 色；单位 unit_pt 号灰色
    不加粗，同一段落所以同一基线。单位前补一个空格（% 紧贴数字）。
    字段不含数值时整串按大数字写。返回 (数字 run, 单位 run 或 None)。"""
    number, unit = split_number(value)
    num_run = add_run(paragraph, number, pt, True, color)
    if not unit:
        return num_run, None
    sep = "" if unit.startswith("%") else " "
    return num_run, add_run(paragraph, sep + unit, unit_pt, False, unit_color)


def fit_picture(slide, path, left, top, width, height):
    """图在矩形内等比缩放、居中，完整显示不裁切（原生图片，不用 insert_picture）。"""
    pic = slide.shapes.add_picture(path, left, top)
    scale = min(width / pic.width, height / pic.height)
    pic.width, pic.height = int(pic.width * scale), int(pic.height * scale)
    pic.left = left + (width - pic.width) // 2
    pic.top = top + (height - pic.height) // 2
    return pic


# ---- 文字估算（只用于判断放不放得下 / 是否警告，统一一个口径）-------------------

CJK_EM, LATIN_EM = 1.0, 0.55     # CJK / 全角按 1em，拉丁字符按约 0.55em


def _is_wide(ch):
    return ord(ch) > 0x2E7F


def text_width_in(text, pt):
    """单行文字宽度估算（英寸）。"""
    return sum(CJK_EM if _is_wide(ch) else LATIN_EM for ch in text) * pt / 72


def text_lines(text, pt, width_in):
    """text 在 width_in 宽、pt 号字下约占几行；空文字 0 行。"""
    if not text:
        return 0
    return max(1, -(-text_width_in(text, pt) // width_in))


# ---- 正文行：缩进子列表 ---------------------------------------------------------

_SUB_ITEM = re.compile(r"^[-*+]\s+(.*)$")


def sub_item(page, i):
    """page.lines[i] 是缩进的列表行（`  - 文字`，缩进 ≥1 列）时返回去掉列表符号的文字，
    否则 None。不缩进的 `- ` 行是本版式的条目行，不算子列表。"""
    if page.indents[i] <= 0:
        return None
    m = _SUB_ITEM.match(page.lines[i])
    return m.group(1).strip() if m else None


# ---- 时间线状态（只用于时间线类版式）---------------------------------------------

DONE, DOING, TODO = "done", "doing", "todo"
DONE_GREEN = "2E7D32"         # 已完成：深绿，上面的字 / 对勾用白色
DOING_AMBER = "F2A900"        # 进行中：琥珀，上面的字用深色 DOING_INK
DOING_INK = "1A1A1A"
STATUS_COLORS = {DONE: DONE_GREEN, DOING: DOING_AMBER, TODO: BRAND_RED}  # 未完成只描边
STATUS_LABELS = {DONE: "已完成", DOING: "进行中", TODO: "未完成"}          # 图例文字

_STATUS_WORDS = {"完成": DONE, "已完成": DONE, "done": DONE,
                 "进行中": DOING, "doing": DOING,
                 "未完成": TODO, "todo": TODO}


def parse_status(text, page, n):
    """一条的状态值 → DONE / DOING / TODO；空串 → None（没写）。不区分大小写。
    认不出的值抛 DeckError（含页标题和第 n 条）。"""
    text = text.strip()
    if not text:
        return None
    st = _STATUS_WORDS.get(text.lower())
    if st is None:
        raise DeckError(f"页「{page.title}」第 {n} 条的状态写错了: {text!r}, "
                        f"可选: 完成 / 进行中 / 未完成 (或 done / doing / todo)")
    return st


def parse_statuses(page, raws, required=False):
    """一页各条的状态原文（没写为 ""）→ 状态列表；整页都没写且 required=False 时返回 None
    （旧写法，按黑白灰画）。DeckError（均含页标题）：值写错、只有部分条写了、
    required=True 却有条没写、“进行中”超过一个。"""
    sts = [parse_status(raw, page, n) for n, raw in enumerate(raws, start=1)]
    missing = [n for n, st in enumerate(sts, start=1) if st is None]
    if len(missing) == len(sts) and not required:
        return None
    if missing:
        need = "每条都必须写状态" if required else "状态要么全写、要么全不写 (部分写了)"
        raise DeckError(f"页「{page.title}」{need}, 第 {' / '.join(map(str, missing))} 条没写")
    doing = sts.count(DOING)
    if doing > 1:
        raise DeckError(f"页「{page.title}」“进行中”最多一个, 现在 {doing} 个")
    return sts


# ---- 占位实现（版式票落地前用；用它的版式都实现后可删）-----------------------------

# 看起来是“版式内容”而不是一句话结论的行：列表、编号、重点、小节、Caption、
# 结论要点（> ）、口径（口径： / Source:）
_STRUCTURED = re.compile(
    r"^([-*+]\s|\d+[.)、]\s*|!|>|#{3,}\s|caption\s*[:：]|口径\s*[:：]|source\s*[:：])", re.I)


def default_parse(page):
    """占位实现用的解析：结构化的行原样放进 fields["raw"]，其余普通文字行进红条结论。"""
    raw = []
    for line in page.lines:
        if line:
            (raw if _STRUCTURED.match(line) else page.conclusion).append(line)
    page.fields = {"raw": raw}


def render_stub(prs, page, ctx, layout_index):
    """未实现版式的占位渲染：用模板对应 layout，只填 idx 0/10，打印“未实现”警告。"""
    warn(f"页「{page.title}」的版式 {page.layout} 未实现, 只填了标题 (红条与 Tag 照常)")
    slide = prs.slides.add_slide(prs.slide_layouts[layout_index])
    fill_titles(slide, page)
    add_page_chrome(slide, page, ctx)
    return slide
