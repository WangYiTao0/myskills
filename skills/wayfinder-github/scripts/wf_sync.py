#!/usr/bin/env python3
"""把一个 GitHub 仓库里的 wayfinder 地图导出成 wayfinder-maps 能读的 .plan/ 快照。

只读、单向：GitHub 是唯一真相，快照看完即弃。永远不要反过来把快照写回 GitHub，
也不要把快照提交进仓——那就成了第二份会过期的拷贝。

用法：
    wf_sync.py                     # 仓库自动取自当前目录的 git remote
    wf_sync.py --repo owner/name   # 指定仓库
    wf_sync.py --out <目录>         # 快照落点，默认 ~/.cache/wayfinder-maps/<owner>-<name>
    wf_sync.py --prefix wf:        # label 前缀，默认 wayfinder:

退出码：0 正常，1 出错，2 仓库里没有地图票。
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TYPES = ("research", "prototype", "grilling", "task")

# 票归属哪张图：兼容几种常见写法，第一个捕获组是图的编号
RE_PARENT = re.compile(
    r"^\s*(?:父地图|父票|Part of|Parent|Map)\s*[:：]?\s*#(\d+)", re.M | re.I)
RE_BLOCKED = re.compile(r"^\s*Blocked[ _-]?by\s*[:：]\s*(.+)$", re.M | re.I)
RE_UNDERMINED = re.compile(r"^\s*Undermined[ _-]?by\s*[:：]\s*(.+)$", re.M | re.I)
RE_NUMS = re.compile(r"#?(\d+)")
RE_CLEARS = re.compile(r"clears-with:\s*#?(\d+)", re.I)
RE_HEADING = re.compile(r"^(#{1,6})(\s)")

# 地图正文里这几段会原样搬运，顺序即输出顺序（wayfinder 的 map.md 契约）
MAP_SECTIONS = ("Destination", "Notes", "Decisions so far", "Not yet specified", "Out of scope")


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, check=False, **kw)  # noqa: S603


def gh_json(args):
    p = run(["gh", *args])
    if p.returncode != 0:
        sys.exit(f"gh 失败: gh {' '.join(args)}\n{p.stderr.strip()}")
    return json.loads(p.stdout)


def detect_repo():
    """当前目录所属的 GitHub 仓库。不在 git 仓库里、或没有 GitHub remote 时明确报错。"""
    p = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    if p.returncode != 0 or not p.stdout.strip():
        sys.exit("认不出当前仓库。要么在目标仓库目录里跑，要么用 --repo owner/name 指定。\n"
                 f"gh 说：{p.stderr.strip() or '(无输出)'}")
    return p.stdout.strip()


def write_if_changed(path, text):
    """内容没变就不碰文件。

    查看器的 /api/version 是「map.md + tickets/ 的最新 mtime + 文件数」，前端拿它
    轮询判断要不要重绘。无脑重写会让 mtime 每轮都变，页面就会周期性地无谓刷新。
    """
    try:
        if path.read_text(encoding="utf-8") == text:
            return False
    except FileNotFoundError:
        pass
    path.write_text(text, encoding="utf-8")
    return True


def slugify(title):
    """文件名安全的 slug。解析器的正则是 ^(\\d+)-(.+)\\.md$，中文可以直接留。"""
    s = re.sub(r'[/\\:*?"<>|\n\r\t]', "", title).strip()
    s = re.sub(r"\s+", "-", s)
    return (s[:60] or "untitled").rstrip(".")


def section(body, name):
    """取出 markdown 的 `## <name>` 段落正文，到下一个同级标题为止。"""
    m = re.search(rf"^##\s*{re.escape(name)}\s*$(.*?)(?=^##\s|\Z)", body or "", re.M | re.S)
    return m.group(1).strip() if m else ""


def _heading_lines(text):
    """逐行给出 (行, 标题级别)，代码围栏内的 # 是内容不是标题，级别记 0。"""
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is None:
            if stripped.startswith(("```", "~~~")):
                fence = stripped[:3]
                yield line, 0
                continue
            m = RE_HEADING.match(stripped)
            yield line, (len(m.group(1)) if m else 0)
        else:
            if stripped.startswith(fence):
                fence = None
            yield line, 0


