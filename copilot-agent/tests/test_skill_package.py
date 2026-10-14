"""Agent Builder 技能包（dist/milwaukee-ppt-skill.zip）守住合同。

运行：python3 copilot-agent/tests/test_skill_package.py
限制来自微软文档「Custom skills in declarative agents (preview)」：zip ≤ 50 MB、单文件 ≤ 25 MB、
≤ 350 个文件、目录深度 ≤ 3、SKILL.md 正文 < 20,000 字符、只收支持的文件类型。
"""
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from contract import (AGENT, SKILL, check, finish, generate_blocks, layout_mentions, md_blocks,
                      page_count, registered_layouts, test_no_private_paths)

sys.path.insert(0, str(AGENT))
import build_skill  # noqa: E402

ZIP = AGENT / "dist" / "milwaukee-ppt-skill.zip"
ALLOWED = {".json", ".xml", ".yaml", ".yml", ".ini", ".config", ".utf8", ".docx", ".doc", ".docm",
           ".pdf", ".txt", ".rtf", ".md", ".ppt", ".pptx", ".ppsm", ".xlsx", ".xls", ".xlsm",
           ".csv", ".tsv", ".html", ".htm", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".log",
           ".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".sh", ".bash"}
LIMIT = 20000
MARGIN = 2000


def members():
    with zipfile.ZipFile(ZIP) as z:
        return {i.filename: i for i in z.infolist() if not i.is_dir()}


def skill_md():
    with zipfile.ZipFile(ZIP) as z:
        return z.read("SKILL.md").decode("utf-8")


def test_up_to_date():
    check("技能包存在", ZIP.exists(), ZIP)
    fresh = Path(tempfile.mkdtemp(prefix="skill-build-")) / ZIP.name
    build_skill.build(fresh)
    with zipfile.ZipFile(fresh) as a, zipfile.ZipFile(ZIP) as b:
        same = (sorted(a.namelist()) == sorted(b.namelist())
                and all(a.read(n) == b.read(n) for n in a.namelist()))
    check("技能包是最新构建（改了源文件要重跑 build_skill.py）", same)


def test_limits():
    files = members()
    check("SKILL.md 在 zip 根目录", "SKILL.md" in files, sorted(files)[:5])
    check("zip ≤ 50 MB", ZIP.stat().st_size <= 50 * 2**20, ZIP.stat().st_size)
    check("单文件 ≤ 25 MB", all(i.file_size <= 25 * 2**20 for i in files.values()))
    check("文件数 ≤ 350", len(files) <= 350, len(files))
    deep = [n for n in files if n.count("/") > 3]
    check("目录深度 ≤ 3", not deep, deep)
    bad = [n for n in files if Path(n).suffix.lower() not in ALLOWED]
    check("只含支持的文件类型", not bad, bad)
    check("带上生成器和公司模板",
          {"scripts/generate_ppt.py", "assets/MS_Template.pptx", "scripts/check_env.py"} <= set(files))


def test_skill_md():
    md = skill_md()
    m = re.match(r"---\n(.*?)\n---\n(.*)", md, re.S)
    check("SKILL.md 有 YAML front matter", bool(m))
    if not m:
        return
    front, body = m.groups()
    check("front matter 有 name 和 description",
          re.search(r"(?m)^name:\s*\S", front) and re.search(r"(?m)^description:\s*\S", front), front)
    check(f"SKILL.md 正文 < {LIMIT} 字符，留 {MARGIN} 余量", len(body) <= LIMIT - MARGIN, len(body))
    check("SKILL.md 的版式名集合 = 生成器注册的版式集合", layout_mentions(md) == registered_layouts(),
          layout_mentions(md) ^ registered_layouts())
    for deck, r in generate_blocks(md_blocks(md)):
        check("SKILL.md 里的示例照抄生成，页数完整",
              r.rc == 0 and len(r.slides) >= 1 + page_count(deck), r.stderr or deck[:200])
    check("SKILL.md 含全部 8 个版式的详细写法（版式参考整篇并入）",
          all(f"## {name} " in md or f"### {name} " in md for name in registered_layouts()),
          [n for n in registered_layouts() if f"### {n} " not in md])
    refs = set(re.findall(r"`((?:scripts|assets|references)/[\w./-]+)`", md))
    names = members()
    missing = sorted(r for r in refs if r not in names
                     and not (r.endswith("/") and any(n.startswith(r) for n in names)))
    check("SKILL.md 提到的包内文件都在包里", not missing, missing)


def test_agent_instructions():
    """配合技能包用的 agent 指令：长度在 Instructions 上限内，按技能名引用技能、不抄技能细节。"""
    text = (AGENT / "skill" / "agent-instructions.md").read_text(encoding="utf-8")
    name = re.search(r"(?m)^name:\s*(\S+)", skill_md()).group(1)
    check("agent 指令 ≤ 8000 字符", len(text) <= 8000, len(text))
    check(f"agent 指令按技能名 `{name}` 引用技能", f"`{name}`" in text)
    check("agent 指令不抄技能里的版式细节", not layout_mentions(text), layout_mentions(text))


def test_runs_from_package():
    """解开 zip，按 SKILL.md 的流程先跑自检、再用示例文稿生成，模拟沙箱里的执行。"""
    work = Path(tempfile.mkdtemp(prefix="skill-run-"))
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(work)
    r = subprocess.run([sys.executable, "scripts/check_env.py"], cwd=work,
                       capture_output=True, text=True)
    check("自检脚本退出码 0", r.returncode == 0, r.stdout + r.stderr)
    check("自检报告 python-pptx 和模板可用", "python-pptx" in r.stdout and "OK" in r.stdout, r.stdout)
    deck = work / "references" / "example-deck.md"
    out = work / "out.pptx"
    r = subprocess.run([sys.executable, "scripts/generate_ppt.py", str(deck), "-o", str(out)],
                       cwd=work, capture_output=True, text=True)
    check("包内示例文稿照抄生成", r.returncode == 0 and out.exists(), r.stderr)
    same = (work / "scripts" / "generate_ppt.py").read_bytes() == \
        (SKILL / "scripts" / "generate_ppt.py").read_bytes()
    check("包内生成器与 skill 源文件一致", same)


if __name__ == "__main__":
    test_up_to_date()
    test_limits()
    test_skill_md()
    test_agent_instructions()
    test_runs_from_package()
    test_no_private_paths()
    finish()
