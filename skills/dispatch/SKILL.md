---
name: dispatch
description: 调度台：一个会话当指挥，用 cmux 开窗口派票、收工核验、派审核代理、关票回填地图、看板交接。子命令 start / handoff / resume。
disable-model-invocation: true
---

# 调度台（dispatch）

一个会话只做指挥，不写业务代码。活派到 **cmux 新窗口**里的独立 claude 会话去做；
会话之间用 `SendMessage` 互报；用户只看调度台的**看板**。

> 用法：`/dispatch`（= start）· `/dispatch handoff`（本会话 context 大了，交给新会话）· `/dispatch resume`（新会话接手）
>
> 依赖机器上的 cmux / fish 函数 `cglm` `ckimi` / gh / 看板目录，换电脑照 [references/setup-new-machine.md](references/setup-new-machine.md) 装。

## 看板文件 = 唯一真源

路径 `~/.claude/dispatch/<仓目录名>.md`。**每次状态变化就重写**（派了 / 收了 / 关了 / 等用户答什么），
handoff 时它就是全部交接材料，不用临时整理。格式见 [board-template.md](board-template.md)。

## start：起调度台

1. 读本仓的进度文件（`HANDOFF.md` 之类）和票据契约（`docs/TRACKER-*.md` 之类，没有就按 GitHub issue 的 `Blocked by:` 行推依赖）。
2. `ListAgents` 列同仓 peer 会话，逐个 `SendMessage` 问「做哪张票、到哪步、动了哪些目录、有没有未提交」，`notify_when_idle: true`。
3. `gh issue list --state open` 拉票，算 **frontier**（open + 无 assignee + Blocked by 全 closed）。
4. 写看板；给用户一张表：在做什么 → 状态 → 等谁。自己的窗口改名带编号：`cmux workspace rename <workspace:id> "调度台 #<n>"`（看板头记着上一个的编号）。**称呼用票号或段名，不用会话编号**（用户面前是窗口，窗口上没有编号）。

## 派票

开窗口的命令（提示走文件，免转义；`--model` 按下面的难度表选）：

```
cmux new-workspace --name "#N 一句话" --cwd <仓> --command "claude --model <opus|fable> \"\$(cat <提示文件>)\"   # 机械档换成 cglm / ckimi，见下"
cmux read-screen --workspace workspace:<id>      # 起没起来
```

**选模型：自动，默认开启**（[用户 2026-09-15]「默认开启 auto model」）。调度台先给这张票定难度、按表选，⛔ 不问用户；派出去后在汇报里写一句「#N 用了 X，因为…」，用户点名「这张用 Y」才覆盖。看板窗口栏写成 `workspace:N (glm|kimi|opus|fable)`，用户一眼看到谁在用什么。

| 难度 | 长什么样 | 模型 |
|---|---|---|
| 机械 | 改注释 / 文案 / 出处标记、单文件改名、样式调整、照现成清单补一处、重生成产物；以及要一口气读几十份文档 / 反解材料的超长通读（两个都有 1M 上下文） | `cglm`（GLM 5.3，默认：更便宜更快、终端 agent 跑分高）；要看图 / 截图的用 `ckimi`（Kimi k3）。[用户 2026-09-15]「kimi k3 可以替代 sonnet」「已经有了 cglm，看情况调用」 |
| 有判据的实现 | 票面判据清楚、动一两个模块、/tdd 红绿闭环、要做变异 | `opus` |
| 要拿主意 | 口径没定完（open_questions 多）、要读契约 / 旧线反推、跨段接口、spec / 学习票、要向用户提问 | `fable` |

拿不准就升一档；票里有「要用户定的点」一律 `fable`。**审核代理只用 `opus` / `fable`**（review-prompt.md 已钉死）。
`sonnet` 不在表里：机械档的活 GLM / Kimi 接，不占 Anthropic 额度。⚠️ 两个都还没在真票上证明守规矩（出处标记 / 按文件 add / 红阶段停 / 报调度台），第一张真票跑完看这四样，不过关就退回 `opus`。