def demote_headings(text):
    """把整段标题按同一位移压到 ### 以下，保持相对层级。

    评论里最浅的标题可能是 # 也可能是 ##。只要它没落在 `## Answer` 之下，就会成为
    Answer 的同级兄弟，令 Answer 段为空 —— 解析器据此判「未解决」，票明明结了却
    显示成待办。所以位移量按本段最小级别算，而不是固定降一级。
    """
    rows = list(_heading_lines(text))
    levels = [lv for _, lv in rows if lv]
    if not levels:
        return text
    shift = max(0, 3 - min(levels))
    if not shift:
        return text
    out = []
    for line, lv in rows:
        if not lv:
            out.append(line)
            continue
        indent = len(line) - len(line.lstrip())
        body = line.lstrip()
        m = RE_HEADING.match(body)
        out.append(line[:indent] + "#" * min(6, lv + shift) + m.group(2) + body[m.end():])
    return "\n".join(out)


def claimed_at(repo, num):
    p = run(["gh", "api", f"repos/{repo}/issues/{num}/timeline", "--paginate",
             "--jq", '[.[] | select(.event=="assigned")] | last | .created_at'])
    return p.stdout.strip() if p.returncode == 0 else ""


def fetch(repo, prefix):
    labels = ",".join(f"{prefix}{t}" for t in ("map", *TYPES))
    return gh_json([
        "issue", "list", "--repo", repo, "--state", "all", "--limit", "500",
        "--search", f"label:{labels}",
        "--json", "number,title,body,state,stateReason,labels,assignees,comments,url",
    ])


def ticket_type(labels, prefix):
    for t in TYPES:
        if f"{prefix}{t}" in labels:
            return t
    return "task"


def build_ticket(it, prefix, repo):
    num, body = it["number"], it["body"] or ""
    labels = [lab["name"] for lab in it["labels"]]
    closed = it["state"] == "CLOSED"
    not_planned = (it.get("stateReason") or "") == "NOT_PLANNED"

    fm = [f"type: {ticket_type(labels, prefix)}"]

    blocked = []
    if m := RE_BLOCKED.search(body):
        blocked = [int(n) for n in RE_NUMS.findall(m.group(1))]
    fm.append(f"blocked_by: [{', '.join(str(b) for b in blocked)}]")

    if m := RE_UNDERMINED.search(body):
        if nums := [int(n) for n in RE_NUMS.findall(m.group(1))]:
            fm.append(f"undermined_by: [{', '.join(str(n) for n in nums)}]")

    # 认领只对还开着的票有意义；关掉的票上遗留的 assignee 是死物，不该占住 frontier
    if not closed and it["assignees"]:
        fm.append(f"claimed_by: {it['assignees'][0]['login']}")
        if at := claimed_at(repo, num):
            fm.append(f"claimed_at: {at}")

    out = ["---", *fm, "---", "", f"# {it['title']}", ""]
    q = section(body, "Question")
    out += ["## Question", "", q or "*(票身未写 Question 段)*", ""]

    # 答案在评论区。closed as completed → Answer；closed as not planned → Ruled out。
    if closed:
        comments = [c["body"].strip() for c in (it.get("comments") or [])
                    if (c.get("body") or "").strip()]
        text = "\n\n---\n\n".join(demote_headings(c) for c in comments)
        heading = "Ruled out" if not_planned else "Answer"
        if not text:
            why = "（not planned）" if not_planned else "（completed）"
            text = (f"*(#{num} 已关闭{why}，但评论区没有内容。"
                    f"结论可能只记在地图的 Decisions so far 里。)*")
        out += [f"## {heading}", "", text, ""]

    out += ["---", "", f"来源：{it['url']}（只读快照，改票请去 GitHub）", ""]
    return "\n".join(out)


