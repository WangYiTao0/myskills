"""示例文稿测试：examples/demo/deck.md 一次生成成功，覆盖封面、14 个正文页（12 种版式，含 Agenda 和 3 张隔断页）和收尾页。
示例是通用模式，按方向 C 画：内容页标题下有 lead（Lead + Lead Accent），不画底部红条，写了 Next 的页页底有 Next 行；
审核只打印 REVIEW OK。

运行：python3 skills/milwaukee-ppt/tests/test_example.py
示例图片已提交在 examples/demo/img/，本测试直接用它们，不重新生成。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from deckcheck import (GENERATOR, LAYOUT_INDEX, SKILL, caption_bar, check, finish, one,
                       open_pptx, out_of_bounds, review)

DECK = SKILL / "examples" / "demo" / "deck.md"
BODY_LAYOUTS = ["agenda", "section", "evidence", "process", "section", "before-after",
                "stats", "stats-side", "table", "section", "timeline", "timeline-phase",
                "team", "image-text"]
# 模板 layout 0 的版式靠形状认：页内标记形状名
NAV = {"agenda", "section"}
NEXT_PAGES = 3                  # 示例里写了 Next: 的页数
MARKERS = {"agenda": "Agenda Number 1", "section": "Section Number", "team": "Member Avatar 1",
           "table": "Data Table"}


def texts(slide, prefix):
    return [sh.text_frame.text for sh in slide.shapes
            if sh.name.startswith(prefix) and sh.has_text_frame]


def test_demo_deck():
    out = Path(tempfile.mkdtemp(prefix="mppt-example-")) / "demo.pptx"
    r = subprocess.run([sys.executable, str(GENERATOR), str(DECK), "-o", str(out)],
                       capture_output=True, text=True)
    check("示例文稿：退出码 0", r.returncode == 0, r.stderr)
    check("示例文稿：没有警告", "警告" not in r.stderr, r.stderr)
    if not out.exists():
        check("示例文稿：生成了 pptx", False, r.stderr)
        return
    prs = open_pptx(out)
    slides = list(prs.slides)
    check("示例文稿：页数 = 封面 + 14 页 + 收尾", len(slides) == 16, f"实际 {len(slides)}")
    if len(slides) != 16:
        return
    check("示例文稿：封面和收尾用 Title Slide",
          slides[0].slide_layout.name == slides[-1].slide_layout.name == "Title Slide",
          [slides[0].slide_layout.name, slides[-1].slide_layout.name])
    body = slides[1:-1]
    got = [prs.slide_layouts.index(s.slide_layout) for s in body]
    want = [LAYOUT_INDEX[name] for name in BODY_LAYOUTS]
    check("示例文稿：版式顺序与文稿一致", got == want, got)
    for name, marker in MARKERS.items():
        idx = [i for i, s in enumerate(body) if any(sh.name == marker for sh in s.shapes)]
        wanted = [i for i, n in enumerate(BODY_LAYOUTS) if n == name]
        check(f"示例文稿：{name} 页位置正确", idx == wanted, idx)
    agenda = texts(body[0], "Agenda Name")
    sections = [texts(s, "Section Name")[0] for s in body if BODY_LAYOUTS[body.index(s)] == "section"]
    check("示例文稿：Agenda 章节名与隔断页一致", agenda == sections and len(sections) == 3,
          [agenda, sections])
    bad = out_of_bounds(prs, list(enumerate(slides[1:-1], start=2)))
    check("示例文稿：正文页形状不越界", not bad, bad)
    content = [s for s, name in zip(body, BODY_LAYOUTS) if name not in NAV]
    check("示例文稿（方向 C）：内容页都有 lead 和左侧竖线",
          all(one(s, "Lead") and one(s, "Lead Accent") for s in content),
          [i for i, s in enumerate(content) if not one(s, "Lead")])
    check("示例文稿（方向 C）：不画底部红条", not any(caption_bar(s) for s in body))
    nexts = [s for s in content if one(s, "Next Line")]
    check(f"示例文稿（方向 C）：{NEXT_PAGES} 页有页底 Next 行和细线",
          len(nexts) == NEXT_PAGES and all(one(s, "Next Rule") for s in nexts), len(nexts))
    navs = [s for s, name in zip(body, BODY_LAYOUTS) if name in NAV]
    check("示例文稿（方向 C）：Agenda 和隔断页不画 lead / Next",
          not any(one(s, "Lead") or one(s, "Next Line") for s in navs))
    r = review(DECK, out)
    check("示例文稿：审核只打印 REVIEW OK", r.stdout.strip() == "REVIEW OK", r.stdout + r.stderr)


if __name__ == "__main__":
    test_demo_deck()
    finish()
