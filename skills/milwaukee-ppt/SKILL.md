---
name: milwaukee-ppt
description: 使用 Milwaukee Tool 品牌模板制作专业工作汇报 PPT。当用户提到"Milwaukee 模板"、"Milwaukee PPT"、"MS 模板"、"用红色模板做PPT"、"品牌模板PPT"、"Milwaukee slide"、"客户简报PPT"、"工作汇报"、"项目总结"、或上传了 MS_-_Template1.pptx 并要求制作演示文稿时，使用此 skill。即使用户只说"做个PPT"而上下文涉及 Milwaukee Tool 相关内容，也应触发此 skill。
---

# Milwaukee Tool PPT Skill

为 Milwaukee Tool 内部工作汇报场景制作 PPT。强制执行标题三层结构、设计系统约束、视觉 QA loop。

---

## ⚠️ 三条最重要的规则（违反任一视为失败）

1. **标题三层结构**（中文工作汇报的关键设计）
   - **主标题**（红 banner 上排）= 话题标签，≤ 14 中文 / 28 英文字符
   - **副标题**(红 banner 下排）= action title 结论句
   - **正文 lead**（白色区域顶部大字）= 重申结论 + 支撑数据

2. **生成后必须跑视觉 QA loop**，不允许只输出 .pptx 直接交付
   - 转 PDF → 转 JPG → 用 view 工具逐张检查 → 修复溢出/重叠 → 再生成

3. **配色克制**：白底 + 深灰文字 + 中灰副信息 + Milwaukee Red **仅作视觉锚点**
   - 红色累计面积不超过画布 5%（不含模板自带的顶部 banner）

---

## 标题分层详解

模板的红色 banner 物理空间有限，且中文工作汇报习惯目录式标题（"项目背景"、"项目节点"），所以采用**话题标题 + action title 副标题**的双层结构，正文 lead 再强化一次。

### 转换示例表

| 主标题（话题，红 banner 上排） | 副标题（action title，红 banner 下排） | 正文 lead（白色区域大标题）                    |
| ------------------------------ | -------------------------------------- | ---------------------------------------------- |
| `项目背景 / BACKGROUND`        | `报表分散已成为扩展瓶颈`               | `报表分散管理已成为扩展瓶颈`                   |
| `项目目标 / OBJECTIVES`        | `项目按目标全面交付`                   | `项目按目标全面交付`                           |
| `关键数据 / KEY OUTCOMES`      | `20+ 报表，9 个月稳定运行`             | `项目按目标全面交付`                           |
| `项目节点 / TIMELINE`          | `软件如期，硬件延后 1.5–2 个月`        | `软件如期上线，硬件因 RFQ 流程延后 1.5–2 个月` |
| `硬件改造 / HARDWARE`          | `早会会议室升级为数据运营中心`         | `早会会议室升级为数据运营中心`                 |
| `持续优化 / WHAT'S NEXT`       | `上线只是起点，迭代持续推进`           | `上线只是起点，持续迭代已落地`                 |

### 为什么这样分层

- **主标题稳定** → 中文工作汇报的常规体例，老板扫目录有锚点
- **副标题承担故事** → action title 在这里展开，老板扫副标题就能拼出完整论证
- **正文 lead 强化** → 配合大字号 + 数据支撑，把结论真正"压下来"

### 主标题写法

- 优先用中英双语（`项目背景 / BACKGROUND`），或全英大写（`PAIN POINTS`）
- 简洁有力，**禁止换行**
- 编号可选（`01. 项目背景`），但整 deck 风格统一

---

## 模板机械结构（不要修改）

模板文件：`assets/template.pptx`

### 幻灯片尺寸

- 16:9 宽屏（12192000 × 6858000 EMU）

### 固定元素（在 slideMaster 中，**不要碰**）

- 左上角 Milwaukee 白色 logo
- 顶部红色横幅
- 底部灰色页脚 `Confidential Document Property of MILWAUKEE TOOL...`

### 可编辑占位符

| 占位符 | XML 标识                                    | 用途                           | 字数上限                |
| ------ | ------------------------------------------- | ------------------------------ | ----------------------- |
| 主标题 | `<p:ph type="title"/>`                      | 红色横幅上排，白色粗体 24pt    | **≤ 28 英文 / 14 中文** |
| 副标题 | `<p:ph type="body" sz="quarter" idx="10"/>` | 红色横幅下排，白色 15pt 右对齐 | ≤ 40 字符               |

### 内容安全区（白色区域）

- X: `300000 → 11900000` EMU（左右各留 ~0.33 英寸）
- Y: `925000 → 6450000` EMU（避开顶部 banner 和底部页脚）

---

## 内容硬约束

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
| 正文 lead 标题     | Calibri Bold + Microsoft JhengHei Bold | 2800–3200 (28–32pt) |
| Section header     | Calibri Bold                           | 1700–1800 (17–18pt) |
| Eyebrow（小红字）  | Calibri Bold                           | 1100 (11pt)         |
| 正文 / 列表项      | Calibri + Microsoft JhengHei           | 1300–1400 (13–14pt) |
| 说明 / caption     | Calibri Italic                         | 1000–1100 (10–11pt) |

**字号阶梯硬要求**：同一页最大字号 / 最小字号 ≥ 3:1。

### 间距规则

- 内容区四周留白：左右各 ≥ 700000 EMU（~0.77 英寸）
- 元素间垂直间距：300000–500000 EMU
- 内容总占画布面积 ≤ 70%，剩下 30% 是留白

---

## 制作流程

### 前置依赖（首次使用执行）

```bash
pip install "markitdown[pptx]" Pillow --break-system-packages -q
which soffice pdftoppm    # 两个都必须能找到
```

### Step 1：准备工作目录

```bash
SKILL_DIR="<本 skill 的绝对路径>"
mkdir -p /home/claude/work && cd /home/claude/work
cp "$SKILL_DIR/assets/template.pptx" ./template.pptx
cp "$SKILL_DIR/assets/helpers.py" ./helpers.py
python /mnt/skills/public/pptx/scripts/office/unpack.py ./template.pptx ./unpacked/
```

### Step 2：规划标题序列（必做，禁止跳过）

在动手生成前，先输出标题序列表给用户确认。**注意三层结构**：

| #   | 主标题（话题）          | 副标题（action title）        | Layout         |
| --- | ----------------------- | ----------------------------- | -------------- |
| 1   | DATA OPERATION CENTER   | 项目总结 · Project Summary    | cover          |
| 2   | AGENDA / 目录           | 8 sections                    | agenda         |
| 3   | 项目背景 / BACKGROUND   | 报表分散已成为扩展瓶颈        | hero + 4 cards |
| 4   | 关键数据 / KEY OUTCOMES | 20+ 报表，9 个月稳定运行      | stat grid      |
| 5   | 项目节点 / TIMELINE     | 软件如期，硬件延后 1.5–2 个月 | timeline       |
| ... |

**验收标准**：只读副标题序列，能不能拼出完整故事？不能的话回去改副标题。

### Step 3：复制 slide 并注册到 sldIdLst

```bash
for i in $(seq 1 6); do
  python /mnt/skills/public/pptx/scripts/add_slide.py unpacked/ slide1.xml
done
```

**关键 trap**：`add_slide.py` 不会自动写入 `presentation.xml` 的 `<p:sldIdLst>`，必须手动加：

```xml
<p:sldIdLst>
  <p:sldId id="259" r:id="rId5"/>
  <p:sldId id="260" r:id="rId11"/>
  <p:sldId id="261" r:id="rId12"/>
  <!-- 每个新 slide 一行，rId 从 add_slide.py 输出里抄 -->
</p:sldIdLst>
```

### Step 4：用 helpers.py 生成内容

**强烈建议用 Python 生成器**，不要手工 str_replace 改 XML。

最小示例：

```python
# build_slides.py
import sys
sys.path.insert(0, '/home/claude/work')
from helpers import *

set_output_dir('/home/claude/work/unpacked/ppt/slides')

# Slide 3 示例：项目背景页
shapes = page_header(
    eyebrow_text="PROBLEM",
    lead_title="报表分散管理已成为扩展瓶颈",        # 正文 lead = 强化版结论
    lead_subtitle_en="Scattered reporting has become a scaling bottleneck"
)

# 4 张痛点卡片
pains = [
    ("01", "报表管理分散", "各业务组数据散落在多个网盘路径"),
    ("02", "高度依赖个人", "关键报表无标准化访问入口"),
    ("03", "IT 资源紧张", "请求积压，项目交付周期被拉长"),
    ("04", "缺少统一平台", "无法支撑数字化精益运营能力"),
]
for i, (num, h, body) in enumerate(pains):
    x = 700000 + i * 2690000
    shapes.extend(info_card(x, 3200000, 2580000, 2200000, num, h, body))

write_slide(3,
    title="项目背景 / BACKGROUND",                # 主标题 = 话题标签
    subtitle="报表分散已成为扩展瓶颈",            # 副标题 = action title 结论
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
python /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx
rm -f slide-*.jpg
pdftoppm -jpeg -r 100 output.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

逐张用 view 工具检查：

- [ ] 主标题完整显示在红 banner 内（未换行、未被截断）
- [ ] 副标题完整、且与主标题不重叠
- [ ] 正文 lead 大标题与副标题不重复造成审美疲劳
- [ ] 内容不溢出文本框
- [ ] 元素之间不重叠
- [ ] 中文字体正常渲染
- [ ] 大数字与下方 label 不撞
- [ ] 时间线标签与刻度数字不撞
- [ ] 颜色对比度足够

**发现问题 → 修 build_slides.py → 重新执行 Step 5–6**。

### Step 7：交付

```bash
cp output.pptx /mnt/user-data/outputs/<合适的中文文件名>.pptx
```

用 `present_files` 工具交付。

---

## Layout 库（8 个推荐布局）

每页选一个 layout，不要自创。**每个 layout 都遵循标题三层结构**。

### Layout A — Cover（封面）

| 层级   | 内容                                                                  |
| ------ | --------------------------------------------------------------------- |
| 主标题 | 产品名 / 项目名（如 `DATA OPERATION CENTER`）                         |
| 副标题 | 副定位 + 日期（如 `项目总结 · Project Summary`）                      |
| 正文   | 大号中文主标 60pt + 英文副标 28pt italic muted；左侧红色 vertical bar |

### Layout B — Agenda（目录）

| 层级   | 内容                                                |
| ------ | --------------------------------------------------- |
| 主标题 | `AGENDA` 或 `目录`                                  |
| 副标题 | `8 sections` 或类似数量说明                         |
| 正文   | 双列，每列 4 项；大号红色编号 + 中文标签 + 英文翻译 |

### Layout C — Hero + 4 Cards（结论 + 4 维论证）

| 层级   | 内容                                                                                           |
| ------ | ---------------------------------------------------------------------------------------------- |
| 主标题 | 话题（如 `项目背景 / BACKGROUND`）                                                             |
| 副标题 | action title 结论句                                                                            |
| 正文   | 顶部 eyebrow + lead 标题 + 英文副标；底部 4 张 card（CARD_BG + 顶部红条 + 编号 + 标题 + 描述） |

### Layout D — Stat Grid（关键数据）

| 层级   | 内容                                                                                                |
| ------ | --------------------------------------------------------------------------------------------------- |
| 主标题 | `关键数据 / KEY OUTCOMES` 或类似                                                                    |
| 副标题 | 数据要点（如 `20+ 报表，9 个月稳定运行`）                                                           |
| 正文   | 顶部 eyebrow + lead；底部 4 个大数字（72–96pt 红）+ INK hairline + 中文 label + 英文 caption italic |

### Layout E — Timeline（时间线）

| 层级   | 内容                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------- |
| 主标题 | `项目节点 / TIMELINE`                                                                                           |
| 副标题 | 时间结论（如 `软件如期，硬件延后 1.5–2 个月`）                                                                  |
| 正文   | 顶部 lead + 英文副标；中部水平时间轴 + 月份刻度 + 双线对比（INK / MUTED）+ 红 oval milestone + CARD_BG 瓶颈标注 |

### Layout F — Before / After（对比）

| 层级   | 内容                                                                                                                                 |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| 主标题 | `硬件改造 / HARDWARE` 或类似                                                                                                         |
| 副标题 | 转变结论（如 `早会会议室升级为数据运营中心`）                                                                                        |
| 正文   | 左 BEFORE（CARD_BG + 灰 eyebrow + 灰 bullet）+ 中间红箭头 + 右 AFTER（白底 + HAIRLINE 边 + 顶部红条 + 红 eyebrow + INK bullet 红点） |

### Layout G — Two Column Features（双栏特性）

| 层级   | 内容                                                                           |
| ------ | ------------------------------------------------------------------------------ |
| 主标题 | `持续优化 / WHAT'S NEXT` 或类似                                                |
| 副标题 | 后续动作结论                                                                   |
| 正文   | 双栏，每栏一个 section header；左栏编号 oval + 文字行；右栏左侧红小条 + 文字块 |

### Layout H — Closing（结语）

| 层级   | 内容                                       |
| ------ | ------------------------------------------ |
| 主标题 | `THANK YOU` 或品牌口号                     |
| 副标题 | 团队 / 联系信息                            |
| 正文   | 大号中英标语 + italic muted 翻译；大量留白 |

---

## 常见失败模式与修复

| 症状                       | 原因                                       | 修复                                         |
| -------------------------- | ------------------------------------------ | -------------------------------------------- |
| 主标题在 banner 里换行     | 标题太长                                   | 缩短到 ≤ 14 中文 / 28 英文；长内容移到副标题 |
| 副标题被截断               | 副标题超过 40 字符                         | 拆短或精简                                   |
| 正文 lead 和副标题语义重复 | 两者写了完全相同的结论                     | 副标题写"短结论"，正文 lead 写"结论+数据"    |
| 中文显示为方框             | 缺 `<a:ea typeface="Microsoft JhengHei"/>` | 在 rPr 里补 EA 字体声明                      |
| 文本被截断                 | 文本框 cy 不够                             | 增大 cy 或缩小字号                           |
| 浅灰字看不清               | 字色用了 MUTED 在 CARD_BG 上               | CARD_BG 上用 INK，仅在 WHITE 上用 MUTED      |
| 数字与 label 撞            | 大数字字号过大                             | 留出 ≥ 1500000 EMU 间距，加 hairline 分隔    |
| `&` 字符导致 XML 损坏      | 未做 XML 转义                              | 用 helpers 的 `_esc()`；`&` → `&amp;`        |
| 新 slide 不显示            | 没注册到 sldIdLst                          | 手动编辑 presentation.xml 加 `<p:sldId>`     |
| QA 时图未刷新              | PDF 没重新生成                             | 修改后必须重跑 soffice 转换                  |

---

## 不要做的事

- 不要修改 slideMaster（logo、banner、页脚都在那）
- 不要把 action title 放在主标题位置 —— banner 字号有限，长结论会溢出，且不符合中文汇报体例
- 不要让副标题和正文 lead 完全相同 —— 形成层级递进，不要审美疲劳
- 不要用 python-pptx —— 抽象层太高，做不出今天要求的视觉精度；直接写 OOXML XML
- 不要用 pptxgenjs —— 同上理由；只有完全无模板创建时才考虑
- 不要在 SKILL.md 之外硬编码 design tokens —— 全部走 helpers.py 的常量
- 不要跳过 QA loop —— 没看图就交付的 PPT 100% 有溢出/重叠问题

---

## 文件结构

```
milwaukee-ppt/
├── SKILL.md              # 本文件
└── assets/
    ├── template.pptx     # MS_-_Template1.pptx
    └── helpers.py        # XML 生成器助手（必须 import 使用）
```