def relink(text, slugs, repo):
    """地图里指向票的 GitHub URL 换成 ./tickets/NN-slug.md ——解析器只认后者。"""
    pat = re.compile(rf"https://github\.com/{re.escape(repo)}/issues/(\d+)")

    def sub(m):
        n = int(m.group(1))
        return f"./tickets/{n}-{slugs[n]}.md" if n in slugs else m.group(0)

    return RE_CLEARS.sub(lambda m: f"clears-with: {m.group(1)}", pat.sub(sub, text))


def build_map(mp, slugs, repo):
    body = mp["body"] or ""
    parts = [f"# {mp['title']}", ""]
    for name in MAP_SECTIONS:
        parts += [f"## {name}", "", relink(section(body, name), slugs, repo), ""]
    parts += ["---", "", f"来源：{mp['url']}（只读快照，改图请去 GitHub）", ""]
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description="GitHub issue → wayfinder .plan/ 快照")
    ap.add_argument("--repo", help="owner/name，默认取当前目录的 GitHub remote")
    ap.add_argument("--out", help="快照落点，默认 ~/.cache/wayfinder-maps/<owner>-<name>")
    ap.add_argument("--prefix", default="wayfinder:", help="label 前缀，默认 wayfinder:")
    ap.add_argument("--print-dir", action="store_true", help="只打印快照目录后退出")
    args = ap.parse_args()

    repo = args.repo or detect_repo()
    outroot = Path(args.out).expanduser() if args.out else \
        Path.home() / ".cache" / "wayfinder-maps" / repo.replace("/", "-")

    if args.print_dir:
        print(outroot)
        return 0

    # 标准布局 <root>/.plan/<effort>/ —— wayfinder-maps 的 planDirOf 认这个子目录，
    # 传 <root> 就能列出所有地图，而不是只能一次开一张。
    plan = outroot / ".plan"
    issues = fetch(repo, args.prefix)
    maps = [i for i in issues if f"{args.prefix}map" in [lab["name"] for lab in i["labels"]]]
    tickets = [i for i in issues if i not in maps]
    if not maps:
        print(f"{repo} 里没有带 `{args.prefix}map` 标签的地图票。", file=sys.stderr)
        return 2

    slugs = {i["number"]: slugify(i["title"]) for i in issues}

    by_map = {m["number"]: [] for m in maps}
    orphans = []
    for t in tickets:
        m = RE_PARENT.search(t["body"] or "")
        parent = int(m.group(1)) if m else None
        by_map.get(parent, orphans).append(t)

    plan.mkdir(parents=True, exist_ok=True)
    for mp in maps:
        n = mp["number"]
        d = plan / f"{n}-{slugs[n]}"
        (d / "tickets").mkdir(parents=True, exist_ok=True)

        want = {d / "map.md": build_map(mp, slugs, repo)}
        for t in by_map[n]:
            want[d / "tickets" / f"{t['number']}-{slugs[t['number']]}.md"] = \
                build_ticket(t, args.prefix, repo)

        changed = sum(write_if_changed(p, text) for p, text in want.items())
        # 票可能改了名或换了归属，旧文件要清掉，否则会以幽灵票的身份留在图里
        for old in (d / "tickets").glob("*.md"):
            if old not in want:
                old.unlink()
                changed += 1
        print(f"{d}  ({len(by_map[n])} 张票"
              + (f"，{changed} 处变化)" if changed else "，无变化)"))

    if orphans:
        # 这些票有 wayfinder label 却认不出父地图，任何一张图里都看不到它们
        print(f"⚠ {len(orphans)} 张票没有可识别的父地图，未导出："
              + ", ".join(f"#{t['number']}" for t in orphans)
              + "\n  票身需要一行「父地图：#N」或「Part of #N」。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
