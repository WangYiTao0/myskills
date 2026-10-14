"""搭建说明（setup-guide.md）守住合同。

运行：python3 copilot-agent/tests/test_setup_guide.py
"""
import re

from pptx import Presentation

from contract import (AGENT, SKILL, check, finish, missing_refs, registered_layouts, sections,
                      test_no_private_paths)
from layouts import REGISTRY

GUIDE = AGENT / "setup-guide.md"
TEMPLATE = SKILL / "assets" / "MS_Template.pptx"
# 对照表的行：| `版式名` | 母版 layout 名 | …
_ROW = re.compile(r"(?m)^\|\s*`([a-z][a-z-]*)`\s*\|\s*([^|]+?)\s*\|")
_FILE = re.compile(r"`([\w.-]+\.(?:txt|pptx|docx|pdf))`")
_ITEM = re.compile(r"(?m)^(?:\d+\.|-)\s+\S")
# 租户实测细节：真实 SharePoint 域名（文档示例域名 contoso 除外）、邮箱地址
_TENANT = re.compile(r"\b(?!contoso\b)[\w-]+\.sharepoint\.com|\b[\w.+-]+@[\w-]+\.[\w.]+")


def text():
    return GUIDE.read_text(encoding="utf-8") if GUIDE.exists() else ""


def section(keyword):
    return next((body for heading, body in sections(text()) if keyword in heading), "")


def norm(name):
    return " ".join(name.split())


def test_layout_mapping():
    check("搭建说明存在", GUIDE.exists(), GUIDE.name)
    layouts = Presentation(str(TEMPLATE)).slide_layouts
    rows = dict(_ROW.findall(section("套模板")))
    check("对照表覆盖全部版式", set(rows) == registered_layouts(),
          f"多 {sorted(set(rows) - registered_layouts())}，"
          f"少 {sorted(registered_layouts() - set(rows))}")
    for name, module in sorted(REGISTRY.items()):
        want = norm(layouts[module.LAYOUT_INDEX].name)
        got = norm(rows.get(name, "").strip("`"))
        check(f"{name} → 母版 layout「{want}」", got == want, got)


def test_knowledge_files():
    files = _FILE.findall(section("知识库"))
    check("列出知识库文件", len(files) >= 3, files)
    check("列出的文件都真实存在", not missing_refs(" ".join(files)), missing_refs(" ".join(files)))
    check("全文提到的文件都真实存在", not missing_refs(text()), missing_refs(text()))


def test_starter_prompts():
    n = len(_ITEM.findall(section("起始提示词")))
    check("起始提示词 3–4 条", 3 <= n <= 4, n)


def test_no_tenant_details():
    hits = _TENANT.findall(text())
    check("不含租户域名和邮箱", not hits, hits)
    check("Copilot 限制引用公开的官方文档", "learn.microsoft.com" in text())


if __name__ == "__main__":
    test_layout_mapping()
    test_knowledge_files()
    test_starter_prompts()
    test_no_tenant_details()
    test_no_private_paths()
    finish()
