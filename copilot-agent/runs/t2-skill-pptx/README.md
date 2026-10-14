# 测试：上传技能包，agent 能不能按公司模板直接出 pptx

把 milwaukee-ppt 打包成 Agent Builder 的技能包（里面有生成脚本 + 公司模板），看 Copilot 能不能在自己的沙箱里运行脚本，直接交付一份套好模板的 pptx。全部素材都是虚构的。

这是可行性测试。spec #28 原本把"在 Copilot 里生成 pptx"列为 Out of Scope，结论出来后再决定要不要转方向。

## 文件夹里有什么

| 文件 | 用途 |
| --- | --- |
| `README.md` | 本说明：步骤 + 记录表 |
| `1-自检.txt` | 第一条消息：让 agent 跑自检脚本 |
| `2-生成PPT.txt` | 第二条消息：用虚构素材生成 pptx |
| `3-改一页.txt` | 第三条消息：改一页版式后重新生成 |

要上传的技能包：`copilot-agent/dist/milwaukee-ppt-skill.zip`（整个 zip 上传，不要解压）。

## 第 1 步：建 agent，上传技能包

1. 打开 Copilot（m365.cloud.microsoft），选 **Agents & Skills** → **New agent**，再选 **Skip to configure**（手动配置）。
2. **Name**：`Milwaukee PPT 测试`。**Instructions**：打开 `copilot-agent/skill/agent-instructions.md`，全选复制，整份粘贴。
3. **不要**在 Knowledge 里上传任何文件。官方文档说明，技能和直接上传的知识文件目前不能放在同一个 agent 里。
4. 在 **Configure** 页展开 **Skills**，点 **Add**，上传 `milwaukee-ppt-skill.zip`。
5. 看上传结果：能不能看到技能名 `milwaukee-ppt`、说明和包含的文件。**看不到 Skills 区、上传报错，或提示需要许可证 / Frontier**：把提示原文记进记录表，测试到此结束。
6. 选 **Create** 创建。

## 第 2 步：在 Try it 或新对话里测试

每一步发一条消息，都在**同一个对话**里接着发。

1. **自检**：发 `1-自检.txt` 的内容。agent 应该运行 `scripts/check_env.py`，回复里有 python-pptx 的版本号，最后一行是 `OK`。
   - 如果回复里是 `FAILED`、缺少 python-pptx，或者它说不能运行脚本：记下原文，第 2、3 条照样发，看它会退回成只给 md 文稿，还是做出别的反应。
2. **生成 PPT**：复制 `2-生成PPT.txt` 全文，粘贴发送。
   - 生成了 pptx：下载，改名为 `01-生成.pptx`，放进本文件夹。
   - 没有生成文件：记下它的回复原文（关键句即可）。
3. **改一页**：发 `3-改一页.txt` 的内容。生成了新文件就下载，改名为 `02-改一页.pptx`，放进本文件夹。

## 第 3 步：快速看一眼下载的 pptx

用 PowerPoint 打开，看下面几点，填进记录表：

- 每页顶部有没有红色 banner、左上角有没有 logo、底部有没有页脚（说明用了公司模板）。
- 标题区是不是左侧主标题、下面一行结论（不是普通文本框随意摆放）。
- 页面底部有没有红色结论条。
- 关键数据页是不是大数字分栏。

做完后，把 pptx 和填好的记录表一起 commit、push，告诉我一声。我会逐页转成图片，跟生成脚本在本机做出的同一份汇报逐页对比。

## 记录表

| 步骤 | 结果（成功 / 失败） | 关键回复或报错原文 | 备注 |
| --- | --- | --- | --- |
| 上传技能包 |  |  |  |
| 1 自检（python-pptx 版本 / OK 或 FAILED） |  |  |  |
| 2 生成 PPT（有没有可下载的 pptx） |  |  |  |
| 3 改一页（有没有重新生成） |  |  |  |

| 检查 pptx | 01-生成.pptx | 02-改一页.pptx |
| --- | --- | --- |
| 红色 banner / logo / 页脚 |  |  |
| 标题区：主标题 + 一行结论 |  |  |
| 底部红色结论条 |  |  |
| 关键数据页是大数字分栏 |  |  |
| 页数 |  |  |

## 注意

- 用的是你的 Copilot 许可证。这个测试回答的是"有许可证的人能不能用技能直接出 PPT"；免费版同事能不能用，是另外一个问题。
- 技能功能是预览版，只对加入 Microsoft Frontier Program 的组织开放；入口和行为以后可能会变。
- 只用这里的虚构素材，不要换成真实项目。
