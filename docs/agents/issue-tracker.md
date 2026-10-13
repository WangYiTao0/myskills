# Issue tracker: GitHub

本仓库的问题与规划票存放在 `WangYiTao0/myskills` 的 GitHub Issues，统一使用 `gh`；每次操作显式传入 `--repo WangYiTao0/myskills`，REST 路径使用 `repos/WangYiTao0/myskills`。

## 基本操作

- 创建：`gh issue create --repo WangYiTao0/myskills --title "..." --body "..."`；多行正文使用 heredoc 或 `--body-file`。
- 读取：`gh issue view <number> --repo WangYiTao0/myskills --json number,title,body,labels,comments,assignees`。
- 查询：`gh issue list --repo WangYiTao0/myskills --state open --label "wayfinder:map" --json number,title,body,labels`；创建地图前也查询 closed，避免重复 effort。
- 引用：正文和评论使用 `[票的完整标题](真实 issue URL)`，不使用裸编号或占位链接。

## Wayfinding operations

- **Map**：每个 effort 一个 issue，仅标记 `wayfinder:map`。正文依次为 `Destination` / `Notes` / `Decisions so far` / `Not yet specified` / `Out of scope`；已确认背景放 Notes，决策索引只收已解决票。开放票由 native children 查询，不在正文维护重复清单。
- **Child**：使用 `wayfinder:research`、`wayfinder:prototype`、`wayfinder:grilling` 或 `wayfinder:task` 表达类型。通过 GitHub native sub-issues 链接至地图：`gh api --method POST repos/WangYiTao0/myskills/issues/<map-number>/sub_issues -F sub_issue_id=<child-db-id>`。
- **Blocking**：GitHub native issue dependencies 是唯一阻塞关系：`gh api --method POST repos/WangYiTao0/myskills/issues/<child-number>/dependencies/blocked_by -F issue_id=<blocker-db-id>`。database id 用 `gh api repos/WangYiTao0/myskills/issues/<number> --jq .id` 获取，不是 issue number 或 node_id。
- **Native 查询**：父子用 `gh api --paginate repos/WangYiTao0/myskills/issues/<map-number>/sub_issues`，阻塞用 `gh api --paginate repos/WangYiTao0/myskills/issues/<child-number>/dependencies/blocked_by`。native API 不支持或权限不足时停止并报告；不改用正文 `Part of` / `Blocked by` 或地图 task list fallback。
- **Frontier**：按地图 native children 顺序读取所有开放票，排除已有 assignee 或仍有开放 blocker 的票（`issue_dependencies_summary.blocked_by > 0`）；第一张剩余票优先。创建时按规划顺序添加 children；同批 frontier 也保持此顺序。
- **Claim**：会话的第一项写操作是认领选中的票：`gh issue edit <number> --repo WangYiTao0/myskills --add-assignee @me`，随后重读确认。建图会话不代替后续会话认领。
- **Resolve**：先 `gh issue comment <number> --repo WangYiTao0/myskills --body "<结论与证据>"`，再 `gh issue close <number> --repo WangYiTao0/myskills`，最后在地图 `Decisions so far` 追加简短结论和按标题引用的链接。需要人的决定时，先取得确认；研究推荐不等于人的技术决策。

## Public repo 边界

新 issue、评论和文件只使用通用文字或 100% 模拟材料，不上传或引用可识别的真实公司数据、PPT、截图、业务数字或私人文件路径。现有模板保留，不追加其他公司资产。本配置仅用于 wayfinding，不启用全套 triage setup。
