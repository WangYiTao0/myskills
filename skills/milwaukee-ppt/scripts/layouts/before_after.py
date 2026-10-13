"""before-after 版式（占位实现，待版式票实现）：模板 layout 3「Before / After」。

字段约定（spec #10）：### Before / ### After 两个小节（各一张图或一段短文 + 一行 Caption:），小节外普通文字为 lead；槽位 idx 11–16。
现在只填主标题 / action title，打印“未实现”警告；红条与 Tag 照常。
"""
from .common import default_parse, render_stub

NAME = "before-after"
LAYOUT_INDEX = 3


def parse(page):
    default_parse(page)


def render(prs, page, ctx):
    return render_stub(prs, page, ctx, LAYOUT_INDEX)
