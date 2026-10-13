"""image-text 版式（占位实现，待版式票实现）：模板 layout 7「Image + Text」。

字段约定（spec #10）：一张图 + 若干条无序列表要点（建议 ≤5）；槽位 idx 20 Image Frame、idx 21 Text Area。
现在只填主标题 / action title，打印“未实现”警告；红条与 Tag 照常。
"""
from .common import default_parse, render_stub

NAME = "image-text"
LAYOUT_INDEX = 7


def parse(page):
    default_parse(page)


def render(prs, page, ctx):
    return render_stub(prs, page, ctx, LAYOUT_INDEX)
