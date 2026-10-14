# 搭建说明：Milwaukee 汇报文字稿助手（Copilot agent）

照着本说明，可以在 Microsoft 365 Copilot 的 Agent Builder 里建出这个 agent；同事拿到 agent 写的 md 文稿后，可以按最后一节在 PowerPoint 里手工套模板。

**实测状态**：Agent Builder 的操作步骤和限制依据下方列出的微软公开文档整理。凡是标了「待测」的，还没在 Copilot 里实际验证过，结论以测试卡的结果为准。

本文件夹里的文件：

| 文件 | 用途 |
| --- | --- |
| `instructions.md` | 助手指令，整份粘贴到 Agent Builder 的 Instructions |
| `knowledge/milwaukee-ppt-layout-guide.txt` | 精简版知识文件：8 个版式的写法、反例和示例 |
| `knowledge/example-deck.txt` | 虚构示例 deck：一份完整文稿，覆盖 8 个版式 |
| `test-card.md`、`reference-answer.md` | 发给同事手工执行的测试卡和参考答案（不上传） |
| `evaluate.py`、`runs/` | 评测 Copilot 回答的脚本和回答收集说明（不上传） |

## 在 Agent Builder 里建立

1. 打开 Microsoft 365 Copilot，左侧选 **New agent**，再选 **Skip to configure**，进入手动配置。
2. **Name**：`Milwaukee 汇报文字稿助手`。
3. **Description**：`把项目材料整理成 Milwaukee 汇报 PPT 的逐页文字稿（带 Layout 标记的 md），可直接生成或照着套模板。`
4. **Instructions**：打开 `instructions.md`，全选复制，整份粘贴。不要删改其中的版式名和格式约定。
5. **Knowledge**：按下一节上传或选择知识库文件。
6. **Starter prompts**：按「起始提示词」一节逐条添加。
7. 在右侧 **Try it** 里问一道题，确认回答是一个 markdown 代码块，每页有 `Layout:`。
8. 选 **Create** 创建。创建后默认只有自己可用，要分享时看「分享与权限」。

Instructions 的长度：本指令按 8000 字符上限控制（这个上限出自 Copilot Studio 的配额页面；Agent Builder 页面没有单独写明，待测）。改指令后跑 `python3 copilot-agent/tests/run_all.py`，超限会报错。

## 知识库文件

上传以下 3 个文件：

- `milwaukee-ppt-layout-guide.txt`：版式参考，指令里按这个文件名引用，不要改名。
- `example-deck.txt`：虚构示例 deck。
- `MS_Template.pptx`：公司母版模板，取自仓库 `skills/milwaukee-ppt/assets/`。

知识文件存为 `.txt`，是因为 Agent Builder 的知识库文件类型清单里没有 `.md`（有 .txt、.docx、.pdf、.pptx 等）。

放在哪里，两种做法：

- **直接上传（推荐先用）**：在 Knowledge 区用 Upload 上传，文件嵌入 agent，最多 20 个。分享 agent 时，这些文件随 agent 一起共享，不需要另外设置文件权限。
- **放在 SharePoint**：放进团队网站的文档库，再用 Attach cloud files 选择。适合以后要更新文件、多人维护的情况。不建议放个人 OneDrive：文件归个人所有，人员变动后容易失效。

刚上传的 SharePoint / OneDrive 文件会显示 Preparing，就绪前 agent 不会用到它。

免费版 Copilot Chat 同事能否读到知识库：官方文档说明 SharePoint 和 OneDrive 知识源需要 Microsoft 365 Copilot 许可证，没有许可证的用户要由管理员开通按量计费才能用挂了组织数据的 agent；直接上传的文件对免费版是否可用，待测（测试卡第 1 条）。读不到知识库时，指令本身也能产出可用的文稿。

## 起始提示词

在 Starter prompts 里添加下面 4 条（标题 + 提示词）：

1. **项目汇报**：帮我把下面的项目材料整理成项目汇报 PPT 的逐页文字稿。按项目汇报的章节顺序组织，缺数据的地方先问我。材料如下：
2. **月报**：帮我写这个月的月报文字稿。我会按工作项给你完成情况和下一步，每个工作项一页。月份和作者是：
3. **材料改成 PPT 文字稿**：把下面这段文字改写成 PPT 逐页文字稿，每页一个核心信息，选合适的版式。文字如下：
4. **改版式**：下面这一页的版式不合适，帮我换一个更合适的版式重写，并说明为什么换。这一页是：

