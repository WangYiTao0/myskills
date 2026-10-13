"""process 版式（占位实现，待版式票实现）：模板 layout 4「Process」。

字段约定（spec #10）：3–5 条有序列表「步骤名 | 一句说明」；槽位 idx 17 Process Area。
现在只填主标题 / action title，打印“未实现”警告；红条与 Tag 照常。
"""
from .common import default_parse, render_stub

NAME = "process"
LAYOUT_INDEX = 4


def parse(page):
    default_parse(page)


def render(prs, page, ctx):
    return render_stub(prs, page, ctx, LAYOUT_INDEX)
