"""验证：有 wayfinder label 却认不出父地图的票，会被警告出来（那段曾是死代码）。"""
import io
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import wf_sync


def issue(num, title, labels, body="", state="OPEN"):
    return {"number": num, "title": title, "body": body, "state": state,
            "stateReason": "", "labels": [{"name": n} for n in labels],
            "assignees": [], "comments": [],
            "url": f"https://github.com/o/r/issues/{num}"}


FAKE = [
    issue(1, "地图", ["wayfinder:map"], "## Destination\n去某处\n"),
    issue(2, "认得父图的票", ["wayfinder:task"], "父地图：#1\n\n## Question\n问\n"),
    issue(3, "孤儿票甲", ["wayfinder:task"], "## Question\n没写父地图\n"),
    issue(4, "孤儿票乙", ["wayfinder:research"], "## Question\n也没写\n"),
]

wf_sync.fetch = lambda repo, prefix: FAKE
wf_sync.claimed_at = lambda repo, num: ""

with tempfile.TemporaryDirectory() as tmp:
    sys.argv = ["wf_sync.py", "--repo", "o/r", "--out", tmp]
    err, out = io.StringIO(), io.StringIO()
    with redirect_stderr(err), redirect_stdout(out):
        rc = wf_sync.main()

    stderr = err.getvalue()
    print("退出码:", rc)
    print("stdout:", out.getvalue().strip())
    print("stderr:", stderr.strip() or "(空)")

    ok_warn = "2 张票没有可识别的父地图" in stderr
    ok_nums = "#3" in stderr and "#4" in stderr
    exported = sorted(p.name for p in Path(tmp).glob(".plan/*/tickets/*.md"))
    print("导出的票:", exported)

    print()
    print("孤儿警告出现 :", "✓" if ok_warn else "*** 没有 —— 那段仍是死代码")
    print("点名了 #3 #4 :", "✓" if ok_nums else "*** 没点名")
    print("孤儿未被导出 :", "✓" if len(exported) == 1 else f"*** 导出了 {exported}")
    sys.exit(0 if (ok_warn and ok_nums and len(exported) == 1) else 1)
