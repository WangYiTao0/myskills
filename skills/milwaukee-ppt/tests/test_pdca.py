"""项目汇报模式：frontmatter `report: project` + 各页 `PDCA:` → 正文区右上角的 PDCA 图标。

运行：python3 skills/milwaukee-ppt/tests/test_pdca.py
只走“md 进、pptx 出”：写文稿 → 调生成器 → 看 pptx 里的图片形状。文稿内容全部虚构。
"""
from deckcheck import (BANNER_BOTTOM, EMU, SKILL, check, deck_error, finish, generate, one,
                       pictures, shapes_named, tag_shape)

PNG = {letter: (SKILL / "assets" / "pdca" / f"{letter}_icon.png").read_bytes()
       for letter in "PDCA"}
CONTENT_RIGHT = int(12.76 * EMU)     # 正文区右缘（IMG_LEFT + IMG_W）


def deck(pages, report="report: project"):
    head = "---\ntitle: 工具借还扫码登记 项目汇报\n" + (report + "\n" if report else "") + "---\n\n"
    return head + "\n".join(pages)


EVIDENCE = """\
# 项目背景 / BACKGROUND
## 纸质登记本约三成借出记录缺归还
{extra}
抽查 3 个月的登记本，约三成借出记录没有归还登记
"""


def page(extra):
    return EVIDENCE.format(extra=extra)


def letter_of(pic):
    blob = pic.image.blob
    return next((k for k, v in PNG.items() if v == blob), None)


def test_single_icon_top_right():
    r = generate(deck([page("PDCA: P")]))
    check("单个 PDCA：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    slide = r.slides[1]
    icon = one(slide, "PDCA Icon 1")
    check("单个 PDCA：有一个「PDCA Icon 1」", icon is not None, [sh.name for sh in slide.shapes])
    if icon is None:
        return
    check("单个 PDCA：插的是 P 的 PNG 资产", letter_of(icon) == "P")
    check("单个 PDCA：图标在 banner 以下", icon.top >= BANNER_BOTTOM, icon.top)
    check("单个 PDCA：右缘贴正文区右缘", abs(icon.left + icon.width - CONTENT_RIGHT) <= EMU // 100,
          (icon.left + icon.width, CONTENT_RIGHT))
    check("单个 PDCA：正方形", icon.width == icon.height, (icon.width, icon.height))


def test_page_without_pdca_has_no_icon():
    r = generate(deck([page("PDCA: D"), page("")]))
    check("不写 PDCA 的页：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    check("不写 PDCA 的页：没有图标", not shapes_named(r.slides[2], "PDCA Icon"),
          [sh.name for sh in r.slides[2].shapes])
    check("不写 PDCA 的页：也没有别的图片", not pictures(r.slides[2]))


def test_pdca_without_project_mode_errors():
    r = generate(deck([page("PDCA: D")], report=""))
    check("没写 report: project 却写 PDCA：报错带页标题",
          deck_error(r, "项目背景 / BACKGROUND", "report: project"), r.stderr)
    r = generate(deck([page("")], report="report: monthly"))
    check("report 写了 project 以外的值：报错", r.rc != 0 and "report" in r.stderr, r.stderr)


def test_wrong_letters_error():
    for bad in ("X", "D/X", "DC", "D/", "D/D"):
        r = generate(deck([page(f"PDCA: {bad}")]))
        check(f"PDCA: {bad}：报错带页标题", deck_error(r, "项目背景 / BACKGROUND", "PDCA"), r.stderr)


def test_combined_letters_left_to_right():
    r = generate(deck([page("PDCA: d/c")]))
    check("组合 D/C（小写也认）：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    icons = shapes_named(r.slides[1], "PDCA Icon")
    check("组合 D/C：两个图标，按文稿顺序 D 在左、C 在右",
          [letter_of(sh) for sh in icons] == ["D", "C"] and icons[0].left < icons[1].left,
          [(letter_of(sh), sh.left) for sh in icons])
    if len(icons) != 2:
        return
    check("组合 D/C：同一上沿、同样大小",
          icons[0].top == icons[1].top
          and (icons[0].width, icons[0].height) == (icons[1].width, icons[1].height))
    check("组合 D/C：不互压，右边那个贴正文区右缘",
          icons[0].left + icons[0].width < icons[1].left
          and abs(icons[1].left + icons[1].width - CONTENT_RIGHT) <= EMU // 100)


def test_tag_moves_left_of_icons():
    r = generate(deck([page("PDCA: D/C\nTag: Aug")]))
    check("PDCA + Tag：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    slide = r.slides[1]
    tag, icons = tag_shape(slide), shapes_named(slide, "PDCA Icon")
    check("PDCA + Tag：两者都在", tag is not None and len(icons) == 2)
    if tag is None or len(icons) != 2:
        return
    check("PDCA + Tag：月份标识整个在最左图标左侧（右对齐的字不压图标）",
          tag.left + tag.width < icons[0].left, (tag.left + tag.width, icons[0].left))
    tag_mid = tag.top + int(11 / 72 * 1.2 * EMU) // 2     # 11pt 一行的中线
    icon_mid = icons[0].top + icons[0].height // 2
    check("PDCA + Tag：月份标识文字和图标纵向居中对齐（差不到 0.02\"）",
          abs(tag_mid - icon_mid) <= EMU // 50, (tag_mid / EMU, icon_mid / EMU))


if __name__ == "__main__":
    test_single_icon_top_right()
    test_page_without_pdca_has_no_icon()
    test_pdca_without_project_mode_errors()
    test_wrong_letters_error()
    test_combined_letters_left_to_right()
    test_tag_moves_left_of_icons()
    finish()
