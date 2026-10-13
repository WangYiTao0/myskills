"""evidence 版式（默认版式）测试：图 + 底部红条。

运行：python3 skills/milwaukee-ppt/tests/test_evidence.py
月报格式的逐项回归（红条样式、Tag、多图）在 test_generate.py 的 test_monthly_regression。
"""
from deckcheck import (LAYOUT_INDEX, caption_bar, check, finish, generate,
                       out_of_bounds, placeholder, red_elements, warnings)

MD = """
---
title: Mock Deck
---

# Default Page
![](img/a.png)
Default conclusion.

# Explicit Page
Layout: Evidence
![](img/a.png)
![](img/b.png)
Explicit conclusion.
"""
IMAGES = {"img/a.png": (1600, 900), "img/b.png": ((800, 800), (60, 60, 60))}


def test_explicit_and_default():
    r = generate(MD, images=IMAGES)
    check("evidence：退出码 0", r.rc == 0, r.stderr)
    body = r.slides[1:]
    check("evidence：不写 Layout 与写 Layout: Evidence（大小写不敏感）都用 layout 0",
          len(body) == 2 and all(
              s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX["evidence"]]
              for s in body),
          [s.slide_layout.name for s in body])
    check("evidence：主标题在 idx 0",
          [placeholder(s, 0).text for s in body] == ["Default Page", "Explicit Page"],
          [placeholder(s, 0).text for s in body])
    pics = [len([sh for sh in s.shapes if sh.shape_type == 13]) for s in body]
    check("evidence：图数 = 文稿里的图数", pics == [1, 2], pics)
    check("evidence：Layout 行不进红条",
          all("Layout" not in caption_bar(s).text_frame.text for s in body))
    check("evidence：红色只在底部红条上",
          all(red_elements(s) == ["Caption Bar"] for s in body),
          [red_elements(s) for s in body])
    check("evidence：没有“未实现”警告",
          not [w for w in warnings(r.stderr) if "未实现" in w], r.stderr)
    bad = out_of_bounds(r.prs, body)
    check("evidence：形状在页面内、不压 banner 和页脚", not bad, bad)


if __name__ == "__main__":
    test_explicit_and_default()
    finish()
