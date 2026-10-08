# 公司母版上的可编辑生成与跨平台方案

研究日期：2026-10-08。研究票：[公司母版上的可编辑生成与跨平台方案](https://github.com/WangYiTao0/myskills/issues/5)；上下文：[公司母版 PPT skill：共用布局与项目汇报规则规划](https://github.com/WangYiTao0/myskills/issues/1)。状态：**研究完成，已通过独立内容审核；不是技术选型决议，未实现生成器。**

## 1. 结论与证据边界

- **直接使用现有公司母版：python-pptx 加载现有 `.pptx`，从已有 layout 新建 slide，填已有 placeholder，是有官方文档与源码支撑的路线。** 正文可以另加原生文字、shape、table 与图片，标题不必重画。保留原始母版结构不等于保证每台机器渲染相同。[P1–P5]
- **PptxGenJS 4.0.1 原生 API 不能作为任意 `.pptx` 模板读取/保留器。** `defineSlideMaster()` 是用对象定义新的 layout；构造函数不接受模板，导出从新 ZIP 开始生成 master/layout/theme。它能生成可编辑对象，但重建一个视觉相似的母版，不等于沿用公司原母版。[J1–J3]
- **OOXML 定点修改可最大限度缩小变化面，但不是现成的自动排版功能。** 对现有 slide 的文字节点定点更新、其他 package part 保持不变，与重新生成 master/layout 是两个不同方案；新增页、表格、图片需要维护 relationship、ID、content type 和继承关系。源码库的抽象层可以少写这些细节，不能消除格式风险。[O1–O3]
- **跨平台最重要的风险是字体、继承/直接格式、SVG fallback 与目标应用渲染，而非语言是 Python 还是 JS。** 生成与渲染 QA 要分开；只能写出 `.pptx`，不能声称已完成 PowerPoint 视觉验收。[F1, P4, P6, J4–J6, Q1–Q4]

版本范围：python-pptx **v1.0.2 固定 tag 源码**，配合官方 `latest` 文档（页面自标 1.0.0）；PptxGenJS **v4.0.1 固定 tag 源码**，配合官方文档；OOXML 使用 Microsoft Learn 对 ISO/IEC 29500 的结构说明及 Open XML SDK **3.0.1 API**；OpenCode 只采用 **V2** 文档；Claude Code、Microsoft 365、LibreOffice 采用研究日官方在线文档。**没有把这些版本声称为研究日最新稳定版，也没有外推到未来版本。** python-pptx 安装文档仍有 Python 2.x 旧说明，依赖要求以 v1.0.2 `pyproject.toml` 为准。[P7–P8, J7, H1–H5]

本研究为文档/源码核查，**未运行合成 PPT 实验、未进行 PowerPoint/LibreOffice 渲染、未安装任何工具或依赖**。未读取其他本地仓库的真实 PPT，未提取或新增模板副本、截图、业务数据。模板尺寸与 placeholder 契约使用委派给定事实及本仓库已公开说明，未重新检查二进制。以下“可行”表示 API/文件结构有依据，不表示已通过本公司模板端到端验收。

## 2. 已决条件、旧参考与待决定项分开

### 已有用户方向（来自 map，不是本研究推荐）

目标是同事提供材料后得到基于官方母版的可编辑 `.pptx`，无需写代码或手调坐标；文字、形状、表格可编辑，截图仍是图片；检查溢出、遮挡、字体。共用布局可由 AI 推荐、用户指定；材料需重组时先确认逐页结论、布局及缺失素材。母版及现有资产不动；本轮不实现完整生成器。公共仓库新增材料只能使用通用或全模拟内容。[R1]

### 仓库已有契约（用于能力核查，不把旧规则全部升级为决策）

固定基准 `5f8f4ce0b3a4f1ca7dc52527e0e865a0b08add7a` 的 `skills/milwaukee-ppt/SKILL.md` §5.0 要求标题使用模板已有占位框，母版 banner/logo/footer 不重画。给定尺寸约 **13.333 × 7.5 英寸**；正文 layout 0 的 idx 为 **0/10**，封面 layout 1 为 **0/1**，layout 2 另有正文 OBJECT idx **1**。这里的数字仅为公开模板结构，不是业务数据。[R2]

`references/layout-patterns.md` 是案例参考，不是程序化 layout schema；旧文件对自由设计与部分月报规则的表述不能代替 map 的新方向。**自动选择 layout 的算法、具体 schema、文字容量/拆页阈值、异常输入处理、字体与 SVG 政策、平台验收范围都尚待人决定。** 本研究不制定它们，也不要求使用者编程。[R1–R3]

## 3. 三条路线的能力比较

| 维度 | A：python-pptx 加载模板 | B：PptxGenJS 原生生成 | C：OOXML 定点填充 / 重建 |
| --- | --- | --- | --- |
| 读取已有 `.pptx` | `Presentation(existing.pptx)` 官方支持 | v4.0.1 没有原生模板读取入口 | 直接读 OPC/ZIP parts；SDK 提供低层修改能力 |
| 公司 master/layout/theme | 以原文件为基础保留并引用；需做差异与视觉检查 | 自己定义新 layout、生成新 master/theme，不是保留任意旧模板 | 定点方案可保留未改 parts；重建方案必须重新实现原有结构 |
| 已有标题 placeholder | 可以按 idx 填写，保留继承关系 | 可以定义自己的 named placeholders；不是读取已有 idx 契约 | 保留 `p:ph` 与关系，修改指定 `a:t` 等内容 |
| 封面 | 从公司封面 layout 新建；不是照搬库默认 layout 0 | 需要重建封面 layout/素材/继承 | 定点改现有封面或正确新建其关联 slide |
| 原生文字/shape/table | 支持常见对象与单元格文字 | 支持 `addText/addShape/addTable` | 标准有对应元素；需自行正确构造/修改 |
| 图片 | 原生 picture 对象；图片像素内容不会变成文字/表格 | 同左；SVG 的 Node preview 有额外风险 | 图片 part、`p:pic`、relationship；SVG 还涉及扩展与 fallback |
| 跨平台生成 | Python 与依赖；生成不要求安装 PowerPoint | Node 与依赖，或 browser；生成不要求 PowerPoint | ZIP/XML 工具链，或 .NET SDK；生成不要求 PowerPoint |
| 核心代价 | 有支持边界，不是完整 PowerPoint 对象模型/渲染器 | 若“沿用原模板”是硬要求，单独使用不满足 | 最多控制、最多格式工程；不是自动排版库 |

依据：A [P1–P8]；B [J1–J7]；C [O1–O3]。跨平台生成是 API/依赖层面的能力；本研究没有验证任何具体 Windows/macOS 安装组合。

### A. 模板加载 + 已有 placeholder

1. **必须真的打开公司 `.pptx`。** `Presentation()` 无参数使用库自带模板，不会自动发现公司模板。真正的 `.potx` 与“去掉 slide 的 `.pptx` 模板”也不应混称；本票讨论现有 `.pptx`。[P1]
2. **layout index 是模板约定，不是通用语义。** 官方示例的默认 layout 0 为封面，不代表本模板正文 layout 0 也能照抄。`Slides.add_slide()` 创建 slide、关联给定 layout，并克隆可用 placeholders；它不是复制现有某一页的全部内容。[P2, P5, R2]
3. **idx 是键，不是序号。** `placeholders[10]` 可以有效，即使总数远小于 11；缺失键会报错。slide placeholder 通过相同 idx 向 layout 继承，layout 再按 type 向 master 继承。直接设置位置、字号等会覆盖继承。因此“使用原 placeholder”仍要避免无意覆盖格式。[P2–P3]
4. **替换文本有格式粒度风险。** `shape.text` / `text_frame.text` 会重建文本内容，不能保证保留原来的各 run 格式、链接、字段；`run.text` 更适合保留某个 run 的属性。空 placeholder 依赖 layout 的样式与已有 slide 上的多段富文本不是一回事。封面副标题、混合中英文、已有页定点填充须区别处理。[P4, P6]
5. **OBJECT placeholder 不等于 TABLE/PICTURE 专用 placeholder。** PowerPoint UI 的 content placeholder 能插入多类内容；但 v1.0.2 的 shape factory 只为 CHART/PICTURE/TABLE 分派专用插入类，OBJECT 落入普通 `SlidePlaceholder`。不能假定 layout 2 的 OBJECT idx 1 有 `insert_table()` 或 `insert_picture()`。若需要表格/图片，可在允许的正文区域添加原生对象；这不会自动获得富内容 placeholder 的全部继承语义。[P2–P3, P9, R2]
6. **母版装饰与动态页脚要分开。** banner/logo 作为已有 master/layout 的图形可沿继承链保留；新 slide 的 date/footer/slide-number latent placeholders 不会被上述克隆逻辑自动复制。页脚若依赖动态字段、显示标志而非静态母版图形，需额外核查，不能把“保留母版”推导成“每页动态页码必然正确”。[P5, P9, O1]
7. 官方称未支持的既有内容可以随加载/保存留下；这支持“小变化面”的策略，**不是对任意第三方扩展、签名、复杂媒体或每个渲染器的逐字节保真保证**。保存可能重序列化 XML；不能用整个 ZIP 文件 hash 判断是否保持母版，需要检查解压后的相关 parts、关系与可见结果。[P1, O1]

### B. PptxGenJS 的 master 是新建能力，不是模板导入能力

`defineSlideMaster()` 接收 `title/background/objects/...`，官方说明它导出为可在 PowerPoint Slide Master 视图修改的 first-class layouts；named placeholder 可以绑定新增文字。这个能力是真正可编辑的，不应因为“不读公司模板”就说它只会生成图片。[J1, J3]

但 v4.0.1 `PptxGenJS` 构造函数没有输入文件参数，初始化自己的 slideLayouts/master；`exportPresentation()` 创建 `new JSZip()` 并生成自己的 `theme1.xml`、`slideMaster1.xml`、layouts 和 relationships。**在本次核查版本中，原生 API 不提供任意旧 PPTX 导入/round-trip。** 若另外拼接外部母版、复制 XML 或引入第三方模板解析器，已经是额外的 OOXML 工程，不应宣传成 PptxGenJS 原生能力。[J2]

若以后允许重建母版，可以用它创建原生 shape、text、table 与图片，维护新 cover/body layouts。但要核对主题字体、色彩映射、占位框、页码、背景、relationships；母版截图作背景虽然易保持外观，却丢失原有母版对象结构，也不满足“现有资产不动、沿用占位框”的当前契约。[J1–J3, O1, R2]

**HTML 边界：** 官方 HTML-to-PowerPoint 功能是把 HTML **table** 再建为 PPT table，支持部分单元格 CSS，有嵌套表格/词级格式限制；不是完整 HTML 页面或 CSS 布局的无损转换。HTML 预览视觉接近、全页 PNG 填入 PPT、PDF 页截图，都不能用来证明原生文字/形状/表格可编辑。[J8, O1]

### C. OOXML 定点填充与 OOXML 母版重写必须分开评估

**C1：定点填充既有 slide。** 只更新已定位 placeholder/shape/table cell 中的指定文本节点，不动原 master/layout/theme/media，变化面最小；未改 parts 的未压缩内容可以保持不变。适合已定稿的页或预制示例页，但字段定位、跨 run 文本、XML 转义、超长文本与异常模板仍需规则。不能对 XML 做无边界全局字符串替换，也不能更新母版标题来冒充每页的独立标题。[O1–O2, P4]

**C2：以原母版为基础新增/复制 slide。** 必须处理 presentation 的 slide list、slide ID、part 名称、各级 `.rels`、内容类型以及新增图片/图表所依赖的 parts；复制 slide XML 不会自动复制 notes、charts/workbooks、media 或修复引用。标准说明 slide/layout/master 是有交叉甚至循环引用的 package parts，不是单一 XML。[O1]

**C3：重写 master/layout 或把另一生成器的内容嫁接过去。** 可获得完全原生对象，但需重建继承、主题、背景、显示控制与扩展。复杂度远高于“改几个 `a:t`”，且一旦重建就不再享有 C1 未修改原 parts 的保真优势。Open XML SDK 官方明确定位为低层格式工具，要求格式知识，不提供高层生产力/排版抽象。[O1–O2]

SDK 的 `OpenXmlValidator` 可以按目标文件版本验证 element/part/package；它检查结构而不是字体、遮挡、换行或编辑体验。使用 SVG 等扩展还应与目标 Office 版本匹配。**schema 通过不等于 PowerPoint 正常打开且无修复提示，更不等于视觉 QA 通过。** [O3, S1]

## 4. 可编辑性要按对象验收

| 对象 | 符合本票的含义 | 不应混淆的情况 |
| --- | --- | --- |
| 标题/正文 | 原生 `p:sp/p:txBody` 的段落与 runs，可改字和格式 | 截图里的字、整页图片、转曲路径不是文字编辑 |
| shape/线/卡片 | 独立原生 shape/connector，可改位置、颜色、文字 | 一张包含多张卡片的 SVG/PNG 不等于多张独立 shape |
| table | `p:graphicFrame` 内原生 `a:tbl`，可编辑 cell、行列 | 表格截图或一堆看起来像表格的图片不是原生 table |
| 截图/照片 | 原生 picture，可移动、缩放、裁切/替换图片 | 图片内部的业务字段不会变成可编辑 cell 或文字 |
| SVG 图标 | 图片/graphic 级别编辑与缩放；现代 Office 另有 Convert to Shape 能力 | 不承诺 SVG 自动成为可分别编辑的圆弧和文字，也不承诺旧版本支持 |
| 母版装饰 | 留在 master/layout 中统一继承；可在母版视图处理 | 普通 slide 视图无法直接选中母版对象不代表整页不可编辑；本任务本就不应改装饰 |

对象结构依据 [O1, P2–P4, P9, J3, J5]；Office 对 SVG 的缩放、填色和转换形状依据 [S2]。这是一套验收解释，**不是本研究新增已决 editable schema**。核心文字、形状与表格原生化不妨碍截图或单个图标保留为图片；不得用全页栅格化绕过核心要求。

## 5. 字体：Windows/macOS 的风险与选项

**事实：** 字体名称不是字体文件。python-pptx `Font.name` 只在找到匹配字体时起作用，v1.0.2 setter 修改的是 `a:latin`；中日韩字体仍可能由 `a:ea`、主题的 script 字体、语言与应用 fallback 决定。PptxGenJS v4.0.1 的直接 `fontFace` 会写 latin/ea/cs 名称，其主题生成又有自己的 script 映射。因此只写一个英文 `fontFace`，不能证明中文在两平台字体一致。[P6, J5, O1]

Microsoft 官方说明字体缺失会替换，嵌入可避免部分替换；字体有 Non-embeddable / Preview-Print / Editable / Installable 等限制。只嵌入已使用字符限制后续改字，协作编辑应考虑完整字符集。云字体依赖 Office 用户条件和网络，不能把“Microsoft 365 会下载”当作离线同事、LibreOffice 或其他渲染器的保证。[F1]

以下是**供后续决策的选项，不是用户已选政策**：

- **受控字体安装**：两平台及 QA 环境安装相同、授权允许的字体版本，明确中文/Latin、Regular/Bold 等映射。字体许可、文件分发与企业安装权限仍需确认；不能暗中复制系统字体到公共 skill。
- **Office 嵌入**：通过目标 PowerPoint 的受支持设置嵌入可编辑字体；先核查许可、字符子集和目标版本。官方文档的字体嵌入不等于 python-pptx/PptxGenJS 普通 font 属性会嵌入字体。本研究未确认两库有满足此目标的高层嵌入 API，不能承诺自动完成。
- **允许替换并记录**：如果决定容忍 fallback，必须在换字体后重新查长标题、表格、数字/单位与中文换行；不能仅依赖“相同字号”。

**共同风险：** 模板继承可保留“字体选择规则”，但不能确保收件机上有对应字体。文本转图片或转轮廓只能保外观，会削弱/取消文字编辑能力，不能用来解决核心正文的 editable 要求。[P3, P6, F1, O1]

## 6. SVG 图标与栅格 fallback

- **Office 能力**：Microsoft 365 文档明确 Windows/Mac 支持插入/编辑 SVG；SDK 的 `asvg:svgBlip` API 标注 Office 2019+。这是不同证据范围，不能据此推断所有 Office 2016 build、所有第三方软件都一致。[S1–S2]
- **python-pptx v1.0.2 新插图**：图片解析经 Pillow，支持格式映射没有 SVG；普通 `add_picture(svg)` 不是已支持的新插入路径。已有 PPTX 中的 SVG part 可随包保留与“库能新插入 SVG”是不同问题；前者仍须对实际文件验证，不能保证访问所有 image 属性都成功。[P1, P10]
- **PptxGenJS v4.0.1**：图像构造给 SVG 分配 PNG 与 SVG 两个关系，生成 `asvg:svgBlip` 扩展。这是 SVG 本体支持的源码证据。[J4–J5]
- **特别风险：Node 的 PNG preview 不可盲信。** `gen-media.ts` L136–152 的已有数据 preview 路径在 Node 下置为 `IMG_BROKEN`；本地文件读取路径 L56–64 又只编码原文件字节，没有 SVG→PNG 渲染。browser 路径调用 DOM `Image`/canvas 做预览。因此不能把“提供 SVG 路径/base64”推导成“Node 已生成有效同图 PNG fallback”。这是源码观察，未运行实验，实际输出和应用显示仍需验证。[J6]
- **OOXML 双资源方案**：保留 SVG part 并附有效 PNG fallback 是可构造的包结构方向，但要正确写关系、扩展、图片内容类型，并选定目标版本；不是只把 SVG 文件后缀改成 PNG。[J4–J6, S1, O1]

供决策的低风险选项：只对小图标使用预先正确栅格化的 PNG（或今后使用 SVG+有效 PNG 双资源），正文仍是原生文字/shape/table。图标栅格化损失向量缩放与部件编辑，但不等于全页栅格化；是否接受由人决定。若图标中心字母仍为 SVG text，SVG/PNG 生产环境本身也需正确字体；本轮不修改既有图标资产。转换器与额外 native/browser 依赖必须纳入首次安装和 QA，不假定宿主已提供。

## 7. 生成与渲染 QA：两层能力，至少三种验证

python-pptx/PptxGenJS/OOXML 生成路径写文件结构，不是目标 PowerPoint 的版面渲染器。依据其创建/保存/导出 API 与源码，本研究未找到等价的 PowerPoint 视觉渲染能力；不能声称写入成功已经验收。[P1, J2–J3, O2]

建议后续规格明确以下三层，而非本轮实现它们：

1. **结构与母版契约检查**：尺寸、每页 layout 关系、标题 idx、原生文字/表格/图片类别；比较未授权修改的 master/layout/theme/media 的解压内容或结构差异；检查缺失关系、未替换模拟字段。若采用 XML 重写，可另加 schema validator。母版 shape 不出现在 slide shape 列表中，不能误判为丢 logo。[O1, O3, P3]
2. **实际渲染检查**：目标 `.pptx` 经渲染工具生成 PDF/图片，逐页查溢出、遮挡、页脚、安全区、换行、SVG 及字体。QA 图片只是证据，不替代 editable `.pptx`。LibreOffice 官方提供 `--headless`、`--convert-to`、`--outdir`；需要安装 LibreOffice、字体，并给 user profile 写权限，隔离 profile 是并发/自动化需考虑的环境问题。[Q1]
3. **目标 PowerPoint 打开与编辑 smoke test**：Windows/macOS 的约定版本无修复提示；改一次标题、shape、table cell、替换图片，再保存重开。PowerPoint Windows 对象模型有 `Slide.Export`（文档涉及 Windows 注册表 graphics filter）和 PDF/XPS `ExportAsFixedFormat`；Mac 官方支持 UI 导出 PNG/JPEG/PDF。**不能把 Windows COM/VBA 导出脚本直接宣称为 macOS 通用 headless 方案。** 本研究未验证 Mac 自动化、Office 无人值守运行或 server 环境。[Q2–Q4]

**LibreOffice 是可用的自动渲染检查工具，不是 PowerPoint 像素等价证明。** 使用不同应用渲染时，本研究没有同图对照实验，无法提供差异上限；面向 PowerPoint 收件者，建议至少保留目标 PowerPoint 的跨平台抽检。若机器缺渲染器，应报告“结构已查、视觉未验收”，不静默降级成“QA 已通过”。字体或 SVG fallback 出问题时，要检查 editable PPT 本体，不能只看 PDF 是否恰好正常。[F1, J6, Q1–Q4]

## 8. Claude Code / OpenCode skill 与首次安装

### skill 不是运行时依赖安装包

Agent Skills 规格允许 `scripts/ references/ assets/` 与 `compatibility`，但脚本支持的语言依赖宿主。Claude Code 文档将 skill 定义为按需加载的指令与支持文件；OpenCode V2 也先载入 Markdown，再由 agent 读取文件/调用工具。**安装一份 SKILL.md 不代表安装了 Python、Node、字体、LibreOffice/PowerPoint 或转换器。** `compatibility` 是描述，不能当作强制依赖验证机制。[H1–H3]

| 层级 | 可确认的要求/约束 | 本轮未承诺的东西 |
| --- | --- | --- |
| 宿主 | Claude Code 有 Windows/macOS 官方安装；OpenCode V2 提供两平台 CLI/desktop binaries | 不保证某企业账号权限/网络策略/每种 shell 配置 |
| skill 发现 | Claude Code 常用 `.claude/skills`；OpenCode V2 支持 `.opencode/skills` 及 `.claude/.agents` 兼容源 | 仓库裸 `skills/` 不等于所有宿主自动发现；需相应安装或配置 |
| 文件访问 | 通过已加载 skill 的 base directory/相对资源找模板，不依赖用户当前目录 | 不硬编码个人绝对路径，不依赖另一仓库的真实 PPT |
| 执行权限 | shell、文件、外部目录与网络受宿主权限控制；两宿主规则语义并不完全相同 | 不用跳过权限模式掩盖首次安装；不假定 `allowed-tools` 跨宿主等效 |
| PPT 生成 | A 需要 Python 与 python-pptx；B 需要 Node 与 npm 包（browser 为另一运行环境）；C 需要选定 XML 工具链/SDK | 宿主自带 native binary 不代表 Node/Python 可供脚本使用 |
| 视觉验收 | 独立渲染器、字体、输出目录/profile 权限；PowerPoint 许可与可用版本另确认 | 不保证仅装 skill 就能完成全自动跨平台 QA |

宿主依据 [H1–H6]；依赖依据 [P7–P8, J7, O2, Q1]。OpenCode **只引用 V2 安装说明**：官方说明 Windows package managers 不受支持，同时提供 standalone Windows CLI/desktop；不要搬用 V1 的安装命令/配置。Claude Code 原生安装不应被误认为它提供供生成器用的 Node/Python。[H4–H5]

### 供将来实现/分发规格参考的首次运行检查（不是本轮新增脚本）

1. 识别 OS/架构/实际 shell 与宿主版本，读取安装的 skill revision、模板相对路径/版本；避免把一个宿主的动态 shell 注入语法当作通用功能。[H1–H5]
2. 检测生成路线的运行时与锁定依赖是否可用。python-pptx v1.0.2 要求 **Python ≥3.8**，依赖 Pillow、lxml、XlsxWriter、typing_extensions；这只是最低声明，不推荐团队使用已停止维护的 Python。PptxGenJS v4.0.1 manifest 有 jszip/image-size 等依赖且没有 `engines` 下限声明；不能从 `@types/node` 版本反推出运行时最低 Node 版本，应在今后的发布环境中选定并测试受维护版本。[P7, J7]
3. 展示将安装的组件、版本、网络访问与写入位置，获得授权后再做项目/skill 隔离安装；例如 A 可用独立 Python 环境，B 可用锁文件。首次包获取可能需网络/企业镜像；离线或无权限时返回可操作的缺失项。这里是分发建议，不是宿主官方承诺的自动流程。[H6, P8, J7]
4. 分别检查字体、SVG 转换能力、渲染器和目标 PowerPoint。不能把“可生成”与“可渲染 QA”合并成一个成功标记。[F1, J6, Q1–Q4]
5. 将脚本、资源解析、错误解释封装给 skill/维护者，使用者仅提供内容与确认提示，不让同事编程或手动调坐标。[R1, H1–H3]

公共分发只讨论通用结构、模拟数据和依赖；字体许可与公司资产访问方式需另行确认。本轮不复制、再上传模板或任何私人业务资产，不做安装器、不测试第三方账号，不决定内部发布方式。

## 9. 推荐与未决事项

**研究者建议（待人决定）：**

- 对“沿用现有母版与标题占位框”的当前目标，**优先评估 A**：从现有 `.pptx` 加载、填已有 placeholder、在正文区用原生对象。理由是能力与现有契约直接吻合，且少做母版重写，不是因为 Python 天生渲染更准。[P1–P5, R2]
- **C1 可作局部格式保留手段**，仅在明确的既有富文本/对象填充场景评估；把扩大到 C2/C3 的复杂性作为显式决策，不默认选择全套 OOXML 生成。[O1–O3, P4]
- **B 不能单独满足任意原模板读取保留这一点**。只有将来允许重建母版或明确选择额外模板移植层时再评估；原生可编辑能力不抵消导入能力缺口。[J1–J3]
- 字体与 SVG 风险必须进入首轮模拟原型验收；不要通过全页 PNG 或正文转曲避开问题。缺渲染器如实标注未验收。[F1, J6, Q1–Q4]

待主助手/用户决定：最终路线；最小 OS/Office 版本组合；字体授权/分发/嵌入政策；图标需向量还是允许 PNG；自动选版边界与具体 layout schema；结构、视觉、人工编辑验收各自是否为发布门槛；首次安装授权、企业网络与依赖锁定方式。**本研究没有替用户选择任何一项。**

下一步若获授权做有限验证，应仅用全合成母版/材料测试 cover/body 继承、标题 idx、多 run 保留、OBJECT 与 TABLE 区别、原生表格编辑、中文字体、SVG+fallback，再在约定 Windows/macOS PowerPoint 与 LibreOffice 上对照。合成测试能证明选定机制，不足以代表未知公司模板；公司现有模板的内部最终验收仍需由获准环境完成。

## 10. Primary-source 索引

以下关键来源均在研究日读取；源码链接固定到 tag（SDK README 为研究日 `main`，不把其滚动内容当作 3.0.1 的固定实现）。仓库引用固定到本票基准；在线 docs 会变化，升级版本应重查。

- **R1**：[公司母版 PPT skill：共用布局与项目汇报规则规划](https://github.com/WangYiTao0/myskills/issues/1)的 Destination/Notes；[公司母版上的可编辑生成与跨平台方案](https://github.com/WangYiTao0/myskills/issues/5)。是本任务第一方需求，不是第三方库技术证明。
- **R2**：[仓库 `SKILL.md` §5.0](https://github.com/WangYiTao0/myskills/blob/5f8f4ce0b3a4f1ca7dc52527e0e865a0b08add7a/skills/milwaukee-ppt/SKILL.md#50-模板占位框契约生成-pptx-时必须遵守)，约 L168–196。
- **R3**：[仓库 `references/layout-patterns.md`](https://github.com/WangYiTao0/myskills/blob/5f8f4ce0b3a4f1ca7dc52527e0e865a0b08add7a/skills/milwaukee-ppt/references/layout-patterns.md)，使用定位与选版速查。
- **P1**：[python-pptx Working with Presentations](https://python-pptx.readthedocs.io/en/latest/user/presentations.html)，Opening/REALLY opening；已有文件与默认模板、保留未操作内容。
- **P2**：[Working with placeholders](https://python-pptx.readthedocs.io/en/latest/user/placeholders-using.html)，idx 字典语义、专用插入类型及继承。
- **P3**：[Understanding placeholders](https://python-pptx.readthedocs.io/en/latest/user/placeholders-understanding.html)，各类 placeholder 与 slide/layout/master 继承。
- **P4**：[Working with text](https://python-pptx.readthedocs.io/en/latest/user/text.html)，text frame / paragraph / run 格式层级和 `.text` shortcut。
- **P5**：[v1.0.2 `src/pptx/slide.py`](https://raw.githubusercontent.com/scanny/python-pptx/v1.0.2/src/pptx/slide.py)，`Slides.add_slide` L268–273；`SlideLayout.iter_cloneable_placeholders` L304–316。
- **P6**：[v1.0.2 `src/pptx/text/text.py`](https://raw.githubusercontent.com/scanny/python-pptx/v1.0.2/src/pptx/text/text.py)，`TextFrame.text` L153–178；`Font.name` L350–369；`_Paragraph.text` L592–616；`_Run.text` L664–681。
- **P7**：[v1.0.2 `pyproject.toml`](https://raw.githubusercontent.com/scanny/python-pptx/v1.0.2/pyproject.toml)，`requires-python` 与 `dependencies`。
- **P8**：[Installing](https://python-pptx.readthedocs.io/en/latest/user/install.html)，pip 安装方法；其旧 Python 版本陈述不作为 v1.0.2 要求。
- **P9**：[v1.0.2 `src/pptx/shapes/shapetree.py`](https://raw.githubusercontent.com/scanny/python-pptx/v1.0.2/src/pptx/shapes/shapetree.py)，`add_picture` L353 起；`add_table` L589 起；`clone_layout_placeholders` L602–609；placeholder factory L845–860。
- **P10**：[v1.0.2 `src/pptx/parts/image.py`](https://raw.githubusercontent.com/scanny/python-pptx/v1.0.2/src/pptx/parts/image.py)，`Image.ext` 的格式映射 L220–238；Pillow 解析 L264–275。
- **J1**：[PptxGenJS Masters and Placeholders](https://gitbrent.github.io/PptxGenJS/docs/masters/)，master layout 对象定义与 named placeholders。
- **J2**：[v4.0.1 `src/pptxgen.ts`](https://raw.githubusercontent.com/gitbrent/PptxGenJS/v4.0.1/src/pptxgen.ts)，`constructor()`、`exportPresentation()`、`defineSlideMaster()`；新 package/master/theme 导出与无模板输入构造函数。
- **J3**：[v4.0.1 `src/slide.ts`](https://raw.githubusercontent.com/gitbrent/PptxGenJS/v4.0.1/src/slide.ts)，`addImage` L181、`addShape` L213、`addTable` L229、`addText` L241。
- **J4**：[v4.0.1 `src/gen-objects.ts`](https://raw.githubusercontent.com/gitbrent/PptxGenJS/v4.0.1/src/gen-objects.ts)，SVG 双 image relationships L464 起。
- **J5**：[v4.0.1 `src/gen-xml.ts`](https://raw.githubusercontent.com/gitbrent/PptxGenJS/v4.0.1/src/gen-xml.ts)，`a:tbl` L182、`p:sp` L409、`p:pic` L557、`asvg:svgBlip` L584；fontFace L996–999；`makeXmlTheme` L1767 起。
- **J6**：[v4.0.1 `src/gen-media.ts`](https://raw.githubusercontent.com/gitbrent/PptxGenJS/v4.0.1/src/gen-media.ts)，Node 读取 L56–64、browser SVG preview L110–115、Node preview L136–152、canvas L162 起；[官方 Images 文档](https://gitbrent.github.io/PptxGenJS/docs/api-images/)的 SVG 版本条件。
- **J7**：[v4.0.1 `package.json`](https://raw.githubusercontent.com/gitbrent/PptxGenJS/v4.0.1/package.json)，runtime dependencies 与无 engines 声明；[Installation](https://gitbrent.github.io/PptxGenJS/docs/installation/)的 npm/browser 安装说明。
- **J8**：[HTML to PowerPoint](https://gitbrent.github.io/PptxGenJS/docs/html-to-powerpoint/)，HTML table 转换范围与 CSS/嵌套限制；API 对照以 J2 源码为准。
- **O1**：[Microsoft Learn：Structure of a PresentationML document](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document)，parts、relations、master/layout/theme、原生对象与唯一 slide ID；本研究依据此页对 ISO/IEC 29500 的引用，没有声称通读完整 ISO 标准。
- **O2**：[Open XML SDK 官方 README](https://raw.githubusercontent.com/dotnet/Open-XML-SDK/main/README.md)，low-level API、格式知识前提与不提供高层抽象的定位。
- **O3**：[OpenXmlValidator 3.0.1 API](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.validation.openxmlvalidator?view=openxml-3.0.1)，目标 FileFormatVersions 与 element/part/package 验证范围。
- **F1**：[Microsoft Support：Benefits of embedding custom fonts](https://support.microsoft.com/en-us/office/benefits-of-embedding-custom-fonts-cb3982aa-ea76-4323-b008-86670f222dbc)，字体替换、云字体、嵌入授权级别、完整字符/子集与编辑限制；未从该页证明特定 Mac build 的自动嵌入能力。
- **S1**：[SVGBlip 3.0.1 API](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.office2019.drawing.svg.svgblip?view=openxml-3.0.1)，Office 2019+ 与 `asvg:svgBlip/r:embed`。
- **S2**：[Microsoft Support：Edit SVG images in Microsoft 365](https://support.microsoft.com/en-us/office/edit-svg-images-in-microsoft-365-69f29d39-194a-4072-8c35-dbe5e7ea528c)，Windows/Mac SVG 能力、graphic 级格式与 Convert to Shape；不外推自动转换或各平台全部功能等效。
- **Q1**：[LibreOffice：Starting with Parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html)，页面自标 26.8 Help；headless/convert-to/outdir 与 user profile 写权限；不作与 PowerPoint 渲染等价的证据。
- **Q2**：[PowerPoint `Slide.Export`](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.export)，graphics filter 与像素参数，文档有 Windows registry 前提。
- **Q3**：[PowerPoint `Presentation.ExportAsFixedFormat`](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.exportasfixedformat)，静态 PDF/XPS 导出与字体 bitmap/substitution 说明。
- **Q4**：[PowerPoint for Mac Export](https://support.microsoft.com/en-us/office/export-your-powerpoint-for-mac-presentation-as-a-different-file-format-0547523c-56c4-4799-b5f7-6257907c09ee)，UI 导出逐页 PNG/JPEG/PDF；未证实 headless 自动化。
- **H1**：[Agent Skills Specification](https://agentskills.io/specification)，目录、compatibility、支持脚本语言依赖宿主与相对路径。
- **H2**：[Claude Code Skills](https://code.claude.com/docs/en/skills)，skill/支持文件、发现位置、compatibility 与宿主扩展差别。
- **H3**：[OpenCode V2 Skills](https://opencode.ai/v2/docs/skills)，base directory、发现/显式 skills sources、加载与权限；不使用 V1 文档。
- **H4**：[Claude Code Setup](https://code.claude.com/docs/en/setup)，Windows/macOS、native install、shell/WSL 与安装方式；不表示附送生成/渲染依赖。
- **H5**：[OpenCode V2 Intro/Install](https://opencode.ai/v2/docs/)，两平台 binaries、Windows package-manager 限制及 native 包安装行为。
- **H6**：[OpenCode V2 Permissions](https://opencode.ai/v2/docs/permissions)；[Claude Code Permissions](https://code.claude.com/docs/en/permissions)，tool/shell/file/network 权限与不同规则语义。
