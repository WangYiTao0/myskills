---
name: wayfinder-github
description: 把存在 GitHub issue 里的 wayfinder 地图画成星图看。当用户说「看地图」「打开 map」「wayfinder 地图长什么样」「哪些票能领」「frontier 是什么」，或想知道一堆调查票的阻塞关系与进度全貌时使用。票留在 GitHub 不动，本 skill 只拉一份只读快照喂给 wayfinder-maps 查看器，并持续跟随。也管这套 GitHub adapter 的字段约定（label、关闭原因、Blocked by、认领）。不负责规划方法本身——那是 wayfinder-maps skill 的事。
---

# 看 GitHub 上的 wayfinder 地图

wayfinder 把一件大而模糊的事拆成一张**调查票的地图**，一次会话只解决一张票。票放在 GitHub issue 里有原生的阻塞关系、认领和原子编号，但**看不到全貌**——哪些票卡着哪些、边界在哪、还剩多少，issue 列表答不了。

`wayfinder-maps` 那个查看器能画星图，可它**只读本地 `.plan/` 目录的 markdown**。本 skill 架的就是这段桥：拉一份只读快照，喂给查看器，并在后台持续跟随。

**快照是单向的、看完即弃的。GitHub 是唯一真相。** 别编辑快照，别提交进仓——那就成了一个事实两个家，其中一个必然过期。快照默认落在 `~/.cache/wayfinder-maps/<owner>-<repo>/` 而不是项目里，就是为了让"顺手改一下"不成为一个可能的动作。

## 用

```bash
scripts/wf-map            # 原生窗口；仓库取自当前目录的 git remote
scripts/wf-map serve      # 浏览器，:7777
```

跑起来后**别的都不用管**：后台每 45 秒重拉一次，查看器前端自己轮询快照的 mtime，所以在 GitHub 上改完票，页面会自己更新。关掉查看器，后台同步跟着停。

不在目标仓目录下时用 `WF_REPO=owner/name scripts/wf-map`。其余开关：`WF_INTERVAL`（同步间隔，默认 45）、`WF_ONCE=1`（只同步一次）、`WF_PREFIX`（label 前缀，默认 `wayfinder:`）、`WF_OUT`（快照落点）、`PORT`（serve 端口）。

只要数字不要界面时，直接跑同步再用查看器的命令行子命令：

```bash
python3 scripts/wf_sync.py --print-dir      # 快照目录在哪
python3 scripts/wf_sync.py                  # 拉一次
wayfinder-maps status <快照目录>/.plan/<某张图>/   # frontier 与计数
wayfinder-maps lint   <快照目录>/.plan/<某张图>/   # 图有没有漂移
```

## 前置

- **`gh` 已登录** —— 私有仓也能读，认证走 gh。
- **`wayfinder-maps` 在 PATH 里** —— 从 [releases](https://github.com/rengwu/wayfinder-maps/releases) 下对应平台的包（macOS/Windows/Linux 都有预编译版，**不需要 Go 工具链**），二进制丢进 `~/.local/bin` 即可。`wf-map` 会检查这两项，缺哪个报哪个。
- python3。

## 仓库那边要长什么样

这套映射就是 wayfinder 的 **GitHub adapter**。新仓库照着建 label 即可开工。

| wayfinder 概念 | GitHub 上怎么表达 |
|---|---|
| 地图 | issue + label `wayfinder:map`，body 分 `## Destination` / `## Notes` / `## Decisions so far` / `## Not yet specified` / `## Out of scope` |
| 票 | issue + label `wayfinder:research` / `:prototype` / `:grilling` / `:task` |
| 票属于哪张图 | body 里一行 `父地图：#N`（也认 `Part of #N` / `Parent: #N`） |
| 问题 | body 的 `## Question` 段 |
| 阻塞 | body 里一行 `Blocked by: #12, #13` |
| 认领 | assignee（认领时间从 issue timeline 的 assigned 事件取，不用手写） |
| **已解决** | issue **closed as completed** |
| **超出范围** | issue **closed as not planned** |
| 答案 | 发在**评论区**（body 是问题，评论是回答） |
| 结论被推翻 | body 里一行 `Undermined by: #N` |

两处容易搞错，都会安静地给出错误的图：

- **关闭原因必须分两种。** `not planned` 是关闭的，但**关闭不等于已解决**——它不满足任何阻塞边。一张票被 not-planned 的票挡着就永远不该解锁，这时是两者之一定错了范围。若两种关闭不加区分，被超范围票挡住的票会**错误地显示成可以开工**。
  ```bash
  gh issue close <N> --reason completed      # 已解决，答案已发评论区
  gh issue close <N> --reason "not planned"  # 判定超出这张图的范围
  ```
- **没写父地图的票不会出现在任何图里。** 同步时会在 stderr 点名警告（`⚠ N 张票没有可识别的父地图`），别忽略它——那些票在星图上是隐形的。

**不要建 `status` label。** 状态已经写在 issue 自己身上（开/关、关闭原因、有没有 assignee），存第二份就多一处会过期。

## 同步时替你抹平的两处差异

改 `wf_sync.py` 前先知道它们在防什么，否则很容易"简化"掉：

- **票的答案在评论区，而解析器要的是 `## Answer` 段里的正文。** 评论往往自带 `## 决议：` / `# 定案` 这样的标题，原样贴进去会成为 `## Answer` 的同级兄弟，令该段为空——票明明结了却显示成"未解决"。脚本按**整段最小标题级别整体下移**，压进 Answer 段内。注意不是"降一级"：评论用 `#` 还是 `##` 开头都有，固定降一级对前者不够。
- **地图里指向票的链接是 GitHub URL，解析器只认 `./tickets/NN-slug.md`。** 按票号改写。

还有一条不是差异而是性能：**内容没变就不重写文件**。查看器靠快照的 mtime 判断要不要重绘，无脑重写会让页面每轮无谓刷新一次。

## 改完要核对

数字错了界面不会报错，只会安静地显示一个错的数字。所以改过 `wf_sync.py` 之后：

1. `wayfinder-maps lint <快照>/.plan/<图>/` —— `wf-map` 每次启动会自动跑一遍，有漂移就打印。
2. `python3 tests/test_orphan_warning.py` —— 用构造数据验孤儿票警告没退化成死代码（它曾经是：`return` 排在检查之前）。
3. **把手上所有的图都跑一遍 `status` 核对，不要只跑触发问题的那一张。** 同一个 bug 常有多个数据形态（标题级别就是），只修见到的那个、只验那一个样本，另一张图会照样错——而主样本从"很错"变成"全对"这个大幅改善，本身很像修好了。

## 与 wayfinder-maps skill 的分工

`wayfinder-maps` skill 是**方法**：怎么把一件模糊的事拆成票、一次只解决一张、怎么记决策。本 skill 是**这套方法落在 GitHub 上的适配层加可视化**。规划找它，看图找这里。
