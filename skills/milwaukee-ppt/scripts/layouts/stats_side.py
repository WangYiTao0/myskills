"""stats-side 版式（占位实现，待票 #23 实现）：模板 layout 5「Stats」，槽位 idx 18。

字段约定（spec #20）：2–3 条「- [!]标签 | 数字 | 一句说明」画成左侧竖排横卡；
`> ` 开头的行是右侧结论区要点（自动编号，最多 4 条）；`口径：` / `Source:` 一行放底部；
其余普通文字行进底部红条。
现在只填主标题 / action title，打印“未实现”警告；红条与 Tag 照常。
"""
from .common import default_parse, render_stub

NAME = "stats-side"
LAYOUT_INDEX = 5


def parse(page):
    default_parse(page)


def render(prs, page, ctx):
    return render_stub(prs, page, ctx, LAYOUT_INDEX)
