"""版式层：每种版式一个模块，注册表按 Layout 名分派。

每个版式模块（evidence.py、before_after.py …）提供同样的接口：
    NAME: str               文稿里 `Layout:` 写的名字
    LAYOUT_INDEX: int       用模板的第几个 slide layout
    parse(page) -> None     读 page.lines（本页除通用字段外的原始正文行，空行为 ""），
                            填 page.fields（本版式字段）并往 page.conclusion 追加红条结论行；
                            文稿有错抛 DeckError，信息含页标题
    render(prs, page, ctx) -> slide
                            新建一页、填 idx 0/10、画本版式内容，
                            最后调 common.add_page_chrome 画 Tag 和底部红条
共用部件都在 common.py；版式模块之间互不 import。
"""
from mdparse import DeckError

from . import (before_after, evidence, image_text, process, stats, stats_side, timeline,
               timeline_phase)
from .common import Context  # noqa: F401  （装配层用 layouts.Context）

REGISTRY = {m.NAME: m for m in
            (evidence, before_after, process, stats, stats_side, timeline, timeline_phase,
             image_text)}
DEFAULT_LAYOUT = evidence.NAME


def parse_page(page):
    """校验版式名并交给版式模块解析本页字段。"""
    module = REGISTRY.get(page.layout)
    if module is None:
        raise DeckError(f"页「{page.title}」的版式名未知: {page.layout!r}, "
                        f"可选: {' / '.join(REGISTRY)}")
    module.parse(page)


def render(prs, page, ctx):
    return REGISTRY[page.layout].render(prs, page, ctx)
