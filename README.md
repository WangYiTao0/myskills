# myskills

Personal Claude Code plugin — a collection of custom skills for daily workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [milwaukee-ppt](skills/milwaukee-ppt/) | 使用 Milwaukee Tool 品牌模板制作 PPT |
| [pq-splitter](skills/pq-splitter/) | 将 Power BI 合并的 Power Query 代码拆分为多个独立 `.m` 文件 |
| [pbip-mcp-workflow](skills/pbip-mcp-workflow/) | PBIP + powerbi-modeling MCP 安全工作流规则 |

## Installation

### Via npx (recommended)

```bash
npx skills add WangYiTao0/myskills
```

### Via Claude Code plugin system

```bash
/plugin marketplace add WangYiTao0/myskills
```

### Manual (local clone)

```jsonc
// ~/.claude/settings.json
{
  "plugins": [
    "/path/to/myskills"
  ]
}
```
