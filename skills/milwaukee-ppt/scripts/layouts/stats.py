"""stats 版式（占位实现，待版式票实现）：模板 layout 5「Stats」。

字段约定（spec #10）：2–4 条无序列表「标签 | 数字 | 一句说明」，最多一条行首 ! 标为红色重点；槽位 idx 18 Stats Area。
现在只填主标题 / action title，打印“未实现”警告；红条与 Tag 照常。
"""
from .common import default_parse, render_stub

NAME = "stats"
LAYOUT_INDEX = 5


def parse(page):
    default_parse(page)


def render(prs, page, ctx):
    return render_stub(prs, page, ctx, LAYOUT_INDEX)
