"""
Milwaukee PPT skill - helpers.py
=================================

Reusable OOXML generators for the Milwaukee Tool PPT template.

Usage:
    from helpers import *
    set_output_dir('/path/to/unpacked/ppt/slides')

    shapes = []
    shapes.append(rect(700000, 1000000, 5000000, 500000,
        paragraphs=para(run("Hello", sz=1800, bold=True, color=INK))))

    write_slide(1, title="MY TITLE", subtitle="My subtitle", content_shapes=shapes)

Coordinate system: EMU (English Metric Units)
- 16:9 slide = 12192000 x 6858000 EMU
- 1 inch = 914400 EMU
- Content safe area: x ∈ [300000, 11900000], y ∈ [925000, 6450000]

API summary:
    Constants:
        RED, INK, MUTED, HAIRLINE, CARD_BG, WHITE, LATIN, EA

    Setup:
        set_output_dir(path)   - where slide{N}.xml will be written

    Run/paragraph builders:
        run(text, sz, bold, color, italic, lang, typeface)
        para(runs_xml, algn, margin_l, indent, line_spc, space_before)

    Shape builders (return XML strings, append to shapes list):
        rect(x, y, cx, cy, fill, line, line_w, paragraphs, prst)
        oval(x, y, cx, cy, fill, line, paragraphs)
        line_shape(x, y, cx, cy, color, w)

    Placeholders:
        title_ph(text)      - red banner top row
        subtitle_ph(text)   - red banner bottom row

    Slide writer:
        write_slide(n, title, subtitle, content_shapes)
"""

import os

# ============================================================
# Design Tokens — change here to retheme entire deck
# ============================================================

RED       = "DB021D"   # Milwaukee Red — visual anchor only
INK       = "1A1A1A"   # primary text
MUTED     = "6B6B6B"   # secondary text, labels
HAIRLINE  = "E5E5E5"   # dividers, card borders
CARD_BG   = "F7F7F7"   # subtle card differentiation
WHITE     = "FFFFFF"   # never change page background

LATIN = "Calibri"
EA    = "Microsoft JhengHei"

# Slide canvas
SLIDE_CX = 12192000
SLIDE_CY = 6858000

# Content safe area
SAFE_X_MIN = 300000
SAFE_X_MAX = 11900000
SAFE_Y_MIN = 925000     # below red banner
SAFE_Y_MAX = 6450000    # above confidential footer

# ============================================================
# State
# ============================================================

_OUT_DIR = None
_sp_id = 100

def set_output_dir(path):
    """Set where slide{N}.xml files are written."""
    global _OUT_DIR
    _OUT_DIR = path

def _next_id():
    global _sp_id
    _sp_id += 1
    return _sp_id

def reset_id_counter():
    """Call between slides if you want IDs to restart at 100."""
    global _sp_id
    _sp_id = 100

# ============================================================
# Text builders
# ============================================================

def _esc(s):
    """Escape XML special characters."""
    return (str(s).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))

def run(text, sz=1400, bold=False, color=INK, italic=False, lang="zh-TW", typeface=None):
    """Build a single <a:r> text run."""
    b = ' b="1"' if bold else ''
    i = ' i="1"' if italic else ''
    tf = f'<a:latin typeface="{typeface or LATIN}"/><a:ea typeface="{EA}"/>'
    return (f'<a:r><a:rPr lang="{lang}" sz="{sz}"{b}{i} dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'{tf}'
            f'</a:rPr><a:t>{_esc(text)}</a:t></a:r>')

def para(runs_xml, algn="l", margin_l=0, indent=0, line_spc=None, space_before=None):
    """Wrap one or more run XML strings into a paragraph."""
    attrs = f' algn="{algn}"'
    if margin_l: attrs += f' marL="{margin_l}"'
    if indent:   attrs += f' indent="{indent}"'
    inner = ""
    if line_spc:
        inner += f'<a:lnSpc><a:spcPct val="{line_spc}"/></a:lnSpc>'
    if space_before:
        inner += f'<a:spcBef><a:spcPts val="{space_before}"/></a:spcBef>'
    pPr = f'<a:pPr{attrs}>{inner}</a:pPr>'
    return f'<a:p>{pPr}{runs_xml}</a:p>'

