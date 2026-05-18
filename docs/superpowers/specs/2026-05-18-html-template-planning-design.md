# Milwaukee PPT — HTML 模版规划设计

**状态**：设计已与用户对齐，待评审进入实现计划
**日期**：2026-05-18
**目标 skill**：`skills/milwaukee-ppt/`（轻度依赖外部 skill `html-ppt`）

---

## 1. 背景与目标

当前 `milwaukee-ppt` 是个完整的 python-pptx 渲染器，含 6 套 HTML 预览 variant（`scripts/deck.py` + `scripts/preview.py`）。用户希望：

1. **在生成 PPT 之前，先通过 HTML 进行规划与样式微调**——浏览器看到效果、对话式增删改、定稿后再出 .pptx
2. **复用现有 skill**——不要重复造轮子
3. **milwaukee-ppt 简化为"格式 + 颜色限定"**——把 HTML 工作交给现成的 `html-ppt` skill

## 2. 架构决策：P3 双轨

```
content.yaml                             ← 唯一内容真理
    │
    ├─ html-ppt 路径（浏览器预览/规划/演讲）
    │     └─ Milwaukee 主题 + 模板（自包含在 milwaukee-ppt 内）
    │           └─ 输出 deck 引用 html-ppt 的 runtime.js / base.css
    │
    └─ milwaukee-ppt 路径（.pptx 交付）
          └─ build_ppt.py（保留，新增 build_from_yaml() 入口）
```

**关键约束**：

- HTML 和 PPT **像素级一致**：HTML deck 容器固定 1280×720 px @ 96 DPI，与 PPT 模板 13.333"×7.5" 等价
- 一份 `tokens.json` 同时驱动两条路径的颜色/字体/字号/chrome 几何
- `html-ppt` 仓**零改动**——milwaukee-ppt 输出的 deck 是自包含 portable 文件夹，运行时去 html-ppt 的安装目录拷贝 `runtime.js` 和 `base.css`

### 备选方案及落选理由

- **方案 Z**（在 milwaukee-ppt 里加 HTML 预览迭代）：用户拒绝，因为不复用 html-ppt 的成熟资产
- **方案 Y1 / Y2**（HTML → PPTX 桥接）：所有现成 skill 都做不到 HTML → PPTX 转换（pptx-html-fidelity-audit 只审计不生成；pptx / pptx-generator 是目录广告，本地无代码）。要做必须新写桥接代码，与"只用现有 skill"矛盾
- **方案 X**（纯 HTML 交付）：用户需要 .pptx 文件，排除

## 3. 各 skill 责任

| skill | 职责 | 是否改动 |
|---|---|---|
| `milwaukee-ppt` | 品牌 token / PPT 渲染 / HTML 模板 / YAML schema / fill_html 桥 | 是（瘦身重构） |
| `html-ppt` | HTML 创作运行时（runtime.js、base.css、render.sh PNG 导出） | **否** |
| `pptx-html-fidelity-audit` | 不使用 | 否 |
| `pptx` / `pptx-generator` | 不使用（目录广告，无实质代码） | 否 |

## 4. 文件结构（最终态）

```
milwaukee-ppt/
  ├── assets/
  │   ├── template.pptx                 (保留：PPT 渲染用)
  │   ├── logo.png                      (保留：HTML + PPT 共用)
  │   ├── tokens.json                   ★ 新增：共享 token
  │   └── html-template/                ★ 新增：自包含 HTML 模板
  │       ├── milwaukee.css             Milwaukee 主题 + chrome 几何
  │       └── deck.html.j2              Jinja2：整个 deck 骨架，覆盖 9 种 slide type
  ├── scripts/
  │   ├── build_ppt.py                  (保留 + 新增 build_from_yaml() / CLI)
  │   ├── fill_html.py                  ★ 新增（~80 行）
  │   └── polish.py                     (保留：PPT 输出后 linter)
  ├── tests/                            ★ 新增
  │   ├── test_tokens_roundtrip.py
  │   ├── test_yaml_schema.py
  │   ├── test_fill_html_output.py
  │   └── test_build_pptx_output.py
  ├── sample/                           ★ 新增
  │   └── content.yaml                  端到端验证用样例（也作为 SKILL.md 示例）
  ├── references/
  │   └── design-guidelines.md          (保留)
  └── SKILL.md                          ★ 重写到 ~100 行
```

**删除**：

- `scripts/deck.py`（6 套 variant 渲染器，已被 html-ppt 取代）
- `scripts/preview.py`（6 套 variant CLI）
- `SKILL.md` 中"HTML 预览 → 选版式"章节、6 套 variant 表格

## 5. 数据契约

### 5.1 `assets/tokens.json`

