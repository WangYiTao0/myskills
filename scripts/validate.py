#!/usr/bin/env python3
"""校验 marketplace.json 与 skills/ 目录的一致性。

检查项：
  1. marketplace.json 里每个 plugin 的 source 目录存在，且含 SKILL.md
  2. SKILL.md frontmatter 含 name 和 description，且 name 与 plugin name 一致
  3. skills/ 下每个目录都已注册进 marketplace.json
  4. skills/ 下没有游离的非目录文件（如打包产物 .skill）

用法：python3 scripts/validate.py   （在仓库根目录运行，退出码非 0 表示有错误）
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
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
    registered = {}

    for plugin in data.get("plugins", []):
        name = plugin.get("name", "<missing name>")
        source = plugin.get("source", "")
        skill_dir = (ROOT / source).resolve()
        registered[skill_dir.name] = name

        if not skill_dir.is_dir():
            errors.append(f"[{name}] source 目录不存在: {source}")
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"[{name}] 缺少 SKILL.md: {source}")
            continue

        fm = parse_frontmatter(skill_md)
        if not fm:
            errors.append(f"[{name}] SKILL.md 缺少 frontmatter")
            continue
        if "name" not in fm:
            errors.append(f"[{name}] frontmatter 缺少 name")
        elif fm["name"] != name:
            errors.append(
                f"[{name}] frontmatter name 不一致: {fm['name']!r} != {name!r}"
            )
        if not fm.get("description"):
            errors.append(f"[{name}] frontmatter 缺少 description")
        if not plugin.get("version"):
            errors.append(f"[{name}] marketplace.json 缺少 version")

    for entry in sorted(SKILLS_DIR.iterdir()):
        if entry.name in (".DS_Store",):
            continue
        if not entry.is_dir():
            errors.append(f"skills/ 下有游离文件（应删除或移走）: {entry.name}")
        elif entry.name not in registered:
            errors.append(f"目录未注册进 marketplace.json: skills/{entry.name}")

    if errors:
        print(f"✗ 校验失败，共 {len(errors)} 个问题：")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"✓ 校验通过：{len(registered)} 个 skill 全部一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
