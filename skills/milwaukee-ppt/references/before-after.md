# Before / After 模板使用

用生成器出这一页时（`Layout: before-after`），文稿写法、报错与警告见 `layouts.md` 的 before-after 小节；本文件管槽位几何、事实对应和验收。

## 来源与边界

- `assets/MS_Template.pptx` 保留原 3 页、原 3 个布局，追加 layout index `3`（`Before / After`）与第 4 页干净样例。
- 参考内部月报的 Before/After 排布：左右对置框（黑色 0.75pt 细框），caption 紧贴框下，底部一条单行红色结论条。
- 仅借用几何关系；没有引入报告的业务图、部门/负责人表、业务数字、状态角标或链接。
- 通用页仍用 Milwaukee 原母版、logo、页脚；不是内部月报专用的英文汇报格式。
- 此页可用于流程、系统或实景对比；先确认两侧事实可以按同一问题对应，再选它。

## Slot 契约

位置单位为英寸；`idx` 是 `slide.placeholders[idx]` 的键，不是 shapes 的序号。

| idx | 类型 / 角色 | L / T / W / H |
| --- | --- | --- |
| 0 | TITLE / banner 主标题 | 沿用 layout 0，不改变原位置与样式 |
| 10 | BODY / banner action title | 沿用 layout 0，不改变原位置与样式 |
| 11 | BODY / BEFORE 标题 | 2.035 / 1.80 / 2.90 / 0.42 |
| 12 | BODY / AFTER 标题 | 8.395 / 1.80 / 2.90 / 0.42 |
| 13 | BODY / 改前内容区 | 0.66 / 2.42 / 5.65 / 2.99 |
| 14 | BODY / 改后内容区 | 7.02 / 2.42 / 5.65 / 2.99 |
| 15 | BODY / 改前 caption（16pt bold，最多两行） | 0.61 / 5.57 / 5.80 / 0.58 |
| 16 | BODY / 改后 caption（16pt bold，最多两行） | 6.97 / 5.57 / 5.80 / 0.58 |

layout 上的原生形状：左对比框 0.56 / 2.32 / 5.85 / 3.19，右对比框 6.92 / 2.32 / 5.85 / 3.19（黑色 0.75pt 细框），中间灰色箭头 6.43 / 3.665 / 0.47 / 0.50。内容区在框内四边各留 0.10"；caption 紧贴框下。

- `13/14` 是原生 BODY placeholder，不是 PICTURE placeholder；适合短文或作为图片/原生图形的定位空位。
- 放图时在槽的矩形内等比缩放、居中插入真实且已脱敏的图片，再删掉这个空槽；不用 `insert_picture()`。没写 caption 的一侧也删掉 caption 槽，编辑视图里不留提示文字。
- 双框、灰色转换箭头是 layout 上的原生 shape；需要改框时在布局中编辑，不替换为整页图片。
- 样例页的 `Lead` 与 `Conclusion` 是可直接编辑的原生 text box，不属于 placeholder。
- 从 layout 3 新建时自行加正文 lead（0.56 / 1.30 / 11.90 / 0.42）与可选底部结论条（0.56 / 6.43 / 12.21 / 0.55）。
- 底部结论条：`#DB011C` 实色底、白字 24pt、单行，在 caption 之下、页脚（7.25"）之上；不用证据页那种向上长高的红条。有 Next 时作为第二行，结论条顶边不动向下长（最低到 7.22"）；结论或 Next 超过一行时生成器警告。有没有结论条，caption 都在同一位置。

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
3. 每侧 caption 只写一句，最多两行；中文约 50 字以内，英文按实际字宽重渲检查。
4. 主标题、action title 仍填 `0/10`；正文 lead 写结论与证据，底部结论只在有事实支撑时填写。
5. 无量化来源就定性表达；资产数量、去重数量或工具数量的变化不能直接写成时间/成本收益。

## 红色与验收

- AFTER 标题和底部结论条用 `#DB011C`；其余元素黑白灰。
- 不加入绿色勾叉或完成状态；样例文字是填写提示，不是已完成声明。
- 保持正文原生可编辑；图片只用于证据，不用整页截图代替布局与文字。
- 样例页不是正式内容页；交付报告时先移除模板样例，再检查是否仍有填写提示。
- 改完标题、caption、lead、结论条或图后重新渲染整页，检查行数、溢出、对齐、图片边界与页脚间距。
- 从模板生成的文件执行 pptx `validate --original assets/MS_Template.pptx`，并逐页看全分辨率 PNG。
- 新页及引入 parts 检查姓名/邮箱/财务数据、notes、alt text、媒体、嵌入对象与外部链接；保留原品牌页脚。
