"""机械检查：测试不碰版式层的内部常量，只看外部行为。

运行：python3 skills/milwaukee-ppt/tests/test_test_imports.py
规则（扫描 tests/*.py 的语法树）：
- 从 `layouts` 或 `layouts.<模块>` 取到的名字，全大写（如 MARK_SHAPE、DESC_PT、LINE_SPACING）
  或下划线开头的，算内部常量 / 内部实现，不准用；`from ... import` 和
  `team.MARK_SHAPE` 这类属性访问都算。
- 允许：公开函数和类（小写或驼峰、不以下划线开头，如 common.wrap_lines、Context），
  以及子模块本身（`from layouts import team`）。
- 例外：probe_layout.py 是测试专用版式，跑在生成器进程里，按版式模块的规矩用 common。
期望值写成规格里的数（文档 / 品牌规范给的），或从生成出的 pptx、审核输出里读，
不从实现里抄。
"""
import ast
import re
from pathlib import Path

from deckcheck import SKILL, check, finish

HERE = Path(__file__).resolve().parent
EXEMPT = {"probe_layout.py"}
SUBMODULES = {p.stem for p in (SKILL / "scripts" / "layouts").glob("*.py")}
_INTERNAL = re.compile(r"^(_.*|[A-Z][A-Z0-9_]*)$")


def _layouts_path(module):
    """module 是 layouts 或 layouts.<子模块> 时返回点分路径，否则 None。"""
    if module == "layouts" or (module or "").startswith("layouts."):
        return module
    return None


def violations(source):
    """返回 [(行号, 'layouts.x.NAME')]：源码里用到的版式层内部名字。"""
    tree = ast.parse(source)
    aliases = {}     # 本地名 → layouts 点分路径
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if _layouts_path(a.name):
                    if a.asname:
                        aliases[a.asname] = a.name
                    else:
                        aliases["layouts"] = "layouts"
        elif isinstance(node, ast.ImportFrom) and _layouts_path(node.module):
            for a in node.names:
                if node.module == "layouts" and a.name in SUBMODULES:
                    aliases[a.asname or a.name] = f"layouts.{a.name}"
                elif _INTERNAL.match(a.name):
                    found.append((node.lineno, f"{node.module}.{a.name}"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):    # 内层属性链也会走到，重复的靠 set 去掉
            continue
        chain = []
        cur = node
        while isinstance(cur, ast.Attribute):
            chain.append(cur.attr)
            cur = cur.value
        if not isinstance(cur, ast.Name) or cur.id not in aliases:
            continue
        path = aliases[cur.id]
        for attr in reversed(chain):
            if path == "layouts" and attr in SUBMODULES:
                path = f"layouts.{attr}"
                continue
            if _INTERNAL.match(attr):
                found.append((node.lineno, f"{path}.{attr}"))
            break
    return sorted(set(found))


def test_rule_examples():
    """规则本身：该拦的拦、该放的放。"""
    bad = ("from layouts.team import MARK_SHAPE\n"
           "from layouts.common import LINE_SPACING, _helper\n"
           "from layouts import team\nteam.MARK_SHAPE\n"
           "import layouts\nlayouts.stats.DESC_PT\n"
           "import layouts.table as t\nt.ROW_H\n")
    got = {name for _, name in violations(bad)}
    want = {"layouts.team.MARK_SHAPE", "layouts.common.LINE_SPACING", "layouts.common._helper",
            "layouts.stats.DESC_PT", "layouts.table.ROW_H"}
    check("检查规则：内部常量 / 下划线名字的各种取法都拦下", got == want, got ^ want)
    ok = ("from layouts.common import wrap_lines, Context\n"
          "from layouts import team\nteam.render\n"
          "from deckcheck import BRAND_RED, LINE_SPACING\n")
    check("检查规则：公开函数、类、子模块和测试自己的常量放行", violations(ok) == [], violations(ok))


def test_tests_use_external_behaviour():
    for path in sorted(HERE.glob("*.py")):
        if path.name in EXEMPT:
            continue
        bad = violations(path.read_text(encoding="utf-8"))
        check(f"{path.name}：不从 layouts 取内部常量",
              not bad, [f"第 {line} 行 {name}" for line, name in bad])


if __name__ == "__main__":
    test_rule_examples()
    test_tests_use_external_behaviour()
    finish()
