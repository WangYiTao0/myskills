"""评测 Copilot 的回答：同一道题的多份回答，逐份看能否生成、版式是否合法，再比较几次之间的漂移。

运行：python3 copilot-agent/evaluate.py <回答目录 或 回答文件...>

- 目录：读其中所有 .md，跳过 question.md 和 README.md；按文件名排序。
- 每份回答取第一个含 `# ` 页的代码块（```markdown / ```md / 不带语言都行）；没有代码块但全文以
  frontmatter 开头时用全文。
- 文稿里的图片一律换成现生成的纯色占位图，评测只看文稿结构，不看图。
- 输出 Markdown 报告，可直接贴成 issue 评论；报告里不含本机路径。
"""
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

AGENT = Path(__file__).resolve().parent
SKILL = AGENT.parent / "skills" / "milwaukee-ppt"
GENERATOR = SKILL / "scripts" / "generate_ppt.py"
sys.path.insert(0, str(GENERATOR.parent))

from layouts import DEFAULT_LAYOUT, REGISTRY  # noqa: E402

SKIP = {"question.md", "readme.md"}
_FENCE = re.compile(r"^```[ \t]*(markdown|md)?[ \t]*\n(.*?)^```", re.S | re.M | re.I)
_LAYOUT = re.compile(r"(?im)^layout\s*[:：]\s*(\S+)\s*$")
_TITLE = re.compile(r"(?m)^##\s+(.+?)\s*$")
_IMG = re.compile(r"(!\[[^\]]*\]\()([^)]+)(\))")


@dataclass
class Answer:
    name: str
    found: bool = False          # 找到文稿
    generated: bool = False      # 生成器退出码 0
    error: str = ""              # 生成器报错（已去掉临时目录路径）
    layouts: list = field(default_factory=list)       # 每页版式，不写 = evidence
    titles: list = field(default_factory=list)        # 每页 `## ` 副标题
    bad_layouts: list = field(default_factory=list)   # 生成器不认的版式名
    warnings: int = 0            # 生成器的 `警告:` 行数（多为文字估计溢出）

    @property
    def layouts_ok(self):
        return self.found and not self.bad_layouts


@dataclass
class Drift:
    page_counts: list
    layout_seqs: list
    title_seqs: list
    differing_pages: list        # 版式或副标题不一致的页（从 1 数）

    @property
    def pages_same(self):
        return len(set(self.page_counts)) <= 1

    @property
    def layouts_same(self):
        return len({tuple(s) for s in self.layout_seqs}) <= 1

    @property
    def titles_same(self):
        return len({tuple(s) for s in self.title_seqs}) <= 1


def extract_deck(text):
    for _, body in _FENCE.findall(text):
        if re.search(r"(?m)^# ", body):
            return body
    if text.lstrip().startswith("---") and re.search(r"(?m)^# ", text):
        return text.lstrip()
    return None


def pages(deck):
    return re.split(r"(?m)^# ", deck)[1:]


def generate(deck):
    """图片换成占位图后交给生成器；返回 (是否成功, 报错, 警告行数)。"""
    from PIL import Image
    work = Path(tempfile.mkdtemp(prefix="copilot-eval-"))
    (work / "img").mkdir()
    count = 0

    def placeholder(m):
        nonlocal count
        count += 1
        name = f"img/placeholder-{count}.png"
        Image.new("RGB", (1600, 900), (120, 120, 120)).save(work / name)
        return m.group(1) + name + m.group(3)

    (work / "deck.md").write_text(_IMG.sub(placeholder, deck), encoding="utf-8")
    r = subprocess.run([sys.executable, str(GENERATOR), str(work / "deck.md"),
                        "-o", str(work / "out.pptx")], capture_output=True, text=True)
    error = r.stderr.strip().replace(str(work) + "/", "").replace(str(work), "")
    warnings = sum(line.startswith("警告") for line in r.stderr.splitlines())
    return r.returncode == 0, ("" if r.returncode == 0 else error), warnings


def evaluate_answer(path):
    path = Path(path)
    a = Answer(path.name)
    deck = extract_deck(path.read_text(encoding="utf-8"))
    if deck is None:
        a.error = "回答里没有找到文稿代码块"
        return a
    a.found = True
    for page in pages(deck):
        m = _LAYOUT.search(page)
        layout = m.group(1).lower() if m else DEFAULT_LAYOUT
        a.layouts.append(layout)
        if layout not in REGISTRY:
            a.bad_layouts.append(layout)
        t = _TITLE.search(page)
        a.titles.append(t.group(1) if t else "")
    a.generated, a.error, a.warnings = generate(deck)
    return a


def drift(answers):
    found = [a for a in answers if a.found]
    differing = []
    for i in range(max((len(a.layouts) for a in found), default=0)):
        cells = {(a.layouts[i], a.titles[i]) if i < len(a.layouts) else None for a in found}
        if len(cells) > 1:
            differing.append(i + 1)
    return Drift([len(a.layouts) for a in found], [a.layouts for a in found],
                 [a.titles for a in found], differing)


def answer_files(args):
    files = []
    for arg in map(Path, args):
        if arg.is_dir():
            files += sorted(p for p in arg.glob("*.md") if p.name.lower() not in SKIP)
        else:
            files.append(arg)
    return files


def _yn(ok):
    return "是" if ok else "否"


def report(answers, title):
    n = len(answers)
    lines = [f"## 评测：{title}", "",
             "| 回答 | 找到文稿 | 可生成 | 版式合法 | 警告 | 页数 | 每页版式 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for a in answers:
        lines.append(f"| {a.name} | {_yn(a.found)} | {_yn(a.generated)} | {_yn(a.layouts_ok)} | {a.warnings} "
                     f"| {len(a.layouts)} | {' / '.join(a.layouts)} |")
    lines += ["", f"生成成功 {sum(a.generated for a in answers)}/{n}，"
                  f"版式合法 {sum(a.layouts_ok for a in answers)}/{n}"]
    errors = [a for a in answers if a.error]
    if errors:
        lines += ["", "### 报错"]
        lines += [f"- {a.name}：{a.error.splitlines()[-1]}" for a in errors]
        illegal = sorted({x for a in answers for x in a.bad_layouts})
        if illegal:
            lines.append(f"- 非法版式名：{', '.join(illegal)}")
    d = drift(answers)
    lines += ["", "### 一致性",
              f"- 页数：{' / '.join(map(str, d.page_counts))} → {'一致' if d.pages_same else '不一致'}",
              f"- 每页版式：{'一致' if d.layouts_same else '不一致'}",
              f"- 每页副标题：{'一致' if d.titles_same else '不一致'}"]
    found = [a for a in answers if a.found]
    for i in d.differing_pages:
        lines.append(f"- 第 {i} 页：")
        for a in found:
            cell = (f"`{a.layouts[i - 1]}` {a.titles[i - 1]}" if i <= len(a.layouts)
                    else "（无此页）")
            lines.append(f"  - {a.name}：{cell}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    files = answer_files(args)
    if not files:
        print("错误: 没有找到回答文件", file=sys.stderr)
        return 2
    title = Path(args[0]).name if len(args) == 1 else f"{len(files)} 份回答"
    print(report([evaluate_answer(p) for p in files], title), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
