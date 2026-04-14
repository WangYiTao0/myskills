---
name: milwaukee-ppt
description: 使用 Milwaukee Tool 品牌模板制作 PPT。当用户提到"Milwaukee 模板"、"Milwaukee PPT"、"MS 模板"、"用红色模板做PPT"、"品牌模板PPT"、"Milwaukee slide"、"客户简报PPT"、或上传了 MS_-_Template1.pptx 并要求制作演示文稿时，使用此 skill。即使用户只说"做个PPT"而上下文涉及 Milwaukee Tool 相关内容，也应触发此 skill。
---

# Milwaukee Tool PPT Template Skill

## 模板结构

模板文件：`assets/template.pptx`（位于本 skill 目录下）

### 幻灯片尺寸
- 标准 16:9 宽屏（12192000 x 6858000 EMU）

### 固定元素（在 slideMaster 中，不要修改）
- **左上角**：Milwaukee 白色 logo（image1.png）
- **顶部红色横幅**：全宽红色背景条
- **底部页脚**：灰色 "Confidential Document Property of MILWAUKEE TOOL Brookfield, Wisconsin 53005"

### 可编辑占位符（在 slideLayout1 中）

| 占位符 | XML 标识 | 位置 | 用途 |
|--------|----------|------|------|
| **主标题** | `<p:ph type="title"/>` (name="Title 2") | 右上红色横幅上排 (x=4644601, y=87850, cx=7543800, cy=369350) | 大写粗体白色文字，24pt |
| **副标题** | `<p:ph type="body" idx="10"/>` (name="Text Placeholder 1") | 右上红色横幅下排 (x=4663651, y=457200, cx=7524750, cy=381000) | 白色文字，15pt，右对齐 |

### 内容区域（白色空白区，需自行添加形状）
- Y 范围：~900000 到 ~6500000 EMU（红色横幅下方到页脚上方）
- X 范围：~300000 到 ~11900000 EMU（左右留边距）
- 此区域没有预设占位符，需通过添加 `<p:sp>` 形状来放置文字、表格、图片等

---

## 制作流程

### 前置依赖

```bash
pip install "markitdown[pptx]" Pillow --break-system-packages -q
```

### Step 1：准备工作目录

```bash
# 获取 skill 目录下的模板
SKILL_DIR="<本skill的绝对路径>"
cp "$SKILL_DIR/assets/template.pptx" /home/claude/template.pptx

# 解包
python /mnt/skills/public/pptx/scripts/office/unpack.py /home/claude/template.pptx /home/claude/unpacked/
```

### Step 2：规划幻灯片

根据用户提供的内容，规划每一页的：
- 主标题（大写英文或中文，显示在红色横幅上排）
- 副标题（显示在红色横幅下排）
- 内容区域的布局类型和内容

### Step 3：复制幻灯片

模板只有 1 页（slide1.xml）。为每个额外页面复制：

```bash
# 为第 N 页复制 slide1
python /mnt/skills/public/pptx/scripts/add_slide.py /home/claude/unpacked/ slide1.xml
```

将输出的 `<p:sldId>` 插入 `ppt/presentation.xml` 的 `<p:sldIdLst>` 中。

### Step 4：编辑每页内容

对每个 `slideN.xml`：

#### 4a. 编辑主标题
找到 `<p:ph type="title"/>` 所在的 `<p:sp>`，在其 `<p:txBody>` 中填入文字：

```xml
<p:txBody>
  <a:bodyPr/>
  <a:lstStyle/>
  <a:p>
    <a:r>
      <a:rPr lang="en-US" dirty="0"/>
      <a:t>YOUR TITLE HERE</a:t>
    </a:r>
  </a:p>
</p:txBody>
```

#### 4b. 编辑副标题
找到 `<p:ph type="body" sz="quarter" idx="10"/>` 所在的 `<p:sp>`，填入文字：

```xml
<p:txBody>
  <a:bodyPr/>
  <a:lstStyle/>
  <a:p>
    <a:r>
      <a:rPr lang="en-US" dirty="0"/>
      <a:t>Your Subtitle Here</a:t>
    </a:r>
  </a:p>
</p:txBody>
```

#### 4c. 添加内容区域

在 `<p:spTree>` 中追加新的 `<p:sp>` 形状。以下是常用内容模板：

**纯文字框：**
```xml
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="100" name="Content 1"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="457200" y="1000000"/>
      <a:ext cx="11277600" cy="5400000"/>
    </a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" rtlCol="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="zh-TW" sz="1800" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="333333"/></a:solidFill>
          <a:latin typeface="Calibri"/>
          <a:ea typeface="Microsoft JhengHei"/>
        </a:rPr>
        <a:t>段落标题</a:t>
      </a:r>
    </a:p>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="zh-TW" sz="1400" dirty="0">
          <a:solidFill><a:srgbClr val="333333"/></a:solidFill>
          <a:latin typeface="Calibri"/>
          <a:ea typeface="Microsoft JhengHei"/>
        </a:rPr>
        <a:t>正文内容</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

**带项目符号的列表：**
在 `<a:p>` 中添加 `<a:pPr marL="342900" indent="-342900"><a:buChar char="&#x2022;"/></a:pPr>`

**表格：** 使用 `<a:graphicFrame>` + `<a:tbl>` 结构（参考 OOXML 表格规范）

> **注意**：每个新增 `<p:sp>` 的 `id` 必须在整个 slide 中唯一，从 100 开始递增即可。

### Step 5：清理和打包

```bash
python /mnt/skills/public/pptx/scripts/clean.py /home/claude/unpacked/
python /mnt/skills/public/pptx/scripts/office/pack.py /home/claude/unpacked/ /home/claude/output.pptx --original /home/claude/template.pptx
```

### Step 6：QA 检查

```bash
# 内容检查
python -m markitdown /home/claude/output.pptx

# 视觉检查
python /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf /home/claude/output.pptx
rm -f /home/claude/slide-*.jpg
pdftoppm -jpeg -r 150 /home/claude/output.pdf /home/claude/slide
ls -1 "$PWD"/slide-*.jpg
```

用 view 工具查看每张 slide 图片，确认：
- 标题和副标题在红色横幅内正确显示
- 内容区域没有溢出或重叠
- 中文字体正确渲染

### Step 7：输出

```bash
cp /home/claude/output.pptx /mnt/user-data/outputs/
```

使用 `present_files` 工具交付给用户。

---

## 设计规范

| 元素 | 规范 |
|------|------|
| 主标题字体 | 继承模板（粗体，白色，24pt，阴影效果） |
| 副标题字体 | 继承模板（白色，15pt，右对齐） |
| 内容标题 | Calibri Bold / Microsoft JhengHei Bold, 18-20pt, #333333 |
| 内容正文 | Calibri / Microsoft JhengHei, 14-16pt, #333333 |
| 强调色 | Milwaukee 红 #DB021D 用于重点标注 |
| 背景 | 保持白色，不要修改 |

## 注意事项

- **不要修改 slideMaster**：logo、红色横幅、页脚都在 master 中
- **主标题建议用大写英文**：与 Milwaukee 品牌风格一致
- **中文内容**：使用 `lang="zh-TW"` 并指定 `<a:ea typeface="Microsoft JhengHei"/>`
- **每页 id 不冲突**：新增形状 id 从 100 开始
- **Use str_replace_tool (Edit tool) for XML edits**，不要用 sed 或 Python 脚本修改 XML
