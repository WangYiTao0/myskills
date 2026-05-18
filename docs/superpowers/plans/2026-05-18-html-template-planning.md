# Milwaukee PPT — HTML 模版规划实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 milwaukee-ppt 重构为"品牌 token + 双轨渲染器"——一份 `content.yaml` 同时驱动 html-ppt 兼容的 HTML deck 和 python-pptx 的 .pptx 输出。

**Architecture:** P3 双轨。`assets/tokens.json` 为共享真理（颜色、字号、chrome 几何）。`fill_html.py` 用 Jinja2 渲染独立的 HTML deck 文件夹，并从 html-ppt skill 目录拷贝 `runtime.js`/`base.css`。`build_ppt.py` 新增 `build_from_yaml()` 入口，复用既有 `MilwaukeeDeck` API。html-ppt 仓代码零改动。

**Tech Stack:** Python 3.11+、python-pptx、PyYAML、Jinja2、pytest。CSS 用浏览器内置渲染（无 SCSS）。

**Spec:** `docs/superpowers/specs/2026-05-18-html-template-planning-design.md`

---

## 文件结构

```
skills/milwaukee-ppt/
├── assets/
│   ├── template.pptx                  (保留)
│   ├── logo.png                       (保留)
│   ├── tokens.json                    ★ Task 1
│   └── html-template/
│       ├── milwaukee.css              ★ Task 2
│       └── deck.html.j2               ★ Task 3
├── scripts/
│   ├── build_ppt.py                   (保留；Task 7 加 build_from_yaml)
│   ├── fill_html.py                   ★ Task 4
│   ├── polish.py                      (保留)
│   ├── deck.py                        (Task 9 删)
│   └── preview.py                     (Task 9 删)
├── sample/
│   └── content.yaml                   ★ Task 5
├── tests/
│   ├── __init__.py                    ★ Task 1
│   ├── conftest.py                    ★ Task 1
│   ├── test_tokens_roundtrip.py                 ★ Task 1
│   ├── test_yaml_schema.py            ★ Task 4
│   ├── test_fill_html_output.py              ★ Task 4
│   └── test_build_pptx_output.py             ★ Task 7
├── SKILL.md                           (Task 10 重写)
└── references/design-guidelines.md    (保留)
```

**职责划分**：

- `tokens.json` —— 唯一的颜色/字号/chrome 几何来源。改这里同时影响 HTML 和 PPT
- `milwaukee.css` —— CSS 主题，所有数值通过 `var(--mw-*)` 引用，由 `fill_html.py` 在运行时注入
- `deck.html.j2` —— Jinja2 模板，含 9 种 slide type 的 macro
- `fill_html.py` —— YAML + tokens + 模板 → 独立 HTML deck 文件夹
- `build_ppt.py` —— YAML + tokens + template.pptx → .pptx

---

## Phase A — HTML 渲染（视觉验证）

### Task 1: 装依赖 + tokens.json + 测试脚手架

**Files:**
- Modify: `skills/milwaukee-ppt/.venv` (install deps)
- Create: `skills/milwaukee-ppt/assets/tokens.json`
- Create: `skills/milwaukee-ppt/tests/__init__.py`
- Create: `skills/milwaukee-ppt/tests/conftest.py`
- Create: `skills/milwaukee-ppt/tests/test_tokens_roundtrip.py`

- [ ] **Step 1.1: 装依赖**

```bash
cd /Users/mitumao/Repo/myskills/skills/milwaukee-ppt
source .venv/bin/activate
pip install PyYAML Jinja2 pytest
```

Expected: 三个包安装成功。

- [ ] **Step 1.2: 写 tokens.json**

Create `skills/milwaukee-ppt/assets/tokens.json`:

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
    "title":      32,
    "subtitle":   20,
    "body":       16,
    "body_dense": 14,
    "kpi":        96,
    "quote":      22,
    "section":    44
  },
  "chrome": {
    "banner_height_px":  96,
    "logo":              { "left": 8, "top": 8, "width": 176, "height": 79 },
    "footer_height_px":  16,
    "footer_text":       "Confidential Document Property of MILWAUKEE TOOL Brookfield, Wisconsin 53005",
    "content_top_px":    96,
    "content_bottom_px": 696
  },
  "canvas": {
    "width_px":  1280,
    "height_px": 720,
    "dpi":       96
  }
}
```

- [ ] **Step 1.3: 写测试脚手架**

Create `skills/milwaukee-ppt/tests/__init__.py` (空文件)。

Create `skills/milwaukee-ppt/tests/conftest.py`:

```python
"""pytest fixtures shared across milwaukee-ppt tests."""
from pathlib import Path
import sys

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
```

- [ ] **Step 1.4: 写 test_tokens_roundtrip.py（先红后绿 TDD）**

Create `skills/milwaukee-ppt/tests/test_tokens_roundtrip.py`:

```python
"""Tokens.json structural + value tests.

These values must stay in lock-step with template.pptx — if you change
the template chrome, update tokens.json AND this test together.
"""
import json
import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
TOKENS_PATH = SKILL_DIR / "assets" / "tokens.json"


@pytest.fixture(scope="module")
def tokens():
    return json.loads(TOKENS_PATH.read_text())


def test_primary_color_matches_template(tokens):
    """Color must match template.pptx Rectangle 3 fill (extracted 2026-05-18)."""
    assert tokens["colors"]["primary"] == "#DB011C"


def test_all_colors_are_valid_hex(tokens):
    pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
    for name, value in tokens["colors"].items():
        assert pattern.match(value), f"colors.{name}={value} is not valid 6-digit hex"


def test_canvas_matches_template(tokens):
    """1280x720 @ 96 DPI = 13.333" x 7.5" — equals template slide size."""
    assert tokens["canvas"]["width_px"] == 1280
    assert tokens["canvas"]["height_px"] == 720
    assert tokens["canvas"]["dpi"] == 96


def test_chrome_geometry_matches_template(tokens):
    """All chrome px values were extracted from template.pptx slide_master."""
    chrome = tokens["chrome"]
    assert chrome["banner_height_px"] == 96   # Rectangle 3 height
    assert chrome["content_top_px"] == 96     # = banner bottom
    assert chrome["content_bottom_px"] == 696 # = footer top
    assert chrome["footer_height_px"] == 16
    logo = chrome["logo"]
    assert (logo["left"], logo["top"]) == (8, 8)
    assert (logo["width"], logo["height"]) == (176, 79)


