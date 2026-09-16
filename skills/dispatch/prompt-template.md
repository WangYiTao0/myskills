# 派票提示模板

写到 scratchpad 文件里，`claude "$(cat 文件)"` 起窗口。尖括号处换掉，其余照抄。

```
接票 #<N>「<票标题>」。先 gh issue view <N> --repo <owner/repo> --comments 读票面和决议，
再读 <本段的 CLAUDE.md / spec / 开发步骤>，按 /tdd 做，红阶段停一次给用户看。
⭐ 每条测试写一行 docstring 说「这条钉住什么」，用人话、带一张真工单或真料号、带出处标记；
讲业务规则的测试夹具用真单号（纯结构测试不用）。红阶段报告要过闸门：
`uv run pytest -q --tb=no > /tmp/红-<N>.txt` → `python ~/Repo/myskills/skills/dispatch/assets/红阶段清单.py <测试目录> --红 /tmp/红-<N>.txt`，
退出码必须是 0（有 ⛔ 说明还有测试没写钉住什么）。清单**原样**发给调度台，⛔ 别自己重新总结一遍。
背景：<上游刚落地的事实，一两句，例：#142 已关，中间表多了 FIRST_ISSUE_DATE 列>。
约束：只动 <目录 A> 和字典里自己的新词条；
⛔ 不动 <目录 B>（#<M> 另一个窗口正在改它）、<目录 C>（#<K> 在做）、<旧线目录>、HANDOFF.md；
提交按文件 git add，⛔ 禁 git add .；⛔ 禁 git commit --amend / git reset / git rebase（同仓多窗口并行，HEAD 随时是别人的 commit —— 2026-09-16 #144 窗口 --amend 把 #166 的字典 commit 改写成了自己的提交信息）；写错了提交信息就再提一条更正，别改历史；
跑全量看到 <别人半成品的红长什么样> 是 #<M> 的，不是你的<（要的话给排除参数）>。
状态一变自己挪 cmux 侧栏分组（$CMUX_WORKSPACE_ID 是你所在窗口，shell 里已有；组号见调度台看板）：
  开始写代码 / 文档、用户点头后转绿 → cmux workspace-group add --group <执行中组> --workspace $CMUX_WORKSPACE_ID && cmux workspace status set working
  停在红阶段 / 等用户拍板        → cmux workspace-group add --group <待你确认组> --workspace $CMUX_WORKSPACE_ID && cmux workspace status set needs-attention
  做完报调度台之后              → cmux workspace-group add --group <待审核组> --workspace $CMUX_WORKSPACE_ID && cmux workspace status set review
做完不关票，发消息给调度台会话 <调度台名> 报「#<N> 做完，最后 commit xxx<，本票要用户定的点是 …>」。
红阶段先报一次：⛔ 别把清单贴给调度台（它不转给用户，用户会自己来窗口看），
只报「闸门过了，N 条红，清单在窗口里」+ 每个要用户拍板的点写成四行 ——
【N】标题 / 背景一句 / 一个具体工单的例子（带真数字）/ 二选一 / 你倾向哪个、选另一个会怎样。
```

要点：
- 「别碰谁」要写票号 + 目录，实现者才判断得了自己改的文件归谁。
- 上游刚改过的文件点名（「先 git log -3 看一眼」），免得它基于旧印象写。
- 半成品的红先告诉它长什么样，它就不会去修别人的东西。
- 清单是**他到窗口时读的**（[用户 2026-09-16]「我去窗口主要是看红的测试到底在钉什么」），
  docstring 写好了他这一趟就快。⛔ 别往调度台贴 —— 216 条汇总成一张他读不下去，试过了。
- 挪组由窗口自己做（[用户 2026-09-16]「要有个机制让它自动换组」）：用户在窗口里点头、窗口转绿这一步调度台看不见，只有窗口自己知道；调度台收到「做完」时再对一遍组。
