"""审核脚本 review_deck.py 的方向 C 规则（spec #47 / #48）：结论 / Next 是否画进了 pptx、
lead 和副标题相同、对比页两个 lead。

运行：python3 skills/milwaukee-ppt/tests/test_review_lead.py
做法：生成器按文稿出 pptx（正样本，不报），再用 python-pptx 改坏（负样本，报对应规则）；
只看审核脚本的输出。文稿内容全部虚构。
"""
from deckcheck import broken, check, finish, generated, lines_with, review

RULES = ("结论没画出来", "Next 没画出来", "lead 和副标题相同", "对比页两个 lead")

PAGES = """
# 现场证据 / EVIDENCE
## 充电位高峰排队超过 20 分钟
![](img/a.png)
早班交接时 6 台叉车同时排队充电
Next: 9 月起按电量排班

# 新流程 / PROCESS
## 排班改为系统分配，三步完成
Layout: process
1. 登记 | 交班时登记剩余电量
2. 排队 | 系统按电量排序
3. 充电 | 到点去指定充电位
B 仓试运行 3 周，高峰排队从 6 台降到 2 台
"""
GENERAL = "---\ntitle: 叉车充电排班 项目汇报\n---\n" + PAGES
MONTHLY = "---\nmonth: 2026-08\nauthor: Mock.Author\n---\n" + PAGES
IMAGES = {"img/a.png": (1600, 900)}


def new_rule_lines(out):
    return [line for line in out.splitlines() if any(line.startswith(f"[{r}]") for r in RULES)]


def drop(name, page=2):
    def change(prs):
        for sh in list(prs.slides[page - 1].shapes):
            if sh.name == name:
                sh._element.getparent().remove(sh._element)
    return change


def retext(name, text, page=2):
    def change(prs):
        for sh in prs.slides[page - 1].shapes:
            if sh.name == name:
                sh.text_frame.paragraphs[0].runs[0].text = text
    return change


def test_generator_output_passes():
    for label, md in (("通用模式", GENERAL), ("月报模式", MONTHLY),
                      ("项目模式", GENERAL.replace("title:", "report: project\ntitle:", 1)
                       .replace("Layout: process", "Layout: process\nPDCA: D")
                       .replace("## 充电位", "PDCA: P\n## 充电位"))):
        r = review(*generated(md, IMAGES))
        check(f"{label}：生成器原样输出不报新规则", r.returncode == 0 and not new_rule_lines(r.stdout),
              r.stdout + r.stderr)


def test_conclusion_not_drawn():
    md, pptx = generated(GENERAL, IMAGES)
    for label, change, rule in (
            ("删掉 Lead", drop("Lead"), "结论没画出来"),
            ("Lead 文字和结论行不一致", retext("Lead", "另写的一句话"), "结论没画出来"),
            ("删掉 Next Line", drop("Next Line"), "Next 没画出来"),
            ("Next Line 文字和 Next 不一致", retext("Next Line", "Next: 另一件事"), "Next 没画出来")):
        r = review(md, broken(pptx, change))
        found = [ln for ln in lines_with(r.stdout, rule) if "第 2 页" in ln and " → " in ln]
        check(f"通用模式 {label}：报「{rule}」，带第 2 页", bool(found), r.stdout)
    md, pptx = generated(MONTHLY, IMAGES)
    r = review(md, broken(pptx, drop("Caption Bar")))
    check("月报模式删掉红条：报「结论没画出来」和「Next 没画出来」",
          any("第 2 页" in ln for ln in lines_with(r.stdout, "结论没画出来"))
          and any("第 2 页" in ln for ln in lines_with(r.stdout, "Next 没画出来")), r.stdout)


def test_lead_same_as_subtitle():
    md = GENERAL.replace("早班交接时 6 台叉车同时排队充电", "充电位高峰排队超过 20 分钟")
    r = review(*generated(md, IMAGES))
    check("lead 等于副标题：报「lead 和副标题相同」",
          any("现场证据 / EVIDENCE" in ln for ln in lines_with(r.stdout, "lead 和副标题相同")),
          r.stdout)
    md = MONTHLY.replace("早班交接时 6 台叉车同时排队充电", "充电位高峰排队超过 20 分钟")
    r = review(*generated(md, IMAGES))
    check("月报模式（红条不是 lead）：不报「lead 和副标题相同」",
          not lines_with(r.stdout, "lead 和副标题相同"), r.stdout)


BEFORE_AFTER = """
# 排队对比 / BEFORE-AFTER
## 排队改为系统分配，高峰不再扎堆
Layout: before-after
同一仓库、同一批叉车，改前改后各统计 3 周

### Before
司机凭经验到充电区排队

### After
系统按剩余电量分配充电时段

高峰排队从 6 台降到 2 台
"""


def test_before_after_two_leads():
    r = review(*generated("---\ntitle: 叉车充电排班 项目汇报\n---\n" + BEFORE_AFTER))
    check("对比页写了两个 lead：报「对比页两个 lead」",
          any("排队对比 / BEFORE-AFTER" in ln and " → " in ln
              for ln in lines_with(r.stdout, "对比页两个 lead")), r.stdout)
    r = review(*generated("---\nmonth: 2026-08\nauthor: Mock.Author\n---\n" + BEFORE_AFTER))
    check("月报模式（第一个 ### 前的文字仍画成 lead）：不报「对比页两个 lead」",
          not lines_with(r.stdout, "对比页两个 lead"), r.stdout)


if __name__ == "__main__":
    test_generator_output_passes()
    test_conclusion_not_drawn()
    test_lead_same_as_subtitle()
    test_before_after_two_leads()
    finish()
