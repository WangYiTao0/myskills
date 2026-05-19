---
name: milwaukee-ppt
description: 使用 Milwaukee Tool 品牌模板制作专业工作汇报 PPT。当用户提到"Milwaukee 模板"、"Milwaukee PPT"、"MS 模板"、"用红色模板做PPT"、"品牌模板PPT"、"Milwaukee slide"、"客户简报PPT"、"工作汇报"、"项目总结"、或上传了 MS_-_Template1.pptx 并要求制作演示文稿时，使用此 skill。即使用户只说"做个PPT"而上下文涉及 Milwaukee Tool 相关内容，也应触发此 skill。
---

# Milwaukee Tool PPT Skill

为 Milwaukee Tool 内部工作汇报场景制作 PPT。强制执行内容硬约束、设计系统约束、视觉 QA loop。

---

## ⚠️ 三条最重要的规则（违反任一视为失败）

2. **生成后必须跑视觉 QA loop**，不允许只输出 .pptx 直接交付
   - 转 PDF → 转 JPG → 用 view 工具逐张检查 → 修复溢出/重叠 → 再生成

3. **配色克制**：白底 + 深灰文字 + 中灰副信息 + Milwaukee Red **仅作视觉锚点**
   - 红色累计面积不超过画布 5%（不含模板自带的顶部 banner）

---

## 模板机械结构（不要修改）

模板文件：`assets/template.pptx`

### 幻灯片尺寸

- 16:9 宽屏（12192000 × 6858000 EMU）

### 固定元素（在 slideMaster 中，**不要碰**）

- 左上角 Milwaukee 白色 logo
- 顶部红色横幅
- 底部灰色页脚 `Confidential Document Property of MILWAUKEE TOOL...`

### 可编辑占位符（在 slide 中）

| 占位符 | XML 标识                                    | 用途                           | 字数上限                                      |
| ------ | ------------------------------------------- | ------------------------------ | --------------------------------------------- |
| 主标题 | `<p:ph type="title"/>`                      | 红色横幅上排，白色粗体 24pt    | **≤ 28 个英文字符 / 14 个中文字符**（防溢出） |
| 副标题 | `<p:ph type="body" sz="quarter" idx="10"/>` | 红色横幅下排，白色 15pt 右对齐 | ≤ 40 字符                                     |

### 内容安全区（白色区域）

- X: `300000 → 11900000` EMU（左右各留 ~0.33 英寸）
- Y: `925000 → 6450000` EMU（避开顶部 banner 和底部页脚）

---

## 内容硬约束

### Action Title 原则（最重要的内容规则）

每页主标题陈述这页的**核心结论**，让老板只看标题序列就能拼出完整故事。这是 McKinsey 简报法的核心。

**转换示例：**

| 话题标签（差） | Action Title（好）                |
| -------------- | --------------------------------- |
| 项目背景       | 报表分散已成为扩展瓶颈            |
| 项目目标       | 项目按目标全面交付                |
| 关键数据       | 集成 20+ 报表，稳定运行 9 个月    |
| 项目节点       | 软件如期上线，硬件延后 1.5–2 个月 |
| 持续优化       | 上线只是起点，迭代持续推进        |
| 团队           | 7 个部门协同完成交付              |

副标题用来放话题标签 / 英文翻译 / 简短说明。

### 每页一个核心信息

- 一页只回答一个问题，禁止多议题混搭
- 内容超出时拆成两页，不要塞满
- bullet list 是最后选择，能用大数字 / 对比 / 时间线 / 流程图就用

### 禁用元素清单

- ❌ **Emoji 占位符**（📷 📊 📈 等）—— 改用真实形状或简短文字描述
- ❌ **两栏 bullet list 堆砌** —— AI slop 标志
- ❌ **同一页 4+ 个 bullet 段落** —— 改用 card 网格或图表
- ❌ **标题下方 accent line** —— AI 生成 PPT 的标志性丑陋元素
- ❌ **全宽装饰性彩色条 / 渐变背景** —— 让模板自带的红 banner 做唯一锚点
- ❌ **SmartArt 风格的方框+箭头流程** —— 改用极简数字标号 + 文字
- ❌ **米色/奶油色背景** —— 永远用白色 `FFFFFF`

---

## 设计系统（Design Tokens）

### 配色（严格只用这 5 个值）

| Token      | 值        | 用途                                                             |
| ---------- | --------- | ---------------------------------------------------------------- |
| `RED`      | `#DB021D` | Milwaukee Red，仅作视觉锚（强调数字、small bar、点状 milestone） |
| `INK`      | `#1A1A1A` | 主文本色                                                         |
| `MUTED`    | `#6B6B6B` | 副文本、标签、描述                                               |
| `HAIRLINE` | `#E5E5E5` | 细分割线、卡片边框                                               |
| `CARD_BG`  | `#F7F7F7` | 卡片背景（差异化用，禁止大面积铺色）                             |
| `WHITE`    | `#FFFFFF` | 页面背景，永远不变                                               |

### 字体

