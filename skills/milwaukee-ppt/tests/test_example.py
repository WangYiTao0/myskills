"""示例文稿测试：examples/demo/deck.md 一次生成成功，覆盖封面、6 个版式和收尾页。

运行：python3 skills/milwaukee-ppt/tests/test_example.py
示例图片已提交在 examples/demo/img/，本测试直接用它们，不重新生成。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from deckcheck import (GENERATOR, LAYOUT_INDEX, SKILL, check, finish, open_pptx,
                       out_of_bounds)

DECK = SKILL / "examples" / "demo" / "deck.md"
BODY_LAYOUTS = ["evidence", "process", "before-after", "stats", "timeline", "image-text"]


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
    check("示例文稿：页数 = 封面 + 6 页 + 收尾", len(slides) == 8, f"实际 {len(slides)}")
    if len(slides) != 8:
        return
    check("示例文稿：封面和收尾用 Title Slide",
          slides[0].slide_layout.name == slides[-1].slide_layout.name == "Title Slide",
          [slides[0].slide_layout.name, slides[-1].slide_layout.name])
    got = [prs.slide_layouts.index(s.slide_layout) for s in slides[1:-1]]
    want = [LAYOUT_INDEX[name] for name in BODY_LAYOUTS]
    check("示例文稿：6 个版式各一页、顺序与文稿一致", got == want, got)
    bad = out_of_bounds(prs, list(enumerate(slides[1:-1], start=2)))
    check("示例文稿：正文页形状不越界", not bad, bad)


if __name__ == "__main__":
    test_demo_deck()
    finish()
