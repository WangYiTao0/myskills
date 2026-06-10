#!/usr/bin/env python3
"""校验插件清单与 skills/ 目录的一致性。

仓库结构：整个仓库是一个名为 myskills 的插件（marketplace 单条目，source 指向根），
skills/ 下每个目录是一个 skill，调用形式为 /myskills:<skill-name>。

检查项：
  1. marketplace.json 只有一个 plugin，name 为 myskills，source 指向仓库根
  2. plugin.json 存在，name/version 与 marketplace.json 一致
  3. skills/ 下每个目录含 SKILL.md，frontmatter 含 name 和 description，且 name 与目录名一致
  4. skills/ 下没有游离的非目录文件（如打包产物 .skill）

用法：python3 scripts/validate.py   （在仓库根目录运行，退出码非 0 表示有错误）
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
SKILLS_DIR = ROOT / "skills"

errors = []


def parse_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if kv:
            fields[kv.group(1)] = kv.group(2).strip()
    return fields


def main() -> int:
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    plugins = data.get("plugins", [])

    if len(plugins) != 1:
        errors.append(f"marketplace.json 应只有 1 个 plugin（整仓库即插件），实际 {len(plugins)} 个")
    plugin = plugins[0] if plugins else {}
    if plugin.get("name") != "myskills":
        errors.append(f"plugin name 应为 'myskills'，实际 {plugin.get('name')!r}")
    if (ROOT / plugin.get("source", "")).resolve() != ROOT:
        errors.append(f"plugin source 应指向仓库根，实际 {plugin.get('source')!r}")
    if not plugin.get("version"):
        errors.append("marketplace.json 缺少 version")

    if not PLUGIN_JSON.is_file():
        errors.append("缺少 .claude-plugin/plugin.json")
    else:
        pj = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        if pj.get("name") != plugin.get("name"):
            errors.append(f"plugin.json name 不一致: {pj.get('name')!r} != {plugin.get('name')!r}")
        if pj.get("version") != plugin.get("version"):
            errors.append(f"plugin.json version 不一致: {pj.get('version')!r} != {plugin.get('version')!r}")

    count = 0
    for entry in sorted(SKILLS_DIR.iterdir()):
        if entry.name in (".DS_Store",):
            continue
        if not entry.is_dir():
            errors.append(f"skills/ 下有游离文件（应删除或移走）: {entry.name}")
            continue
        count += 1
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"[{entry.name}] 缺少 SKILL.md")
            continue
        fm = parse_frontmatter(skill_md)
        if not fm:
            errors.append(f"[{entry.name}] SKILL.md 缺少 frontmatter")
            continue
        if "name" not in fm:
            errors.append(f"[{entry.name}] frontmatter 缺少 name")
        elif fm["name"] != entry.name:
            errors.append(
                f"[{entry.name}] frontmatter name 与目录名不一致: {fm['name']!r}"
            )
        if not fm.get("description"):
            errors.append(f"[{entry.name}] frontmatter 缺少 description")

    if errors:
        print(f"✗ 校验失败，共 {len(errors)} 个问题：")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"✓ 校验通过：myskills 插件下 {count} 个 skill 全部一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
