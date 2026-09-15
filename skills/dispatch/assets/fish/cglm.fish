function cglm --description 'Claude Code CLI on GLM 5.3 backend (Zhipu bigmodel.cn, 1M context)'
    # 密钥从环境变量读取，不硬编码。首次使用前执行：
    #   set -Ux GLM_API_KEY <你的智谱密钥>
    # 与 glm（GLM 5.2）共用同一个智谱密钥。
    if not set -q GLM_API_KEY
        echo "cglm: 环境变量 GLM_API_KEY 未设置。" >&2
        echo "      先运行: set -Ux GLM_API_KEY <你的智谱密钥>" >&2
        return 1
    end

    # 仅在本函数作用域内导出，不影响原生 claude（-l 局部 + -x 导出给子进程）
    set -lx ANTHROPIC_BASE_URL https://open.bigmodel.cn/api/anthropic
    set -lx ANTHROPIC_AUTH_TOKEN $GLM_API_KEY

    # GLM-5.3 原生支持 1M 上下文，不需要像 5.2 那样额外加 [1M] 后缀。
    # 思考强度：GLM-5.3 读的是顶层 reasoning_effort 字段（low/high/max，默认 max），
    # 跟 Claude Code 自己的 CLAUDE_CODE_EFFORT_LEVEL（写进 output_config.effort，
    # 只有 Anthropic 自家模型认）不是一回事，设了也传不到位。默认已经是 max，不用设。
    set -l model glm-5.3
    set -lx ANTHROPIC_MODEL $model
    set -lx ANTHROPIC_REASONING_MODEL $model
    set -lx ANTHROPIC_DEFAULT_OPUS_MODEL $model
    set -lx ANTHROPIC_DEFAULT_SONNET_MODEL $model
    set -lx ANTHROPIC_DEFAULT_FABLE_MODEL $model
    set -lx ANTHROPIC_DEFAULT_HAIKU_MODEL $model
    set -lx ANTHROPIC_DEFAULT_OPUS_MODEL_NAME $model
    set -lx ANTHROPIC_DEFAULT_SONNET_MODEL_NAME $model
    set -lx ANTHROPIC_DEFAULT_FABLE_MODEL_NAME $model
    set -lx ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME $model
    set -lx CLAUDE_CODE_SUBAGENT_MODEL $model

    set -lx CLAUDE_CODE_MAX_CONTEXT_TOKENS 1048576
    set -lx CLAUDE_CODE_AUTO_COMPACT_WINDOW 1048576

    command claude $argv
end