```json
{
  "colors": {
    "primary":     "#DB011C",
    "text_dark":   "#333333",
    "text_mid":    "#666666",
    "bg_light":    "#F5F5F5",
    "white":       "#FFFFFF",
    "status_ok":   "#2EB67D",
    "status_warn": "#ECB22E",
    "status_bad":  "#E01E5A"
  },
  "fonts": {
    "en_sans":      "Calibri",
    "cjk_sans":     "Microsoft JhengHei",
    "fallback_cjk": ["PingFang TC", "Heiti TC", "Noto Sans TC"]
  },
  "sizes_pt": {
    "title": 32, "subtitle": 20, "body": 16, "body_dense": 14,
    "kpi": 96, "quote": 22, "section": 44
  },
  "chrome": {
    "banner_height_px":   96,
    "logo":               { "left": 8, "top": 8, "width": 176, "height": 79 },
    "footer_height_px":   16,
    "footer_text":        "Confidential Document Property of MILWAUKEE TOOL Brookfield, Wisconsin 53005",
    "content_top_px":     96,
    "content_bottom_px":  696
  },
  "canvas": {
    "width_px":  1280,
    "height_px": 720,
    "dpi":       96
  }
}
```

**所有数值都来自 template.pptx 实测**，不准凭空填。改红色等同时改 build_ppt.py 和 milwaukee.css。

### 5.2 `content.yaml` schema

```yaml
meta:
  title: Q2 Product Review
  author: Milwaukee APAC Team
  date: 2026-05-18

slides:
  - type: title
    title: PRODUCT OVERVIEW
    subtitle: M18 FUEL · 2026

  - type: bullets
    title: KEY FEATURES
    items: [POWERSTATE 无刷电机, REDLINK PLUS 智能保护, 续航提升 30%]

  # 共支持 9 种 type：title / text / bullets / table / kpi / quote / section / image / columns
  # 各 type 的字段与当前 deck.py 完全一致
```

完整 schema 见 `references/design-guidelines.md`（迁移中更新）。

### 5.3 单位换算

- pt → px：`1pt = 1.3333px @ 96 DPI`。`fill_html.py` 启动时算好 px 值注入 `:root`
- CSS 用 `--mw-title-size: 42.67px /* 32pt */` 这种形式，注释保留 pt 原值

## 6. 关键组件

### 6.1 `fill_html.py`（~80 行）

```
INPUT:  content.yaml
OUTPUT: <out-dir>/index.html, theme.css, logo.png, runtime.js, base.css

流程：
  1. yaml.safe_load(content.yaml)
  2. 读 milwaukee-ppt/assets/tokens.json
  3. 把 tokens.colors 和 tokens.sizes_pt（转 px）和 tokens.chrome 注入 milwaukee.css 的 :root → 写出 theme.css
  4. Jinja2 渲染 deck.html.j2，传入 content.slides，每个 slide dict 按 type 走对应 macro
  5. 拷贝 logo.png 到 out_dir
  6. 找 html-ppt 路径（参数 → 环境变量 → 默认搜索路径），拷贝 runtime.js + base.css 到 out_dir
  7. 找不到 runtime.js → 仍然输出，只在 stderr 警告"键盘导航不可用"
```

**html-ppt 路径解析顺序**：

1. `--html-ppt-dir <path>` 命令行参数
2. `HTML_PPT_SKILL_DIR` 环境变量
3. 默认路径（按当前用户机器）：
   ```
   ~/Repo/myskills/.claude/skills/html-ppt/
   ~/.claude/plugins/cache/*/skills/html-ppt/
   ```
4. 找不到 → 警告，跳过 runtime.js / base.css 拷贝

### 6.2 `build_ppt.py` 改动

保留所有现有 API（`MilwaukeeDeck`, `add_slide`, `add_bullets`...），**新增**：

```python
def build_from_yaml(content_path: str, out_path: str, tokens_path: str | None = None) -> str:
    """YAML → .pptx 一站式入口"""

# CLI: python build_ppt.py content.yaml --out final.pptx
```

内部就是 9 种 type 的 dispatch，每个 case 调既有 `add_*` 方法。~60 行新代码。

### 6.3 `milwaukee.css`（~80 行）

- 锁 `.slide { width: 1280px; height: 720px; position: relative; }`
- `::before` 画红横幅（高 96px，背景 `--mw-primary`）
- `.mw-logo` 绝对定位 (8, 8) 176×79
- `.mw-footer` 底部 16px confidential 文字
- `.mw-content` 内容区 padding 24px 48px，top: 96, bottom: 16
- 9 种 slide type 的 layout class（title/bullets/table/kpi/quote/section/image/columns/text）

所有几何数值通过 `var(--mw-*)` 引用，不写死。

### 6.4 `deck.html.j2`

Jinja2 模板，一个文件搞定整个 deck：

```jinja
<!DOCTYPE html>
<html><head>
  <link rel="stylesheet" href="base.css">
  <link rel="stylesheet" href="theme.css">
</head><body class="deck">
{% for slide in slides %}
  <section class="slide" data-type="{{ slide.type }}">
    <img class="mw-logo" src="logo.png">
    {% if slide.type == 'title' %}{{ macros.title(slide) }}
    {% elif slide.type == 'bullets' %}{{ macros.bullets(slide) }}
    ...
    {% endif %}
    <div class="mw-footer">{{ chrome.footer_text }}</div>
  </section>
{% endfor %}
<script src="runtime.js"></script>
</body></html>
```

## 7. 用户工作流

