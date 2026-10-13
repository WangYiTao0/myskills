# Before / After 模板使用

用生成器出这一页时（`Layout: before-after`），文稿写法、报错与警告见 `layouts.md` 的 before-after 小节；本文件管槽位几何、事实对应和验收。

## 来源与边界

- `assets/MS_Template.pptx` 保留原 3 页、原 3 个布局，追加 layout index `3`（`Before / After`）与第 4 页干净样例。
- 版式参考 MyDoc2026 的 boss-monthly 月报及 Before After 示例：左右对置框，框下各一句 caption。
- 仅借用版式关系；没有引入报告的业务图、部门/负责人表、业务数字、状态角标、链接或底部全红结论条。
- 通用页仍用 Milwaukee 原母版、logo、页脚；不是 boss-monthly 专用英文汇报格式。
- 此页可用于流程、系统或实景对比；先确认两侧事实可以按同一问题对应，再选它。

## Slot 契约

位置单位为英寸；`idx` 是 `slide.placeholders[idx]` 的键，不是 shapes 的序号。

| idx | 类型 / 角色 | L / T / W / H |
| --- | --- | --- |
| 0 | TITLE / banner 主标题 | 沿用 layout 0，不改变原位置与样式 |
| 10 | BODY / banner action title | 沿用 layout 0，不改变原位置与样式 |
| 11 | BODY / BEFORE 标题 | 2.035 / 1.96 / 2.90 / 0.43 |
| 12 | BODY / AFTER 标题 | 8.395 / 1.96 / 2.90 / 0.43 |
| 13 | BODY / 改前内容区 | 0.78 / 2.78 / 5.41 / 2.91 |
| 14 | BODY / 改后内容区 | 7.14 / 2.78 / 5.41 / 2.91 |
| 15 | BODY / 改前 caption | 0.56 / 6.12 / 5.85 / 0.35 |
| 16 | BODY / 改后 caption | 6.92 / 6.12 / 5.85 / 0.35 |

- `13/14` 是原生 BODY placeholder，不是 PICTURE placeholder；适合短文或作为图片/原生图形的定位空位。
- 放图时清空该槽文本，在槽的矩形内等比缩放、居中插入真实且已脱敏的图片；不用 `insert_picture()`。
- 双框、灰色转换箭头是 layout 上的原生 shape；需要改框时在布局中编辑，不替换为整页图片。
- 样例页的 `Lead` 与 `Conclusion` 是可直接编辑的原生 text box，不属于 placeholder。
- 从 layout 3 新建时自行加正文 lead（0.56 / 1.30 / 11.90 / 0.42）与可选结论（0.56 / 6.68 / 12.21 / 0.36）。

```python
slide = prs.slides.add_slide(prs.slide_layouts[3])
slide.placeholders[0].text = topic
slide.placeholders[10].text = action_title
slide.placeholders[11].text = 'BEFORE'
slide.placeholders[12].text = 'AFTER'
slide.placeholders[13].text = before_fact
slide.placeholders[14].text = after_fact
slide.placeholders[15].text = before_caption
slide.placeholders[16].text = after_caption
```

## 填内容的顺序

1. 列出同一任务的改前方式、改后方式和对应证据；对象、时间窗口与统计口径一致才进行数量对比。
2. 在双框内放对应事实或图片；BEFORE 平实描述原步骤与工作方式，不贬旧方案。
3. 每侧 caption 只写一句，保持单行；中文约 20 字作为起点，英文按实际字宽重渲检查。
4. 主标题、action title 仍填 `0/10`；正文 lead 写结论与证据，底部结论只在有事实支撑时填写。
5. 无量化来源就定性表达；资产数量、去重数量或工具数量的变化不能直接写成时间/成本收益。

## 红色与验收

- 新增正文只有 AFTER 标题用 `#DB011C`；其余元素黑白灰，banner 外红色面积 ≤5%。
- 不加入绿色勾叉或完成状态；样例文字是填写提示，不是已完成声明。
- 保持正文原生可编辑；图片只用于证据，不用整页截图代替布局与文字。
- 样例页不是正式内容页；交付报告时先移除模板样例，再检查是否仍有填写提示。
- 改完标题、caption、lead 或图后重新渲染整页，检查单行、溢出、对齐、图片边界与页脚间距。
- 从模板生成的文件执行 pptx `validate --original assets/MS_Template.pptx`，并逐页看全分辨率 PNG。
- 新页及引入 parts 检查姓名/邮箱/财务数据、notes、alt text、媒体、嵌入对象与外部链接；保留原品牌页脚。