| 元素               | 字体                                   | 字号                |
| ------------------ | -------------------------------------- | ------------------- |
| 大数字 (hero stat) | Calibri Bold                           | 7200–9600 (72–96pt) |
| 页面 lead 标题     | Calibri Bold + Microsoft JhengHei Bold | 2800–3200 (28–32pt) |
| Section header     | Calibri Bold                           | 1700–1800 (17–18pt) |
| Eyebrow（小红字）  | Calibri Bold                           | 1100 (11pt)         |
| 正文 / 列表项      | Calibri + Microsoft JhengHei           | 1300–1400 (13–14pt) |
| 说明 / caption     | Calibri Italic                         | 1000–1100 (10–11pt) |

**字号阶梯硬要求**：同一页最大字号 / 最小字号 ≥ 3:1。没有强对比，画面就平。

### 间距规则

- 内容区四周留白：左右各 ≥ 700000 EMU（~0.77 英寸）
- 元素间垂直间距：300000–500000 EMU
- 内容总占画布面积 ≤ 70%，剩下 30% 是留白

---

## 制作流程

### 前置依赖（首次使用执行）

```bash
pip install "markitdown[pptx]" Pillow --break-system-packages -q
# 必须确认这两个命令可用：
which soffice pdftoppm
```

### Step 1：准备工作目录

```bash
SKILL_DIR="<本 skill 的绝对路径>"
mkdir -p /home/claude/work && cd /home/claude/work
cp "$SKILL_DIR/assets/template.pptx" ./template.pptx
cp "$SKILL_DIR/assets/helpers.py" ./helpers.py

# 解包
python /mnt/skills/public/pptx/scripts/office/unpack.py ./template.pptx ./unpacked/
```

### Step 2：规划幻灯片（必做，禁止跳过）

在动手生成前，先输出一个**标题序列表**给用户确认：

| #   | Action Title（中）     | Subtitle（英）           | Layout 类型    |
| --- | ---------------------- | ------------------------ | -------------- |
| 1   | 数据运营中心           | Data Operation Center    | cover          |
| 2   | （目录）               | Agenda                   | agenda         |
| 3   | 报表分散已成为扩展瓶颈 | Why we needed a data hub | hero + 4 cards |
| ... |

把标题序列读一遍——能否拼出完整故事？如果不能，回去改标题。

### Step 3：复制 slide 并注册到 sldIdLst

```bash
# 模板只有 1 页，需要复制 N-1 次。例如要 7 页：
for i in $(seq 1 6); do
  python /mnt/skills/public/pptx/scripts/add_slide.py unpacked/ slide1.xml
done
```

**关键 trap**：`add_slide.py` 不会自动把新 slide 写入 `presentation.xml` 的 `<p:sldIdLst>`，必须手动加：

```xml
<p:sldIdLst>
  <p:sldId id="259" r:id="rId5"/>
  <p:sldId id="260" r:id="rId11"/>
  <p:sldId id="261" r:id="rId12"/>
  <!-- ... 每个新 slide 一行，rId 从命令输出里抄 -->
</p:sldIdLst>
```

### Step 4：用 helpers.py 生成内容（推荐方式）

**强烈建议用 Python 生成器写每一页**，不要手工 str_replace 改 XML。原因：

- XML 转义、ID 唯一性、坐标计算容易出错
- 改设计时只改一处变量（如 `RED` 色值），全 deck 同步
- 一份生成器脚本可以做无限页

最小示例：

```python
# build_slides.py
import sys
sys.path.insert(0, '/home/claude/work')
from helpers import *

OUT_DIR = '/home/claude/work/unpacked/ppt/slides'
set_output_dir(OUT_DIR)

# Slide 1: cover
shapes = []
shapes.append(rect(457200, 1900000, 91440, 1900000, fill=RED))  # 左侧红色 vertical bar
shapes.append(rect(700000, 1820000, 10500000, 800000,
    paragraphs=para(run("数据运营中心", sz=6000, bold=True, color=INK))))
shapes.append(rect(700000, 2700000, 10500000, 500000,
    paragraphs=para(run("Data Operation Center", sz=2800, color=MUTED, italic=True, lang="en-US"))))

write_slide(1,
    title="DATA OPERATION CENTER",
    subtitle="项目总结  ·  Project Summary",
    content_shapes=shapes)
```

完整 helpers API 见 `assets/helpers.py` 文件头注释。

### Step 5：清理 + 打包

```bash
python build_slides.py
python /mnt/skills/public/pptx/scripts/clean.py unpacked/
python /mnt/skills/public/pptx/scripts/office/pack.py unpacked/ output.pptx --original template.pptx
```

### Step 6：**强制视觉 QA Loop**（不可跳过）

