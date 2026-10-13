#!/usr/bin/env python3
"""md 文稿 → Milwaukee 格式 pptx。

用法:
    python3 generate_ppt.py <文稿.md>              # 输出名按 frontmatter 推导
    python3 generate_ppt.py <文稿.md> -o out.pptx  # 指定输出

三层：mdparse（md → 文档模型）、layouts（每种版式一个渲染函数）、
本文件（装配：封面 → 各页 → 收尾，并清理模板样例页）。
"""
import argparse
import os
import sys

from pptx import Presentation
from pptx.oxml.ns import qn

import layouts
import mdparse
from mdparse import DeckError

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "MS_Template.pptx")

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

LAYOUT_TITLE_SLIDE = 1


def delete_template_slides(prs):
    """删除模板自带样例页，同时断开关系，避免保存时部件名冲突。"""
    sld_id_lst = prs.slides._sldIdLst
    for sld_id in list(sld_id_lst):
        rid = sld_id.get(qn("r:id"))
        if rid:
            prs.part.drop_rel(rid)
        sld_id_lst.remove(sld_id)


def add_cover(prs, meta):
    year, mon = meta["month"].split("-")
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TITLE_SLIDE])
    slide.placeholders[0].text = f"{MONTHS[int(mon)]}. {year} Working Summary"
    date = meta.get("date", "").strip()
    slide.placeholders[1].text = f"{date}   {meta['author']}".strip()


def add_closing(prs, text):
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TITLE_SLIDE])
    slide.placeholders[0].text = text
    slide.placeholders[1].text = ""


def build(doc):
    prs = Presentation(TEMPLATE)
    delete_template_slides(prs)
    add_cover(prs, doc.meta)
    ctx = layouts.Context(source_dir=doc.source_dir,
                          year=doc.meta["month"].split("-")[0])
    for page in doc.pages:
        layouts.render(prs, page, ctx)
    add_closing(prs, "Thank You")
    return prs


def default_output(doc):
    year, mon = doc.meta["month"].split("-")
    name = (f"Monthly Working Summary_{doc.meta['author']}_"
            f"{MONTHS[int(mon)]}_{year}.pptx")
    return os.path.join(doc.source_dir, name)


def main(argv=None):
    ap = argparse.ArgumentParser(description="md 文稿 → Milwaukee 格式 pptx")
    ap.add_argument("md", help="输入 markdown 文稿")
    ap.add_argument("-o", "--output", help="输出 pptx 路径")
    args = ap.parse_args(argv)
    try:
        doc = mdparse.parse(args.md)
        prs = build(doc)
        out = args.output or default_output(doc)
        if os.path.isdir(out):
            raise DeckError(f"输出路径是目录, 请指定文件名: {out}")
        try:
            prs.save(out)
        except OSError as e:
            raise DeckError(f"保存失败 ({out}): {e}")
    except DeckError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    print(f"已生成: {out}  ({len(doc.pages)} 页正文)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