```bash
# 1) 写内容
vim content.yaml

# 2) 浏览器预览/规划/演讲
python milwaukee-ppt/scripts/fill_html.py content.yaml --out ~/talks/q2/
open ~/talks/q2/index.html
# ← → 翻页、S 演讲者模式、F 全屏

# 3) 改 → 重新填 → 浏览器刷新（迭代）
vim content.yaml
python milwaukee-ppt/scripts/fill_html.py content.yaml --out ~/talks/q2/

# 4) 满意后出 .pptx
python milwaukee-ppt/scripts/build_ppt.py content.yaml --out q2-final.pptx
python milwaukee-ppt/scripts/polish.py q2-final.pptx   # linter
```

## 8. 错误处理

| 场景 | 行为 |
|---|---|
| `content.yaml` 缺必填字段（如 `bullets.items`） | fill_html / build_ppt 都报"slide #N type=bullets 缺 items 字段" |
| `type` 不在 9 种里 | 同上，列出合法 type 列表 |
| `tokens.json` 颜色非 6 位 hex | fill_html 启动即报错 |
| html-ppt 路径找不到 | fill_html stderr 警告 + 继续输出（键盘导航不可用，CSS 看上去仍正确） |
| `template.pptx` 缺失 | build_ppt 报错 |
| PowerPoint 正在打开输出文件（`~$xxx.pptx`） | build_ppt 报错并拒绝写入（现有 polish.py 已有该检查） |

## 9. 测试方案

**单元测试**（pytest）：

| 文件 | 验什么 |
|---|---|
| `test_tokens_roundtrip.py` | tokens.json 解析；颜色合法；尺寸值与 template.pptx 实测一致 |
| `test_yaml_schema.py` | 9 种 type 各跑一个最小例子；缺字段时报清楚错误 |
| `test_fill_html_output.py` | 输出 HTML 含正确数量 `<section>`；theme.css 含 `--mw-primary: #DB011C` |
| `test_build_pptx_output.py` | 同份 YAML → .pptx，python-pptx 读回：slide 数匹配、标题文字匹配、模板 chrome 高度 = 914400 EMU |

**端到端**（手动，一次）：

```bash
python scripts/fill_html.py sample/content.yaml --out /tmp/mw-html/
python scripts/build_ppt.py  sample/content.yaml --out /tmp/mw.pptx

# HTML PNG 截图
<html-ppt-dir>/scripts/render.sh /tmp/mw-html/index.html 8 /tmp/mw-html-png

# PPT PNG 截图
soffice --headless --convert-to pdf /tmp/mw.pptx
pdftoppm -png -r 96 mw.pdf /tmp/mw-pptx-png/slide

# 肉眼比对：红横幅高度、logo 位置、内容区边界、字号
```

**不写视觉自动 diff**：图像 diff 受字体渲染影响假阳性高，得不偿失。

## 10. 迁移计划（分两阶段）

### 阶段 A（视觉对齐验证）

A1. 建 `assets/tokens.json`
A2. 写 `assets/html-template/milwaukee.css`
A3. 写 `assets/html-template/deck.html.j2`（含 9 种 type 的 macro）
A4. 写 `scripts/fill_html.py`
A5. 写 `sample/content.yaml`，跑 fill_html.py，浏览器看效果

→ **Gate**：用户审核视觉效果后才进阶段 B

### 阶段 B（PPT 路径 + 删除旧代码）

B1. 改 `build_ppt.py` 加 `build_from_yaml()` + CLI
B2. 写 4 个 pytest 测试
B3. 跑端到端验证（HTML PNG ↔ PPT PNG 肉眼比对）
B4. 删 `scripts/deck.py`、`scripts/preview.py`
B5. 重写 `SKILL.md`
B6. git commit（建议拆 3 个 commit：`feat: tokens + html-template` / `feat: build_from_yaml + tests` / `refactor: drop legacy preview variants + rewrite SKILL.md`）

## 11. 不在本次范围

- 给 html-ppt 加 Milwaukee 主题（用户明确拒绝改 html-ppt）
- 视觉自动 diff
- 多语言/RTL 支持
- 自定义 variant 设计（CSS 已经写死 chrome，主题切换会 no-op）
- 把 `references/design-guidelines.md` 拆到 milwaukee.css 注释里（保留为外部文档）

## 12. 风险

| 风险 | 缓解 |
|---|---|
| HTML 字体在浏览器渲染与 PowerPoint 渲染存在差异（CJK fallback 链不同） | 阶段 A 端到端验证时肉眼检查；CSS 注释里列 fallback；告诉用户最终交付前转 PDF 以锁字体 |
| `1pt = 1.3333px` 浮点误差累积 | px 值保留两位小数；几何关键值（banner_height、content_top）直接给 px 整数 |
| html-ppt 升级改了 runtime.js API | fill_html.py 在拷贝时记录 runtime.js 的 mtime/size 到 manifest，未来可加 sanity check |
| 用户改了 tokens.json 但忘了重跑 fill_html.py | 在 SKILL.md 工作流里写明"改 tokens 后必须重新生成两边" |
