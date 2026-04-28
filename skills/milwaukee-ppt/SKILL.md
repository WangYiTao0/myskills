---
name: milwaukee-ppt
description: 使用 Milwaukee Tool 品牌模板制作 PPT。当用户明确提到"Milwaukee 模板"、"Milwaukee PPT"、"MS 模板"、"Milwaukee slide"、"Milwaukee 品牌简报"，或上传了 MS_-_Template1.pptx / 当前 skill 的 template.pptx 并要求制作演示文稿时使用。仅在 Milwaukee 品牌上下文下触发——不要因为用户单纯说"做个PPT"就启用。
---

# Milwaukee Tool PPT Template Skill

跨平台（macOS / Linux）。基于 `python-pptx` 生成，不手编 XML。

## 模板结构

模板文件：`assets/template.pptx`

- 16:9 宽屏，33.87 × 19.05 cm（EMU 12192000 × 6858000）
- 单 layout：`Blank Slide`
- 固定元素（在 slideMaster 中，**不要改**）：左上 Milwaukee logo、顶部红色横幅、底部灰色页脚
- 占位符（在 slideLayout1 + slide1 中）：
  - **idx=0** TITLE — 红色横幅右上排，白色粗体大写，约 24pt
  - **idx=10** BODY  — 红色横幅右下排，白色 15pt 右对齐（用作副标题）
- 内容白区：约 left=1cm, top=2.5cm, right=32.87cm, bottom=17.5cm

## 前置依赖

```bash
# 推荐用 venv（Mac 上 brew Python 不允许全局 pip）
python3 -m venv .venv && source .venv/bin/activate
pip install python-pptx Pillow markitdown[pptx]
```

## 制作流程

### Step 1：写一个调用脚本（参考 `scripts/build_ppt.py` 的 API）

`scripts/build_ppt.py` 提供 `MilwaukeeDeck` 类。每页一个 `add_slide(title, subtitle)`，再链式加内容。**第一页会复用模板自带的 slide1**，后续页通过 layout 自动拷贝（保留 logo/横幅/页脚）。

```python
import sys
sys.path.insert(0, "<skill绝对路径>/scripts")
from build_ppt import MilwaukeeDeck

deck = MilwaukeeDeck()  # 默认加载 assets/template.pptx

# --- 页 1：纯文字介绍 ---
s1 = deck.add_slide("PRODUCT OVERVIEW", "M18 FUEL Series · 2026")
s1.add_paragraphs([
    ("产品定位", {"size": 18, "bold": True}),
    ("面向专业用户的高扭矩冲击钻系列，电池续航提升 30%。", {"size": 14}),
])

# --- 页 2：项目符号列表 ---
s2 = deck.add_slide("KEY FEATURES", "Why M18 FUEL")
s2.add_bullets([
    "POWERSTATE 无刷电机，扭矩 1200 Nm",
    "REDLINK PLUS 智能保护",
    "REDLITHIUM HIGH OUTPUT 电池兼容",
])

# --- 页 3：表格 ---
s3 = deck.add_slide("SPEC COMPARISON", "Models")
s3.add_table([
    ["Model", "Torque (Nm)", "Speed (RPM)", "Weight (kg)"],
    ["M18-A", "1000", "0-2000", "1.8"],
    ["M18-B", "1200", "0-2100", "2.0"],
])

# --- 页 4：图片 + 说明 ---
s4 = deck.add_slide("PRODUCT SHOT", "Hero image")
s4.add_image("/path/to/product.png", left_cm=2, top_cm=3, width_cm=12)
s4.add_paragraphs(
    [("便携、强劲、耐用。", {"size": 16, "bold": True})],
    left_cm=15, top_cm=6, width_cm=15, height_cm=2,
)

deck.save("output.pptx")  # 保存到当前工作目录
```

### Step 2：运行

```bash
python build_my_deck.py
```

### Step 3：QA

```bash
# 内容核对
python -m markitdown output.pptx | head -80

# 视觉核对（macOS：brew install --cask libreoffice && brew install poppler）
soffice --headless --convert-to pdf output.pptx
pdftoppm -png -r 100 output.pdf slide
# 然后 view slide-*.png
```

## API 速查（`scripts/build_ppt.py`）

| 方法 | 作用 | 关键参数 |
|------|------|----------|
| `MilwaukeeDeck(template_path?)` | 初始化（可指定模板） | 默认 `assets/template.pptx` |
| `deck.add_slide(title, subtitle="")` | 加一页 | 返回 `_Slide` |
| `slide.add_paragraphs(items, left_cm?, top_cm?, width_cm?, height_cm?)` | 多段文字 | `items` 是 `[(text, style_dict), ...]` |
| `slide.add_bullets(bullets, size=14, ...)` | 项目符号列表 | |
| `slide.add_table(rows, header=True, ...)` | 表格（首行红底白字） | `rows` 是 `list[list[str]]` |
| `slide.add_image(path, left_cm?, top_cm?, width_cm?, height_cm?)` | 嵌入图片 | |
| `deck.save(path)` | 保存 | 返回绝对路径 |

`style_dict` 支持：`size`（pt）、`bold`、`color`（`RGBColor`）、`align`（`'l'/'c'/'r'`）、`bullet`、`name`（latin 字体）、`ea`（中文字体）。

省略坐标时按内置内容流自动堆叠（每个块下方留 0.3cm）。

## 单位换算

- 1 cm = 360000 EMU
- 1 inch = 914400 EMU
- 幻灯片：33.87cm × 19.05cm（13.33" × 7.5"）

## 字体兜底

`build_ppt.py` 中文默认 `Microsoft JhengHei`；macOS 没装时系统会回退（Mac 常见可用：`PingFang TC`、`Heiti TC`）。客户机如严重在意一致性，把 PPT 转 PDF 再发。

## 设计规范

| 元素 | 规范 |
|------|------|
| 主标题 | 模板继承（粗体白色 24pt 阴影） |
| 副标题 | 模板继承（白色 15pt 右对齐） |
| 内容标题 | Calibri Bold 18-20pt #333333 |
| 内容正文 | Calibri 14-16pt #333333 |
| 强调色 | Milwaukee 红 `#DB021D`（已暴露为 `MILWAUKEE_RED`） |

## 注意事项

- 不要修改 `slideMaster` 或 `slideLayout1`——logo / 横幅 / 页脚都在那
- 主标题建议大写英文，符合品牌语气
- 模板开发于 macOS。Linux 也能跑，沙箱环境如果带 `/mnt/skills/public/pptx/scripts/` 也可继续用那套老路径，但本 skill 不再依赖它
