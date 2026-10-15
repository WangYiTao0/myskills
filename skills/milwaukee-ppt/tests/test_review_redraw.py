"""审核脚本 review_deck.py 的「正文形状被改过」（spec #47 / #52）：审核时按当前 md 重新渲染一份，
逐页比较正文形状（占位框以外）的名字集合，多出、缺少都报；不比几何和字号，手工细调不报。

运行：python3 skills/milwaukee-ppt/tests/test_review_redraw.py
做法：生成器按文稿出 pptx（正样本，不报），再用 python-pptx 改：按形状名删掉正文、用新名字
重画（原型 prototype/ppt-visual-directions 的后处理做法，报）；只挪位置、只改字号（细调，不报）。
只看审核脚本的输出。文稿内容全部虚构。
"""
from pptx.util import Inches, Pt

from deckcheck import SKILL, broken, check, finish, generated, lines_with, review
import test_review_project as full

RULE = "正文形状被改过"

PAGES = """
# 新流程 / PROCESS
## 排班改为系统分配，三步完成
Layout: process
1. 登记 | 交班时登记剩余电量
2. 排队 | 系统按电量排序
3. 充电 | 到点去指定充电位
B 仓试运行 3 周，高峰排队从 6 台降到 2 台
Next: 9 月起推广到 A 仓

# 试点结果 / RESULT
## 高峰排队从 6 台降到 2 台
Layout: stats
- 高峰排队 | 2 台 | 改前 6 台
- !等待时长 | 5 分钟 | 改前 20 分钟
- 充电位利用率 | 85% | 改前 60%
试运行 3 周，三项指标都改善
"""
GENERAL = "---\ntitle: 叉车充电排班 项目汇报\n---\n" + PAGES
MONTHLY = "---\nmonth: 2026-08\nauthor: Mock.Author\n---\n" + PAGES


def redraw(page=2):
    """原型的后处理：删掉正文区所有非占位框形状，再用自己起的名字画一个文本框。"""
    def change(prs):
        slide = prs.slides[page - 1]
        for sh in list(slide.shapes):
            if not sh.is_placeholder:
                sh._element.getparent().remove(sh._element)
        box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(10), Inches(3))
        box.name = "Redrawn Body"
        box.text_frame.text = "登记 → 排队 → 充电"
    return change


def drop_one(name, page=2):
    def change(prs):
        for sh in list(prs.slides[page - 1].shapes):
            if sh.name == name:
                sh._element.getparent().remove(sh._element)
    return change


def fine_tune(page=2):
    """细调：每个正文形状往右下挪 0.05"，有文字的字号加 2pt。"""
    def change(prs):
        for sh in prs.slides[page - 1].shapes:
            if sh.is_placeholder:
                continue
            sh.left += Inches(0.05)
            sh.top += Inches(0.05)
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size is not None:
                            run.font.size = Pt(run.font.size.pt + 2)
    return change


def hits(out, page):
    return [ln for ln in lines_with(out, RULE) if f"第 {page} 页" in ln and " → " in ln]


def test_generator_output_passes():
    for label, md in (("通用模式", GENERAL), ("月报模式", MONTHLY),
                      ("项目模式全版式", full.PROJECT_FULL), ("通用模式全版式", full.plain_full())):
        r = review(*generated(md, full.IMAGES))
        check(f"{label}：生成器原样输出不报「{RULE}」", not lines_with(r.stdout, RULE), r.stdout)


def test_redrawn_body_reported():
    for label, md in (("通用模式", GENERAL), ("月报模式", MONTHLY)):
        md_path, pptx = generated(md)
        r = review(md_path, broken(pptx, redraw()))
        found = hits(r.stdout, 2)
        check(f"{label}按形状名删掉正文、用新名字重画：报「{RULE}」，带第 2 页、多出和缺少的形状名",
              len(found) == 1 and "Redrawn Body" in found[0] and "Process" in found[0]
              and "REVIEW: " in r.stdout and not hits(r.stdout, 3), r.stdout)


def test_missing_shape_reported():
    md, pptx = generated(GENERAL)
    r = review(md, broken(pptx, drop_one("Stat Number 2", page=3)))
    found = hits(r.stdout, 3)
    check(f"删掉一个正文形状：报「{RULE}」，点名缺少的形状",
          len(found) == 1 and "Stat Number 2" in found[0], r.stdout)


def test_fine_tune_not_reported():
    for label, md in (("通用模式", GENERAL), ("月报模式", MONTHLY)):
        md_path, pptx = generated(md)
        r = review(md_path, broken(pptx, fine_tune()))
        check(f"{label}只挪位置、只改字号的细调稿：不报「{RULE}」", not lines_with(r.stdout, RULE),
              r.stdout)


def test_docs():
    readme = (SKILL / "scripts" / "README.md").read_text(encoding="utf-8")
    check("scripts README：审核命令列出「正文形状被改过」和「红色面积超配额」",
          "正文形状被改过" in readme and "红色面积超配额" in readme)
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    tune = skill.split("### 生成后细调", 1)[1].split("\n## ", 1)[0]
    check("SKILL.md 细调：写明细调后再审——挪位置、改字号不报，新加形状报「正文形状被改过」",
          "再审" in tune and RULE in tune and "挪位置" in tune and "新加" in tune, tune[-600:])
    review_md = (SKILL.parent / "ppt-review" / "SKILL.md").read_text(encoding="utf-8")
    check("ppt-review：交付 / 细调处写明细调稿再审时「正文形状被改过」怎么看",
          RULE in review_md and "细调" in review_md)


if __name__ == "__main__":
    test_docs()
    test_generator_output_passes()
    test_redrawn_body_reported()
    test_missing_shape_reported()
    test_fine_tune_not_reported()
    finish()
