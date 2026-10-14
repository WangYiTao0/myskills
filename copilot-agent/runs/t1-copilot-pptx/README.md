# 测试：Copilot 能不能直接做出 pptx

目的：不经过生成脚本，看公司 Copilot 自己能不能做出一份套用公司模板、符合汇报规范的 pptx。分两条路测，每条路做 1 次就够。全部素材都是虚构的。

这是可行性测试。spec #28 原本把"在 Copilot 里生成 pptx"列为 Out of Scope，测试结论出来后再决定要不要改方向。

## 文件夹里有什么

| 文件 | 用途 |
| --- | --- |
| `README.md` | 本说明：步骤 + 记录表 |
| `A-Copilot-Chat-提示词.txt` | 路线 A 要发的消息（已含素材） |
| `B-PowerPoint-Copilot-提示词.txt` | 路线 B 要发的消息（已含素材） |
| `素材.txt` | 单独的素材原文，路线 B 需要"从文件创建"时用 |

还要用到仓库里的两个文件（作为附件上传）：

- 公司模板：`skills/milwaukee-ppt/assets/MS_Template.pptx`
- 版式参考：`copilot-agent/knowledge/milwaukee-ppt-layout-guide.txt`

## 路线 A：Copilot Chat 直接出文件

1. 打开 Copilot Chat，新建聊天。
2. 上传两个附件：`MS_Template.pptx`、`milwaukee-ppt-layout-guide.txt`。
3. 复制 `A-Copilot-Chat-提示词.txt` 全文，粘贴发送。
4. 看它有没有给出可下载的 .pptx 文件：
   - 有：下载，改名为 `A.pptx`，放进本文件夹。
   - 没有（只给文字、说做不到、给的是图片）：在记录表里照实写下它的回复，截取关键原句。
5. 如果它只给了文字稿，再追问一次：`请把上面的内容生成为 .pptx 文件，使用附件模板。` 结果同样记录。

## 路线 B：PowerPoint 里的 Copilot

1. 用 PowerPoint 打开 `MS_Template.pptx`，另存为一个新文件（不要改原模板）。
2. 打开右上角的 **Copilot** 按钮。看不到 Copilot 按钮、或提示需要许可证：在记录表里写下提示原文，路线 B 到此结束。
3. 在 Copilot 窗格里选"创建演示文稿"（或直接对话），复制 `B-PowerPoint-Copilot-提示词.txt` 全文，粘贴发送。
   - 如果它只接受"从文件创建"：选 `素材.txt`（不接受 txt 时，把素材粘进一个 Word 文档再选）。
4. 生成完后另存为 `B.pptx`，放进本文件夹。
5. 顺便看一下：生成的页是不是用了模板里的版式（红色 banner、logo、页脚还在不在）。

## 做完之后

把 `A.pptx`、`B.pptx`（有几个放几个）和填好的记录表一起 commit、push，告诉我一声。我会把 pptx 逐页转成图片，对照汇报规范检查，并和生成脚本做出来的同一份汇报对比。

## 记录表

| 路线 | Copilot 类型（免费版 / 有许可证） | 能不能直接出 pptx | 用没用公司模板（banner / logo / 页脚） | 页数 | Copilot 的关键回复或报错原文 |
| --- | --- | --- | --- | --- | --- |
| A Copilot Chat |  |  |  |  |  |
| B PowerPoint Copilot |  |  |  |  |  |

另外记一条你之前看到的现象：Copilot 生成的 markdown 预览后变成了一张 png 图片。这是在哪个入口出现的（Chat / Teams / 网页）？当时点的是什么按钮？

| 入口 | 操作 | 结果 |
| --- | --- | --- |
|  |  |  |

## 注意

- 只用这里的虚构素材，不要换成真实项目。
- 生成的 pptx 里如果出现公司真实信息（理论上不会），不要提交，在记录表里注明。
