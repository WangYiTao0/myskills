"""timeline-phase 版式（占位实现，待票 #25 实现）：模板 layout 6「Timeline」，槽位 idx 19。

字段约定（spec #20）：3–6 条「- [!]日期 | 标题 | 说明 | 状态」，每条都必须写状态，
画成箭头式阶段条；其余普通文字行进底部红条。
现在只填主标题 / action title，打印“未实现”警告；红条与 Tag 照常。
"""
from .common import default_parse, render_stub

NAME = "timeline-phase"
LAYOUT_INDEX = 6


def parse(page):
    default_parse(page)


def render(prs, page, ctx):
    return render_stub(prs, page, ctx, LAYOUT_INDEX)