def bullet_para(runs_xml, algn="l", color=INK):
    """Paragraph with a bullet character. Use sparingly."""
    bullet = (f'<a:pPr{" algn=" + chr(34) + algn + chr(34)} '
              f'marL="342900" indent="-342900">'
              f'<a:buClr><a:srgbClr val="{color}"/></a:buClr>'
              f'<a:buChar char="&#x2022;"/></a:pPr>')
    return f'<a:p>{bullet}{runs_xml}</a:p>'

# ============================================================
# Shape builders
# ============================================================

def rect(x, y, cx, cy, fill=None, line=None, line_w=12700,
         paragraphs="", body_pr_extra="", prst="rect"):
    """
    Generic rectangle / preset shape with optional text body.

    Args:
        x, y, cx, cy: EMU position and size
        fill: hex color string (no #), or None for no fill
        line: hex color string for border, or None for no border
        line_w: border width in EMU (default 12700 ≈ 1pt)
        paragraphs: XML from para() / bullet_para()
        body_pr_extra: extra attributes for <a:bodyPr> (e.g. 'anchor="ctr"')
        prst: preset geometry (rect, rightArrow, roundRect, etc.)
    """
    sid = _next_id()
    fill_xml = (f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
                if fill else '<a:noFill/>')
    ln_xml = (f'<a:ln w="{line_w}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
              if line else '<a:ln><a:noFill/></a:ln>')
    body = paragraphs if paragraphs else '<a:p><a:endParaRPr lang="en-US"/></a:p>'
    return f"""<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{sid}" name="Shape{sid}"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>
    {fill_xml}
    {ln_xml}
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" rtlCol="0" anchor="t" {body_pr_extra}/>
    <a:lstStyle/>
    {body}
  </p:txBody>
</p:sp>"""

def oval(x, y, cx, cy, fill, line=None, paragraphs=""):
    """Ellipse / circle shape."""
    sid = _next_id()
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
    ln_xml = (f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
              if line else '<a:ln><a:noFill/></a:ln>')
    body = paragraphs if paragraphs else '<a:p><a:endParaRPr lang="en-US"/></a:p>'
    return f"""<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{sid}" name="Oval{sid}"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    {fill_xml}{ln_xml}
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" anchor="ctr" anchorCtr="1"/>
    <a:lstStyle/>
    {body}
  </p:txBody>
</p:sp>"""

def line_shape(x, y, cx, cy, color=HAIRLINE, w=9525):
    """
    Straight line connector.
    For horizontal line: cy=0; for vertical: cx=0.
    """
    sid = _next_id()
    return f"""<p:cxnSp>
  <p:nvCxnSpPr>
    <p:cNvPr id="{sid}" name="Line{sid}"/>
    <p:cNvCxnSpPr/>
    <p:nvPr/>
  </p:nvCxnSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="{w}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>
  </p:spPr>
  <p:style>
    <a:lnRef idx="1"><a:schemeClr val="accent1"/></a:lnRef>
    <a:fillRef idx="0"><a:schemeClr val="accent1"/></a:fillRef>
    <a:effectRef idx="0"><a:schemeClr val="accent1"/></a:effectRef>
    <a:fontRef idx="minor"><a:schemeClr val="tx1"/></a:fontRef>
  </p:style>
</p:cxnSp>"""

# ============================================================
# Placeholders (red banner)
# ============================================================

def title_ph(text):
    """Main title in red banner top row. Keep ≤ 28 EN / 14 CN chars."""
    return f"""<p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Title 2"/>
          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph type="title"/></p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/><a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" dirty="0"/>
              <a:t>{_esc(text)}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>"""

def subtitle_ph(text):
    """Subtitle in red banner bottom row."""
    return f"""<p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Text Placeholder 1"/>
          <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph type="body" sz="quarter" idx="10"/></p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/><a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="zh-TW" dirty="0">
                <a:ea typeface="{EA}"/>
              </a:rPr>
              <a:t>{_esc(text)}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>"""