```bash
# 1. 转 PDF
python /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx

# 2. 转 JPG（清空旧图）
rm -f slide-*.jpg
pdftoppm -jpeg -r 100 output.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

然后**逐张用 view 工具查看**，检查清单：

- [ ] 主标题是否完整显示在红 banner 内（未换行、未被截断）
- [ ] 副标题未与主标题重叠
- [ ] 内容是否溢出文本框边界
- [ ] 元素之间是否重叠
- [ ] 中文字体正常渲染（不是方框 / 不是英文 fallback）
- [ ] 大数字未与下方 label 撞到
- [ ] 时间线上的标签未与刻度数字撞到
- [ ] 颜色对比度足够（无浅灰字在浅灰底上）

**发现任一问题 → 修 build_slides.py → 重新执行 Step 5–6**。

允许的修复方式：

- 主标题太长 → 缩写或拆分；不要硬塞
- 元素重叠 → 调整 EMU 坐标；不要硬撑
- 内容溢出 → 减字号或拆页；不要超框

### Step 7：交付

```bash
cp output.pptx /mnt/user-data/outputs/<合适的中文文件名>.pptx
```

用 `present_files` 工具交付。

---

## Layout 库（8 个推荐布局）

每页选一个 layout，不要自创。这是经过验证的工作汇报模式。

### Layout A — Cover（封面）

- 左侧红色 vertical bar（**不是**横向 banner，避开 AI slop）
- 大号中文主标题 60pt + 英文副标 28pt italic muted
- Hairline 分割线下放 presenter / date

### Layout B — Agenda（目录）

- 双列，每列 4 项
- 大号红色编号 36pt + 中文标签 18pt bold + 英文翻译 11pt muted
- 不加装饰线，纯靠字号对比

### Layout C — Hero + 4 Cards（结论 + 4 维论证）

- 顶部：eyebrow（11pt 红字标签）+ lead 标题 32pt + 英文副标 italic
- 底部：4 张 card（CARD_BG 底，顶部 50000 EMU 红色细条），含编号 + 标题 + 描述

### Layout D — Stat Grid（关键数据）

- 顶部：eyebrow + 结论标题
- 底部：4 个大数字（72–96pt 红色）+ INK hairline + 中文 label + 英文 caption italic

### Layout E — Timeline（时间线）

- 顶部：eyebrow + 结论标题
- 中部：水平时间轴 + 月份刻度
- 双线对比：上方 INK 实心 bar（如软件），下方 MUTED 实心 bar（如硬件）
- 关键 milestone 用红色 oval（直径 140000 EMU）+ 日期 caption
- 瓶颈期用 CARD_BG 浅块标注

### Layout F — Before / After（对比）

- 左右两张同尺寸 card
- 左侧 BEFORE：CARD_BG 底 + 灰色 eyebrow + 灰色 bullet
- 右侧 AFTER：白底 + HAIRLINE 边框 + 顶部 60000 EMU 红条 + 红色 eyebrow + INK bullet（bullet 点用红色）
- 中间一个小红色右箭头（rightArrow prstGeom）

### Layout G — Two Column Features（双栏特性）

- 两栏，每栏一个 section header（eyebrow + 标题）
- 左栏用编号 oval + 文字行
- 右栏用左侧红色小条 + 文字块

### Layout H — Closing（结语）

- 大号中英标语，居中或右对齐
- 仅一行 highlight 文字 + italic muted 翻译
- 大量留白

---

## 常见失败模式与修复

| 症状                   | 原因                                       | 修复                                      |
| ---------------------- | ------------------------------------------ | ----------------------------------------- |
| 主标题在 banner 里换行 | 标题太长                                   | 缩短到 ≤ 14 个中文字符 / 28 个英文字符    |
| 中文显示为方框         | 缺 `<a:ea typeface="Microsoft JhengHei"/>` | 在 rPr 里补 EA 字体声明                   |
| 文本被截断             | 文本框 cy 不够                             | 增大 cy 或缩小字号                        |
| 浅灰字看不清           | 字色用了 MUTED 在 CARD_BG 上               | CARD_BG 上用 INK，仅在 WHITE 上用 MUTED   |
| 数字与 label 撞        | 大数字字号过大                             | 留出 ≥ 1500000 EMU 间距，加 hairline 分隔 |
| `&` 字符导致 XML 损坏  | 未做 XML 转义                              | 用 helpers 的 `_esc()`；`&` → `&amp;`     |
| 新 slide 不显示        | 没注册到 sldIdLst                          | 手动编辑 presentation.xml 加 `<p:sldId>`  |
| QA 时图未刷新          | PDF 没重新生成                             | 修改后必须重跑 soffice 转换               |

---

## 不要做的事

- 不要修改 slideMaster（logo、banner、页脚都在那）
- 不要用 python-pptx —— 抽象层太高，做不出今天要求的视觉精度；直接写 OOXML XML
- 不要用 pptxgenjs —— 同上理由；只有完全无模板创建时才考虑
- 不要在 SKILL.md 之外的位置硬编码 design tokens —— 全部走 helpers.py 的常量
- 不要跳过 QA loop —— 没看图就交付的 PPT 100% 有溢出 / 重叠问题

---

## 文件结构

```
milwaukee-ppt/
├── SKILL.md              # 本文件
└── assets/
    ├── template.pptx     # MS_-_Template1.pptx
    └── helpers.py        # XML 生成器助手（必须 import 使用）
```
