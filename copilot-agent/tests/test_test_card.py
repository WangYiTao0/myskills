"""测试卡（test-card.md）和参考答案（reference-answer.md）守住合同。

运行：python3 copilot-agent/tests/test_test_card.py
"""
import re

from contract import (AGENT, check, finish, generate_md, layout_mentions, page_count,
                      registered_layouts, sections, test_no_private_paths)

CARD = AGENT / "test-card.md"
ANSWER = AGENT / "reference-answer.md"
GUIDE = AGENT / "setup-guide.md"
COLUMNS = ["怎么做", "期望", "记录"]
# 必须覆盖的测试项：(说明, 条目标题里要出现的关键词)
COVERAGE = [("5 次一致性", "5 次"), ("产出可生成", "生成"), ("按模板改版式", "版式"),
            ("用词核对", "用词")]


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def items():
    """测试项 = 标题以「第 N 条」开头的小节。"""
    return [(h, b) for h, b in sections(read(CARD)) if re.match(r"第\s*\d+\s*条", h)]


def test_items():
    check("测试卡存在", CARD.exists(), CARD.name)
    found = items()
    check("至少 5 条测试项", len(found) >= 5, [h for h, _ in found])
    check("第 1 条是免费版可用性（能否打开 agent、读到知识源）",
          bool(found) and "免费版" in found[0][0] and "知识" in found[0][0] + found[0][1],
          found[:1] and found[0][0])
    for label, keyword in COVERAGE:
        check(f"覆盖{label}", any(keyword in h for h, _ in found), [h for h, _ in found])
    for heading, body in found:
        missing = [c for c in COLUMNS if c not in body]
        check(f"「{heading}」有怎么做 / 期望 / 记录", not missing, missing)


def test_uses_starter_prompts():
    guide = dict(sections(read(GUIDE)))
    prompts = next((b for h, b in guide.items() if "起始提示词" in h), "")
    titles = re.findall(r"(?m)^\d+\.\s+\*\*(.+?)\*\*", prompts)
    used = [t for t in titles if t in read(CARD)]
    check("测试卡使用搭建说明里的起始提示词", bool(used), titles)


def test_reference_answer():
    md = read(ANSWER)
    check("参考答案存在", bool(md), ANSWER.name)
    if not md:
        return
    r = generate_md(md)
    check("参考答案照抄生成，退出码 0", r.rc == 0, r.stderr)
    check("参考答案没有警告", "警告" not in r.stderr, r.stderr)
    check("参考答案的版式都被识别", layout_mentions(md) <= registered_layouts(),
          layout_mentions(md) - registered_layouts())
    check("参考答案每页都生成出来", len(r.slides) >= 1 + page_count(md),
          (len(r.slides), page_count(md)))
    check("测试卡引用参考答案", ANSWER.name in read(CARD))


if __name__ == "__main__":
    test_items()
    test_uses_starter_prompts()
    test_reference_answer()
    test_no_private_paths()
    finish()
