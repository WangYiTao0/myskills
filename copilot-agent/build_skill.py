"""构建 Agent Builder 技能包：dist/milwaukee-ppt-skill.zip。

运行：python3 copilot-agent/build_skill.py
SKILL.md = skill/SKILL-head.md（frontmatter + 沙箱里的执行流程）+ instructions.md（文稿规范）
+ 知识文件（版式参考），后两者标题降一级；和 Copilot 指令、知识库共用同一份源文件。
生成脚本和模板直接取自 skills/milwaukee-ppt，不复制进仓库。
zip 内时间戳固定，同样的源文件构建出同样的内容。
"""
import re
import sys
import zipfile
from pathlib import Path

AGENT = Path(__file__).resolve().parent
SKILL = AGENT.parent / "skills" / "milwaukee-ppt"
OUT = AGENT / "dist" / "milwaukee-ppt-skill.zip"
STAMP = (2026, 1, 1, 0, 0, 0)


def demote(text, levels=1):
    """代码块以外的 Markdown 标题降级（代码块里的 `# ` 是示例文稿的页，不能动）。"""
    out, fenced = [], False
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#+ ", line):
            line = "#" * levels + line
        out.append(line)
    return "".join(out)


def skill_md():
    """head + 文稿规范（instructions.md）+ 版式参考（知识文件），后两者挂在一级标题下。"""
    head = (AGENT / "skill" / "SKILL-head.md").read_text(encoding="utf-8")
    rules = (AGENT / "instructions.md").read_text(encoding="utf-8")
    rules = rules.replace("知识库里的 `milwaukee-ppt-layout-guide.txt`", "下方「版式参考」")
    guide = (AGENT / "knowledge" / "milwaukee-ppt-layout-guide.txt").read_text(encoding="utf-8")
    guide = guide.split("\n", 1)[1]                  # 去掉知识文件自己的一级标题
    return (head.rstrip("\n") + "\n\n" + demote(rules).rstrip("\n")
            + "\n\n# 版式参考\n" + demote(guide))


def entries():
    """(包内路径, 内容 bytes)，按包内路径排序。"""
    files = {"SKILL.md": skill_md().encode("utf-8"),
             "scripts/check_env.py": (AGENT / "skill" / "check_env.py").read_bytes(),
             "scripts/review_deck.py": (AGENT / "skill" / "review_deck.py").read_bytes(),
             "assets/MS_Template.pptx": (SKILL / "assets" / "MS_Template.pptx").read_bytes(),
             "references/example-deck.md": (AGENT / "knowledge" / "example-deck.txt").read_bytes()}
    for py in sorted((SKILL / "scripts").rglob("*.py")):
        files["scripts/" + py.relative_to(SKILL / "scripts").as_posix()] = py.read_bytes()
    for img in sorted((SKILL / "examples" / "demo" / "img").glob("*.png")):
        files["references/img/" + img.name] = img.read_bytes()
    return sorted(files.items())


def build(out=OUT):
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries():
            z.writestr(zipfile.ZipInfo(name, STAMP), data, zipfile.ZIP_DEFLATED)
    return out


if __name__ == "__main__":
    path = build()
    print(f"已构建: {path.relative_to(AGENT.parent)}  ({path.stat().st_size // 1024} KB)")
    sys.exit(0)
