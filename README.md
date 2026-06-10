# myskills

Personal Claude Code plugin marketplace — a collection of custom skills for daily workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [milwaukee-ppt](skills/milwaukee-ppt/) | Milwaukee Tool 工作汇报 PPT 的格式与视觉规范（品牌锚点、Agenda/PDCA、标题三层结构） |
| [pbip-mcp-workflow](skills/pbip-mcp-workflow/) | PBIP + powerbi-modeling MCP 安全工作流规则 |
| [ppt-design-principles](skills/ppt-design-principles/) | 《写给大家看的设计书》CRAP 四原则浓缩版 — PPT 单页视觉判断框架 |
| [prompt-advise](skills/prompt-advise/) | 把模糊需求扩展成几个实质不同的候选 prompt，选定后执行或复制 |
| [report-voice](skills/report-voice/) | 工作汇报/邮件/公告的务实用词规范 — 剔除浮夸空洞表达 |
| [sediment](skills/sediment/) | 复盘会话，沉淀经验为 skill / CLAUDE.md 规则 / 记忆 |

每个 skill 的完整说明见对应目录下的 `SKILL.md`。

## Installation

### Via Claude Code plugin system

```bash
/plugin marketplace add WangYiTao0/myskills
```

### Via npx

```bash
npx skills add WangYiTao0/myskills
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

## Repo conventions

- 每个 skill 一个目录：`skills/<name>/SKILL.md`（必须），按需加 `references/`、`assets/`、`scripts/`
- `SKILL.md` frontmatter 的 `description` 写"什么时候用 + 触发关键词"，不是"这是什么"
- 版本号只维护在 `.claude-plugin/marketplace.json` 一处
- 新增/修改 skill 后运行校验：

```bash
python3 scripts/validate.py
```

校验内容：marketplace.json 与 `skills/` 目录一一对应、SKILL.md 存在且 frontmatter 完整、无游离文件。
