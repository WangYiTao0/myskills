"""Milwaukee Tool brand deck builder (python-pptx wrapper).

Usage:
    from build_ppt import MilwaukeeDeck

    deck = MilwaukeeDeck()
    s1 = deck.add_slide("PRODUCT OVERVIEW", "M18 FUEL Series")
    s1.add_paragraphs([
        ("产品定位", {"bold": True, "size": 18}),
        ("面向专业用户的高扭矩冲击钻系列。", {"size": 14}),
    ])

    s2 = deck.add_slide("KEY SPECS", "Performance")
    s2.add_table(
        [["Model", "Torque", "RPM"],
         ["M18-1", "1000 Nm", "0-2000"],
         ["M18-2", "1200 Nm", "0-2100"]],
        header=True,
    )
    s2.add_image("/path/to/product.png", left_cm=2, top_cm=10, width_cm=10)

    deck.save("output.pptx")

Coordinates are EMU under the hood. Helpers accept cm via *_cm kwargs.
1 cm = 360000 EMU. Slide is 33.87 cm x 19.05 cm (16:9).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pptx import Presentation
from pptx.util import Cm, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from lxml import etree


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "template.pptx"

# Brand
MILWAUKEE_RED = RGBColor(0xDB, 0x02, 0x1D)
TEXT_DARK = RGBColor(0x33, 0x33, 0x33)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# Font fallback chain. python-pptx font.name sets latin typeface only;
# for east-asian (zh) we set <a:ea> via direct rPr edit.
LATIN_FONT = "Calibri"
EA_FONT_PRIMARY = "Microsoft JhengHei"  # zh-TW preferred
EA_FONT_FALLBACKS = ["PingFang TC", "Microsoft YaHei", "Heiti TC", "SimHei"]

# Content area bounds (inside the white area, below red banner, above footer)
CONTENT_LEFT_CM = 1.0
CONTENT_TOP_CM = 2.5
CONTENT_RIGHT_CM = 32.87  # = slide_width 33.87 - 1.0
CONTENT_BOTTOM_CM = 17.5  # leave room for footer
CONTENT_WIDTH_CM = CONTENT_RIGHT_CM - CONTENT_LEFT_CM
CONTENT_HEIGHT_CM = CONTENT_BOTTOM_CM - CONTENT_TOP_CM


def _set_run_font(run, *, name=None, size=None, bold=None, color=None, ea=None):
    """Set run formatting including east-asian typeface (which python-pptx
    doesn't expose directly)."""
    if name is not None:
        run.font.name = name
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    if ea is not None:
        rPr = run._r.get_or_add_rPr()
        for tag in ("a:ea",):
            existing = rPr.find(qn(tag))
            if existing is not None:
                rPr.remove(existing)
        ea_el = etree.SubElement(rPr, qn("a:ea"))
        ea_el.set("typeface", ea)


class _Slide:
    def __init__(self, slide):
        self._slide = slide
        self._next_top_cm = CONTENT_TOP_CM

    # ---- placeholders ----
    def set_title(self, text: str):
        ph = self._slide.placeholders[0]
        ph.text_frame.text = text
        return self

    def set_subtitle(self, text: str):
        ph = self._slide.placeholders[10]
        ph.text_frame.text = text
        return self

    # ---- content helpers ----
    def add_paragraphs(
        self,
        items: Iterable[tuple[str, dict]],
        *,
        left_cm: float | None = None,
        top_cm: float | None = None,
        width_cm: float | None = None,
        height_cm: float | None = None,
    ):
        """Add a textbox of paragraphs.
        items: iterable of (text, style_dict). style_dict keys:
          size (pt), bold, color (RGBColor), align ('l'|'c'|'r'),
          bullet (bool), ea (str, east-asian typeface).
        """
        left = Cm(left_cm if left_cm is not None else CONTENT_LEFT_CM)
        top = Cm(top_cm if top_cm is not None else self._next_top_cm)
        width = Cm(width_cm if width_cm is not None else CONTENT_WIDTH_CM)
        height = Cm(height_cm if height_cm is not None else 5.0)

        tb = self._slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True

        for i, (text, style) in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            align = style.get("align")
            if align:
                p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            if style.get("bullet"):
                _apply_bullet(p)
            run = p.add_run()
            run.text = text
            _set_run_font(
                run,
                name=style.get("name", LATIN_FONT),
                size=style.get("size", 14),
                bold=style.get("bold"),
                color=style.get("color", TEXT_DARK),
                ea=style.get("ea", EA_FONT_PRIMARY),
            )

        self._next_top_cm = (top + height) / 360000 + 0.3
        return tb

    def add_bullets(
        self,
        bullets: list[str],
        *,
        size: int = 14,
        **box_kwargs,
    ):
        return self.add_paragraphs(
            [(b, {"size": size, "bullet": True}) for b in bullets],
            **box_kwargs,
        )

    def add_table(
        self,
        rows: list[list[str]],
        *,
        header: bool = True,
        left_cm: float | None = None,
        top_cm: float | None = None,
        width_cm: float | None = None,
        height_cm: float | None = None,
    ):
        n_rows = len(rows)
        n_cols = max(len(r) for r in rows)
        left = Cm(left_cm if left_cm is not None else CONTENT_LEFT_CM)
        top = Cm(top_cm if top_cm is not None else self._next_top_cm)
        width = Cm(width_cm if width_cm is not None else CONTENT_WIDTH_CM)
        height = Cm(height_cm if height_cm is not None else 0.8 * n_rows + 0.4)

        gf = self._slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
        table = gf.table
        for r, row in enumerate(rows):
            for c in range(n_cols):
                cell = table.cell(r, c)
                cell.text = row[c] if c < len(row) else ""
                p = cell.text_frame.paragraphs[0]
                run = p.runs[0]
                if header and r == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = MILWAUKEE_RED
                    _set_run_font(run, name=LATIN_FONT, size=12, bold=True, color=WHITE, ea=EA_FONT_PRIMARY)
                else:
                    _set_run_font(run, name=LATIN_FONT, size=11, color=TEXT_DARK, ea=EA_FONT_PRIMARY)

        self._next_top_cm = (top + height) / 360000 + 0.3
        return gf

    def add_image(
        self,
        path: str | Path,
        *,
        left_cm: float | None = None,
        top_cm: float | None = None,
        width_cm: float | None = None,
        height_cm: float | None = None,
    ):
        kwargs = {}
        if width_cm is not None:
            kwargs["width"] = Cm(width_cm)
        if height_cm is not None:
            kwargs["height"] = Cm(height_cm)
        left = Cm(left_cm if left_cm is not None else CONTENT_LEFT_CM)
        top = Cm(top_cm if top_cm is not None else self._next_top_cm)
        pic = self._slide.shapes.add_picture(str(path), left, top, **kwargs)
        self._next_top_cm = (pic.top + pic.height) / 360000 + 0.3
        return pic


def _apply_bullet(paragraph):
    """Add a • bullet to a paragraph via direct pPr edit (python-pptx
    doesn't expose buChar)."""
    pPr = paragraph._pPr
    if pPr is None:
        pPr = paragraph._p.get_or_add_pPr()
    pPr.set("marL", "342900")
    pPr.set("indent", "-342900")
    for tag in ("a:buChar", "a:buAutoNum", "a:buNone"):
        existing = pPr.find(qn(tag))
        if existing is not None:
            pPr.remove(existing)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", "•")


class MilwaukeeDeck:
    def __init__(self, template_path: str | Path = DEFAULT_TEMPLATE):
        template_path = Path(template_path)
        if not template_path.exists():
            raise FileNotFoundError(f"template not found: {template_path}")
        self._prs = Presentation(str(template_path))
        # Reuse the bundled slide1 as the first page; subsequent pages added
        # via the blank layout (which carries the same title/body placeholders).
        self._first_used = False
        self._layout = self._prs.slide_layouts[0]

    def add_slide(self, title: str, subtitle: str = "") -> _Slide:
        if not self._first_used:
            slide = self._prs.slides[0]
            self._first_used = True
        else:
            slide = self._prs.slides.add_slide(self._layout)
        wrapper = _Slide(slide)
        wrapper.set_title(title)
        if subtitle:
            wrapper.set_subtitle(subtitle)
        return wrapper

    def save(self, path: str | Path) -> Path:
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._prs.save(str(path))
        return path
