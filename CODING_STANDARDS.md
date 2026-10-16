# Coding Standards

只收需要判断的规则；能机械检查的做成测试。目前规则都针对 `skills/milwaukee-ppt`。

## 测试

- **测试只看外部行为**：md → pptx（读生成的形状名、位置、字号）、md + pptx → 审核 / inspect 输出、文档和生成结果一致；期望值取规格写的数（references、品牌规范），不从 `scripts/` 里抄常量或调内部函数。
  理由：从实现抄期望值，实现改错了测试跟着错，测试就失去了守门作用。
- **月报路径逐字节不变由测试守**（`test_generate.py` 的 `MONTHLY_SHA` / 月报全版式基线），改月报模式的输出要先征得用户同意，再更新基线。
  理由：月报是已在用的定稿版式，任何字节变化都可能是用户没要的视觉改动。

## 版式代码（`scripts/layouts/`）

- **月报 / 通用·项目模式只按 `ctx.lead` 分支**，两种写法二选一：只差字号、颜色等数值时，定义 `MONTHLY` / `GENERAL` 两个 `SimpleNamespace`，在 `render` 开头取一次 `st = GENERAL if ctx.lead else MONTHLY`（见 `stats.py`）；画法不同（形状不一样）时，`render` 第一行 `if ctx.lead: return _render_<画法>(prs, page, ctx)`，下面原样留月报路径（见 `team.py`、`process.py`）。
  理由：分支集中在一处，改通用模式时一眼看出没碰月报路径；月报路径中间散落的 `if ctx.lead` 是待收拢的旧写法，新代码照上面两种写。
- **多个版式共用的画法和换算放 `common.py`**：居中文本框、黑底圆写白字、行高换算（字号 × 1.25）这类两个以上版式要用的，写进 common 由各版式调用。
  理由：同一条规格多处实现会各自漂移；现有重复（如 `process._centered_text` / `team._centered`、各版式的 `_line_h` / `_height_in`）留待后续收拢，收拢时以月报逐字节测试兜底。

机械检查：测试不从 `layouts` 取内部常量由 `skills/milwaukee-ppt/tests/test_test_imports.py` 守，规则写在该文件开头。
