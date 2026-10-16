"""运行：python3 -m unittest discover -s tools -p 'test_*.py'"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import gh_batch as g  # noqa: E402


def cp(rc=0, out="", err=""):
    return mock.Mock(returncode=rc, stdout=out, stderr=err)


class RetryTest(unittest.TestCase):
    def test_retries_eof_then_succeeds(self):
        with mock.patch("subprocess.run", side_effect=[cp(1, err="EOF"), cp(1, err="EOF"), cp(0, "ok")]) as r:
            sl = mock.Mock()
            with redirect_stderr(io.StringIO()):
                self.assertEqual(g.run_gh(["gh", "x"], sleep=sl), "ok")
            self.assertEqual(r.call_count, 3)
            self.assertEqual([c.args[0] for c in sl.call_args_list], [2.0, 4.0])

    def test_gives_up_after_4(self):
        with mock.patch("subprocess.run", return_value=cp(1, err="Post: EOF")) as r:
            with redirect_stderr(io.StringIO()), self.assertRaises(g.GhError):
                g.run_gh(["gh", "x"], sleep=lambda s: None)
            self.assertEqual(r.call_count, 4)

    def test_422_not_retried(self):
        with mock.patch("subprocess.run", return_value=cp(1, err="HTTP 422: Validation Failed")) as r:
            with self.assertRaises(g.GhError):
                g.run_gh(["gh", "x"], sleep=lambda s: None)
            self.assertEqual(r.call_count, 1)


class CreateTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        p = Path(self.d.name)
        (p / "01-a.md").write_text("# 标题A\n\n正文A\n", encoding="utf-8")
        (p / "02-b.md").write_text("# 标题B\n\nBlocked-by: 01\n正文B\n", encoding="utf-8")
        (p / "notes.txt").write_text("忽略", encoding="utf-8")

    def tearDown(self):
        self.d.cleanup()

    def run_main(self, argv, side):
        calls = []

        def fake(args, sleep=None):
            calls.append(args)
            return side(args)

        out = io.StringIO()
        with mock.patch.object(g, "run_gh", fake), redirect_stdout(out):
            rc = g.main(argv)
        return rc, out.getvalue(), calls

    def test_parse(self):
        items = g.load_dir(self.d.name)
        self.assertEqual([i[2] for i in items], ["标题A", "标题B"])
        self.assertEqual(items[1][4], ["01"])
        self.assertEqual(items[1][3], "正文B")

    def test_dry_run_creates_nothing(self):
        rc, out, calls = self.run_main(["create", self.d.name, "--repo", "o/r", "--dry-run"], lambda a: "")
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [])
        self.assertIn("标题B", out)

    def test_create_with_parent_and_deps(self):
        counter = iter([11, 12])

        def side(a):
            if a[:3] == ["gh", "issue", "list"]:
                return "[]"
            if a[:3] == ["gh", "issue", "create"]:
                return f"https://github.com/o/r/issues/{next(counter)}\n"
            if "--jq" in a:
                return str(1000 + int(a[2].rsplit("/", 1)[1])) + "\n"
            return ""

        rc, out, calls = self.run_main(
            ["create", self.d.name, "--repo", "o/r", "--label", "x", "--parent", "5"], side)
        self.assertEqual(rc, 0)
        self.assertIn("01-a.md -> #11", out)
        self.assertIn("02-b.md -> #12", out)
        creates = [c for c in calls if c[:3] == ["gh", "issue", "create"]]
        self.assertEqual(creates[0][creates[0].index("--title") + 1], "标题A")
        self.assertEqual(creates[1][creates[1].index("--body") + 1], "正文B")
        self.assertIn("--label", creates[0])
        dep = [c for c in calls if c[-2:] == ["-F", "issue_id=1011"]]
        self.assertEqual(len(dep), 1)
        self.assertIn("repos/o/r/issues/12/dependencies/blocked_by", dep[0])
        subs = [c for c in calls if any("sub_issues" in x for x in c)]
        self.assertEqual(len(subs), 2)

    def test_idempotent_skip_existing(self):
        def side(a):
            if a[:3] == ["gh", "issue", "list"]:
                return '[{"number": 7, "title": "标题A"}]'
            if a[:3] == ["gh", "issue", "create"]:
                return "https://github.com/o/r/issues/8\n"
            if "--jq" in a:
                return "1\n"
            return ""

        rc, out, calls = self.run_main(["create", self.d.name, "--repo", "o/r"], side)
        self.assertIn("01-a.md -> #7 (已存在，跳过)", out)
        self.assertEqual(len([c for c in calls if c[:3] == ["gh", "issue", "create"]]), 1)
        self.assertIn("#8 blocked-by #7", out)

    def test_unknown_blocker(self):
        (Path(self.d.name) / "03-c.md").write_text("# C\nBlocked-by: 09\n", encoding="utf-8")
        with redirect_stderr(io.StringIO()):
            rc, _, _ = self.run_main(["create", self.d.name, "--repo", "o/r", "--dry-run"], lambda a: "")
        self.assertEqual(rc, 1)


class RetryCmdTest(unittest.TestCase):
    def test_passthrough(self):
        out = io.StringIO()
        with mock.patch.object(g, "run_gh", return_value="hi\n") as r, redirect_stdout(out):
            self.assertEqual(g.main(["retry", "--", "gh", "issue", "view", "1"]), 0)
        r.assert_called_once_with(["gh", "issue", "view", "1"])
        self.assertEqual(out.getvalue(), "hi\n")


if __name__ == "__main__":
    unittest.main()
