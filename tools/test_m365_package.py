"""tools/m365_package.py 的测试：从命令行入口 main(argv) 观察退出码、输出和产出的 zip。

运行：python3 tools/test_m365_package.py
"""
import contextlib
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m365_package  # noqa: E402

GOOD_MD = "---\nname: {name}\ndescription: 测试用技能。\n---\n\n# 正文\n"


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = m365_package.main([str(a) for a in argv])
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.out = self.root / "dist"

    def tearDown(self):
        self._tmp.cleanup()

    def skill(self, name, files=None, md=None):
        d = self.root / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(md if md is not None else GOOD_MD.format(name=name), encoding="utf-8")
        for rel, data in (files or {}).items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, bytes):
                p.write_bytes(data)
            else:
                p.write_text(data, encoding="utf-8")
        return d

    def names(self, name):
        with zipfile.ZipFile(self.out / f"{name}.zip") as z:
            return sorted(z.namelist())


class Packaging(Base):
    def test_builds_zip_with_skill_folder_and_skips_dev_files(self):
        d = self.skill("demo", {
            "scripts/run.py": "print(1)\n",
            "scripts/__pycache__/run.cpython-314.pyc": b"x",
            "scripts/old.pyc": b"x",
            "tests/test_run.py": "pass\n",
            "prototypes/try.py": "pass\n",
            "assets/.DS_Store": b"x",
            "assets/logo.png": b"png",
        })
        code, text = run([d, "-o", self.out])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.names("demo"), [
            "demo/SKILL.md", "demo/assets/logo.png", "demo/scripts/run.py",
        ])

    def test_m365ignore_patterns_are_skipped_and_not_packaged(self):
        d = self.skill("demo", {
            ".m365ignore": "# 注释\nassets/*.svg\nexamples/demo/img/\n",
            "assets/a.svg": "<svg/>",
            "assets/a.png": b"png",
            "examples/demo/deck.md": "# x\n",
            "examples/demo/img/x.png": b"png",
        })
        code, text = run([d, "-o", self.out])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.names("demo"), [
            "demo/SKILL.md", "demo/assets/a.png", "demo/examples/demo/deck.md",
        ])

    def test_flat_puts_files_at_zip_root(self):
        d = self.skill("demo", {"scripts/run.py": "print(1)\n"})
        code, text = run([d, "-o", self.out, "--flat"])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.names("demo"), ["SKILL.md", "scripts/run.py"])

    def test_multiple_skills_each_get_a_zip(self):
        a = self.skill("a")
        b = self.skill("b")
        code, text = run([a, b, "-o", self.out])
        self.assertEqual(code, 0, text)
        self.assertEqual(self.names("a"), ["a/SKILL.md"])
        self.assertEqual(self.names("b"), ["b/SKILL.md"])


class Checks(Base):
    def assertViolation(self, argv, *needles):
        code, text = run(argv)
        self.assertNotEqual(code, 0, text)
        for n in needles:
            self.assertIn(n, text)
        return text

    def test_skill_md_must_be_under_20000_chars(self):
        body = "汉" * 20000
        d = self.skill("big", md=GOOD_MD.format(name="big") + body)
        self.assertViolation([d, "-o", self.out], "big", "SKILL.md", "20000")

    def test_skill_md_19999_chars_is_ok(self):
        head = GOOD_MD.format(name="ok")
        d = self.skill("ok", md=head + "汉" * (19999 - len(head)))
        code, text = run([d, "-o", self.out])
        self.assertEqual(code, 0, text)

    def test_frontmatter_needs_name_and_description(self):
        d = self.skill("nofm", md="---\nname: nofm\n---\n\n正文\n")
        self.assertViolation([d, "-o", self.out], "nofm", "description")
        e = self.skill("nofm2", md="# 没有 frontmatter\n")
        self.assertViolation([e, "-o", self.out], "nofm2", "name", "description")

    def test_missing_skill_md(self):
        d = self.root / "skills" / "empty"
        d.mkdir(parents=True)
        self.assertViolation([d, "-o", self.out], "empty", "SKILL.md")

    def test_350_files_total_is_ok(self):
        a = self.skill("a", {f"r/{i}.md": "x" for i in range(199)})  # 200 个
        b = self.skill("b", {f"r/{i}.md": "x" for i in range(149)})  # 150 个
        code, text = run([a, b, "-o", self.out])
        self.assertEqual(code, 0, text)

    def test_351_files_total_is_violation(self):
        a = self.skill("a", {f"r/{i}.md": "x" for i in range(200)})  # 201 个
        b = self.skill("b", {f"r/{i}.md": "x" for i in range(149)})  # 150 个
        self.assertViolation([a, b, "-o", self.out], "351", "350")

    def test_directory_depth_at_most_3_counting_skill_folder_as_1(self):
        ok = self.skill("ok", {"scripts/layouts/x.py": "pass\n"})
        code, text = run([ok, "-o", self.out])
        self.assertEqual(code, 0, text)
        deep = self.skill("deep", {"examples/demo/img/x.png": b"png"})
        self.assertViolation([deep, "-o", self.out], "deep/examples/demo/img/x.png", "深度 4")

    def test_extension_must_be_allowed(self):
        d = self.skill("ext", {"assets/a.svg": "<svg/>", "Makefile": "all:\n"})
        text = self.assertViolation([d, "-o", self.out], "ext/assets/a.svg", "ext/Makefile")
        self.assertIn(".svg", text)

    def test_single_file_over_25mb(self):
        d = self.skill("huge", {"assets/big.pptx": b"\0" * (25 * 1024 * 1024 + 1)})
        self.assertViolation([d, "-o", self.out], "huge/assets/big.pptx", "25")

    def test_zip_over_50mb(self):
        import os
        files = {f"assets/r{i}.pptx": os.urandom(13 * 1024 * 1024) for i in range(4)}
        d = self.skill("fat", files)
        self.assertViolation([d, "-o", self.out], "fat.zip", "50")

    def test_no_zip_left_when_any_skill_violates(self):
        good = self.skill("good")
        bad = self.skill("bad", {"a.svg": "x"})
        self.assertViolation([good, bad, "-o", self.out], "bad/a.svg")
        self.assertFalse((self.out / "good.zip").exists())
        self.assertFalse((self.out / "bad.zip").exists())

    def test_lists_every_violation(self):
        d = self.skill("many", {"a.svg": "x", "b.exe": "x"}, md="# 无 frontmatter\n")
        text = self.assertViolation([d, "-o", self.out], "a.svg", "b.exe", "name", "description")
        self.assertGreaterEqual(text.count("many"), 4)


if __name__ == "__main__":
    unittest.main()
