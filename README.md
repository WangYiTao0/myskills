# myskills

Personal Claude Code plugin — a collection of custom skills for daily workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [milwaukee-ppt](skills/milwaukee-ppt/) | Milwaukee Tool 工作汇报格式规范 — 输出 NotebookLM Markdown |
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

---

## milwaukee-ppt — quick reference

Milwaukee Tool 工作汇报**格式规范**。强制执行固定 Agenda 顺序、PDCA 阶段标注、"已落地 vs 未来"严格分离、标题三层结构。**输出 Markdown 文档**，用户把它喂给 NotebookLM 渲染成最终 PPT。本 skill 不直接生成 .pptx。

### 五条强制规则（违反任一会被驳回）

1. **Agenda 8 节固定顺序**：项目背景 → 项目目标 → 项目范围 → 项目应用场景 → 项目节点 → 项目行动与成果 → 项目团队 → 持续优化与经验沉淀
2. **PDCA 标注**：每节标 `P` / `D` / `C` / `A`，做成正文区右上角的小图标（不写进红 banner 副标题）
3. **不写未来**：禁止 Next Step / Roadmap / 画饼（月报底部"下一步计划"是唯一例外，且必须是已确定、有 owner、有时间的动作）
4. **标题三层**：主标题（话题）+ 副标题（action title）+ 正文 lead（结论 + 数据）
5. **每节一个核心信息**：超出就拆，不要塞满

### 交付物

- 一份 Markdown 文档：每张 slide 用 `---` 分隔，块内含 `layout` / `section` / `pdca` / 三层标题 / 正文
- 一份图片建议清单：明确每张配图是 **Claude 生成** 还是 **必须用户提供**（实拍照、内部数据图表、含品牌识别的真实场景一律走"用户提供"）

### 资源（已内置，无需额外安装）

- 模板：`skills/milwaukee-ppt/assets/MS_Template.pptx`（顶部红 banner + 左上 logo + 底部页脚）
- Logo：`skills/milwaukee-ppt/assets/logo.png`
- 品牌色：Milwaukee Red `#DB011C`（红色累计面积 ≤ 画布 5%）

完整规范见 [`skills/milwaukee-ppt/SKILL.md`](skills/milwaukee-ppt/SKILL.md)。
