# M365 Copilot 技能打包与发布

把本仓库的 skill 上传到 M365 Copilot 声明式 agent（Agent Builder，上传 skill .zip）前读本文件。当前要上线的是 ppt-grill → milwaukee-ppt → ppt-review 三段流程。

## 平台限制

来源：[Custom skills in declarative agents (preview)](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-skills)，页面 ms.date 2026-09-03，2026-10-16 查阅。预览功能，限制可能变；上传失败时先回来源页核对。

| 项 | 限制（Agent Builder） | 本仓库怎么守 |
| --- | --- | --- |
| SKILL.md 指令 | < 20,000 字符；YAML frontmatter 要有 name、description | 检查脚本按整个文件的 Python 字符数算（含 frontmatter，偏保守）。milwaukee-ppt 目标 ≤ 18,000 留余量，部分分支才用的细则放 `references/` |
| 每个 agent 的技能数 | ≤ 8 | 三段流程 3 个 + 探针 1 个 |
| 上传包 | 单个技能一个 `.zip`，≤ 50 MB；不能逐个文件上传 | 检查脚本 |
| 单文件 | ≤ 25 MB | 检查脚本 |
| 文件数 | 所有技能合计 ≤ 350 | 检查脚本按一次传入的全部技能合计 |
| 目录深度 | ≤ 3 | 见下「深度计法」 |
| 文件类型 | 资源：`.json .xml .yaml .yml .ini .config .utf8 .docx .doc .docm .pdf .txt .rtf .md .ppt .pptx .ppsm .xlsx .xls .xlsm .csv .tsv .html .htm .png .jpg .jpeg .gif .bmp .log`；脚本：`.py .js .mjs .cjs .ts .mts .sh .bash` | 检查脚本按此白名单；**`.svg`、无扩展名文件都不行** |
| 沙箱 | 无网络、不能装包；只能用沙箱预装的包，"未确认可用就别依赖" | python-pptx / lxml / Pillow 是否预装**未确认**，明天用探针查 |
| 其他 | 技能和 embedded files 不能同时用；需 Frontier 预览；启用 Information Barriers 的租户不可用；不能跨 agent 复用 | agent 里不要再挂知识文件 |

**深度计法**（官方没写清楚怎么数，按保守口径）：zip 里的 skill 目录算第 1 层，文件的深度 = 它所在目录的层数。`milwaukee-ppt/SKILL.md` 深度 1，`milwaukee-ppt/scripts/layouts/stats.py` 深度 3（上限），`milwaukee-ppt/examples/demo/img/x.png` 深度 4（违规）。如果平台实际按「zip 根 = 第 1 层」或只数子目录，这个口径只会更严，不会放过违规。

## 打包命令

```bash
python3 tools/m365_package.py skills/ppt-grill skills/milwaukee-ppt skills/ppt-review tools/m365-probe
```

- 每个技能输出 `dist/<skill>.zip`（`dist/` 已在 `.gitignore`），zip 根下是 `<skill>/SKILL.md`；`-o <目录>` 改输出位置；`--flat` 让 zip 根下直接是 `SKILL.md`（上传报「找不到 SKILL.md」时换这个试）。
- 全过打印每个 zip 的文件数与大小、退出码 0；有违规逐条打印 `[skill] 问题`、删掉本次产出的 zip、退出码 1。合计文件数只算同一次命令里传入的技能，所以**要放进同一个 agent 的技能一次传齐**。
- 不进 zip 的开发文件：任意层级的 `tests/`、`prototypes/`、`__pycache__/`，以 `.` 开头的文件和目录，`*.pyc` / `*.pyo`、`Thumbs.db`、`~$*`。技能目录下可放 `.m365ignore`（每行一个相对技能目录的 glob，`/` 结尾表示整个目录）再排除。
- milwaukee-ppt 的 `.m365ignore` 排除了 `assets/pdca/*.svg`（生成器只用同名 PNG）和 `examples/demo/img/`、`examples/demo/make_images.py`（第 4 层，超深度）。包里的 `examples/demo/deck.md` 只作写法示例：它引用的配图不在包里，**不要在 M365 里直接用它生成**。
- 脚本测试：`python3 tools/test_m365_package.py`。

当前结果（2026-10-16）：ppt-grill 1 个文件、milwaukee-ppt 33 个文件、ppt-review 1 个文件、m365-probe 3 个文件，合计 38 个，全部通过。

## 跨技能引用的风险

