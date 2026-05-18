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

---

## milwaukee-ppt — quick reference

Milwaukee Tool 品牌 PPT 生成。一份 `content.yaml` 同时产出浏览器预览（HTML）和最终交付（`.pptx`），双轨像素级对齐。

### 安装依赖（一次）

```bash
cd skills/milwaukee-ppt
python3 -m venv .venv && source .venv/bin/activate
pip install python-pptx PyYAML Jinja2 Pillow pytest
```

### 三步工作流

```bash
# 1) 写内容（拷贝样例当起点）
cp sample/content.yaml my_deck.yaml
# 编辑 my_deck.yaml — 改标题、bullets、表格等

# 2) 浏览器预览 / 规划 / 演讲
python scripts/fill_html.py my_deck.yaml --out ~/talks/my-deck/
open ~/talks/my-deck/index.html
# ← → 翻页 / S 演讲者模式 / F 全屏（需 html-ppt skill 提供 runtime.js）
# 改内容 → 重跑 fill_html.py → 浏览器刷新即可迭代

# 3) 出最终 .pptx
python scripts/build_ppt.py my_deck.yaml --out my-deck.pptx
python scripts/polish.py my-deck.pptx   # 可选 linter
```

### content.yaml 支持的 9 种 slide type

| type | 必填字段 | 说明 |
|---|---|---|
| `title` | — | 仅红横幅（标题 + 副标题），内容区空白 |
| `text` | `blocks: [{text, bold?, size?, color?}]` | 多段正文 |
| `bullets` | `items: [str]` | 项目符号列表 |
| `table` | `rows: [[str]]` | 首行表头（红底白字） |
| `kpi` | `value`, `label` | 巨大数字 + 说明 |
| `quote` | `text`, `author?` | 居中斜体引述 |
| `section` | `text?` | 章节封面（默认用 title） |
| `image` | `path`, `caption?` | 嵌入图片 |
| `columns` | `columns: [{head, body}]` | 多列并排 |

每页都可选加 `title` / `subtitle`，会渲染到红横幅。完整样例见 `skills/milwaukee-ppt/sample/content.yaml`。

### 品牌规范（自动应用，无需配置）

- 主色 `#DB011C`、Canvas 1280×720 px @ 96 DPI
- 红横幅 96 px、左上 Milwaukee logo (8,8) 176×79、底部 16 px confidential footer
- 横幅标题 24 pt 白色粗体右对齐、副标题 15 pt 白色右对齐
- 英文 Calibri / 中文 Microsoft JhengHei（macOS fallback：PingFang TC, Heiti TC, Noto Sans TC）

改 `assets/tokens.json` 同时影响 HTML 和 PPT 输出。完整文档见 [`skills/milwaukee-ppt/SKILL.md`](skills/milwaukee-ppt/SKILL.md)。

### 进阶：imperative API（绕过 YAML）

```python
import sys; sys.path.insert(0, "skills/milwaukee-ppt/scripts")
from build_ppt import MilwaukeeDeck

deck = MilwaukeeDeck()
deck.add_slide("KEY FEATURES", "Why M18 FUEL").add_bullets(["POWERSTATE 电机", "REDLINK 保护"])
deck.add_slide("SPEC").add_table([["Model","Torque"],["A","1000Nm"]])
deck.save("out.pptx")
```

`_Slide` 方法：`add_paragraphs / add_bullets / add_table / add_image / add_kpi / add_quote / add_section_divider / columns / add_speaker_notes`。
