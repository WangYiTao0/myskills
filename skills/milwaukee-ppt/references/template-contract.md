# 模板占位框契约（SKILL.md §5.0）

自己写代码生成或手工改 `assets/MS_Template.pptx` 时读本文件；`scripts/generate_ppt.py` 已按本契约填充。

> ⚠️ **用 `MS_Template.pptx` 生成或手工改 pptx 时，主标题 / 副标题必须填进模板已有的占位框（placeholder），禁止为它们另建 text box。** 另建文本框会导致位置飘、与 banner 不对齐、跨页不一致——这正是本节要杜绝的问题。`scripts/generate_ppt.py` 已按本契约填充；下表也是自己写代码生成时的依据。

模板 16:9（13.33″ × 7.5″）。红 banner（顶部 0–1.0″ 全宽 `#DB011C`）、左上 logo、底部页脚都在 **母版** 里，生成时不用画、不要动。8 个版式各自的占位框如下（`idx` = `slide.placeholders[idx]` 的键，位置单位：英寸）：

| 版式 index | 版式名 | 用途 | 占位框（idx → 角色，位置 L/T/W/H） |
| --- | --- | --- | --- |
| 1 | `Title Slide` | 封面 | `0` 主标题（居中，1.0 / 4.83 / 11.33 / 0.5）；`1` 副标题（2.0 / 5.42 / 9.33 / 0.5） |
| 0 | `Blank  Slide` | 正文页（默认） | `0` 主标题（banner 右上，5.08 / 0.1 / 8.25 / 0.4）；`10` 副标题（紧贴主标题下，5.08 / 0.5 / 8.25 / 0.42） |
| 2 | `Blank  Slide WITH BULLETS` | 带正文框的正文页 | 同上两个 + `1` 大正文框（0.56 / 1.42 / 12.44 / 5.75） |
| 3 | `Before / After` | 双框对比页 | `0/10` 沿用正文页；`11/12` 左右标题（2.035 / 1.96、8.395 / 1.96，2.90 × 0.43）、`13/14` BODY 内容区（0.78 / 2.78、7.14 / 2.78，5.41 × 2.91，在对比框内）、`15/16` caption 一句话、一行（0.56 / 6.12、6.92 / 6.12，5.85 × 0.35，框下）；有底部红条（月报）或页底 Next 行（通用 / 项目模式）时生成器把 caption 挪进对比框底部，详见 `references/before-after.md` |
| 4 | `Process` | 流程页 | `0/10` 沿用正文页；`17` 流程区（0.56 / 1.30 / 12.21 / 4.30） |
| 5 | `Stats` | 数据对比页 | `0/10` 沿用正文页；`18` 数据区（0.56 / 1.30 / 12.21 / 4.30） |
| 6 | `Timeline` | 时间线页 | `0/10` 沿用正文页；`19` 时间线区（0.56 / 1.30 / 12.21 / 4.30） |
| 7 | `Image + Text` | 左图右文页 | `0/10` 沿用正文页；`20` 图框 16:9（0.56 / 1.30 / 7.64 / 4.30）、`21` 文字区（8.50 / 1.30 / 4.27 / 4.30） |

layout 4–7 的槽位只是定位用的 BODY 占位框：生成器在槽位矩形内画原生形状，画完删掉空槽位。按 `idx` 找槽位，不按名字找（落到页面上名字会变成 "Text Placeholder N"）。

**填充规则（生成时照做）**：

```python
from pptx import Presentation
prs = Presentation('assets/MS_Template.pptx')

# 正文页：从「Blank Slide」版式新建，只填占位框，不新建标题/副标题文本框
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.placeholders[0].text = '项目背景 / BACKGROUND'    # 主标题（banner 右上）
slide.placeholders[10].text = '报表分散已成为扩展瓶颈'   # 副标题（紧贴主标题下方）
# PDCA 图标、正文 lead、正文内容 → 在 banner 以下的正文区自行排布
```

- 主标题（§4 第一层）→ 永远填 `placeholders[0]`
- 副标题 action title（§4 第二层）→ 正文页填 `placeholders[10]`、封面填 `placeholders[1]`
- 找不到某个 idx 时按 `placeholder_format.type` 兜底定位（TITLE / CENTER_TITLE = 主标题，SUBTITLE / BODY = 副标题），**仍然不要新建文本框**
- 正文 lead、PDCA 图标、正文内容不属于占位框，照 §2/§4/§6 在正文区自行排布