## 分享与权限

- 分享入口：agent 的 **Share**。可以添加个人或组；组只能是 **Can chat**（只能对话），要给编辑权限只能逐个添加个人。也可以打开组织内共享（Org-wide sharing），前提是管理员允许。
- 分享给组时用安全组：管理员给无许可证用户开通按量计费时，计费策略也是绑定到指定安全组，只有组内成员能用挂了组织数据的 agent。
- SharePoint 知识文件：分享 agent 时可以顺带把你添加进 agent 的文件和文件夹共享给对方，前提是你对这些文件有分享权限；整个网站的权限不会自动给出。共享失败时 agent 照样分享出去，但对方读不到这些文件，需要找文件所有者或网站管理员授权。
- 对方的许可证决定能用哪些能力：许可证不够时，使用 agent 可能报错。
- 改了已分享的 agent（含 SharePoint 知识文件）后，选 **Update** 发布，并对同一批人重新分享一次。

## 手工套模板

agent 给出的 md 每个 `# ` 是一页。同事没有生成脚本时，在 PowerPoint 里照下面的步骤套模板。

**待测**：本节按生成脚本的画法整理，还没有人照着在 PowerPoint 里完整做过一遍；测试卡第 4 条会验证，结果出来后再修订。

1. 用 `MS_Template.pptx` 新建演示文稿（或打开它另存一份）。
2. 封面：新建一页，版式选 **Title Slide**，主标题填 frontmatter 的 `title`，副标题填 `subtitle` 和日期、作者。月报封面写「<英文月份缩写>. <年份> Working Summary」，如 `Oct. 2026 Working Summary`。
3. 每个 `# ` 新建一页：开始 → 新建幻灯片 → 按下表选母版 layout。
4. 标题区：`# ` 后面的文字填进顶部红色 banner 里的主标题框，`## ` 后面的文字填进紧贴其下的副标题框。
5. 正文：按下表把版式字段填进内容区。
6. 结论行和 `Next:`：放在页面底部，用模板配色（品牌红底白字的结论条）。
7. 文稿 frontmatter 写了 `closing` 时，最后加一页收尾页。

| `Layout:` | 母版 layout | 怎么填 |
| --- | --- | --- |
| `evidence` | Blank Slide | 内容区放 0–3 张截图或照片，横排；底部写结论 |
| `before-after` | Before / After | lead 写在内容区顶部；Before、After 小标题填左右两个标题框，图或短文填左右内容框，Caption 填框下的说明框 |
| `process` | Process | 内容区画 3–5 张等宽卡片，每张写序号、步骤名、一句说明 |
| `stats` | Stats | 内容区分 2–4 栏，每栏写标签、大数字、一句说明和解读；标了 `!` 的数字用品牌红，其余深灰；口径写在内容区底部 |
| `stats-side` | Stats | 左边竖排 2–3 张数字卡，右边写结论小标题和编号要点 |
| `timeline` | Timeline | 横线上按顺序放 3–6 个节点，线上写日期，线下写标题和说明；写了状态时，完成 / 进行中 / 未完成分别用绿 / 琥珀 / 红色描边 |
| `timeline-phase` | Timeline | 一排 3–6 个箭头段，段内写阶段标题，段上写日期，段下写说明；按状态着色 |
| `image-text` | Image + Text | 图片放左边图框，要点填右边文字框（最多 5 条） |

母版里的 banner、logo、页脚已经画好，不要移动或改色。红色只给结论条、标了 `!` 的数字和 After 标题，其余用黑白灰。

## 参考的官方文档

- [Agent Builder overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder)
- [Add knowledge sources to an agent in Agent Builder](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-add-knowledge)
- [Share and manage agents built in Agent Builder](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-share-manage-agents)
- [Plan licensing and cost for Microsoft 365 Copilot extensibility](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/cost-considerations)
- [Quotas and limits - Microsoft Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-quotas)
