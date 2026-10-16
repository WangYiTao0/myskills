#!/usr/bin/env python3
"""批量建 GitHub issue 与带重试的 gh 封装（仅标准库 + gh）。

用法：
  tools/gh_batch.py create DIR --repo OWNER/REPO [--label L]... [--parent N] [--dry-run]
  tools/gh_batch.py retry -- gh issue comment 12 --repo OWNER/REPO --body "..."

DIR 内每个 `NN-slug.md`：第一行 `# 标题`，其余为正文；可含一行 `Blocked-by: 01, 03`
（同批文件编号），建好后用 GitHub 原生 dependencies/blocked_by 设依赖。
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RETRIES = 4  # 总共最多尝试次数
BASE_DELAY = 2.0  # 间隔：2s、4s、6s...
TRANSIENT = re.compile(
    r"EOF|timeout|timed out|connection (reset|refused|closed)|TLS|"
    r"no such host|temporary|HTTP 5\d\d|i/o error|broken pipe",
    re.I,
)
FILE_RE = re.compile(r"^(\d+)-.+\.md$")
BLOCKED_RE = re.compile(r"^\s*Blocked-by:\s*(.*?)\s*$", re.I | re.M)


class GhError(RuntimeError):
    pass


def run_gh(args, sleep=time.sleep):
    """运行 gh 命令（args 含 'gh' 本身）。瞬时错误重试，确定性错误（422 等）直接抛出。"""
    last = ""
    for attempt in range(1, RETRIES + 1):
        p = subprocess.run(args, capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout
        last = (p.stderr or "") + (p.stdout or "")
        if not TRANSIENT.search(last):
            raise GhError(last.strip())
        if attempt < RETRIES:
            print(f"[retry {attempt}/{RETRIES - 1}] {last.strip()[:120]}", file=sys.stderr)
            sleep(BASE_DELAY * attempt)
    raise GhError(f"重试 {RETRIES} 次仍失败：{last.strip()}")


def parse_file(path):
    """返回 (编号字符串, 标题, 正文, blocked_by 编号列表)。"""
    m = FILE_RE.match(path.name)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"{path.name}: 第一行必须是 `# 标题`")
    title = lines[0][2:].strip()
    body = "\n".join(lines[1:]).strip("\n")
    blockers = []
    bm = BLOCKED_RE.search(body)
    if bm:
        blockers = [x for x in re.split(r"[,\s]+", bm.group(1)) if x]
        body = BLOCKED_RE.sub("", body, count=1).strip("\n")
    return m.group(1), title, body, blockers


def load_dir(d):
    files = sorted(p for p in Path(d).iterdir() if FILE_RE.match(p.name))
    if not files:
        raise ValueError(f"{d}: 没有 NN-slug.md 文件")
    return [(p, *parse_file(p)) for p in files]


def issue_id(repo, number):
    return int(run_gh(["gh", "api", f"repos/{repo}/issues/{number}", "--jq", ".id"]).strip())


def open_titles(repo):
    out = run_gh(["gh", "issue", "list", "--repo", repo, "--state", "open",
                  "--limit", "1000", "--json", "number,title"])
    return {i["title"]: i["number"] for i in json.loads(out)}


def cmd_create(a):
    items = load_dir(a.dir)
    known = {it[1] for it in items}
    for it in items:
        for b in it[4]:
            if b not in known:
                raise ValueError(f"{it[0].name}: Blocked-by 引用了不存在的编号 {b}")
    existing = {} if a.dry_run else open_titles(a.repo)
    made = {}  # 编号 -> issue 号
    new = set()
    for path, num, title, body, blockers in items:
        if a.dry_run:
            extra = f"  blocked-by {','.join(blockers)}" if blockers else ""
            print(f"{path.name} -> (dry-run) {title}{extra}")
            continue
        if title in existing:
            made[num] = existing[title]
            print(f"{path.name} -> #{existing[title]} (已存在，跳过)")
            continue
        cmd = ["gh", "issue", "create", "--repo", a.repo, "--title", title, "--body", body]
        for lb in a.label or []:
            cmd += ["--label", lb]
        url = run_gh(cmd).strip().splitlines()[-1]
        made[num] = int(url.rstrip("/").rsplit("/", 1)[1])
        new.add(num)
        print(f"{path.name} -> #{made[num]}")
    if a.dry_run:
        return 0
    for path, num, title, body, blockers in items:
        if num not in new:
            continue
        if a.parent:
            run_gh(["gh", "api", "--method", "POST",
                    f"repos/{a.repo}/issues/{a.parent}/sub_issues",
                    "-F", f"sub_issue_id={issue_id(a.repo, made[num])}"])
        for b in blockers:
            run_gh(["gh", "api", "--method", "POST",
                    f"repos/{a.repo}/issues/{made[num]}/dependencies/blocked_by",
                    "-F", f"issue_id={issue_id(a.repo, made[b])}"])
            print(f"  #{made[num]} blocked-by #{made[b]}")
    return 0


def cmd_retry(a):
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        raise ValueError("retry 后需跟要执行的 gh 命令")
    sys.stdout.write(run_gh(cmd))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="sub", required=True)
    c = sub.add_parser("create", help="按目录批量建 issue")
    c.add_argument("dir")
    c.add_argument("--repo", required=True)
    c.add_argument("--label", action="append")
    c.add_argument("--parent", type=int)
    c.add_argument("--dry-run", action="store_true")
    c.set_defaults(fn=cmd_create)
    r = sub.add_parser("retry", help="带重试地透传任意 gh 命令")
    r.add_argument("cmd", nargs=argparse.REMAINDER)
    r.set_defaults(fn=cmd_retry)
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except (GhError, ValueError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
