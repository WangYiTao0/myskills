---
name: milwaukee-ppt
description: Milwaukee Tool 品牌 PPT 生成（需配合 html-ppt skill 提供浏览器预览运行时）。当用户明确提到"Milwaukee 模板"、"Milwaukee PPT"、"MS 模板"、"Milwaukee slide"、"Milwaukee 品牌简报"，或上传了 MS_-_Template1.pptx / 当前 skill 的 template.pptx 并要求制作演示文稿时使用。仅在 Milwaukee 品牌上下文下触发——不要因为用户单纯说"做个PPT"就启用。
requires:
  skills: [html-ppt]
---

# Milwaukee Tool PPT Skill

跨平台（macOS / Linux）。**双轨**：一份 `content.yaml` 同时驱动浏览器预览（HTML）和最终 `.pptx` 交付。

## 依赖

- **html-ppt skill**（必装）：提供 HTML deck 的浏览器运行时（`runtime.js` 键盘导航 + 演讲者模式、`base.css` 排版基线、`scripts/render.sh` PNG 导出）。本 skill 在生成 HTML 时会从已安装的 html-ppt 目录拷贝这两个文件到输出 deck 文件夹。
  - 通过 `npx skills add WangYiTao0/myskills` 安装本仓库时，`skills-lock.json` 会自动同步安装 html-ppt
  - 手动安装：`npx skills add lewislulu/html-ppt-skill`
  - 已安装但路径不在默认搜索范围：传 `--html-ppt-dir <path>` 或设置环境变量 `HTML_PPT_SKILL_DIR`
- **Python 包**：`python-pptx`、`PyYAML`、`Jinja2`、`Pillow`（可选）、`pytest`（可选，跑测试）
- **LibreOffice + poppler**（可选，PPT → PDF → PNG 验证用）：`brew install --cask libreoffice && brew install poppler`

## 工作流

```bash
# 0) 装依赖（一次）
cd skills/milwaukee-ppt
python3 -m venv .venv && source .venv/bin/activate
pip install python-pptx PyYAML Jinja2 Pillow pytest

# 1) 写内容
cp sample/content.yaml my_deck.yaml
# 编辑 my_deck.yaml

# 2) 浏览器预览 / 规划 / 演讲（依赖 html-ppt skill 提供 runtime.js）
python scripts/fill_html.py my_deck.yaml --out ~/talks/my-deck/
open ~/talks/my-deck/index.html
# ← → 翻页、S 演讲者模式、F 全屏（如 runtime.js 可用）
# 改 → 重跑 fill_html.py → 浏览器刷新

# 3) 出 .pptx
python scripts/build_ppt.py my_deck.yaml --out my-deck.pptx

# 4) Linter（可选）
python scripts/polish.py my-deck.pptx
```

## content.yaml schema

支持 9 种 slide `type`，每页可选 `title` + `subtitle`（嵌入红横幅）：

| type | 必填字段 | 说明 |
|---|---|---|
| `title` | — | 仅红横幅显示，内容区空白 |
| `text` | `blocks: [{text, bold?, size?, color?}]` | 多段正文 |
| `bullets` | `items: [str]` | 项目符号列表 |
| `table` | `rows: [[str]]` | 首行表头（红底白字） |
| `kpi` | `value`, `label` | 巨大数字 + 说明 |
| `quote` | `text`, `author?` | 居中斜体引述 |
| `section` | `text?` | 章节封面（默认用 title） |
| `image` | `path`, `caption?` | 嵌入图片 |
| `columns` | `columns: [{head, body}]` | 多列并排 |

完整样例见 `sample/content.yaml`。

## 品牌规范（来源：`assets/tokens.json` + template.pptx 实测）

| 元素 | 值 |
|---|---|
| 主色 | `#DB011C`（PPT 模板 Rectangle 3 fill 实测） |
| Canvas | 1280×720 px @ 96 DPI（= 13.333" × 7.5"） |
| 红横幅 | 顶部满宽，高 96 px |
| Logo | 左上 (8, 8)，176×79 px |
| Footer | 底部 16 px："**Confidential Document** Property of MILWAUKEE TOOL Brookfield, Wisconsin 53005" |
| 内容区 | top=96 px（横幅下）/ bottom=696 px（footer 上） |
| 横幅标题 | 24 pt 白色粗体大写右对齐 |
| 横幅副标题 | 15 pt 白色右对齐 |
| 英文字体 | Calibri |
| 中文字体 | Microsoft JhengHei（fallback: PingFang TC, Heiti TC, Noto Sans TC） |

改 `assets/tokens.json` 同时影响 HTML 和 PPT 输出。

## 文件结构

```
skills/milwaukee-ppt/
├── assets/
│   ├── template.pptx          PowerPoint 母版（logo/横幅/footer 在 slideMaster）
│   ├── logo.png               HTML chrome 用
│   ├── tokens.json            共享 token（颜色 / 字号 / chrome 几何）
│   └── html-template/
│       ├── milwaukee.css      HTML 主题
│       └── deck.html.j2       Jinja2 deck 模板
├── scripts/
│   ├── fill_html.py           YAML → 独立 HTML deck 文件夹
│   ├── build_ppt.py           YAML → .pptx（含 MilwaukeeDeck 类，可手动构建）
│   └── polish.py              PPT linter
├── sample/
│   └── content.yaml           示例 deck
├── tests/                     pytest（19 测试）
└── references/
    └── design-guidelines.md   完整设计规范
```

## fill_html.py 查找 html-ppt skill 的顺序

1. `--html-ppt-dir <path>` 参数
2. `HTML_PPT_SKILL_DIR` 环境变量
3. 默认路径：`~/Repo/myskills/.claude/skills/html-ppt/`、`~/.claude/plugins/cache/*/skills/html-ppt/`
4. 找不到 → 输出 stub runtime.js + 警告（CSS 仍正确，键盘导航不可用）

## 进阶：直接用 imperative API

如要精细控制位置/样式，绕过 YAML 用 `MilwaukeeDeck` 类：

```python
import sys
sys.path.insert(0, "<skill绝对路径>/scripts")
from build_ppt import MilwaukeeDeck, MILWAUKEE_RED

deck = MilwaukeeDeck()
s = deck.add_slide("KEY FEATURES", "Why M18 FUEL")
s.add_bullets(["POWERSTATE 电机", "REDLINK 保护"])
s2 = deck.add_slide("SPEC")
s2.add_table([["Model","Torque"],["A","1000Nm"]])
deck.save("out.pptx")
```

`_Slide` 提供方法：`add_paragraphs / add_bullets / add_table / add_image / add_kpi / add_quote / add_section_divider / columns / add_speaker_notes`。完整 API 见 `scripts/build_ppt.py` 顶部 docstring。

## 单位换算

- 1 pt = 1.3333 px @ 96 DPI（`fill_html.py` 自动换算注入 CSS）
- 1 cm = 360000 EMU；1 inch = 914400 EMU
- 幻灯片：13.333" × 7.5"（EMU 12192000 × 6858000）

## 设计规范

完整版见 `references/design-guidelines.md`：字号阶梯、配色规则、反模式。

## 注意事项

- **不要修改 `slideMaster`**——logo/横幅/footer 都在那
- 改 `tokens.json` 后必须重新跑 `fill_html.py` 和 `build_ppt.py` 才会同步到输出
- HTML 预览/演讲依赖 html-ppt skill 的 runtime.js（不修改 html-ppt 仓本身）
- HTML 锁 1280×720 设计画布 + CSS transform 缩放适配视口；PPT 像素级一致
