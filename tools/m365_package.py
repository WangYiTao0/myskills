#!/usr/bin/env python3
"""把 skill 目录打成 M365 Copilot（声明式 agent，Agent Builder 上传）用的 .zip，并按平台限制检查。

用法：
    python3 tools/m365_package.py skills/ppt-grill skills/milwaukee-ppt skills/ppt-review
    python3 tools/m365_package.py <skill 目录>... [-o 输出目录] [--flat]

  -o      输出目录，默认仓库根下 dist/（已在 .gitignore）
  --flat  zip 根下直接放 SKILL.md（默认 zip 根下是 <skill 名>/SKILL.md）

包含规则（不进 zip 的开发文件）：
  - 目录 tests/、prototypes/、__pycache__/（任意层级）
  - 以 . 开头的文件或目录（.DS_Store、.m365ignore 等）、*.pyc / *.pyo、Thumbs.db、Office 锁文件 ~$*
  - skill 目录下可选的 .m365ignore：每行一个相对 skill 目录的 glob（fnmatch），以 / 结尾表示整个目录，# 开头是注释

检查（限制与来源见 docs/agents/m365-copilot.md）：
  - SKILL.md 存在、整个文件字符数 < 20000、frontmatter 有 name 和 description
  - 所有传入技能合计文件数 ≤ 350（只算进 zip 的文件）
  - 目录深度 ≤ 3：zip 里的 skill 目录算第 1 层，文件深度 = 它所在目录的层数。
    例：<skill>/SKILL.md 深度 1，<skill>/scripts/layouts/x.py 深度 3，<skill>/examples/demo/img/x.png 深度 4（违规）。
    --flat 时同样按「skill 目录 = 第 1 层」计。
  - 单文件 ≤ 25 MB、每个 zip ≤ 50 MB
  - 扩展名在 M365 支持列表内（无扩展名的文件也算违规）

有违规时逐条打印 `[skill] 问题`、删掉本次产出的 zip、退出码 1；全过打印每个 zip 的路径与大小、退出码 0。
"""
import argparse
import fnmatch
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAX_SKILL_MD_CHARS = 20000  # 必须 < 此值
MAX_TOTAL_FILES = 350
MAX_DEPTH = 3
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_ZIP_BYTES = 50 * 1024 * 1024

ALLOWED_EXTS = {
    # 指令与资源文件
    ".json", ".xml", ".yaml", ".yml", ".ini", ".config", ".utf8", ".docx", ".doc", ".docm",
    ".pdf", ".txt", ".rtf", ".md", ".ppt", ".pptx", ".ppsm", ".xlsx", ".xls", ".xlsm",
    ".csv", ".tsv", ".html", ".htm", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".log",
    # 脚本
    ".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".sh", ".bash",
}

EXCLUDED_DIRS = {"tests", "prototypes", "__pycache__"}
EXCLUDED_FILE_GLOBS = ("*.pyc", "*.pyo", "Thumbs.db", "~$*")
IGNORE_FILE = ".m365ignore"


def load_ignore(skill_dir):
    f = skill_dir / IGNORE_FILE
    if not f.is_file():
        return []
    lines = (ln.strip() for ln in f.read_text(encoding="utf-8").splitlines())
    return [ln for ln in lines if ln and not ln.startswith("#")]


def is_ignored(rel, patterns):
    """rel 是相对 skill 目录的 posix 路径。"""
    parts = rel.split("/")
    if any(p.startswith(".") for p in parts):
        return True
    if any(p in EXCLUDED_DIRS for p in parts[:-1]):
        return True
    if any(fnmatch.fnmatch(parts[-1], g) for g in EXCLUDED_FILE_GLOBS):
        return True
    for pat in patterns:
        if pat.endswith("/"):
            if rel.startswith(pat) or fnmatch.fnmatch(rel, pat + "*"):
                return True
        elif fnmatch.fnmatch(rel, pat):
            return True
    return False