def test_required_sizes_present(tokens):
    required = {"title", "subtitle", "body", "kpi", "quote", "section"}
    assert required.issubset(tokens["sizes_pt"].keys())
    for name, pt in tokens["sizes_pt"].items():
        assert pt > 0, f"sizes_pt.{name}={pt} must be positive"
```

- [ ] **Step 1.5: 跑测试确认全绿**

```bash
cd /Users/mitumao/Repo/myskills/skills/milwaukee-ppt
source .venv/bin/activate
pytest tests/test_tokens_roundtrip.py -v
```

Expected: 5 passed.

---

### Task 2: 写 Milwaukee 主题 CSS

**Files:**
- Create: `skills/milwaukee-ppt/assets/html-template/milwaukee.css`

CSS 没有自动测试（视觉效果靠 Task 5 端到端验证）。本任务只写文件，跑一遍语法检查。

- [ ] **Step 2.1: 写 milwaukee.css**

Create `skills/milwaukee-ppt/assets/html-template/milwaukee.css`:

```css
/* Milwaukee Tool brand theme. Source of truth: ../tokens.json.
   Values in :root are injected by fill_html.py at render time — do NOT
   hand-edit the var values, edit tokens.json instead.

   All px values assume a 1280x720 canvas (PPT 13.333" x 7.5" @ 96 DPI). */

:root {
  /* Injected by fill_html.py from tokens.json */
  --mw-primary: #DB011C;
  --mw-text-dark: #333333;
  --mw-text-mid: #666666;
  --mw-bg-light: #F5F5F5;
  --mw-white: #FFFFFF;

  --mw-font-en: Calibri, sans-serif;
  --mw-font-cjk: "Microsoft JhengHei", "PingFang TC", "Heiti TC", "Noto Sans TC", sans-serif;

  --mw-title-size: 42.67px;   /* 32pt */
  --mw-subtitle-size: 26.67px; /* 20pt */
  --mw-body-size: 21.33px;    /* 16pt */
  --mw-body-dense-size: 18.67px; /* 14pt */
  --mw-kpi-size: 128px;       /* 96pt */
  --mw-quote-size: 29.33px;   /* 22pt */
  --mw-section-size: 58.67px; /* 44pt */

  --mw-canvas-w: 1280px;
  --mw-canvas-h: 720px;
  --mw-banner-h: 96px;
  --mw-logo-w: 176px;
  --mw-logo-h: 79px;
  --mw-logo-left: 8px;
  --mw-logo-top: 8px;
  --mw-footer-h: 16px;
  --mw-content-top: 96px;
  --mw-content-bottom: 696px;
}

/* Slide canvas — locked to 1280x720 px to match PPT pixel-for-pixel */
.slide {
  width: var(--mw-canvas-w);
  height: var(--mw-canvas-h);
  position: relative;
  background: var(--mw-white);
  font-family: var(--mw-font-cjk), var(--mw-font-en);
  color: var(--mw-text-dark);
  overflow: hidden;
}

/* Red banner — drawn via ::before so we don't need to add markup per slide */
.slide::before {
  content: '';
  position: absolute;
  left: 0; top: 0;
  width: 100%;
  height: var(--mw-banner-h);
  background: var(--mw-primary);
  z-index: 1;
}

/* Logo in red banner left */
.slide .mw-logo {
  position: absolute;
  left: var(--mw-logo-left);
  top: var(--mw-logo-top);
  width: var(--mw-logo-w);
  height: var(--mw-logo-h);
  z-index: 2;
}

/* Banner title (right side, white, bold) */
.slide .mw-title {
  position: absolute;
  left: 488px;
  top: 9px;
  width: 792px;
  height: 39px;
  z-index: 2;
  color: var(--mw-white);
  font-size: var(--mw-title-size);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  line-height: 1;
  padding-right: 16px;
}

/* Banner subtitle (below title, white, right-aligned) */
.slide .mw-subtitle {
  position: absolute;
  left: 490px;
  top: 48px;
  width: 790px;
  height: 40px;
  z-index: 2;
  color: var(--mw-white);
  font-size: var(--mw-subtitle-size);
  font-weight: 400;
  text-align: right;
  padding-right: 16px;
  line-height: 1.2;
}

/* Footer text strip */
.slide .mw-footer {
  position: absolute;
  left: 0; bottom: 0;
  width: 100%;
  height: var(--mw-footer-h);
  font-size: 9px;
  color: var(--mw-text-mid);
  text-align: center;
  line-height: var(--mw-footer-h);
  z-index: 2;
}

/* Content area — between banner and footer */
.slide .mw-content {
  position: absolute;
  left: 38px;
  top: calc(var(--mw-content-top) + 32px);
  right: 38px;
  bottom: calc(var(--mw-footer-h) + 16px);
  z-index: 3;
}

/* ---- per-type layouts ---- */

.slide[data-type="title"] .mw-content {
  /* Title-page body unused; banner already carries title+subtitle. */
  display: none;
}

.slide[data-type="bullets"] .mw-bullets {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: var(--mw-body-size);
  line-height: 1.6;
}
.slide[data-type="bullets"] .mw-bullets li {
  padding-left: 28px;
  margin-bottom: 14px;
  position: relative;
}
.slide[data-type="bullets"] .mw-bullets li::before {
  content: '';
  position: absolute;
  left: 8px; top: 14px;
  width: 8px; height: 8px;
  background: var(--mw-primary);
  border-radius: 50%;
}

.slide[data-type="text"] .mw-paragraph {
  font-size: var(--mw-body-size);
  line-height: 1.55;
  margin-bottom: 12px;
}
.slide[data-type="text"] .mw-paragraph.mw-bold {
  font-weight: 700;
}

.slide[data-type="table"] table.mw-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--mw-body-dense-size);
}
.slide[data-type="table"] table.mw-table th {
  background: var(--mw-primary);
  color: var(--mw-white);
  text-align: left;
  padding: 10px 14px;
  font-weight: 700;
}
.slide[data-type="table"] table.mw-table td {
  padding: 8px 14px;
  border-bottom: 1px solid var(--mw-bg-light);
}

.slide[data-type="kpi"] .mw-kpi-value {
  font-size: var(--mw-kpi-size);
  font-weight: 800;
  color: var(--mw-primary);
  text-align: center;
  line-height: 1;
  margin-top: 60px;
}
.slide[data-type="kpi"] .mw-kpi-label {
  font-size: var(--mw-subtitle-size);
  color: var(--mw-text-mid);
  text-align: center;
  margin-top: 18px;
}

