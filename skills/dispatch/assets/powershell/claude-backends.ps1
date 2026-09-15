# cglm / ckimi 的 PowerShell 版 —— 和 assets/fish/*.fish 同一套逻辑：
# 换 ANTHROPIC_BASE_URL + 钉模型，再起 claude；用完把环境变量还原，不影响原生 claude。
# 装法：把本文件内容贴进 $PROFILE（notepad $PROFILE），或在 $PROFILE 里加一行：
#   . "$HOME\Repo\myskills\skills\dispatch\assets\powershell\claude-backends.ps1"
# 密钥先设成用户级环境变量（只设一次，新开的窗口都能读到）：
#   [Environment]::SetEnvironmentVariable('GLM_API_KEY',  '<智谱密钥>',     'User')
#   [Environment]::SetEnvironmentVariable('KIMI_API_KEY', '<Kimi Code 密钥>', 'User')

function Invoke-ClaudeWithBackend {
    param(
        [Parameter(Mandatory)] [string] $BaseUrl,
        [Parameter(Mandatory)] [string] $Token,
        [Parameter(Mandatory)] [string] $Model,
        [string[]] $ClaudeArgs = @()
    )
    $names = @(
        'ANTHROPIC_BASE_URL', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_API_KEY',
        'ANTHROPIC_MODEL', 'ANTHROPIC_REASONING_MODEL',
        'ANTHROPIC_DEFAULT_OPUS_MODEL', 'ANTHROPIC_DEFAULT_SONNET_MODEL',
        'ANTHROPIC_DEFAULT_FABLE_MODEL', 'ANTHROPIC_DEFAULT_HAIKU_MODEL',
        'ANTHROPIC_DEFAULT_OPUS_MODEL_NAME', 'ANTHROPIC_DEFAULT_SONNET_MODEL_NAME',
        'ANTHROPIC_DEFAULT_FABLE_MODEL_NAME', 'ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME',
        'CLAUDE_CODE_SUBAGENT_MODEL',
        'CLAUDE_CODE_MAX_CONTEXT_TOKENS', 'CLAUDE_CODE_AUTO_COMPACT_WINDOW'
    )
    # 环境变量是进程级的，函数退出不会自动还原，所以先存后还
    $saved = @{}
    foreach ($n in $names) { $saved[$n] = [Environment]::GetEnvironmentVariable($n, 'Process') }
    try {
        $env:ANTHROPIC_BASE_URL = $BaseUrl
        $env:ANTHROPIC_AUTH_TOKEN = $Token
        $env:ANTHROPIC_API_KEY = $Token
        foreach ($n in $names) {
            if ($n -like 'ANTHROPIC_*MODEL*' -or $n -eq 'CLAUDE_CODE_SUBAGENT_MODEL') {
                [Environment]::SetEnvironmentVariable($n, $Model, 'Process')
            }
        }
        $env:CLAUDE_CODE_MAX_CONTEXT_TOKENS = '1048576'
        $env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = '1048576'
        & claude @ClaudeArgs
    }
    finally {
        foreach ($n in $names) { [Environment]::SetEnvironmentVariable($n, $saved[$n], 'Process') }
    }
}

# GLM 5.3（智谱 bigmodel.cn，1M 上下文）
function cglm {
    if (-not $env:GLM_API_KEY) {
        Write-Error "cglm: 环境变量 GLM_API_KEY 未设置。先运行: [Environment]::SetEnvironmentVariable('GLM_API_KEY','<智谱密钥>','User') 然后重开窗口"
        return
    }
    Invoke-ClaudeWithBackend -BaseUrl 'https://open.bigmodel.cn/api/anthropic' -Token $env:GLM_API_KEY -Model 'glm-5.3' -ClaudeArgs $args
}

# Kimi k3（1M 上下文变体 k3[1m]，要 Allegretto 及以上会员）
function ckimi {
    if (-not $env:KIMI_API_KEY) {
        Write-Error "ckimi: 环境变量 KIMI_API_KEY 未设置。密钥在 https://www.kimi.com/code/console 生成，然后 [Environment]::SetEnvironmentVariable('KIMI_API_KEY','<密钥>','User') 并重开窗口"
        return
    }
    Invoke-ClaudeWithBackend -BaseUrl 'https://api.kimi.com/coding/' -Token $env:KIMI_API_KEY -Model 'k3[1m]' -ClaudeArgs $args
}

# 派票开窗口（Windows Terminal）。用法：
#   New-DispatchWindow -Title "#167 UPH 源表" -Repo "$HOME\Repo\X" -PromptFile "$env:TEMP\p167.txt" -Launcher opus
#   -Launcher 取 opus / fable（走原生 claude --model）或 glm / kimi（走上面两个函数）
function New-DispatchWindow {
    param(
        [Parameter(Mandatory)] [string] $Title,
        [Parameter(Mandatory)] [string] $Repo,
        [Parameter(Mandatory)] [string] $PromptFile,
        [ValidateSet('opus', 'fable', 'glm', 'kimi')] [string] $Launcher = 'opus'
    )
    $launch = switch ($Launcher) {
        'glm'  { 'cglm' }
        'kimi' { 'ckimi' }
        default { "claude --model $Launcher" }
    }
    # -Raw 整文件当一个参数；提示走文件就不用管转义
    $cmd = "$launch (Get-Content -Raw -LiteralPath '$PromptFile')"
    if (Get-Command wt -ErrorAction SilentlyContinue) {
        # -w 0 = 开在当前 Windows Terminal 窗口里当新标签；nt = new-tab
        wt -w 0 nt --title $Title -d $Repo pwsh -NoExit -Command $cmd
    } else {
        Start-Process pwsh -WorkingDirectory $Repo -ArgumentList '-NoExit', '-Command', $cmd
    }
}