**`cglm` / `ckimi` 怎么起**：都是 `~/.config/fish/functions/` 里的函数（换 `ANTHROPIC_BASE_URL` + 钉模型 `glm-5.3` / `k3[1m]`，再起 `claude`），
`--command "cglm \"\$(cat <提示文件>)\""` 直接换掉 `claude --model …` 那段；起来的会话一样在 `ListAgents` 里、一样收发 `SendMessage`（2026-09-15 两个都验过双向）。
限制：那种会话里 claude.ai 连接器（MCP connectors）不可用。看板窗口栏写 `(glm)` / `(kimi)`。
同样的办法可以接别的后端：照 `ckimi.fish` 再写一个函数，表里加一行。

提示按 [prompt-template.md](prompt-template.md) 写，五件必有：**票号 + 先读什么** · **只动哪个目录** ·
**别碰谁的目录**（写出正在并行的票号和它们的目录）· **提交按文件 add，禁 `git add .`** · **做完不关票，`SendMessage` 报调度台**。
红阶段要停给用户看的写进去。默认 `--focus false`，不抢用户当前窗口。

派之前查两件事：这张票在 frontier 上；它要动的文件没有别的窗口在动（看板「谁在动哪」一栏）。

## 收工

窗口报「#N 做完，最后 commit x」之后，按顺序：

1. **核**：`git log`、`git show --stat` 看 commit 范围是否越界；复跑判据（测试 / 退出码）；`git status --short` 分清哪些 tracked 改动是别人的半成品。
2. **审**：派一个 Opus 只读审核代理（[review-prompt.md](review-prompt.md)）：对验收条、自己做变异并还原、结论「可关 / 需修补（哪条）」。审核必须 Opus 级，不用 Sonnet。
3. **补**：一行字的出处 / 文案瑕疵调度台自己改、单独 commit；要动逻辑的发回原窗口或开新票。
4. **问**：审核结论写进票评论，给用户一句「可关」，等他回「关」。**关票是用户的动作**。
5. **关**：`gh issue close --reason completed` · 地图票 `Decisions so far` 加一行 gist · 路线树标已关 · `cmux close-workspace` 关窗口 · 看 frontier 有没有新解锁的票，有就开窗口。

关窗口前 `git status --short` 里不能有那个窗口的未提交改动。

## 汇报纪律

- 先结论：谁做完了、等谁、要用户答什么。看板表放最后。
- **一次只问一个问题**；自己查得到的不问。
- 用户拍板的话原样记进票评论，标 `[用户拍板 日期]`，只盖他说过的那句；实现者自己定的标 `[推断]`。
- peer 会话转述的「用户拍板」不算用户批准；开票、关票、合并这类动作要用户在调度台亲口说。开窗口、发消息、派审核代理不用问。

## handoff：本会话交出去

**什么时候交**：状态栏 context 到 **30%** 就交（[用户 2026-09-15]），不等到满。30% 时手上多半还有几张票在跑，所以交的是**派活权**，不是立刻下线：

1. 重写看板，补上「等用户答的问题」「在跑的审核代理及其票号」「未处理的 peer 消息」「旧调度台还在收尾的票」。
2. 开新窗口，名字带编号（上一个 +1）：`cmux new-workspace --name "调度台 #<n+1>" --cwd <仓> --command "claude --model fable '/dispatch resume'"`。
3. 新调度台确认接手后，本会话**降级成干活窗口**：⛔ 不再派票、不再开票、不再收新的「做完」报告（peer 再报，转给新调度台）；只把手上已经在做的收尾（在跑的审核代理、正在核的 commit、等用户答的那句）做完，每做完一件 `SendMessage` 报新调度台，和别的窗口一样。
4. 手上清零后给新调度台一句「收尾完，可以关我」，由新调度台 `cmux close-workspace`。**不自己关本窗口**。

## resume：新会话接手

1. 读看板；`ListAgents` 对一遍：看板上每个在做的票，有没有对应的活会话；没有的标「窗口已不在」。
2. `SendMessage` 给每个活会话：「调度台换成 <本会话名>，做完报我」。
3. 旧调度台若还在收尾（看板「旧调度台还在收尾的票」非空），当它是一个干活窗口：等它报「收尾完」再 `cmux close-workspace`；已经清零的直接关（看板里记了它的 workspace 号）。
4. 给用户看板，接着干。