.slide[data-type="quote"] .mw-quote-text {
  font-size: var(--mw-quote-size);
  font-style: italic;
  text-align: center;
  margin-top: 80px;
  line-height: 1.5;
}
.slide[data-type="quote"] .mw-quote-author {
  font-size: var(--mw-body-size);
  color: var(--mw-text-mid);
  text-align: right;
  margin-top: 24px;
}

.slide[data-type="section"] .mw-content {
  display: flex;
  align-items: center;
  justify-content: center;
}
.slide[data-type="section"] .mw-section-text {
  font-size: var(--mw-section-size);
  font-weight: 800;
  color: var(--mw-primary);
  text-align: center;
  text-transform: uppercase;
}

.slide[data-type="image"] .mw-image-wrap {
  text-align: center;
}
.slide[data-type="image"] img.mw-image {
  max-width: 100%;
  max-height: 460px;
  object-fit: contain;
}
.slide[data-type="image"] .mw-image-caption {
  font-size: var(--mw-body-size);
  color: var(--mw-text-mid);
  text-align: center;
  margin-top: 12px;
}

.slide[data-type="columns"] .mw-columns {
  display: grid;
  gap: 32px;
  height: 100%;
}
.slide[data-type="columns"] .mw-column-head {
  font-size: var(--mw-subtitle-size);
  font-weight: 700;
  color: var(--mw-primary);
  margin-bottom: 12px;
}
.slide[data-type="columns"] .mw-column-body {
  font-size: var(--mw-body-size);
  line-height: 1.55;
}
```

- [ ] **Step 2.2: 语法 sanity check**

```bash
python -c "
import re
css = open('skills/milwaukee-ppt/assets/html-template/milwaukee.css').read()
open_braces = css.count('{')
close_braces = css.count('}')
assert open_braces == close_braces, f'brace mismatch {open_braces} vs {close_braces}'
print(f'OK: {open_braces} CSS rule blocks')
"
```

Expected: `OK: NN CSS rule blocks` (NN > 20).

---

### Task 3: 写 deck.html.j2

**Files:**
- Create: `skills/milwaukee-ppt/assets/html-template/deck.html.j2`

- [ ] **Step 3.1: 写 deck.html.j2**

Create `skills/milwaukee-ppt/assets/html-template/deck.html.j2`:

```jinja
{#- Milwaukee deck template. Rendered by fill_html.py.
    Context vars:
      meta   -- dict with title/author/date
      slides -- list of slide dicts (see content.yaml schema)
      chrome -- tokens.chrome dict (for footer text injection)
-#}
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>{{ meta.title | default("Milwaukee Deck") }}</title>
<link rel="stylesheet" href="base.css">
<link rel="stylesheet" href="theme.css">
</head>
<body class="deck">

{%- macro render_banner(slide) %}
  <img class="mw-logo" src="logo.png" alt="Milwaukee">
  {%- if slide.title %}<div class="mw-title">{{ slide.title }}</div>{% endif %}
  {%- if slide.subtitle %}<div class="mw-subtitle">{{ slide.subtitle }}</div>{% endif %}
{%- endmacro %}

{%- macro render_footer() %}
  <div class="mw-footer">{{ chrome.footer_text }}</div>
{%- endmacro %}

{% for slide in slides %}
<section class="slide" data-type="{{ slide.type }}">
  {{ render_banner(slide) }}

  {%- if slide.type == "title" %}
  <div class="mw-content"></div>

  {%- elif slide.type == "bullets" %}
  <div class="mw-content">
    <ul class="mw-bullets">
      {%- for item in slide["items"] %}
      <li>{{ item }}</li>
      {%- endfor %}
    </ul>
  </div>

  {%- elif slide.type == "text" %}
  <div class="mw-content">
    {%- for block in slide.blocks %}
    <p class="mw-paragraph{% if block.bold %} mw-bold{% endif %}"
       {% if block.size %}style="font-size: {{ block.size }}pt"{% endif %}>
      {{ block.text }}
    </p>
    {%- endfor %}
  </div>

  {%- elif slide.type == "table" %}
  <div class="mw-content">
    <table class="mw-table">
      {%- for row in slide.rows %}
      {%- if loop.first %}
      <thead><tr>{% for cell in row %}<th>{{ cell }}</th>{% endfor %}</tr></thead>
      <tbody>
      {%- else %}
      <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
      {%- endif %}
      {%- endfor %}
      </tbody>
    </table>
  </div>

  {%- elif slide.type == "kpi" %}
  <div class="mw-content">
    <div class="mw-kpi-value">{{ slide.value }}</div>
    <div class="mw-kpi-label">{{ slide.label }}</div>
  </div>

  {%- elif slide.type == "quote" %}
  <div class="mw-content">
    <div class="mw-quote-text">"{{ slide.text }}"</div>
    {%- if slide.author %}
    <div class="mw-quote-author">— {{ slide.author }}</div>
    {%- endif %}
  </div>

  {%- elif slide.type == "section" %}
  <div class="mw-content">
    <div class="mw-section-text">{{ slide.text | default(slide.title) }}</div>
  </div>

  {%- elif slide.type == "image" %}
  <div class="mw-content">
    <div class="mw-image-wrap">
      <img class="mw-image" src="{{ slide.path }}" alt="{{ slide.caption | default('') }}">
      {%- if slide.caption %}
      <div class="mw-image-caption">{{ slide.caption }}</div>
      {%- endif %}
    </div>
  </div>

  {%- elif slide.type == "columns" %}
  <div class="mw-content">
    <div class="mw-columns" style="grid-template-columns: repeat({{ slide.columns | length }}, 1fr);">
      {%- for col in slide.columns %}
      <div>
        <div class="mw-column-head">{{ col.head }}</div>
        <div class="mw-column-body">{{ col.body }}</div>
      </div>
      {%- endfor %}
    </div>
  </div>

  {%- else %}
  <div class="mw-content">
    <p style="color: red">Unknown slide type: {{ slide.type }}</p>
  </div>
  {%- endif %}

  {{ render_footer() }}
</section>
{% endfor %}

<script src="runtime.js"></script>
</body>
</html>
```

---

### Task 4: 写 fill_html.py + 单元测试

**Files:**
- Create: `skills/milwaukee-ppt/scripts/fill_html.py`
- Create: `skills/milwaukee-ppt/tests/test_yaml_schema.py`
- Create: `skills/milwaukee-ppt/tests/test_fill_html_output.py`

- [ ] **Step 4.1: 写 test_yaml_schema.py（先写测试）**

Create `skills/milwaukee-ppt/tests/test_yaml_schema.py`:

```python
"""YAML schema validation tests for content.yaml.

The validator must accept all 9 slide types and reject malformed input
with a clear error message naming the offending slide and field.
"""
import pytest

from fill_html import validate_content  # imported via conftest sys.path


def test_minimal_valid_deck():
    content = {
        "meta": {"title": "T"},
        "slides": [{"type": "title", "title": "X"}],
    }
    validate_content(content)  # should not raise


def test_all_9_types_valid():
    content = {
        "meta": {"title": "T"},
        "slides": [
            {"type": "title", "title": "A"},
            {"type": "text", "title": "T", "blocks": [{"text": "x"}]},
            {"type": "bullets", "title": "B", "items": ["a"]},
            {"type": "table", "title": "T", "rows": [["a"]]},
            {"type": "kpi", "title": "K", "value": "1", "label": "x"},
            {"type": "quote", "title": "Q", "text": "x"},
            {"type": "section", "title": "S", "text": "x"},
            {"type": "image", "title": "I", "path": "x.png"},
            {"type": "columns", "title": "C", "columns": [{"head": "h", "body": "b"}]},
        ],
    }
    validate_content(content)


def test_missing_slides_key_rejected():
    with pytest.raises(ValueError, match="missing 'slides'"):
        validate_content({"meta": {"title": "x"}})


def test_unknown_type_rejected():
    content = {"slides": [{"type": "rocketship", "title": "x"}]}
    with pytest.raises(ValueError, match="slide #1.*unknown type.*rocketship"):
        validate_content(content)


def test_bullets_missing_items_rejected():
    content = {"slides": [{"type": "bullets", "title": "x"}]}
    with pytest.raises(ValueError, match="slide #1.*bullets.*missing.*items"):
        validate_content(content)


def test_kpi_missing_value_rejected():
    content = {"slides": [{"type": "kpi", "title": "x", "label": "y"}]}
    with pytest.raises(ValueError, match="slide #1.*kpi.*missing.*value"):
        validate_content(content)
```

- [ ] **Step 4.2: 跑测试确认全红（红阶段）**

```bash
pytest tests/test_yaml_schema.py -v
```

Expected: collection error (fill_html module not found) — that's OK, we're about to create it.

- [ ] **Step 4.3: 写 fill_html.py（最小实现让测试过）**

Create `skills/milwaukee-ppt/scripts/fill_html.py`:

```python
"""Render a content.yaml into a portable Milwaukee-branded HTML deck.

Outputs an independent folder containing:
  index.html   -- deck rendered from deck.html.j2
  theme.css    -- milwaukee.css with :root vars injected from tokens.json
  logo.png     -- copied from milwaukee-ppt/assets/
  runtime.js   -- copied from html-ppt skill (if found)
  base.css     -- copied from html-ppt skill (if found)

Usage:
    python fill_html.py content.yaml --out ~/talks/q2/
    python fill_html.py content.yaml --out ~/talks/q2/ --html-ppt-dir <path>
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

SKILL_DIR = Path(__file__).resolve().parent.parent
TOKENS_PATH = SKILL_DIR / "assets" / "tokens.json"
TEMPLATE_DIR = SKILL_DIR / "assets" / "html-template"
LOGO_PATH = SKILL_DIR / "assets" / "logo.png"

PT_TO_PX = 96.0 / 72.0  # 1.3333

# Required keys per slide type. Empty list = only `type` and `title` required.
REQUIRED_FIELDS = {
    "title":   [],
    "text":    ["blocks"],
    "bullets": ["items"],
    "table":   ["rows"],
    "kpi":     ["value", "label"],
    "quote":   ["text"],
    "section": [],  # "text" optional (falls back to title)
    "image":   ["path"],
    "columns": ["columns"],
}


def validate_content(content: dict) -> None:
    """Raise ValueError with a clear message if content fails schema check."""
    if "slides" not in content:
        raise ValueError("content.yaml missing 'slides' key")
    slides = content["slides"]
    if not isinstance(slides, list):
        raise ValueError("'slides' must be a list")
    for i, slide in enumerate(slides, start=1):
        if "type" not in slide:
            raise ValueError(f"slide #{i} missing 'type' field")
        t = slide["type"]
        if t not in REQUIRED_FIELDS:
            raise ValueError(
                f"slide #{i} unknown type {t!r}; allowed: {sorted(REQUIRED_FIELDS)}"
            )
        for field in REQUIRED_FIELDS[t]:
            if field not in slide:
                raise ValueError(
                    f"slide #{i} type={t} missing required field {field!r}"
                )


def find_html_ppt_dir(explicit: str | None) -> Path | None:
    """Resolve html-ppt skill root. Returns None if not found."""
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if (p / "assets" / "runtime.js").exists():
            return p
        return None
    if env := os.environ.get("HTML_PPT_SKILL_DIR"):
        p = Path(env).expanduser().resolve()
        if (p / "assets" / "runtime.js").exists():
            return p
    candidates = [
        Path.home() / "Repo" / "myskills" / ".claude" / "skills" / "html-ppt",
    ]
    for c in candidates:
        if (c / "assets" / "runtime.js").exists():
            return c
    for c in (Path.home() / ".claude" / "plugins" / "cache").glob(
        "*/skills/html-ppt"
    ):
        if (c / "assets" / "runtime.js").exists():
            return c
    return None


def build_css(tokens: dict) -> str:
    """Read milwaukee.css and inject :root from tokens.

    Strategy: regex-replace the entire `:root { ... }` block with one
    computed from tokens. Falls back to leaving the file untouched if
    the block isn't found (then user sees defaults baked into the CSS).
    """
    css = (TEMPLATE_DIR / "milwaukee.css").read_text()
    colors = tokens["colors"]
    fonts = tokens["fonts"]
    sizes = tokens["sizes_pt"]
    chrome = tokens["chrome"]
    canvas = tokens["canvas"]
    logo = chrome["logo"]

    lines = [
        ":root {",
        f"  --mw-primary: {colors['primary']};",
        f"  --mw-text-dark: {colors['text_dark']};",
        f"  --mw-text-mid: {colors['text_mid']};",
        f"  --mw-bg-light: {colors['bg_light']};",
        f"  --mw-white: {colors['white']};",
        "",
        f"  --mw-font-en: {fonts['en_sans']}, sans-serif;",
        '  --mw-font-cjk: "'
        + fonts["cjk_sans"]
        + '", '
        + ", ".join(f'"{f}"' for f in fonts["fallback_cjk"])
        + ", sans-serif;",
        "",
        f"  --mw-title-size: {sizes['title'] * PT_TO_PX:.2f}px;",
        f"  --mw-subtitle-size: {sizes['subtitle'] * PT_TO_PX:.2f}px;",
        f"  --mw-body-size: {sizes['body'] * PT_TO_PX:.2f}px;",
        f"  --mw-body-dense-size: {sizes['body_dense'] * PT_TO_PX:.2f}px;",
        f"  --mw-kpi-size: {sizes['kpi'] * PT_TO_PX:.2f}px;",
        f"  --mw-quote-size: {sizes['quote'] * PT_TO_PX:.2f}px;",
        f"  --mw-section-size: {sizes['section'] * PT_TO_PX:.2f}px;",
        "",
        f"  --mw-canvas-w: {canvas['width_px']}px;",
        f"  --mw-canvas-h: {canvas['height_px']}px;",
        f"  --mw-banner-h: {chrome['banner_height_px']}px;",
        f"  --mw-logo-w: {logo['width']}px;",
        f"  --mw-logo-h: {logo['height']}px;",
        f"  --mw-logo-left: {logo['left']}px;",
        f"  --mw-logo-top: {logo['top']}px;",
        f"  --mw-footer-h: {chrome['footer_height_px']}px;",
        f"  --mw-content-top: {chrome['content_top_px']}px;",
        f"  --mw-content-bottom: {chrome['content_bottom_px']}px;",
        "}",
    ]
    injected = "\n".join(lines)

    import re
    pattern = re.compile(r":root\s*\{[^}]*\}", re.DOTALL)
    if pattern.search(css):
        return pattern.sub(injected, css, count=1)
    return injected + "\n" + css


def render_html(content: dict, tokens: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template("deck.html.j2")
    return tpl.render(
        meta=content.get("meta", {}),
        slides=content["slides"],
        chrome=tokens["chrome"],
    )


def fill(content_path: Path, out_dir: Path, html_ppt_dir: Path | None) -> Path:
    content = yaml.safe_load(content_path.read_text())
    validate_content(content)
    tokens = json.loads(TOKENS_PATH.read_text())

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "theme.css").write_text(build_css(tokens))
    (out_dir / "index.html").write_text(render_html(content, tokens))
    shutil.copyfile(LOGO_PATH, out_dir / "logo.png")

    if html_ppt_dir:
        for fn in ("runtime.js", "base.css"):
            src = html_ppt_dir / "assets" / fn
            if src.exists():
                shutil.copyfile(src, out_dir / fn)
            else:
                print(f"warning: {src} not found", file=sys.stderr)
    else:
        print(
            "warning: html-ppt skill not found; keyboard navigation disabled.\n"
            "  pass --html-ppt-dir <path> or set HTML_PPT_SKILL_DIR.",
            file=sys.stderr,
        )
        # Write a stub base.css and empty runtime.js so the HTML still loads
        (out_dir / "runtime.js").write_text("// html-ppt runtime not available\n")
        (out_dir / "base.css").write_text("/* html-ppt base.css not available */\n")

    return out_dir / "index.html"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Milwaukee YAML → HTML deck")
    p.add_argument("content", help="path to content.yaml")
    p.add_argument("--out", required=True, help="output directory")
    p.add_argument("--html-ppt-dir", default=None, help="html-ppt skill root")
    args = p.parse_args(argv)

    out = fill(
        content_path=Path(args.content),
        out_dir=Path(args.out),
        html_ppt_dir=find_html_ppt_dir(args.html_ppt_dir),
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4.4: 跑 test_yaml_schema.py 确认全绿**

```bash
pytest tests/test_yaml_schema.py -v
```

Expected: 6 passed.

- [ ] **Step 4.5: 写 test_fill_html_output.py（输出断言）**

Create `skills/milwaukee-ppt/tests/test_fill_html_output.py`:

```python
"""End-to-end fill_html.py output assertions.

Validates that a minimal content.yaml produces a well-formed deck folder
with all required artifacts and CSS variable injection.
"""
import re
from pathlib import Path

import pytest

from fill_html import build_css, fill, find_html_ppt_dir
import json


SKILL_DIR = Path(__file__).resolve().parent.parent
TOKENS = json.loads((SKILL_DIR / "assets" / "tokens.json").read_text())


def test_build_css_injects_primary_color():
    css = build_css(TOKENS)
    assert "--mw-primary: #DB011C;" in css


def test_build_css_injects_pt_to_px_conversion():
    css = build_css(TOKENS)
    # title 32pt * 1.3333 = 42.67px
    assert re.search(r"--mw-title-size:\s*42\.67px", css)
    # banner_height = 96 (px directly, no conversion)
    assert "--mw-banner-h: 96px;" in css


def test_fill_writes_all_artifacts(tmp_path):
    content = SKILL_DIR / "sample" / "content.yaml"
    if not content.exists():
        pytest.skip("sample/content.yaml not yet written (Task 5)")
    out = tmp_path / "deck"
    fill(content, out, html_ppt_dir=None)
    assert (out / "index.html").exists()
    assert (out / "theme.css").exists()
    assert (out / "logo.png").exists()
    # runtime.js / base.css get stubs when html-ppt not found
    assert (out / "runtime.js").exists()
    assert (out / "base.css").exists()


def test_fill_output_has_correct_slide_count(tmp_path):
    content = SKILL_DIR / "sample" / "content.yaml"
    if not content.exists():
        pytest.skip("sample/content.yaml not yet written (Task 5)")
    import yaml
    expected = len(yaml.safe_load(content.read_text())["slides"])
    out = tmp_path / "deck"
    fill(content, out, html_ppt_dir=None)
    html = (out / "index.html").read_text()
    assert html.count('<section class="slide"') == expected


def test_find_html_ppt_dir_returns_none_when_explicit_missing():
    assert find_html_ppt_dir("/nonexistent/path/12345") is None
```

- [ ] **Step 4.6: 跑 test_fill_html_output.py（前两条应过；后两条 skip 等 Task 5）**

```bash
pytest tests/test_fill_html_output.py -v
```

Expected: 3 passed, 2 skipped。

---

### Task 5: 写 sample/content.yaml + 端到端运行 + 视觉验证 + 第一次 commit

**Files:**
- Create: `skills/milwaukee-ppt/sample/content.yaml`

- [ ] **Step 5.1: 写 sample/content.yaml**

Create `skills/milwaukee-ppt/sample/content.yaml`:

```yaml
meta:
  title: M18 FUEL Q2 Review
  author: Milwaukee APAC
  date: 2026-05-18

slides:
  - type: title
    title: PRODUCT OVERVIEW
    subtitle: M18 FUEL · 2026

  - type: bullets
    title: KEY FEATURES
    subtitle: Why M18 FUEL
    items:
      - POWERSTATE 无刷电机，扭矩 1200 Nm
      - REDLINK PLUS 智能保护
      - REDLITHIUM HIGH OUTPUT 电池续航提升 30%

  - type: text
    title: STRATEGY
    subtitle: Why M18 FUEL Now
    blocks:
      - { text: "市场定位", bold: true, size: 22 }
      - { text: "面向专业用户的高扭矩冲击钻系列，电池续航提升 30%。", size: 16 }

  - type: table
    title: SPEC COMPARISON
    subtitle: Models
    rows:
      - [Model, Torque (Nm), Speed (RPM), Weight (kg)]
      - [M18-A, "1000", 0-2000, "1.8"]
      - [M18-B, "1200", 0-2100, "2.0"]

  - type: kpi
    title: MARKET IMPACT
    subtitle: FY2025 Recap
    value: "+34%"
    label: 全球专业渠道销售同比增长

  - type: quote
    title: VOICE OF CUSTOMER
    subtitle: Field Feedback
    text: M18 FUEL 让我每天少充两次电。
    author: 资深木工 · 香港

  - type: section
    title: CHAPTER 02
    text: WHAT'S NEXT

  - type: columns
    title: THREE PILLARS
    subtitle: Product Strategy
    columns:
      - { head: Power,      body: 无刷电机驱动 }
      - { head: Protection, body: REDLINK PLUS 智能保护 }
      - { head: Endurance,  body: HIGH OUTPUT 长续航 }
```

- [ ] **Step 5.2: 跑 fill_html.py 生成 deck**

```bash
cd /Users/mitumao/Repo/myskills/skills/milwaukee-ppt
source .venv/bin/activate
python scripts/fill_html.py sample/content.yaml --out /tmp/mw-preview/
```

Expected: `wrote /tmp/mw-preview/index.html`（可能带一行 html-ppt 警告，正常）。

- [ ] **Step 5.3: 跑 test_fill_html_output.py 全部测试（现在 sample 存在了）**

```bash
pytest tests/test_fill_html_output.py -v
```

Expected: 5 passed.

- [ ] **Step 5.4: 浏览器打开看视觉效果**

```bash
open /tmp/mw-preview/index.html
```

肉眼检查每一页的红横幅 / logo / 内容布局。这是 Phase A 的关键产出。

- [ ] **Step 5.5: 第一次 commit**

```bash
cd /Users/mitumao/Repo/myskills
git add skills/milwaukee-ppt/assets/tokens.json \
        skills/milwaukee-ppt/assets/html-template/ \
        skills/milwaukee-ppt/scripts/fill_html.py \
        skills/milwaukee-ppt/sample/content.yaml \
        skills/milwaukee-ppt/tests/
git commit -m "feat(milwaukee-ppt): add tokens.json + HTML template + fill_html.py

Introduces the dual-track foundation: tokens.json is the shared source
of truth for colors/fonts/chrome geometry; milwaukee.css + deck.html.j2
render an html-ppt-compatible deck via fill_html.py. Pixel-locked to
1280x720 to match template.pptx (13.333x7.5 @ 96 DPI).

Output deck folders are portable: runtime.js + base.css are copied
from the html-ppt skill at render time if discoverable, otherwise
stubs are written and a stderr warning is printed."
git status --short
```

Expected: commit succeeds; `deck.py`, `preview.py`, `logo.png` 仍 untracked (后续处理)。

---

### Task 6: GATE — 用户视觉验证

- [ ] **Step 6.1: 暂停，请用户复核 `/tmp/mw-preview/index.html` 的视觉效果**

不要在用户口头/书面批准前进入 Task 7。

如用户要求调整 CSS / Jinja 模板 / tokens，回到 Task 2-5 修改并重新生成。

---

## Phase B — PPT 渲染 + 清理

### Task 7: 给 build_ppt.py 加 build_from_yaml() + 单元测试

**Files:**
- Modify: `skills/milwaukee-ppt/scripts/build_ppt.py`（末尾追加）
- Create: `skills/milwaukee-ppt/tests/test_build_pptx_output.py`

- [ ] **Step 7.1: 写 test_build_pptx_output.py（红阶段）**

Create `skills/milwaukee-ppt/tests/test_build_pptx_output.py`:

```python
"""Validate build_from_yaml(): same content.yaml → correct .pptx."""
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.util import Emu

from build_ppt import build_from_yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
SAMPLE = SKILL_DIR / "sample" / "content.yaml"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    if not SAMPLE.exists():
        pytest.skip("sample/content.yaml missing")
    out = tmp_path_factory.mktemp("pptx") / "out.pptx"
    build_from_yaml(str(SAMPLE), str(out))
    return out


def test_slide_count_matches_yaml(built):
    import yaml
    expected = len(yaml.safe_load(SAMPLE.read_text())["slides"])
    p = Presentation(str(built))
    assert len(p.slides) == expected


def test_template_chrome_preserved(built):
    """Red banner shape from slideMaster must remain unchanged."""
    p = Presentation(str(built))
    # The banner lives in slideMaster, not the slides themselves.
    # Pull it back via the master shapes to verify it survived.
    master = p.slide_masters[0]
    banners = [
        s for s in master.shapes
        if s.shape_type == 1 and s.height == Emu(914400)  # 1 inch = banner
    ]
    assert len(banners) >= 1, "red banner shape missing from slideMaster"


def test_first_slide_title_matches_yaml(built):
    import yaml
    spec = yaml.safe_load(SAMPLE.read_text())
    p = Presentation(str(built))
    first_slide = p.slides[0]
    title_text = ""
    for shape in first_slide.shapes:
        if shape.has_text_frame and shape.text_frame.text:
            title_text = shape.text_frame.text
            break
    assert spec["slides"][0]["title"] in title_text
```

- [ ] **Step 7.2: 跑测试确认全红**

```bash
pytest tests/test_build_pptx_output.py -v
```

Expected: ImportError on `build_from_yaml`（OK，正要实现）。

- [ ] **Step 7.3: 给 build_ppt.py 末尾追加 build_from_yaml() + CLI**

Append to `skills/milwaukee-ppt/scripts/build_ppt.py` (在文件末尾):

```python
# ---------------------------------------------------------------------------
# YAML entry point (added 2026-05-18 — dual-track refactor)
# ---------------------------------------------------------------------------

def _render_slide_from_spec(deck: "MilwaukeeDeck", spec: dict) -> None:
    """Dispatch one slide spec to the appropriate MilwaukeeDeck API."""
    t = spec["type"]
    title = spec.get("title", "")
    subtitle = spec.get("subtitle", "")
    s = deck.add_slide(title, subtitle)

    if t == "title":
        return

    if t == "text":
        items = []
        for block in spec.get("blocks", []):
            style = {k: v for k, v in block.items() if k != "text"}
            items.append((block["text"], style))
        s.add_paragraphs(items)
    elif t == "bullets":
        s.add_bullets(spec["items"])
    elif t == "table":
        s.add_table(spec["rows"])
    elif t == "kpi":
        s.add_kpi(spec["value"], spec["label"])
    elif t == "quote":
        s.add_quote(spec["text"], spec.get("author", ""))
    elif t == "section":
        s.add_section_divider(spec.get("text", title))
    elif t == "image":
        s.add_image(spec["path"])
        if caption := spec.get("caption"):
            s.add_paragraphs([(caption, {"size": 14, "color": TEXT_MID})])
    elif t == "columns":
        cols = spec["columns"]
        rects = s.columns(len(cols))
        for col, rect in zip(cols, rects):
            s.add_paragraphs(
                [
                    (col["head"], {"size": 20, "bold": True, "color": MILWAUKEE_RED}),
                    (col["body"], {"size": 16}),
                ],
                **rect,
            )
    else:
        raise ValueError(f"unknown slide type {t!r}")


def build_from_yaml(content_path: str, out_path: str,
                    template_path: str | None = None) -> str:
    """YAML → .pptx one-shot entry. Validates schema, dispatches each slide
    to the matching MilwaukeeDeck API, saves the result.

    Returns the absolute output path.
    """
    import yaml
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from fill_html import validate_content

    content = yaml.safe_load(Path(content_path).read_text())
    validate_content(content)

    deck = MilwaukeeDeck(template_path or DEFAULT_TEMPLATE)
    for spec in content["slides"]:
        _render_slide_from_spec(deck, spec)
    return deck.save(out_path)


def _cli() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Milwaukee YAML → .pptx")
    p.add_argument("content", help="path to content.yaml")
    p.add_argument("--out", required=True, help="output .pptx path")
    p.add_argument("--template", default=None, help="override template.pptx")
    args = p.parse_args()
    out = build_from_yaml(args.content, args.out, args.template)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
```

- [ ] **Step 7.4: 跑 test_build_pptx_output.py 全部测试**

```bash
pytest tests/test_build_pptx_output.py -v
```

Expected: 3 passed.

- [ ] **Step 7.5: 跑全部测试套件**

```bash
pytest tests/ -v
```

Expected: 全部 passed（5 tokens + 6 yaml schema + 5 fill_html + 3 build_pptx = 19 tests）。

- [ ] **Step 7.6: 第二次 commit**

```bash
git add skills/milwaukee-ppt/scripts/build_ppt.py \
        skills/milwaukee-ppt/tests/test_build_pptx_output.py
git commit -m "feat(milwaukee-ppt): add build_from_yaml entry to build_ppt.py

Same content.yaml that drives fill_html.py now also produces a .pptx
via build_from_yaml(). Dispatches each slide spec to existing
MilwaukeeDeck methods (add_bullets, add_table, add_kpi, etc.) — no new
rendering logic. CLI: python build_ppt.py content.yaml --out final.pptx"
```

---

### Task 8: 端到端 PNG 比对验证（手动）

**Files:** none

- [ ] **Step 8.1: 用 sample 同时跑两路渲染**

```bash
cd /Users/mitumao/Repo/myskills/skills/milwaukee-ppt
source .venv/bin/activate
python scripts/fill_html.py sample/content.yaml --out /tmp/mw-html/
python scripts/build_ppt.py  sample/content.yaml --out /tmp/mw.pptx
```

Expected: 两个命令都成功；`/tmp/mw-html/index.html` 和 `/tmp/mw.pptx` 都生成。

- [ ] **Step 8.2: HTML deck 出 PNG（headless Chrome）**

```bash
mkdir -p /tmp/mw-html-png
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu \
  --screenshot=/tmp/mw-html-png/full.png \
  --window-size=1280,720 \
  file:///tmp/mw-html/index.html
```

Expected: `/tmp/mw-html-png/full.png` 生成。

- [ ] **Step 8.3: PPT 出 PNG（LibreOffice → PDF → PNG）**

需要先安装：`brew install --cask libreoffice && brew install poppler`（如果没装）。

```bash
mkdir -p /tmp/mw-pptx-png
cd /tmp
soffice --headless --convert-to pdf mw.pptx
pdftoppm -png -r 96 mw.pdf /tmp/mw-pptx-png/slide
```

Expected: `/tmp/mw-pptx-png/slide-*.png` 一系列文件（每页一张）。

- [ ] **Step 8.4: 肉眼比对**

```bash
open /tmp/mw-html-png/full.png /tmp/mw-pptx-png/slide-1.png
```

检查项：
- 红横幅高度（应该都是 96px）
- Logo 位置（左上 8,8）
- 标题字号 / 颜色 / 大写
- 内容区起始 y 坐标
- footer 文字位置

差异点记录到笔记里，但不阻塞 Task 9（除非有严重几何错位）。

---

### Task 9: 删除旧代码

**Files:**
- Delete: `skills/milwaukee-ppt/scripts/deck.py`
- Delete: `skills/milwaukee-ppt/scripts/preview.py`

- [ ] **Step 9.1: 检查没有任何脚本 import 它们**

```bash
cd /Users/mitumao/Repo/myskills
grep -rn "from deck import\|from preview import\|import deck\b\|import preview\b" \
  skills/milwaukee-ppt/ --include="*.py" | grep -v "scripts/deck.py\|scripts/preview.py"
```

Expected: 无输出。如有，先消除引用再继续。

- [ ] **Step 9.2: 删文件**

```bash
rm skills/milwaukee-ppt/scripts/deck.py
rm skills/milwaukee-ppt/scripts/preview.py
```

- [ ] **Step 9.3: 跑测试确认未坏**

```bash
cd skills/milwaukee-ppt && source .venv/bin/activate && pytest tests/ -v
```

Expected: 仍全绿。

---

### Task 10: 重写 SKILL.md + 最终 commit

**Files:**
- Modify: `skills/milwaukee-ppt/SKILL.md`（全文重写）

- [ ] **Step 10.1: 重写 SKILL.md**

Replace entire content of `skills/milwaukee-ppt/SKILL.md` with:

```markdown
---
name: milwaukee-ppt
description: Milwaukee Tool 品牌 PPT 生成。当用户明确提到 "Milwaukee 模板"、"Milwaukee PPT"、"MS 模板"、"Milwaukee slide"、"Milwaukee 品牌简报"，或上传了 MS_-_Template1.pptx / 本 skill 的 template.pptx 并要求制作演示文稿时使用。仅在 Milwaukee 品牌上下文下触发——不要因为用户单纯说"做个PPT"就启用。
---

# Milwaukee Tool PPT Skill

跨平台（macOS / Linux）。**双轨架构**：一份 `content.yaml` 同时驱动浏览器预览（HTML）和最终交付（.pptx）。

## 工作流

```bash
# 0) 装依赖（一次）
cd skills/milwaukee-ppt
python3 -m venv .venv && source .venv/bin/activate
pip install python-pptx PyYAML Jinja2 Pillow

# 1) 写内容
cp sample/content.yaml my_deck.yaml
# 编辑 my_deck.yaml

# 2) 浏览器预览/规划/演讲（依赖 html-ppt skill 提供 runtime.js）
python scripts/fill_html.py my_deck.yaml --out ~/talks/my-deck/
open ~/talks/my-deck/index.html
# ← → 翻页、S 演讲者模式、F 全屏（如 runtime.js 可用）

# 3) 出 .pptx
python scripts/build_ppt.py my_deck.yaml --out my-deck.pptx

# 4) Linter
python scripts/polish.py my-deck.pptx
```

## content.yaml schema

支持 9 种 slide `type`：

| type | 必填字段 |
|---|---|
| `title` | `title`, `subtitle?` |
| `text` | `blocks: [{text, bold?, size?, color?}]` |
| `bullets` | `items: [str]` |
| `table` | `rows: [[str]]`（第一行为表头） |
| `kpi` | `value`, `label` |
| `quote` | `text`, `author?` |
| `section` | `text?`（默认用 title） |
| `image` | `path`, `caption?` |
| `columns` | `columns: [{head, body}]` |

完整样例见 `sample/content.yaml`。

## 品牌规范

| 元素 | 值 | 来源 |
|---|---|---|
| 主色 | `#DB011C` | template.pptx 实测 |
| Canvas | 1280×720 px @ 96 DPI | = 13.333" × 7.5" |
| 红横幅高 | 96 px | slideMaster Rectangle 3 |
| Logo | (8, 8) 176×79 | slideMaster Picture 6 |
| Footer | 底部 16 px 灰色 confidential | slideMaster Text Box 2 |
| 英文字体 | Calibri | tokens.json |
| 中文字体 | Microsoft JhengHei (fallback: PingFang TC, Heiti TC, Noto Sans TC) | tokens.json |

所有数值集中在 `assets/tokens.json`，改一处同时影响 HTML 和 PPT。

## 文件结构

```
assets/
  template.pptx         (PowerPoint 模板，logo/横幅/footer 在 slideMaster)
  logo.png              (HTML chrome 用)
  tokens.json           (共享 token：颜色 / 字号 / chrome 几何)
  html-template/
    milwaukee.css       (HTML 主题)
    deck.html.j2        (Jinja2 deck 模板)

scripts/
  fill_html.py          (YAML → 独立 HTML deck 文件夹)
  build_ppt.py          (YAML → .pptx；也可用 MilwaukeeDeck 类手动构建)
  polish.py             (PPT linter)

sample/
  content.yaml          (示例 deck)

tests/                  (pytest)
```

## fill_html.py 找 html-ppt skill 的顺序

1. `--html-ppt-dir <path>` 参数
2. `HTML_PPT_SKILL_DIR` 环境变量
3. 默认搜索路径：`~/Repo/myskills/.claude/skills/html-ppt/`、`~/.claude/plugins/cache/*/skills/html-ppt/`
4. 找不到 → 输出 stub runtime.js + 警告（键盘导航不可用，CSS 仍正确）

## 进阶：直接用 imperative API

```python
from build_ppt import MilwaukeeDeck, MILWAUKEE_RED

deck = MilwaukeeDeck()
s = deck.add_slide("KEY FEATURES", "Why M18 FUEL")
s.add_bullets(["POWERSTATE 电机", "REDLINK 保护"])
deck.save("out.pptx")
```

`_Slide` 提供 `add_paragraphs / add_bullets / add_table / add_image / add_kpi / add_quote / add_section_divider / columns / add_speaker_notes` 方法。详见 `scripts/build_ppt.py` 顶部 docstring。

## 设计规范

完整版见 `references/design-guidelines.md`：字号阶梯、配色规则、反模式。

## 注意事项

- 不要修改 `slideMaster`——logo/横幅/footer 都在那
- 改 tokens.json 后必须重新跑 fill_html.py 和 build_ppt.py 才会同步到输出
- HTML 预览演讲依赖 html-ppt skill 的 runtime.js（不修改 html-ppt 仓本身）
```

- [ ] **Step 10.2: 检查 SKILL.md 语法**

```bash
head -5 skills/milwaukee-ppt/SKILL.md  # 验证 frontmatter
wc -l skills/milwaukee-ppt/SKILL.md    # 应在 ~120 行内
```

Expected: 前 5 行有 `---` frontmatter；总行数 < 150。

- [ ] **Step 10.3: 第三次 commit**

```bash
cd /Users/mitumao/Repo/myskills
git add -u skills/milwaukee-ppt/scripts/  # 含删除的 deck.py / preview.py
git add skills/milwaukee-ppt/SKILL.md
git commit -m "refactor(milwaukee-ppt): drop legacy 6-variant HTML preview + rewrite SKILL.md

Remove scripts/deck.py and scripts/preview.py — their job (HTML preview
+ visual planning) is now done by fill_html.py + html-ppt skill runtime.
SKILL.md rewritten to document the new dual-track workflow."
git status --short
git log --oneline -5
```

Expected: 提交成功；git log 显示三个 feat/refactor commit。

---

## 完成标志

- [ ] 所有 19 个 pytest 测试通过
- [ ] `sample/content.yaml` 双轨各跑一次都成功
- [ ] 浏览器打开 HTML deck 视觉符合 Milwaukee 品牌
- [ ] PPT 在 PowerPoint / Keynote 打开正常，logo/横幅/footer 完整
- [ ] HTML 截图与 PPT 截图肉眼几何吻合（红横幅高度 / logo 位置等）
- [ ] 三个 commit 完成
- [ ] `scripts/deck.py` 和 `scripts/preview.py` 已删除
- [ ] SKILL.md 重写到 ~120 行内
