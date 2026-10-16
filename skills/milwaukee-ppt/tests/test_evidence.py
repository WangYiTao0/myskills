"""evidence 版式（默认版式）测试：图 + 底部红条。

运行：python3 skills/milwaukee-ppt/tests/test_evidence.py
月报格式的逐项回归（红条样式、Tag、多图）在 test_generate.py 的 test_monthly_regression；
这里另测 http(s) 图片的下载与缓存（本地 http.server，缓存目录用 MILWAUKEE_PPT_CACHE 指向临时目录）。
"""
import functools
import http.server
import tempfile
import threading
from pathlib import Path

from deckcheck import (LAYOUT_INDEX, caption_bar, check, finish, generate, make_image,
                       out_of_bounds, pictures, placeholder, red_elements)

MD = """
---
month: 2026-10
author: Mock.Author
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
    body = r.slides[1:-1]          # 月报模式：最后一页是 Thank You
    check("evidence：不写 Layout 与写 Layout: Evidence（大小写不敏感）都用 layout 0",
          len(body) == 2 and all(
              s.slide_layout == r.prs.slide_layouts[LAYOUT_INDEX["evidence"]]
              for s in body),
          [s.slide_layout.name for s in body])
    check("evidence：主标题在 idx 0",
          [placeholder(s, 0).text for s in body] == ["Default Page", "Explicit Page"],
          [placeholder(s, 0).text for s in body])
    pics = [len(pictures(s)) for s in body]
    check("evidence：图数 = 文稿里的图数", pics == [1, 2], pics)
    check("evidence：Layout 行不进红条",
          all("Layout" not in caption_bar(s).text_frame.text for s in body))
    check("evidence：红色只在底部红条上",
          all(red_elements(s) == ["Caption Bar"] for s in body),
          [red_elements(s) for s in body])
    bad = out_of_bounds(r.prs, body)
    check("evidence：形状在页面内、不压 banner 和页脚", not bad, bad)


URL_MD = """
---
month: 2026-10
author: Mock.Author
---

# URL Page
![]({url})
URL conclusion.
"""


def test_url_image_and_cache():
    """http(s) 图片：下载后进 MILWAUKEE_PPT_CACHE 缓存；服务停掉后用缓存照常生成；
    下载失败报错并带页标题。"""
    served = Path(tempfile.mkdtemp(prefix="mppt-served-"))
    make_image(served / "shot.png", (1600, 900))
    cache = Path(tempfile.mkdtemp(prefix="mppt-cache-"))
    handler = functools.partial(QuietHandler, directory=str(served))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    env = {"MILWAUKEE_PPT_CACHE": str(cache)}
    try:
        r = generate(URL_MD.format(url=f"{base}/shot.png"), env=env)
        check("evidence（URL）：下载图片后生成，退出码 0", r.rc == 0, r.stderr)
        check("evidence（URL）：页上有这张图",
              len(r.slides) > 1 and len(pictures(r.slides[1])) == 1)
        check("evidence（URL）：缓存目录里有一份 .png", len(list(cache.glob("*.png"))) == 1,
              list(cache.iterdir()))
        r = generate(URL_MD.format(url=f"{base}/missing.png"), env=env)
        check("evidence（URL）：下载失败 → 非零退出、含页标题和 URL",
              r.rc != 0 and "URL Page" in r.stderr and "missing.png" in r.stderr
              and not r.path.exists(), (r.rc, r.stderr))
    finally:
        server.shutdown()
        server.server_close()
    r = generate(URL_MD.format(url=f"{base}/shot.png"), env=env)
    check("evidence（URL）：服务停掉后用缓存照常生成", r.rc == 0
          and len(r.slides) > 1 and len(pictures(r.slides[1])) == 1, r.stderr)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


if __name__ == "__main__":
    test_explicit_and_default()
    test_url_image_and_cache()
    finish()
