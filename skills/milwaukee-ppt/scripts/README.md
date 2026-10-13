# 生成器代码约定（给版式票的实现者）

- 三层：`mdparse.py` 只切页并取通用字段（`#` `##` `Layout:` `Tag:` `Next:`），其余正文行原样放进 `page.lines`；`layouts/<版式>.py` 解析本版式字段并渲染；`generate_ppt.py` 装配封面 / 各页 / 收尾。
- 每个版式一个模块：`layouts/evidence.py`、`before_after.py`、`process.py`、`stats.py`、`timeline.py`、`image_text.py`，接口相同：`NAME`、`LAYOUT_INDEX`、`parse(page)`、`render(prs, page, ctx) -> slide`。
- `parse(page)` 读 `page.lines`（空行为 `""`），写 `page.fields`，把红条结论行追加到 `page.conclusion`；文稿有错抛 `DeckError`，信息里带 `页「{page.title}」`。
- `render` 用 `prs.slide_layouts[LAYOUT_INDEX]` 建页，`fill_titles` 填 idx 0/10，按 idx 取槽位画内容，最后调 `add_page_chrome(slide, page, ctx)` 画 Tag 和底部红条。
- 共用部件只放 `layouts/common.py`（`warn`、`load_image`、`fill_titles`、`add_page_chrome`、红条、Tag）；版式模块之间不互相 import。注册表在 `layouts/__init__.py`，已登记全部 6 个版式，版式票不用改它。
- 测试：每个版式一个 `tests/test_<版式>.py`，只走“md 进、pptx 出”；辅助函数在 `tests/deckcheck.py`。`python3 tests/run_all.py` 跑全部。
- 版式票只改：`layouts/<版式>.py` + `tests/test_<版式>.py`（需要新的共用部件时再动 `common.py` / `deckcheck.py`，尽量只追加）。
