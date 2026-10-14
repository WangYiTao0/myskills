#!/usr/bin/env python3
"""PROTOTYPE，用完即弃。不是正式代码，不要 import、不要接进生成器或测试。

回答的问题：生成的汇报 PPT「很普通」，三个结构不同的视觉方向哪个更好？
  0 = 基线（正式生成器原样输出）
  A = 保留红条，内容撑满
  B = 薄结论条（红条压成细条），正文吃满释放的高度
  C = 结论前置（lead），不画底部红条，加视觉锚点（编号圆 + 连接线、首字头像）

做法：先用 scripts/generate_ppt.py 生成基线，再按形状名删掉正文形状、用 python-pptx
按方向重画（借用 layouts/common.py 的小工具，只 import 不改）。最后 soffice + pdftoppm
转 PNG（-r 80），每个方向拼一张 2×3 总览图，并对 A/B/C 各跑一次 review_deck.py。

用法（仓库根目录或任意目录）：
    python3 skills/milwaukee-ppt/prototypes/visual-directions-PROTOTYPE/make_variants.py
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "..", "scripts"))
sys.path.insert(0, SCRIPTS)

from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

import mdparse  # noqa: E402
from layouts import common as C  # noqa: E402
from layouts.common import (BRAND_RED, INK, MUTED, add_line, add_number, add_run,  # noqa: E402
                            add_shape, add_textbox, caption_lines)

DECK = os.path.join(HERE, "deck.md")
OUT = os.path.join(HERE, "out")
VARIANTS = ["0", "A", "B", "C"]

BODY = "333333"          # 卡片说明：近黑（比 MUTED 深）
LIGHT = "F5F5F5"
HAIR = "E5E5E5"
GHOST = "EDEDED"         # A/B 流程卡右下角大编号水印
L, W = 0.56, 12.2        # 正文区左缘、宽（英寸）
R = L + W

# 各方向：正文区上下沿（英寸）和字号
CFG = {
    "A": dict(top=1.30, bottom=5.65, side_num=60, stat_num=72, table_pt=18),
    "B": dict(top=1.30, bottom=6.38, side_num=72, stat_num=88, table_pt=20),
    "C": dict(top=2.05, bottom=6.95, side_num=72, stat_num=88, table_pt=18),
}
NOTES = {
    "0": "基线：正式生成器原样输出（月报红条 1.2\"，卡片 14pt 灰字，内容浮在上半）",
    "A": "A 保留红条，内容撑满：红条不动；卡片撑满可用高度，说明 18pt 近黑，流程加箭头，表格放大并垂直居中",
    "B": "B 薄结论条：红条压成 0.42\" 细条，释放约 0.7\" 给正文；大数字 72/88pt；其余同 A",
    "C": "C 结论前置：结论移到标题下作 lead（黑粗字 + 红短竖线），底部不画红条；流程大编号圆 + 连接线，团队首字头像",
}


def I(v):  # noqa: E743  英寸 → EMU
    return Inches(v)


def text(slide, name, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, wrap=True):
    """runs = [(文字, pt, bold, color)]，一段。"""
    tf = add_textbox(slide, name, I(x), I(y), I(w), I(h), anchor, wrap)
    p = tf.paragraphs[0]
    p.alignment = align
    for t, pt, b, c in runs:
        add_run(p, t, pt, b, c)
    return tf


def clear(slide):
    """删掉正文区所有非占位框形状（标题占位框 idx 0 / 10 保留）。"""
    for sh in list(slide.shapes):
        if not sh.is_placeholder:
            C.remove_shape(sh)


def shape_names(slide):
    return {sh.name for sh in slide.shapes}


# ---- 结论的三种放法 -------------------------------------------------------------

def bar_full(slide, page):          # A：月报红条原样
    C.add_caption_bar(slide, page)


def bar_thin(slide, page):          # B：0.42" 细红条，一行白字（结论 ｜ Next）
    lines = caption_lines(page)
    if not lines:
        return
    sp = add_shape(slide, MSO_SHAPE.RECTANGLE, "Caption Bar", 155575, I(6.62), 11874874, I(0.42),
                   BRAND_RED)
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = I(0.2), I(0.2), 0, 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    for k, line in enumerate(lines):
        if k:
            add_run(p, "　｜　", 14, False, "FFFFFF")
        add_run(p, line, 14, k == 0, "FFFFFF")


def lead(slide, page):              # C：标题下的 lead + 红短竖线；Next 放页底一行
    conclusion = " ".join(page.conclusion).strip()
    if conclusion:
        add_shape(slide, MSO_SHAPE.RECTANGLE, "Lead Accent", I(L), I(1.36), I(0.08), I(0.44),
                  BRAND_RED)
        text(slide, "Lead", L + 0.24, 1.3, W - 0.24, 0.56, [(conclusion, 22, True, INK)],
             anchor=MSO_ANCHOR.MIDDLE, wrap=False)
    if page.next:
        add_line(slide, "Next Rule", I(L), I(6.5), I(R), I(6.5), HAIR, 0.75)
        text(slide, "Next Line", L, 6.58, W, 0.36,
             [(f"{page.next_label}：", 16, True, INK), (page.next, 16, True, INK)],
             anchor=MSO_ANCHOR.MIDDLE)


# ---- 各版式重画 -----------------------------------------------------------------

def draw_stats_side(slide, page, v, cfg):
    f = page.fields
    top, bottom = cfg["top"], cfg["bottom"]
    items, gap = f["items"], 0.25
    ch = (bottom - top - gap * (len(items) - 1)) / len(items)
    for n, it in enumerate(items, start=1):
        y = top + (n - 1) * (ch + gap)
        add_shape(slide, MSO_SHAPE.RECTANGLE, f"Side Card {n}", I(L), I(y), I(6.0), I(ch), LIGHT)
        if it["key"]:
            add_shape(slide, MSO_SHAPE.RECTANGLE, f"Side Accent {n}", I(L), I(y), I(0.08), I(ch),
                      BRAND_RED)
        tf = add_textbox(slide, f"Side Number {n}", I(L + 0.3), I(y), I(2.9), I(ch),
                         MSO_ANCHOR.MIDDLE, wrap=False)
        add_number(tf.paragraphs[0], it["value"], cfg["side_num"],
                   BRAND_RED if it["key"] else INK, unit_pt=28)
        tf = add_textbox(slide, f"Side Text {n}", I(L + 3.3), I(y), I(2.5), I(ch),
                         MSO_ANCHOR.MIDDLE)
        add_run(tf.paragraphs[0], it["label"], 20, True, INK)
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        add_run(p, it["note"], 16, False, BODY)
    x, w = L + 6.5, W - 6.5
    text(slide, "Side Conclusion Title", x, top, w, 0.4, [(f["heading"], 20, True, INK)])
    add_shape(slide, MSO_SHAPE.RECTANGLE, "Side Conclusion Rule", I(x), I(top + 0.52), I(w),
              I(0.01), HAIR)
    tf = add_textbox(slide, "Side Points", I(x), I(top + 0.72), I(w), I(bottom - top - 1.4))
    for k, pt_text in enumerate(f["points"], start=1):
        p = tf.paragraphs[0] if k == 1 else tf.add_paragraph()
        if k > 1:
            p.space_before = Pt(16)
        add_run(p, f"{k}   ", 18, True, MUTED)
        add_run(p, pt_text, 18, False, INK)
    if f.get("source"):
        text(slide, "Stat Source", x, bottom - 0.55, w, 0.55, [(f["source"], 12, False, MUTED)],
             anchor=MSO_ANCHOR.BOTTOM)


def draw_process_cards(slide, page, v, cfg):
    """A / B：白卡撑满高度，顶部黑细条，右下角大编号水印，卡间灰色箭头。"""
    steps = page.fields["steps"]
    top, bottom, gap = cfg["top"] + 0.1, cfg["bottom"], 0.5
    n_ = len(steps)
    cw = (W - gap * (n_ - 1)) / n_
    h = bottom - top
    for n, (name, desc) in enumerate(steps, start=1):
        x = L + (n - 1) * (cw + gap)
        add_shape(slide, MSO_SHAPE.RECTANGLE, f"Process Card {n}", I(x), I(top), I(cw), I(h),
                  "FFFFFF", HAIR, 1)
        add_shape(slide, MSO_SHAPE.RECTANGLE, f"Process Strip {n}", I(x), I(top), I(cw), I(0.08),
                  INK)
        text(slide, f"Process Mark {n}", x + cw - 1.9, top + h - 1.75, 1.75, 1.6,
             [(f"{n:02d}", 96, True, GHOST)], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.BOTTOM,
             wrap=False)
        tf = add_textbox(slide, f"Process Text {n}", I(x + 0.3), I(top + 0.45), I(cw - 0.6),
                         I(h - 2.2))
        add_run(tf.paragraphs[0], f"STEP {n}", 14, True, MUTED)
        p = tf.add_paragraph()
        p.space_before = Pt(6)
        add_run(p, name, 24, True, INK)
        p = tf.add_paragraph()
        p.space_before = Pt(12)
        add_run(p, desc, 18, False, BODY)
        if n < n_:
            add_shape(slide, MSO_SHAPE.CHEVRON, f"Process Arrow {n}", I(x + cw + 0.14),
                      I(top + h / 2 - 0.25), I(0.22), I(0.5), "BFBFBF")


def draw_process_circles(slide, page, v, cfg):
    """C：大编号圆 + 连接线，无卡片；标题与说明居中在圆下。"""
    steps = page.fields["steps"]
    n_ = len(steps)
    col = W / n_
    d = 1.1
    group_h = d + 0.35 + 0.5 + 0.15 + 0.7
    cy = cfg["top"] + (cfg["bottom"] - cfg["top"] - group_h) / 2 - 0.1 + d / 2
    for n in range(1, n_):
        x1 = L + (n - 0.5) * col + d / 2 + 0.12
        x2 = L + (n + 0.5) * col - d / 2 - 0.12
        add_line(slide, f"Process Line {n}", I(x1), I(cy), I(x2), I(cy), "BFBFBF", 2.25)
    for n, (name, desc) in enumerate(steps, start=1):
        cx = L + (n - 0.5) * col
        c = add_shape(slide, MSO_SHAPE.OVAL, f"Process Number {n}", I(cx - d / 2), I(cy - d / 2),
                      I(d), I(d), INK)
        tf = c.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        add_run(tf.paragraphs[0], str(n), 40, True, "FFFFFF")
        y = cy + d / 2 + 0.35
        text(slide, f"Process Title {n}", cx - col / 2 + 0.15, y, col - 0.3, 0.5,
             [(name, 24, True, INK)], align=PP_ALIGN.CENTER)
        text(slide, f"Process Desc {n}", cx - col / 2 + 0.2, y + 0.62, col - 0.4, 0.75,
             [(desc, 18, False, BODY)], align=PP_ALIGN.CENTER)


def adjust_timeline(slide, page, v, cfg):
    """时间线本身已居中、有状态色：只放大字号，并按正文区整体平移。"""
    bump = {12: 14, 14: 16, 16: 20, 18: 22}
    legend = [sh for sh in slide.shapes if sh.name.startswith("Legend")]
    body = [sh for sh in slide.shapes if not sh.is_placeholder and sh.name != "Caption Bar"
            and sh not in legend]
    for sh in body:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size.pt in bump:
                        r.font.size = Pt(bump[r.font.size.pt])
    if v == "C":                     # 图例让到 lead 下方
        for sh in legend:
            sh.top += I(cfg["top"] - 1.3)
    top = min(sh.top for sh in body) / 914400
    bot = max(sh.top + sh.height for sh in body) / 914400
    lo = cfg["top"] + (0.75 if v == "C" else 0.35)
    dy = max(0, lo + (cfg["bottom"] - lo - (bot - top)) / 2 - top)
    for sh in body:
        sh.top += I(dy)


def draw_stats(slide, page, v, cfg):
    f = page.fields
    items, gap = f["items"], 0.45
    cw = (W - gap * (len(items) - 1)) / len(items)
    top, bottom = cfg["top"], cfg["bottom"]
    num_pt = cfg["stat_num"]
    num_h = num_pt * 1.2 / 72
    src_h = 0.3
    for n, it in enumerate(items, start=1):
        x = L + (n - 1) * (cw + gap)
        color = BRAND_RED if it["key"] else INK
        add_shape(slide, MSO_SHAPE.RECTANGLE, f"Stat Rule {n}", I(x), I(top), I(cw), I(0.08), color)
        y = top + 0.28
        text(slide, f"Stat Label {n}", x, y, cw, 0.36, [(it["label"], 20, True, INK)])
        y += 0.4
        tf = add_textbox(slide, f"Stat Number {n}", I(x), I(y), I(cw), I(num_h), wrap=False)
        add_number(tf.paragraphs[0], it["value"], num_pt, color, unit_pt=28)
        y += num_h + 0.05
        text(slide, f"Stat Note {n}", x, y, cw, 0.32, [(it["note"], 16, False, MUTED)])
        y += 0.32 + 0.25
        add_line(slide, f"Stat Divider {n}", I(x), I(y), I(x + cw), I(y), HAIR, 0.75)
        y += 0.22
        tf = add_textbox(slide, f"Stat Points {n}", I(x), I(y), I(cw),
                         I(bottom - src_h - 0.15 - y))
        for k, pt_text in enumerate(it.get("points", [])):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            if k:
                p.space_before = Pt(10)
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(int(Pt(18 * 1.4))))
            pPr.set("indent", str(-int(Pt(18 * 1.4))))
            pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
            pPr.append(pPr.makeelement(qn("a:buChar"), {"char": "•"}))
            add_run(p, pt_text, 16, False, BODY)
    if f.get("source"):
        text(slide, "Stat Source", L, bottom - src_h, W, src_h, [(f["source"], 12, False, MUTED)],
             anchor=MSO_ANCHOR.BOTTOM)


def draw_team_cards(slide, page, v, cfg):
    """A / B：卡片加大、字号加大，整体在正文区垂直居中。"""
    members = page.fields["members"]
    gap = 0.3
    cw = (W - gap * 3) / 4
    h = 3.0 if v == "A" else 3.4
    top = cfg["top"] + (cfg["bottom"] - cfg["top"] - h) / 2
    pad = 0.35
    for n, mb in enumerate(members, start=1):
        x = L + (n - 1) * (cw + gap)
        add_shape(slide, MSO_SHAPE.RECTANGLE, f"Member Card {n}", I(x), I(top), I(cw), I(h), LIGHT)
        add_shape(slide, MSO_SHAPE.RECTANGLE, f"Member Strip {n}", I(x), I(top), I(cw), I(0.08), INK)
        y = top + pad + 0.05
        text(slide, f"Member Name {n}", x + pad, y, cw - 2 * pad, 0.5, [(mb["name"], 28, True, INK)])
        y += 0.55
        text(slide, f"Member Role {n}", x + pad, y, cw - 2 * pad, 0.34, [(mb["role"], 18, False, MUTED)])
        y += 0.55
        add_line(slide, f"Member Rule {n}", I(x + pad), I(y), I(x + cw - pad), I(y), "BFBFBF", 0.75)
        y += 0.22
        text(slide, f"Member Duty {n}", x + pad, y, cw - 2 * pad, top + h - pad - y,
             [(mb["duty"], 18, False, INK)])


def draw_team_avatars(slide, page, v, cfg):
    """C：姓名首字圆形头像 + 居中文字，不画卡片。"""
    members = page.fields["members"]
    col = W / len(members)
    d = 1.4
    group_h = d + 0.25 + 0.5 + 0.38 + 0.25 + 0.7
    top = cfg["top"] + (cfg["bottom"] - cfg["top"] - group_h) / 2 - 0.1
    for n, mb in enumerate(members, start=1):
        cx = L + (n - 0.5) * col
        c = add_shape(slide, MSO_SHAPE.OVAL, f"Member Avatar {n}", I(cx - d / 2), I(top), I(d), I(d),
                      INK)
        tf = c.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        add_run(tf.paragraphs[0], mb["name"][0], 44, True, "FFFFFF")
        y = top + d + 0.25
        w = col - 0.4
        text(slide, f"Member Name {n}", cx - w / 2, y, w, 0.5, [(mb["name"], 26, True, INK)],
             align=PP_ALIGN.CENTER)
        y += 0.52
        text(slide, f"Member Role {n}", cx - w / 2, y, w, 0.34, [(mb["role"], 18, False, MUTED)],
             align=PP_ALIGN.CENTER)
        y += 0.48
        add_line(slide, f"Member Rule {n}", I(cx - 0.35), I(y), I(cx + 0.35), I(y), "BFBFBF", 1)
        y += 0.2
        text(slide, f"Member Duty {n}", cx - w / 2, y, w, 0.7, [(mb["duty"], 18, False, INK)],
             align=PP_ALIGN.CENTER)


def adjust_table(slide, page, v, cfg):
    """放大字号、按字号重算行高，整张表在正文区垂直居中；红竖条跟着 ! 行走。"""
    pt = cfg["table_pt"]
    if v == "C" and page.next:       # 页底留给 Next 行
        cfg = dict(cfg, bottom=6.4)
    row_h = I(pt * 1.25 / 72 + 2 * 0.09)
    frame = next(sh for sh in slide.shapes if sh.name == "Data Table")
    tbl = frame.table
    for r, row in enumerate(tbl.rows):
        row.height = row_h
        for cell in row.cells:
            cell.margin_top = cell.margin_bottom = I(0.09)
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(pt)
    total = row_h * len(tbl.rows)
    frame.height = total
    frame.top = int(I(cfg["top"]) + (I(cfg["bottom"]) - I(cfg["top"]) - total) / 2)
    key = page.fields.get("key")
    for sh in slide.shapes:
        if sh.name == "Table Key Bar" and key is not None:
            sh.top = frame.top + row_h * (key + 1)
            sh.height = row_h
            sh.width = I(0.08)


# ---- 装配 -----------------------------------------------------------------------

def build_variant(base, doc, v):
    prs = Presentation(base)
    cfg = CFG[v]
    pages = [p for p in doc.pages]
    for slide, page in zip(list(prs.slides)[1:-1], pages):
        lay = page.layout
        if lay in ("timeline", "table"):
            for sh in list(slide.shapes):
                if sh.name == "Caption Bar":
                    C.remove_shape(sh)
            (adjust_timeline if lay == "timeline" else adjust_table)(slide, page, v, cfg)
        else:
            clear(slide)
            if lay == "stats-side":
                draw_stats_side(slide, page, v, cfg)
            elif lay == "process":
                (draw_process_circles if v == "C" else draw_process_cards)(slide, page, v, cfg)
            elif lay == "stats":
                draw_stats(slide, page, v, cfg)
            elif lay == "team":
                (draw_team_avatars if v == "C" else draw_team_cards)(slide, page, v, cfg)
        {"A": bar_full, "B": bar_thin, "C": lead}[v](slide, page)
    path = os.path.join(OUT, f"deck-{v}.pptx")
    prs.save(path)
    return path


def to_png(pptx, v):
    dst = os.path.join(OUT, v)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, pptx],
                       check=True, capture_output=True)
        pdf = os.path.join(tmp, os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
        subprocess.run(["pdftoppm", "-r", "80", "-png", pdf, os.path.join(dst, "slide")], check=True)
    for f in glob.glob(os.path.join(dst, "slide-*.png")):    # slide-01 → slide-1
        n = int(f.rsplit("-", 1)[1].split(".")[0])
        os.rename(f, os.path.join(dst, f"slide-{n}.png"))
    ims = [Image.open(os.path.join(dst, f"slide-{n}.png")) for n in range(2, 8)]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * 2 + 10, h * 3 + 20), "white")
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % 2) * (w + 10), (k // 2) * (h + 10)))
    sheet.save(os.path.join(OUT, f"overview-{v}.png"))


def review(pptx, v):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "review_deck.py"), DECK, pptx],
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    with open(os.path.join(OUT, f"review-{v}.txt"), "w") as fh:
        fh.write(out + "\n")
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, "deck-0.pptx")
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "generate_ppt.py"), DECK, "-o", base],
                   check=True)
    doc = mdparse.parse(DECK)
    paths = {"0": base}
    for v in "ABC":
        paths[v] = build_variant(base, doc, v)
    for v in VARIANTS:
        to_png(paths[v], v)
        print(f"== {v}: {NOTES[v]}")
        print(review(paths[v], v))
    print(f"输出: {OUT}")


if __name__ == "__main__":
    main()
