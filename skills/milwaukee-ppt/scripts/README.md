# 生成器代码约定（给版式票的实现者）

- 三层：`mdparse.py` 只切页并取通用字段（`#` `##` `Layout:` `Tag:` `Next:`），其余正文行原样放进 `page.lines`；`layouts/<版式>.py` 解析本版式字段并渲染；`generate_ppt.py` 装配封面 / 各页 / 收尾。
- 每个版式一个模块：`layouts/evidence.py`、`before_after.py`、`process.py`、`stats.py`、`timeline.py`、`image_text.py`，接口相同：`NAME`、`LAYOUT_INDEX`、`parse(page)`、`render(prs, page, ctx) -> slide`。
- `parse(page)` 读 `page.lines`（空行为 `""`），写 `page.fields`，把红条结论行追加到 `page.conclusion`；文稿有错抛 `DeckError`，信息里带 `页「{page.title}」`。
- `render` 用 `prs.slide_layouts[LAYOUT_INDEX]` 建页，`fill_titles` 填 idx 0/10，按 idx 取槽位画内容（槽位只用来定位的就 `take_slot` 取矩形并删掉占位框），最后调 `add_page_chrome(slide, page, ctx)` 画 Tag 和底部红条。
- 共用部件只放 `layouts/common.py`，版式模块之间不互相 import：
  - 页面：`warn`、`load_image`、`fill_titles`、`add_page_chrome`（Tag + 底部红条）；
  - 形状：`slot` / `take_slot` / `remove_shape`（按 idx 取槽位、删形状）、`fit_picture`（矩形内等比放图）、`add_run`（Arial + 中文 PingFang SC 的 run）、`strip_theme_style`（去 p:style）；
  - 估算：`text_width_in` / `text_lines`（CJK 1em、拉丁 0.55em），溢出警告一律用它；
  - 常量：`BRAND_RED`、`LATIN_FONT`、`EA_FONT`。
  - 例外：底部红条的加高算法是月报固定样式，不改用 `text_lines`；stats 的卡片几何（大数字字号、标签 / 说明行数）用本版式的逐字宽表。
- 注册表在 `layouts/__init__.py`，已登记全部 6 个版式。
- 测试：每个版式一个 `tests/test_<版式>.py`，只走“md 进、pptx 出”；辅助函数（`generate`、`body_slide`、`pictures`、`shapes_named`、`run_style` 等）和模板槽位常量都在 `tests/deckcheck.py`，测试文件里不要再各写一份。`python3 tests/run_all.py` 跑全部。
- 新增或修改一个版式时，通常只动 `layouts/<版式>.py` + `tests/test_<版式>.py`；需要新的共用部件时再动 `common.py` / `deckcheck.py`。

## 检查命令 `inspect_ppt.py`

生成后细调时用它定位元素：

```
python3 scripts/inspect_ppt.py deck.pptx
```

每页一个标题行 `== 第 N 页 | layout: <名>`，下面每个形状一行：`名字 | 类型 | L= T= W= H=（英寸，两位小数） | 文字前约 30 字`（换行替换成空格）。文件不存在或不是 pptx 时，错误信息写到 stderr，退出码非零。
