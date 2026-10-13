"""timeline 版式（占位实现，待版式票实现）：模板 layout 6「Timeline」。

字段约定（spec #10）：3–6 条无序列表「日期 | 标题 | 说明」；槽位 idx 19 Timeline Area。
现在只填主标题 / action title，打印“未实现”警告；红条与 Tag 照常。
"""
from .common import default_parse, render_stub

NAME = "timeline"
LAYOUT_INDEX = 6


def parse(page):
    default_parse(page)


def render(prs, page, ctx):
    return render_stub(prs, page, ctx, LAYOUT_INDEX)
