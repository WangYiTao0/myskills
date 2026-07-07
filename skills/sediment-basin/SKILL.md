---
name: sediment-basin
description: 经验账本(累积器)。把值得沉淀的经验持久记进每项目的 .sediment/ledger.md,按 Pattern-Key 去重、累加复发,达到成岩阈值(默认复发≥3 × 跨2 commit × 30天内)时冒泡请人转正、写进 CLAUDE.md 或抽成新 skill。当 commit 后 hook 提醒记账、用户想累积/查看经验账本、处理转正、做月度复盘,或提到"记进账本""沉积账本""看账本""该转正吗""月度复盘"时使用。与只诊断不落库的 sediment 分工:sediment 出主意,sediment-basin 落库、去重、改文件。
---

# 经验账本 · Sediment Basin

sediment(顾问)只诊断、不写文件、只看当前会话。**本 skill 承接落库的脏活**:把经验持久堆进账本、按 Pattern-Key 去重计数,攒够火候才转正进 CLAUDE.md。分工同构于参考里 self-improvement / self-healing。

## 账本在哪

每个项目根目录一份 `.sediment/ledger.md`。没有就按 [assets/ledger-template.md](assets/ledger-template.md) 建一个。账本头部三行控制参数(可改):

```
<!-- config: 复发阈值=3 跨commit阈值=2 窗口天数=30 -->
<!-- last-review: YYYY-MM-DD -->
```

账本本身就是"方便翻看的文档"——每条经验一个 markdown 小块,直接读就行。

## 记一条经验(先搜后铸)

commit 后 hook 会提醒你来记。判断这次会话/改动里有没有值得沉淀的(标准同 sediment 四类信号:重复指令 / 解决的难题 / 反复纠正 / 明确偏好)。**没有就别硬凑,直接跳过。** 有的话:

1. **先搜**:在 `.sediment/ledger.md` 里搜有没有语义同款的 Pattern-Key。
   - `grep -n "^### " .sediment/ledger.md` 先看现有键,再判断是否同款。
2. **命中同款** → 该条 `复发` +1、把本次 commit SHA 追加进 commits 列表、刷新 `末见` 日期。
3. **没命中** → 新建一条,`复发: 1`,记 `首见`/`末见` 与首个 commit SHA。

**Pattern-Key 命名走 `域.slug`**(如 `voice.no-hype`、`ppt.center-lines`、`git.no-force-push`)。这道"先搜后铸"纪律是去重的命门——偷懒不搜、铸出近义键,复发就永远攒不到阈值、什么都不会转正。

### 条目格式

```markdown
### [SED-YYYYMMDD-XXX] 域.slug
- 状态: 待处理
- 复发: 2 · commits: a1b2c3 · d4e5f6
- 首见: 2026-07-01 · 末见: 2026-07-05
- 摘要: 一句话:这条经验是什么
- 预防规则: 一句"以后编码前/中该怎么做"(转正时抄进 CLAUDE.md)
- 去向: CLAUDE.md | skill | 未定
```

`预防规则` 一栏记的时候就顺手想好——写"下次该做什么"的短句,不是事故复盘长文。这样转正时直接抄,也逼自己想清楚这条到底可不可执行。

## 成岩阈值 → 转正

一条经验够格转正,三条**同时**满足(数字读账本头部 config,默认 3 / 2 / 30):

- `复发` ≥ 复发阈值(默认 3)
- commits 列表里 ≥ 跨commit阈值 个不同 SHA(默认 2)
- 首见与末见都落在 窗口天数(默认 30)内

### 两条转正通道

- **自动够格**:记账时发现某条刚好越过阈值 → **冒泡**问人:"`域.slug` 成岩了(复发N/跨M commit/窗口内),转正吗?" 人点头才写。
- **手动放行**:人一眼看中某条,不必等凑满阈值,直接说"这条转正"。防单人/单项目场景阈值太严、好经验永远卡在账本里。

### 转正怎么写

人点头后,把 `预防规则` 那句蒸馏干净,写进**目标项目自己的 CLAUDE.md**(短预防规则,别搬长文)。然后把该条 `状态` 改成 `已晋升`。

**第二去向——抽成 skill**:如果这条不只反复、还广泛通用(跨项目也用得上),比起塞进 CLAUDE.md,更该抽成一个可复用 skill(对应老 sediment 的"做成 skill"分支)。这种情况调用 write-a-skill,起草后把 `状态` 改成 `已抽成skill`。

## 条目状态

`待处理` → `已晋升` / `已抽成skill` / `已丢弃`。记账、冒泡前先看状态,**别对已处理的条目反复冒泡**。判定这条一次性、不会再犯的,标 `已丢弃`。

## 看账本

用户说"看账本"时,读 `.sediment/ledger.md`,渲染一张速览表(状态 / Pattern-Key / 复发 / 跨commit / 末见 / 摘要),按"快成岩的"排前面,让人一眼看清攒了啥、谁临门一脚。

## 月度复盘提示

记账时对照账本头部 `last-review` 日期:距今超过 窗口天数(默认30)就提醒用户:"距上次复盘 N 天了,要不要翻一遍账本?" 复盘做完把 `last-review` 更新为当天。

复盘时顺手做一次**近义键体检**:扫一遍 Pattern-Key,把语义重复、实则同一坑的近义键合并(复发次数相加),兜底去重漂移。

## Hook 安装

本 skill 靠一个 Claude Code PostToolUse hook 在 commit 后自动提醒记账。脚本在 [hooks/on-commit.sh](hooks/on-commit.sh)。在全局 `~/.claude/settings.json` 里挂:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "/Users/mitumao/Repo/myskills/skills/sediment-basin/hooks/on-commit.sh" }
        ]
      }
    ]
  }
}
```

脚本只在 Bash 命令含 `git commit` 时才发提醒,其余时候静默退出。换机器 / 只用插件安装版时,把 command 路径改到脚本实际位置即可。

## 重要约束

- **记账、改 CLAUDE.md 前,值得沉淀的才动手。** 宁可跳过,别把一次性小事灌进账本——账本膨胀就没人看了。
- **转正写 CLAUDE.md 一定先冒泡问人**(手动放行除外,那本就是人主动)。这是沉淀家族"人守最后一闸"的基因。
- 阈值三个数字都可调,嫌严就在账本 config 里改松。
