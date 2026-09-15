function ckimi --description 'Claude Code CLI on Kimi k3 (1M context) backend'
    # 密钥从环境变量读取，不硬编码。首次使用前执行：
    #   set -Ux KIMI_API_KEY <你的 Kimi Code 密钥>
    # 密钥在 https://www.kimi.com/code/console 「新建 API Key」处生成，只显示一次。
    if not set -q KIMI_API_KEY
        echo "ckimi: 环境变量 KIMI_API_KEY 未设置。" >&2
        echo "       先运行: set -Ux KIMI_API_KEY <你的 Kimi Code 密钥>" >&2
        echo "       密钥获取: https://www.kimi.com/code/console" >&2
        return 1
    end

    # 仅在本函数作用域内导出，不影响原生 claude（-l 局部 + -x 导出给子进程）
    set -lx ANTHROPIC_BASE_URL https://api.kimi.com/coding/
    set -lx ANTHROPIC_AUTH_TOKEN $KIMI_API_KEY
    set -lx ANTHROPIC_API_KEY $KIMI_API_KEY

    # k3[1m] 是 1M 上下文变体，只在 Claude Code 里这么写；必须加引号，
    # 否则 fish 会把 [..] 当通配符。需要 Allegretto 及以上会员等级。
    set -l model "k3[1m]"
    set -lx ANTHROPIC_MODEL $model
    set -lx ANTHROPIC_DEFAULT_OPUS_MODEL $model
    set -lx ANTHROPIC_DEFAULT_SONNET_MODEL $model
    set -lx ANTHROPIC_DEFAULT_FABLE_MODEL $model
    set -lx ANTHROPIC_DEFAULT_HAIKU_MODEL $model
    set -lx CLAUDE_CODE_SUBAGENT_MODEL $model

    # 注意：CLAUDE_CODE_EFFORT_LEVEL 最终写进请求体的是 Anthropic 自家的
    # output_config.effort 字段，Kimi 读的是自己的顶层 reasoning_effort 字段，
    # 两者不通，设了也没用。Kimi k3 的 reasoning_effort 默认值本来就是 max，
    # 不设反而是对的（想改成 low/high 需要 Kimi 那边支持透传自定义字段才行）。
    set -lx CLAUDE_CODE_MAX_CONTEXT_TOKENS 1048576
    set -lx CLAUDE_CODE_AUTO_COMPACT_WINDOW 1048576

    command claude $argv
end
