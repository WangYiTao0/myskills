---
name: pbip-mcp-workflow
description: Safe workflow rules for editing Power BI semantic models when using powerbi-modeling MCP server with PBIP projects. Use when modifying Power BI models via MCP — creating or updating measures, relationships, table properties, M code, partitions, data sources, or performing batch operations. Triggers on phrases like "改 measure", "改关系", "改 M 代码", "修改 partition", "批量重命名", "PBIP 修改", "power-bi-modeling", "TMDL 修改", or whenever powerbi-modeling MCP tools (connection_operations, table_operations, measure_operations, relationship_operations, model_operations) are about to be invoked. Enforces connection mode discipline to prevent the common "MCP wrote changes but Power BI Desktop didn't refresh" bug, and prevents Desktop from overwriting MCP changes during save.
---

# PBIP + powerbi-modeling MCP 安全工作流

本 skill 用于配合 `github/awesome-copilot` 的 `powerbi-modeling` skill。
`powerbi-modeling` 负责"建模该怎么做"（best practice），本 skill 负责"在 PBIP + MCP 环境下怎么安全执行修改"（workflow safety）。

## 核心问题

`powerbi-modeling-mcp` 有两种连接模式，行为差异巨大：

- **Desktop live**：连到 Desktop 进程的内存模型（语义模型层）。**可以改 DAX measure、query / M 代码、关系、partition、表/列属性** —— 凡是语义模型里的东西都能改。**唯一改不了的是 visual / 报表层**（visual 不在语义模型里，MCP 碰不到）。
  注意两个副作用：Desktop UI 的 Power Query 编辑器有独立 M 缓存，改完 M 不会自动刷新；保存时 Desktop 有可能用旧状态覆盖 MCP 的改动。所以**范围大、改动多的时候不建议用 live**。
- **PBIP 文件**：改动直接写到磁盘 TMDL/PQ 文件，Desktop 必须关闭（否则文件锁冲突）。适合**大范围 / 批量 / 高风险**的改动。

> 关键判断不是「改什么类型」，而是「范围有多大」。小改在 live 直接做；范围一大就关 Desktop 走 PBIP 文件。

详细原理见 `references/connection-modes.md`。

## 强制执行流程

### Step 1：先确认连接模式（必须）

任何 PBIP/MCP 修改操作开始前，**第一步必须执行**：

```
connection_operations(operation: "ListConnections")
```

识别当前连的是 Desktop 实例、PBIP 文件夹、还是 Fabric workspace。
如果没有连接或连接模式不对，**停下来问用户要走哪种模式，不要自行连接**。

### Step 2：根据改动范围判断推荐模式

判断主轴是**范围 / 风险**，不是改动类型。DAX、query/M、关系、partition 在 live 模式都改得了，
只是范围一大 live 的副作用（M 缓存不刷新、保存覆盖）就会咬人，这时才切 PBIP 文件。

| 改动范围                                       | 推荐模式      | Desktop 状态        |
| ---------------------------------------------- | ------------- | ------------------- |
| 探索模型 / 只读查询 / DAX 验证                 | Desktop live  | 开                  |
| 单条 / 少量 DAX measure 小改                   | Desktop live  | 开，改完提示 Ctrl+S |
| 单条 / 少量 query (M) 小改                     | Desktop live  | 开，改完提示刷新查询 |
| **批量改动（>5 个对象）**                      | **PBIP 文件** | **关**              |
| **大范围 M / partition / 数据源重写**          | **PBIP 文件** | **关**              |
| **关系结构大调整（批量新增/删除/改 cardinality）** | **PBIP 文件** | **关**              |
| **批量重命名表/列（影响下游引用）**            | **PBIP 文件** | **关**              |
| 改 visual / 报表层                             | —（MCP 不支持，需手动在 Desktop 改）| —    |

### Step 3：模式不匹配时主动提示切换

如果"当前连接模式 ≠ 推荐模式"，**停下来告诉用户**：

> ⚠️ 这次操作建议改用 [PBIP 文件 / Desktop live] 模式。
> 请：
>
> 1. [关闭 / 保存并关闭] Power BI Desktop
> 2. 我重新连接到 [PBIP 文件夹路径 / Desktop 实例]
> 3. 然后继续操作

不要在错误模式下硬执行。

### Step 4：M 代码修改的特殊纪律

无论 live 还是 PBIP 文件模式，改 M 都要：

1. 改之前先把当前 M 代码完整 echo 给用户看
2. live 模式改完提示用户刷新查询；PBIP 文件模式改完建议重开 Desktop 验证表能加载
3. 永远不在没有备份提示的情况下批量改 M（一个错的 M 会让整张表 fail）
4. 大范围 M 重写优先走 PBIP 文件模式（避开 live 的 M 缓存不刷新问题）

### Step 5：操作完成后给出明确的下一步指引

每次修改完成必须告诉用户：

- 改动写到了哪里（Desktop 内存 / 磁盘文件）
- 用户需要做什么才能让改动生效或可见（Ctrl+S / 重开 Desktop / 刷新查询）
- 怎么验证改动正确

## 快速通道（用户主动豁免）

如果用户在请求中明确说"小改一下，不用走完整流程"、"快速改"、"跳过检查"等，
可以省略 Step 1 的 `ListConnections`，但仍必须遵守 Step 4（M 代码纪律）。
快速通道只适用于**小范围**改动（含 live 模式下的 DAX / query 小改）；
一旦是**大范围 / 批量 / 高风险**改动，仍必须先确认连接模式并优先走 PBIP 文件。

## 禁止行为

- ❌ Desktop 开着的时候用 PBIP 文件模式写入（文件锁 / 覆盖冲突）
- ❌ Desktop live 模式下做大范围 / 批量（>5 个对象）/ 高风险改动 —— 这类要切 PBIP 文件
- ❌ 试图用 MCP 改 visual / 报表层 —— MCP 只能动语义模型，visual 改不了，要手动在 Desktop 改
- ❌ 不先 `ListConnections` 就开始改（除非用户明确触发快速通道）
- ❌ 改完 M 不给验证建议就告诉用户"完成了"
- ❌ 假设 Desktop 会自动感知 MCP 的改动 —— 它不会
