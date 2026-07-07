#!/bin/sh
# sediment-basin — Claude Code PostToolUse hook (matcher: Bash).
# Fires after every Bash tool call; acts only when the command was a git commit.
# On a commit, it nudges the model to invoke the sediment-basin skill to log
# learnings, check promotion thresholds, and (if overdue) prompt a monthly review.
# Detection/judgement lives in the skill (model in the loop); this script is a dumb trigger.

input=$(cat)

case "$input" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

# Emit the reminder as additionalContext so it reaches the model.
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[sediment-basin] 刚做了一次 git commit。请评估本次会话/改动里有没有值得沉淀的经验(重复指令/解决的难题/反复纠正/明确偏好);有则调用 sediment-basin skill 记进本项目 .sediment/ledger.md(先搜后铸 Pattern-Key,同款则复发+1 并追加本次 commit SHA);检查有无条目达到成岩阈值需冒泡转正;并对照账本 last-review 日期,若超过窗口天数则提醒用户做月度复盘。没有值得沉淀的就忽略,不要硬凑。"}}
JSON

exit 0
