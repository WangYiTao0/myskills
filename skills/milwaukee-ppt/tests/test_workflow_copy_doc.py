"""ppt-grill / ppt-review 的文案和 milwaukee-ppt 的说法一致（方向 C：lead 是结论）。

运行：python3 skills/milwaukee-ppt/tests/test_workflow_copy_doc.py
守住：简报页序表和转换表的列名、lead 必须是结论的说明、月报仍说红条；
ppt-review 清单的"lead 是结论"条目和改写后的 `!` 条目。
"""
import re

from deckcheck import SKILL, check, finish

SKILLS = SKILL.parent
GRILL = (SKILLS / "ppt-grill" / "SKILL.md").read_text(encoding="utf-8")
REVIEW = (SKILLS / "ppt-review" / "SKILL.md").read_text(encoding="utf-8")


def review_rows():
    return {m.group(1): m.group(0) for m in re.finditer(r"(?m)^\| (\d+) \|.*$", REVIEW)}


def test_grill_columns():
    header = next((l for l in GRILL.splitlines() if l.startswith("| # | 主标题")), "")
    check("ppt-grill：页序表列名是「lead / Next」", "| lead / Next |" in header, header)
    check("ppt-grill：页序表不再叫「红条结论 / Next」", "红条结论" not in header, header)
    row = next((l for l in GRILL.splitlines() if l.startswith("| 页序表每一行")), "")
    check("ppt-grill：转换表的页序行用「lead / Next」列名并区分月报",
          "lead / Next" in row and "月报" in row and "红条" in row, row)


def test_grill_lead_rule():
    check("ppt-grill：写明 lead 必须是一句结论，最好带数字",
          "lead 必须是一句结论" in GRILL and "带数字" in GRILL)
    check("ppt-grill：口径、范围、前提写进口径表或「口径：」行，不推荐成 lead",
          "口径：" in GRILL and "不能推荐成 lead" in GRILL)
    check("ppt-grill：月报模式保留红条的说法", "月报" in GRILL and "红条" in GRILL)


def test_review_lead_item():
    rows = review_rows()
    lead = [r for r in rows.values() if "lead 是结论" in r]
    check("ppt-review：清单有「lead 是结论」条目", len(lead) == 1, list(rows))
    if lead:
        r = lead[0]
        check("ppt-review：lead 条目举了「作业量相近」反例", "6 月、9 月作业量相近" in r, r)
        check("ppt-review：lead 条目不合格时改标题层", "标题" in r.split("|")[-2], r)
        check("ppt-review：口径限定挪去口径表 / 口径行", "口径" in r, r)


def test_review_bang_item():
    r = review_rows().get("6", "")
    check("ppt-review：第 6 条 `!` 优先标在 `##` 点名的条目", "点名" in r and "`##`" in r, r)
    check("ppt-review：没点名时才按成果页、问题页、timeline 规则",
          "才按" in r and "成果页" in r and "timeline" in r, r)
    r1 = review_rows().get("1", "")
    check("ppt-review：第 1 条不变",
          "一页一个核心信息" in r1 and "支撑本页 `##` 那句结论" in r1, r1)


if __name__ == "__main__":
    test_grill_columns()
    test_grill_lead_rule()
    test_review_lead_item()
    test_review_bang_item()
    finish()
