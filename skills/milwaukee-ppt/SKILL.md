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

**基础内容：**

| 方法 | 作用 | 关键参数 |
|------|------|----------|
| `MilwaukeeDeck(template_path?)` | 初始化（可指定模板） | 默认 `assets/template.pptx` |
| `deck.add_slide(title, subtitle="")` | 加一页 | 返回 `_Slide` |
| `slide.add_paragraphs(items, ...)` | 多段文字 | `items` 是 `[(text, style_dict), ...]` |
| `slide.add_bullets(bullets, size=14, ...)` | 项目符号列表 | |
| `slide.add_table(rows, header=True, ...)` | 表格（首行红底白字） | `rows` 是 `list[list[str]]` |
| `slide.add_image(path, ...)` | 嵌入图片 | `*_cm` 控制位置和尺寸 |
| `deck.save(path, force=False)` | 保存（自动检测 PowerPoint 锁定） | 返回绝对路径 |

**Polish 版式（推荐用于美化）：**

| 方法 | 作用 |
|------|------|
| `slide.columns(n, ratios?, gap_cm=0.5, ...)` | 返回 n 列的 rect 字典列表，喂给 `add_*` 做并列版式 |
| `slide.add_kpi(value, label, color=red)` | 巨大数字 + 下方说明（统计高光页） |
| `slide.add_quote(text, author="")` | 居中斜体引述 + 右对齐署名 |
| `slide.add_section_divider(text)` | 居中超大红字（章节封面） |
| `slide.add_speaker_notes(text)` | 写到 speaker notes，**不出现在幻灯片正面** |

`style_dict` 支持：`size`（pt）、`bold`、`color`（`RGBColor`）、`align`（`'l'/'c'/'r'`）、`bullet`、`name`（latin 字体）、`ea`（中文字体）。

省略坐标时按内置内容流自动堆叠（每个块下方留 0.3cm）。

**调色板常量：**`MILWAUKEE_RED`、`TEXT_DARK`、`TEXT_MID`、`BG_LIGHT`、`WHITE`、`STATUS_OK`、`STATUS_WARN`、`STATUS_DANGER`，或用 `PALETTE` dict 取。

## Polish workflow（美化）

构建完 deck 后跑 linter，把违规指出来再修：

```bash
python scripts/polish.py output.pptx
# 或严格模式（任何 warning 都退出非零）
python scripts/polish.py output.pptx --strict
```

linter 检查项（参见 `references/design-guidelines.md` 的具体阈值）：

- 标题 ≤ 40 字符 / 副标题 ≤ 60 字符
- 字体族 ≤ 2（Latin + CJK）
- 配色在品牌调色板内（红 + 中性灰白 + 状态色）
- 项目符号 ≤ 6 / 页，单条 ≤ 12 字（中）或 ≤ 6 词（英）
- 表格 ≤ 7 行
- 图片 ≥ 1280×720
- 检测 PowerPoint 是否正在打开该文件（`~$xxx.pptx` 锁文件）

设计规范完整版（字号阶梯、配色、间距、反模式）见 `references/design-guidelines.md`。

**Polish 示例：**

```python
# 章节封面
s = deck.add_slide("CHAPTER 01", "Strategy")
s.add_section_divider("Why M18 FUEL Now")

# 三栏对比
s = deck.add_slide("THREE PILLARS", "Product Strategy")
for col, (head, body) in zip(s.columns(3, gap_cm=0.6, top_cm=4, height_cm=10), data):
    s.add_paragraphs([
        (head, {"size": 20, "bold": True, "color": MILWAUKEE_RED, "align": "c"}),
        (body, {"size": 14, "align": "c"}),
    ], **col)

# KPI 高光
s = deck.add_slide("MARKET IMPACT", "FY2025 Recap")
s.add_kpi("+34%", "全球专业渠道销售同比增长", top_cm=4)

# 引述
s = deck.add_slide("VOICE OF CUSTOMER", "Field Feedback")
s.add_quote("M18 FUEL 让我每天少充两次电。", author="资深木工 · 香港", top_cm=5)
```

## 单位换算

- 1 cm = 360000 EMU
- 1 inch = 914400 EMU
- 幻灯片：33.87cm × 19.05cm（13.33" × 7.5"）

## 字体兜底

`build_ppt.py` 中文默认 `Microsoft JhengHei`；macOS 没装时系统会回退（Mac 常见可用：`PingFang TC`、`Heiti TC`）。客户机如严重在意一致性，把 PPT 转 PDF 再发。

## 设计规范（速查）

完整版见 `references/design-guidelines.md`。摘要：

| 元素 | 规范 |
|------|------|
| 主标题 | 模板继承（粗体白色 24pt 阴影） |
| 副标题 | 模板继承（白色 15pt 右对齐） |
| 内容一级标题 | Calibri/JhengHei Bold 28-32pt #333333 |
| 内容二级标题 | Calibri/JhengHei Semibold 20-24pt |
| 正文 | Calibri/JhengHei 16pt #333333（密集场景 14pt） |
| 强调色 | Milwaukee 红 `#DB021D`，每页面积 ≤ 10% |
| 边距 | 1.0 cm（外缘）/ 0.3 cm（段间）/ 0.6 cm（小节间） |
| 字体族数 | ≤ 2（Calibri + Microsoft JhengHei） |
| 项目符号 | ≤ 6 / 页，每条 ≤ 12 字（中）/ ≤ 6 词（英） |

## 注意事项

- 不要修改 `slideMaster` 或 `slideLayout1`——logo / 横幅 / 页脚都在那
- 主标题建议大写英文，符合品牌语气
- 模板开发于 macOS。Linux 也能跑，沙箱环境如果带 `/mnt/skills/public/pptx/scripts/` 也可继续用那套老路径，但本 skill 不再依赖它