# ============================================================
# Slide writer
# ============================================================

_SLIDE_TPL = """<?xml version="1.0" encoding="utf-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      {SUBTITLE_PH}
      {TITLE_PH}
      {CONTENT}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
  <p:transition>
    <p:fade thruBlk="1"/>
  </p:transition>
</p:sld>
"""

def write_slide(n, title, subtitle, content_shapes):
    """
    Write slide{n}.xml to the configured output directory.

    Args:
        n: slide number (1-indexed)
        title: text for red banner top (≤ 28 EN / 14 CN chars)
        subtitle: text for red banner bottom
        content_shapes: list of XML strings from rect/oval/line_shape
    """
    if _OUT_DIR is None:
        raise RuntimeError("Call set_output_dir() first.")
    if len(title) > 50:
        print(f"  ⚠️  Slide {n} title likely too long ({len(title)} chars): {title}")
    xml = _SLIDE_TPL.format(
        TITLE_PH=title_ph(title),
        SUBTITLE_PH=subtitle_ph(subtitle),
        CONTENT="\n".join(content_shapes),
    )
    path = os.path.join(_OUT_DIR, f"slide{n}.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  ✓ Wrote slide{n}.xml — {title[:40]}")

# ============================================================
# High-level layout helpers (optional convenience)
# ============================================================

def page_header(eyebrow_text, lead_title, lead_subtitle_en=None):
    """
    Standard page header used by most layouts: small red eyebrow + lead title + optional English subtitle.
    Returns a list of shape XML strings (append to your shapes list).
    """
    shapes = []
    # Eyebrow (small red label)
    shapes.append(rect(700000, 1100000, 8000000, 350000,
        paragraphs=para(run(eyebrow_text, sz=1100, bold=True, color=RED, lang="en-US"))))
    # Lead title
    shapes.append(rect(700000, 1450000, 10800000, 700000,
        paragraphs=para(run(lead_title, sz=3000, bold=True, color=INK))))
    # English subtitle
    if lead_subtitle_en:
        shapes.append(rect(700000, 2200000, 10800000, 500000,
            paragraphs=para(run(lead_subtitle_en, sz=1400, color=MUTED, italic=True, lang="en-US"))))
    return shapes


def stat_card(x, y, w, big_number, label_cn, caption_en):
    """
    Layout D building block: one large red number + INK hairline + label + caption.
    Returns list of shape XML strings.
    """
    shapes = []
    # Big number
    shapes.append(rect(x, y, w, 1500000,
        paragraphs=para(run(big_number, sz=9600, bold=True, color=RED, lang="en-US"))))
    # Hairline under number
    shapes.append(line_shape(x, y + 1700000, w - 200000, 0, color=INK, w=19050))
    # Label (zh)
    shapes.append(rect(x, y + 1800000, w, 400000,
        paragraphs=para(run(label_cn, sz=1600, bold=True, color=INK))))
    # Caption
    shapes.append(rect(x, y + 2230000, w, 500000,
        paragraphs=para(run(caption_en, sz=1000, color=MUTED, italic=True, lang="en-US"))))
    return shapes


def info_card(x, y, w, h, num, headline, body, accent_top=True):
    """
    Layout C building block: card with optional red top accent + number + headline + body.
    """
    shapes = []
    shapes.append(rect(x, y, w, h, fill=CARD_BG))
    if accent_top:
        shapes.append(rect(x, y, 320000, 50000, fill=RED))
    shapes.append(rect(x + 200000, y + 200000, w - 400000, 500000,
        paragraphs=para(run(num, sz=1400, bold=True, color=RED, lang="en-US"))))
    shapes.append(rect(x + 200000, y + 700000, w - 400000, 600000,
        paragraphs=para(run(headline, sz=1800, bold=True, color=INK))))
    shapes.append(rect(x + 200000, y + 1300000, w - 400000, h - 1500000,
        paragraphs=para(run(body, sz=1100, color=MUTED), line_spc=120000)))
    return shapes
