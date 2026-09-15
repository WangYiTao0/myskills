# 换电脑配置清单（dispatch 调度台）

这份 skill 不是纯提示词，它依赖机器上的几样东西。换电脑照下面逐项装，最后跑「自检」一节。
记录日期 2026-09-15，在 macOS + fish 上验证过。

## 1. 装 skill 本体

二选一：

- **软链接**（推荐，只保留一份、改了即生效）：
  ```bash
  ln -s ~/Repo/myskills/skills/dispatch ~/.claude/skills/dispatch
  ```
- 或走 plugin：`/plugin marketplace add WangYiTao0/myskills` 后启用 `dispatch`。

⚠️ 老电脑（2026-09-15 那台）上 `~/.claude/skills/dispatch` 是**真目录**不是软链接，和仓里这份是两份拷贝，改的时候要同步。

`SKILL.md` frontmatter 有 `disable-model-invocation: true`：只能用户手打 `/dispatch`，模型不会自己触发。

## 2. cmux（终端多窗口，派票就是开它的窗口）

- 装：<https://cmux.dev>（macOS app，装到 `/Applications/cmux.app`；CLI 在 `/Applications/cmux.app/Contents/Resources/bin/cmux`，装完 `which cmux` 要能找到）。验证过的版本 **0.64.23**。
- skill 用到的命令（都在 SKILL.md 里出现过）：

  | 干什么 | 命令 |
  |---|---|
  | 列窗口 | `cmux workspace list` |
  | 开窗口派票 | `cmux new-workspace --name "#N 一句话" --cwd <仓> --command "claude --model opus \"\$(cat <提示文件>)\"" --focus false` |
  | 看起没起来 | `cmux read-screen --workspace workspace:<id>` |
  | 改窗口名 | `cmux workspace rename --workspace workspace:<id> --title "调度台 #3"`（⚠️ 是 `--title` 不是位置参数） |
  | 关窗口 | `cmux close-workspace --workspace workspace:<id>` |

- 坑：**被 pin 住的窗口 CLI 关不掉**，而且 0.64.23 没有 `unpin` 子命令，只能用户在界面上手动取消固定。
- `new-workspace` / `close-workspace` / `read-screen` 是旧写法的别名，每次会打一行提示；`set -Ux CMUX_QUIET=1` 或命令前加 `CMUX_QUIET=1` 静音。

## 3. 便宜后端：`cglm` / `ckimi`（fish 函数）

两个函数在本目录 `assets/fish/` 里，拷到 fish 的函数目录即生效（fish 自动按文件名懒加载，不用 source）：

```bash
cp ~/Repo/myskills/skills/dispatch/assets/fish/*.fish ~/.config/fish/functions/
```

然后各设一个密钥（函数里只读环境变量，**不写死**）：

```fish
set -Ux GLM_API_KEY  <智谱 bigmodel.cn 的密钥>      # cglm：GLM 5.3，1M 上下文
set -Ux KIMI_API_KEY <Kimi Code 密钥>              # ckimi：Kimi k3[1m]，1M 上下文
```

- GLM 密钥：智谱开放平台，和 GLM 5.2 的 `glm` 函数共用一把。
- Kimi 密钥：<https://www.kimi.com/code/console> 「新建 API Key」，只显示一次；`k3[1m]` 要 Allegretto 及以上会员等级。
- 原理：函数在局部作用域换 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`、把所有 `ANTHROPIC_DEFAULT_*_MODEL` 钉成那一个模型，再 `command claude $argv`。不影响原生 `claude`。
- 派票时把 `claude --model opus "$(cat 提示)"` 换成 `cglm "$(cat 提示)"` 即可；起来的会话一样在 `ListAgents` 里、一样收发 `SendMessage`（2026-09-15 两个都验过双向）。
- 限制：这种会话里 claude.ai 连接器（Gmail / Drive 这类 MCP connectors）不可用；要看图 / 截图的票用 `ckimi`，GLM 那边没验过看图。
- 要接别的后端：照 `ckimi.fish` 再写一个函数，SKILL.md 难度表加一行。
- 不用 fish 的话：把那几个 `set -lx` 改成 `export`，逻辑一样。

## 4. 其他依赖

| 东西 | 要求 | 备注 |
|---|---|---|
| `claude` CLI | 要能 `--model opus` / `--model fable` | 审核代理只用 opus / fable（review-prompt.md 钉死） |
| `gh` CLI | `gh auth login` 过 | 票在 GitHub issue；目录名 ≠ 远端仓名的仓一律显式 `--repo owner/repo` |
| 看板目录 | `mkdir -p ~/.claude/dispatch` | 看板文件 `~/.claude/dispatch/<仓目录名>.md`，换电脑把旧看板一起拷过去就能 `/dispatch resume` |
| 审核工作树落点 | `~/Repo/.worktrees/review-<票号>` | `git worktree add --detach ~/Repo/.worktrees/review-N HEAD`；⛔ 别放仓里的 `.claude/worktrees/`（会被当项目文件） |
| 跨会话消息 | 干活窗口和调度台要在**同一台机器、同一权限模式档**（都开 auto mode 最省事） | 不同档时 `SendMessage` 会被对方挂起等它的用户批准 |

## 5. 还没装的：context 30% 自动 handoff

SKILL.md 说 context 到 30% 就交派活权，目前靠人看状态栏。自动触发的设计（2026-09-15 提过、**未装**）：

1. statusline 脚本把 `used_percentage` 写到 `/tmp/claude-ctx-<session_id>`；
2. `UserPromptSubmit` hook 读它，≥ 30% 就注入一行「context N%：/dispatch handoff」；
3. 装法走 `update-config` skill 改 `~/.claude/settings.json` + `statusline-command.sh`。

装了以后在这里把「未装」改掉。

## 6. 自检（全过才算装好）

```bash
which cmux && cmux workspace list          # 能列出窗口
gh auth status                              # 已登录
ls ~/.claude/skills/dispatch/SKILL.md       # skill 在位
ls ~/.claude/dispatch/                      # 看板目录在
type cglm ckimi                             # 两个函数认得
set -q GLM_API_KEY; and set -q KIMI_API_KEY; and echo keys ok
```

再开一个 `cglm` 窗口，在调度台里 `ListAgents` 看得见它、`SendMessage` 发过去它能回，才算通。
