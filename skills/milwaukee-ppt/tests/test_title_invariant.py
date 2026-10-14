"""跨版式不变量：注册表里的每个版式各生成一页，所有正文页的主标题、副标题都填在
模板标题占位框（idx 0 / 10）里，banner 区（0–1.0"）上没有另画的形状。

运行：python3 skills/milwaukee-ppt/tests/test_title_invariant.py
版式名从生成器的未知版式报错里读（registered_layouts），新版式登记进注册表后自动纳入；
在 SAMPLES 里给它补一页最小示例即可，漏补时本测试失败。文稿内容全部虚构。
"""
from deckcheck import (BANNER_BOTTOM, check, finish, generate, placeholder,
                       registered_layouts)

# 版式名 → 一页的版式字段（不含 # / ## 标题行）
SAMPLES = {
    "evidence": """
        ![](img/a.png)
        抽查 3 个月的登记本，约三成借出记录没有归还登记
        """,
    "before-after": """
        Layout: before-after
        同一车间、同一批工具，改前改后各统计 4 周

        ### Before: 纸质登记
        借出时手写登记，归还靠自觉补记

        ### After: 扫码登记
        扫码自动带出工具信息，归还时扫码登记

        试点 4 周内借还记录全部可追溯
        """,
    "process": """
        Layout: process
        1. 贴码 | 每件工具贴唯一二维码
        2. 扫码借出 | 扫码自动带出工具信息
        3. 扫码归还 | 归还时扫码登记
        新流程已在试点车间运行 4 周
        """,
    "stats": """
        Layout: stats
        - 试点工具 | 120 件 | 覆盖试点车间全部手持工具
        - !记录完整率 | 100% | 改前约 70%
        试点 4 周借还记录完整率 100%
        """,
    "stats-side": """
        Layout: stats-side
        - 试点工具 | 120 件 | 覆盖试点车间全部手持工具
        - !记录完整率 | 100% | 改前约 70%
        > 记录完整率达到 100%，抽查不再缺页
        记录完整率达到推广条件
        """,
    "timeline": """
        Layout: timeline
        - Jul | 立项 | 确定车间与工具范围 | 完成
        - !Aug | 表单上线 | 扫码表单开放试用 | 进行中
        - Sep | 试点开始 | 切换为扫码登记 | 未完成
        试点 9 月开始
        """,
    "timeline-phase": """
        Layout: timeline-phase
        - Jul | 立项 | 确定车间与工具范围 | 完成
        - !Aug | 准备 | 表单上线、全部贴码 | 进行中
        - Sep | 试点 | 试点车间切换扫码 | 未完成
        试点 9 月开始
        """,
    "image-text": """
        Layout: image-text
        ![](img/a.png)
        - 按车间显示在借、逾期、闲置数量
        - 每天早班前自动刷新
        看板已在试点车间晨会使用
        """,
    "section": """
        Layout: section
        02 | 试点推进 | PILOT
        """,
    "agenda": """
        Layout: agenda
        01 | 项目目标 | TARGET
        02 | 试点推进 | PILOT
        03 | 下一步 | NEXT STEPS
        """,
    "team": """
        Layout: team
        - 林晓 | 项目负责人 | 统筹进度，对接车间主任
        - 周航 | 现场推进 | 试点车间贴码和培训
        现场推进和数据复盘分开负责
        """,
    "table": """
        Layout: table
        | 车间 | 工具数 | 记录完整率 |
        | --- | --- | --- |
        | 一车间 | 120 件 | 100% |
        | !二车间 | 80 件 | 72% |
        二车间记录完整率最低，下月先推广
        """,
}


def deck(names):
    """每个版式一页：主标题「版式 N / LAYOUT」，副标题「第 N 页副标题写成一句结论」。"""
    pages = []
    for n, name in enumerate(names, start=1):
        body = "\n".join(line.strip() for line in SAMPLES[name].strip("\n").splitlines())
        pages.append(f"# 版式 {n} / {name.upper()}\n## 第 {n} 页副标题写成一句结论\n{body}\n")
    return "---\ntitle: 跨版式不变量\nclosing: Thank You\n---\n\n" + "\n".join(pages)


def test_every_layout_titles_in_placeholders():
    names = registered_layouts()
    missing = [name for name in names if name not in SAMPLES]
    check("注册表里的每个版式都有示例页（新版式在 SAMPLES 补一页）", not missing, missing)
    names = [name for name in names if name in SAMPLES]
    r = generate(deck(names), images={"img/a.png": (1600, 900)})
    check("全部版式一份文稿：生成成功", r.rc == 0, r.stderr)
    if r.rc != 0:
        return
    for n, (name, slide) in enumerate(zip(names, r.slides[1:]), start=1):
        title, sub = placeholder(slide, 0), placeholder(slide, 10)
        check(f"{name}：主标题在 idx 0 占位框里",
              title is not None and title.text_frame.text == f"版式 {n} / {name.upper()}",
              title.text_frame.text if title is not None else None)
        check(f"{name}：副标题在 idx 10 占位框里",
              sub is not None and sub.text_frame.text == f"第 {n} 页副标题写成一句结论",
              sub.text_frame.text if sub is not None else None)
        drawn = [sh.name for sh in slide.shapes
                 if sh.top < BANNER_BOTTOM
                 and not (sh.is_placeholder and sh.placeholder_format.idx in (0, 10))]
        check(f"{name}：banner 区上没有另画的形状", not drawn, drawn)


if __name__ == "__main__":
    test_every_layout_titles_in_placeholders()
    finish()