def package_files(skill_dir):
    """返回会进 zip 的文件（相对 skill 目录的 posix 路径，已排序）。"""
    patterns = load_ignore(skill_dir)
    rels = (p.relative_to(skill_dir).as_posix() for p in skill_dir.rglob("*") if p.is_file())
    return sorted(r for r in rels if not is_ignored(r, patterns))


def parse_frontmatter(text):
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if kv:
            fields[kv.group(1)] = kv.group(2).strip()
    return fields


def check_skill_md(skill_dir):
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        return ["缺少 SKILL.md"]
    text = md.read_text(encoding="utf-8")
    problems = []
    if len(text) >= MAX_SKILL_MD_CHARS:
        problems.append(f"SKILL.md 有 {len(text)} 字符，须 < {MAX_SKILL_MD_CHARS}")
    fm = parse_frontmatter(text)
    for key in ("name", "description"):
        if not fm.get(key):
            problems.append(f"SKILL.md frontmatter 缺少 {key}")
    return problems


def check_files(skill_dir, files):
    name = skill_dir.name
    problems = []
    for rel in files:
        shown = f"{name}/{rel}"
        depth = len(rel.split("/"))  # skill 目录 = 第 1 层
        if depth > MAX_DEPTH:
            problems.append(f"{shown}：目录深度 {depth}，上限 {MAX_DEPTH}（skill 目录算第 1 层）")
        ext = Path(rel).suffix.lower()
        if ext not in ALLOWED_EXTS:
            problems.append(f"{shown}：扩展名 {ext or '（无）'} 不在 M365 支持列表")
        size = (skill_dir / rel).stat().st_size
        if size > MAX_FILE_BYTES:
            problems.append(f"{shown}：{size / 1048576:.1f} MB，单文件上限 25 MB")
    return problems


def build_zip(skill_dir, files, out_dir, flat):
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{skill_dir.name}.zip"
    prefix = "" if flat else f"{skill_dir.name}/"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            z.write(skill_dir / rel, prefix + rel)
    return zpath


def main(argv=None):
    ap = argparse.ArgumentParser(description="打包并检查 M365 Copilot 技能 zip")
    ap.add_argument("skills", nargs="+", type=Path, help="skill 目录（含 SKILL.md）")
    ap.add_argument("-o", "--out", type=Path, default=ROOT / "dist", help="输出目录，默认 dist/")
    ap.add_argument("--flat", action="store_true", help="zip 根下直接放 SKILL.md")
    args = ap.parse_args(argv)

    violations = []  # (skill 名, 问题)
    built = []
    total = 0
    for skill_dir in (p.resolve() for p in args.skills):
        name = skill_dir.name
        if not skill_dir.is_dir():
            violations.append((name, f"不是目录：{skill_dir}"))
            continue
        violations += [(name, p) for p in check_skill_md(skill_dir)]
        files = package_files(skill_dir)
        total += len(files)
        violations += [(name, p) for p in check_files(skill_dir, files)]
        zpath = build_zip(skill_dir, files, args.out, args.flat)
        built.append((name, zpath, len(files)))
        zsize = zpath.stat().st_size
        if zsize > MAX_ZIP_BYTES:
            violations.append((name, f"{zpath.name}：{zsize / 1048576:.1f} MB，zip 上限 50 MB"))

    if total > MAX_TOTAL_FILES:
        violations.append(("全部", f"合计 {total} 个文件，上限 {MAX_TOTAL_FILES}"))

    if violations:
        for name, problem in violations:
            print(f"[{name}] {problem}")
        for _, zpath, _ in built:
            zpath.unlink(missing_ok=True)
        print(f"\n未通过：{len(violations)} 条违规，已删除本次产出的 zip", file=sys.stderr)
        return 1

    for name, zpath, n in built:
        print(f"OK {zpath}  {n} 个文件  {zpath.stat().st_size / 1024:.0f} KB")
    print(f"合计 {total} 个文件（上限 {MAX_TOTAL_FILES}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