ppt-review、ppt-grill 的 SKILL.md 用 `<milwaukee-ppt>` 指 milwaukee-ppt 的目录（本仓库里是 `skills/milwaukee-ppt`），例如 `python3 <milwaukee-ppt>/scripts/review_deck.py`。M365 里每个技能是独立上传的目录，平台没有文档说明技能之间能否互相看到文件、目录在哪：

- 如果沙箱把同一 agent 的技能放在同一父目录下，`<milwaukee-ppt>` 可按「本技能目录的同级 `milwaukee-ppt`」找到，现有写法可用。
- 如果各技能互相隔离，ppt-review 调不到审核脚本；能用的退路是 ppt-review 只做核对清单那一半、审核脚本改由 milwaukee-ppt 一侧调用，或把 ppt-review 的流程并进 milwaukee-ppt。**这需要改行为，明天验证后再定，本次不改。**

## 明天的验证清单

先探针、后流程。每步记下结果（截图或原样输出），失败就停在那一步。

1. **打包**：跑上面的打包命令，确认退出码 0，`dist/` 下有 4 个 zip。
2. **只上传探针**：新建一个测试 agent，只加 `m365-probe.zip`，对它说「跑探针」。核对输出：
   - [ ] `python:` 版本（本机测试用 3.14；python-pptx 1.0 要求 ≥ 3.8，版本过低要先查兼容性）
   - [ ] `import.pptx` / `import.lxml` / `import.PIL` 是否 OK（`typing_extensions`、`xlsxwriter` 一并看）
   - [ ] `read_sample.zipfile` / `read_sample.pptx` OK = 能读包内 .pptx（对应 milwaukee-ppt 读 `assets/MS_Template.pptx`）
   - [ ] `write_output` OK 且聊天里能**下载**到 `m365-probe-output.pptx`
   - [ ] `skill_dir`、`parent_dir_entries`：技能在沙箱里的路径，同级能不能看到别的技能（决定上面的跨技能引用）
   - [ ] `installed_packages`：完整预装包清单，存档
   - 上传失败：看报错；提示结构问题时用 `--flat` 重打再传。
3. **加三段流程**：把 `ppt-grill.zip`、`milwaukee-ppt.zip`、`ppt-review.zip` 加进同一个 agent（可留着探针，共 4 个 ≤ 8）。agent 不挂 embedded files。
4. **ppt-grill**：用一份虚构资料走打磨访谈，确认能产出定稿简报。
5. **milwaukee-ppt**：按简报写 md、跑 `scripts/generate_ppt.py`，确认生成 pptx 且能下载、PowerPoint 打开正常（品牌 banner、logo、PDCA 图标在）。
6. **ppt-review**：确认它能找到并运行 `<milwaukee-ppt>/scripts/review_deck.py`，输出 `[规则] …` 或 `REVIEW OK`；找不到时记下它尝试的路径。
7. 记录：哪些步骤要人提示才走对、`references/` 下的文件是否被按需读到（如项目汇报模式是否读了 `references/project-report.md`）。

## python-pptx 不可用时的备选

探针显示 `import.pptx` FAIL 时：

1. **随包携带 python-pptx（需确认 lxml 预装）**。python-pptx 本身是纯 Python，但依赖 lxml（C 扩展，无法随包带、必须预装）、`typing_extensions`（纯 Python，可带）、Pillow（只在插图片算尺寸时用，生成器没装时退化为等宽）、XlsxWriter（只在图表数据时用）。随包携带要过三道限制：
   - **深度**：python-pptx 包内最深是 `pptx/oxml/chart/*.py`，放在 `milwaukee-ppt/scripts/` 下就是第 5 层，只能放技能根下（`milwaukee-ppt/pptx/...` 仍是第 4 层，也超）。直接放目录过不了深度 3，需要另想办法，例如把包打成单个 zip 文件用 zipimport 加载——但 `.zip` 不在允许扩展名里，要验证改扩展名后平台是否放行、zipimport 是否认。
   - **扩展名**：包里有 `.emf`（OLE 图标）和 `py.typed`，不在白名单，要剔除（生成器不插 OLE 对象）。
   - **文件数**：约 110 个文件，加上现有 38 个仍在 350 以内。
2. lxml 也不可用：python-pptx 走不通，只能改写生成器（如用标准库 `zipfile` + 字符串直接写 OOXML），属于大改，先和用户确认。
3. 退而求其次：M365 里只跑 ppt-grill（纯指令，无脚本）和 milwaukee-ppt 的「写 md 文稿」部分，pptx 在本机生成与审核。
