#!/usr/bin/env python3
"""生成后审核：机械检查 md 文稿和 pptx，列出要改的地方。

用法:
    python3 review_deck.py deck.md [输出.pptx]

每条问题一行：「[规则] 位置：问题 → 怎么改」。没有问题时最后一行打印 REVIEW OK，
有问题时最后一行是「REVIEW: N 条问题」。只报告、不改文件；审完退出码总是 0，
文稿本身读不了（找不到、写错）时为 1。和生成器共用解析器与版式注册表。
给了 pptx 时另查真伪（是不是生成器按当前文稿做的）和几何（出界、压 banner / 页脚、
文字溢出、重叠、错位；只用 python-pptx 和计算，不依赖 LibreOffice）。
需要判断的项（内容是否贴题、页序是否讲得通）留给审核清单，由模型逐条核对。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mdparse  # noqa: E402
from layouts.common import text_width_in  # noqa: E402  生成器估算文字宽度的同一个函数
from mdparse import DeckError  # noqa: E402

# 章节 → 不适合放的版式（目标、范围要写目标和边界，不放流程和改前改后；应用场景不放改前改后）
MISFIT = {"TARGET": {"process", "before-after"}, "SCOPE": {"process", "before-after"},
          "USE CASES": {"before-after"}}
VOICE = ["赋能", "打通", "闭环", "抓手", "拉通", "组合拳", "打造", "未来可期", "令人兴奋", "激动人心",
         "惊艳", "重磅", "大幅", "显著", "大量", "彻底解决", "完美", "全面", "零问题", "革命性",
         "散乱", "低效", "容易出错", "混乱"]
_NUMBER = re.compile(r"^\s*(?:约|~|≈|≥|≤|>|<|\+/-)?\s*[$+\-]?\d")
MAX_PAGES = 10
NO_CONCLUSION = {"section", "agenda"}   # 按设计不放结论红条的版式（隔断页、目录页），不报缺结论行
EMU_PER_IN = 914400
BANNER_BOTTOM = EMU_PER_IN           # 模板顶部红 banner 占 0–1.0"（EMU）
FOOTER_TOP = int(7.25 * EMU_PER_IN)  # 母版页脚文本框上沿
REDRAW = "不要自己写代码画幻灯片；改 md 文稿后用 generate_ppt.py 重新生成"


def where(page):
    return f"页「{page.title}」"


def english(title):
    return title.split("/")[-1].strip().upper() if "/" in title else ""


def chinese(title):
    return title.split("/")[0].strip()


def page_text(page):
    return "\n".join([page.title, page.action_title, *page.lines, page.next])


def review_md(doc):
    """内容检查：只看文稿（版式字段由版式模块解析好）。返回 [(规则, 位置, 问题, 怎么改)]。"""
    issues = []
    pages = doc.pages
    if len(pages) > MAX_PAGES:
        issues.append(("页数过多", "整份文稿", f"{len(pages)} 页",
                       f"合并重复的页，控制在 {MAX_PAGES} 页以内"))
    for prev, page in zip(pages, pages[1:]):
        if prev.layout == page.layout:
            issues.append(("相邻两页版式相同", where(page),
                           f"和上一页「{prev.title}」都是 {page.layout}，连着看像同一页",
                           "合并两页，或给其中一页换更贴合内容的版式"))
    seen_steps = []
    for page in pages:
        title = page.action_title.strip()
        if len(title) < 8 or title == chinese(page.title):
            issues.append(("目录式副标题", where(page), f"副标题「{title}」没有给出结论",
                           "改成一句结论，如「试点 8 周，检验单全部电子化」"))
        if not page.conclusion and page.layout not in NO_CONCLUSION:
            issues.append(("缺结论行", where(page), "没有普通文字结论行，页底没有红条",
                           "在版式字段后加一行本页结论，最好带数字"))
        bad_layouts = MISFIT.get(english(page.title), set())
        if page.layout in bad_layouts:
            issues.append(("章节和版式不配", where(page),
                           f"{english(page.title)} 章节用了 {page.layout}",
                           "目标、范围写目标值和边界（stats / stats-side），流程和改前改后放到对应章节"))
        if page.layout == "process":
            names = {name for name, _ in page.fields["steps"]}
            for other_title, other in seen_steps:
                if len(names & other) * 2 >= min(len(names), len(other)):
                    issues.append(("内容重复", where(page),
                                   f"流程步骤和页「{other_title}」大半相同",
                                   "删掉重复的一页，或改写成不同的内容"))
            seen_steps.append((page.title, names))
        if page.layout in ("stats", "stats-side"):
            for item in page.fields["items"]:
                if "[数据缺失]" in item["value"]:
                    continue
                if not _NUMBER.match(item["value"]):
                    issues.append(("数字卡不是数字", where(page),
                                   f"卡片「{item['label']}」的数字栏是「{item['value']}」",
                                   "数字栏只放数字；文字内容改写进说明、结论要点或别的版式"))
        if page.layout in ("timeline", "timeline-phase"):
            keys = (page.fields["keys"] if page.layout == "timeline"
                    else [item[4] for item in page.fields["items"]])
            if len(keys) >= 3 and sum(keys) * 2 > len(keys):
                issues.append(("关键标记过多", where(page),
                               f"{sum(keys)}/{len(keys)} 个节点标了 !",
                               "只给 1–2 个真正关键的节点加 !"))
        text = page_text(page)
        if "[数据缺失]" in text:
            issues.append(("数据缺失", where(page), "有 [数据缺失] 占位",
                           "交付时告诉用户要补哪项数据；没有数据的指标不单独做数字卡"))
        words = [w for w in VOICE if w in text]
        if words:
            issues.append(("用词", where(page), "用了 " + "、".join(words),
                           "换成具体做了什么、结果是多少"))
    return issues


def review_pptx(doc, path):
    """真伪检查：pptx 是不是生成器按当前文稿做的——页数对得上，标题填在模板标题框
    （idx 0 / 10）里，banner 上没有另画的文本框。返回 [(规则, 位置, 问题, 怎么改)]。"""
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    slides = list(Presentation(path).slides)
    closing = 1 if doc.meta.get("closing", "").strip() or mdparse.is_monthly(doc.meta) else 0
    want = 1 + len(doc.pages) + closing
    issues = []
    if len(slides) != want:
        issues.append(("页数不符", "pptx", f"有 {len(slides)} 页，文稿应生成 {want} 页",
                       "用 generate_ppt.py 按当前文稿重新生成"))
    for n, (slide, page) in enumerate(zip(slides[1:], doc.pages), start=2):
        place = f"pptx 第 {n} 页（{where(page)}）"
        titles = {ph.placeholder_format.idx: ph.text_frame.text.strip()
                  for ph in slide.placeholders if ph.has_text_frame}
        if (titles.get(0) != page.title
                or (page.action_title and titles.get(10) != page.action_title)):
            issues.append(("不是生成脚本做的", place,
                           "主标题、副标题没有填进模板标题框（idx 0 / 10）", REDRAW))
        for sh in slide.shapes:
            if (sh.shape_type == MSO_SHAPE_TYPE.TEXT_BOX and sh.top is not None
                    and sh.top < BANNER_BOTTOM):
                issues.append(("不是生成脚本做的", place,
                               f"banner 上另画了文本框「{sh.name}」", REDRAW))
    return issues


def _inches(emu):
    return f'{emu / EMU_PER_IN:.2f}"'


def check_bounds(slide, width, height, place):
    """出界 / 压 banner / 压页脚。banner 里的模板标题框（idx 0 / 10）不算。"""
    issues = []
    for sh in slide.shapes:
        if sh.is_placeholder and sh.placeholder_format.idx in (0, 10):
            continue
        if None in (sh.left, sh.top, sh.width, sh.height):
            continue
        right, bottom = sh.left + sh.width, sh.top + sh.height
        name = f"形状「{sh.name}」"
        if sh.left < 0 or sh.top < 0 or right > width or bottom > height:
            issues.append(("出界", place, f"{name}超出页面",
                           "把它挪回页面内，或缩小尺寸"))
        elif sh.top < BANNER_BOTTOM:
            issues.append(("压 banner", place,
                           f"{name}上沿在 {_inches(sh.top)}，压住顶部 banner（0–1.0\"）",
                           "下移到 1.0\" 以下；标题只写进模板标题框"))
        elif bottom > FOOTER_TOP:
            issues.append(("压页脚", place,
                           f"{name}下沿在 {_inches(bottom)}，压住页脚（7.25\" 以下）",
                           "上移或缩小，下沿不超过 7.25\""))
    return issues


# 重叠容差：两个形状横、纵两个方向都压进对方超过它才算重叠。生成器坐标由浮点取整，
# 相邻形状（细线连到标记、卡片贴边）可能互相压进几个 EMU；0.02"（96 dpi 下约 2 像素）
# 远小于肉眼能看出的叠压，又能吸收取整误差。
OVERLAP_TOL = int(0.02 * EMU_PER_IN)
# 有意叠放的豁免（按形状名，和 references/layouts.md「审核的几何豁免」一致）：
OVERLAP_EXEMPT = {
    "Caption Bar",   # 底部红条叠在最上层，盖住内容区下沿属设计
    "Month Tag",     # 月份标识框 1.12–1.42"，下沿伸进内容区 0.12"；字只占框的右上角
}
OVERLAP_PAIRS = {("Current Ring", "Milestone"),  # 进行中节点的外圈套在节点上
                 }
_COMPONENT = re.compile(r"^(\S+) .*?(\d+)$")   # 「Process Card 2」→ 组件 (Process, 2)


def _component(name):
    m = _COMPONENT.match(name)
    return (m.group(1), m.group(2)) if m else None


def _overlap_exempt(a, b):
    if a.is_placeholder or b.is_placeholder or {a.name, b.name} & OVERLAP_EXEMPT:
        return True
    ca, cb = _component(a.name), _component(b.name)
    if ca is not None and ca == cb:
        return True
    return any((a.name == x and b.name.split()[0] == y) or (b.name == x and a.name.split()[0] == y)
               for x, y in OVERLAP_PAIRS)


def _placed(slide):
    return [sh for sh in slide.shapes if None not in (sh.left, sh.top, sh.width, sh.height)]


def check_overlap(slide, place):
    """形状矩形互压（豁免见 OVERLAP_EXEMPT / OVERLAP_PAIRS 和同一组件）。"""
    issues = []
    shapes = _placed(slide)
    for i, a in enumerate(shapes):
        for b in shapes[i + 1:]:
            dx = min(a.left + a.width, b.left + b.width) - max(a.left, b.left)
            dy = min(a.top + a.height, b.top + b.height) - max(a.top, b.top)
            if dx > OVERLAP_TOL and dy > OVERLAP_TOL and not _overlap_exempt(a, b):
                issues.append(("重叠", place,
                               f"形状「{a.name}」和「{b.name}」互相压住"
                               f"（横向 {_inches(dx)}、纵向 {_inches(dy)}）",
                               "挪开其中一个或缩小尺寸；文字放不下就精简文稿后重新生成"))
    return issues


# 错位阈值：同类形状（名字去掉编号后相同，如 Process Card 1–4）的上沿 / 中线 / 下沿
# （同一行）或左沿 / 中线 / 右沿（同一列）都没对齐、最近的差值小于它时报告。
# 5 像素（96 dpi，约 0.05"）：手工微调挪歪常见 1–4 像素，肉眼难发现、投影时明显；
# 生成器有意的错开（放大的关键节点、进行中的节点 / 阶段段）中线仍对齐，不会报。
PX_EMU = EMU_PER_IN // 96
MISALIGN_TOL = 5 * PX_EMU
# 差值不到半个像素视为对齐：生成器按浮点算坐标再取整，同类形状间实测有约 0.2 像素的误差，
# 屏幕上看不出来；挪动 1 像素及以上都会被报出。
ALIGN_SNAP = PX_EMU // 2
_NUMBERED = re.compile(r"^(.*\S) \d+$")


def _edges(sh, axis):
    if axis == "row":
        return sh.top, sh.top + sh.height // 2, sh.top + sh.height
    return sh.left, sh.left + sh.width // 2, sh.left + sh.width


def _near_miss(a, b, axis):
    """a、b 在 axis 方向三条边都没对齐、最近的差值小于 MISALIGN_TOL → 差值，否则 None。"""
    diffs = [abs(x - y) for x, y in zip(_edges(a, axis), _edges(b, axis))]
    if min(diffs) <= ALIGN_SNAP or min(diffs) >= MISALIGN_TOL:
        return None
    return min(diffs)


def _aligned(a, b, axis):
    return min(abs(x - y) for x, y in zip(_edges(a, axis), _edges(b, axis))) <= ALIGN_SNAP


def check_alignment(slide, place):
    """同类带编号形状差几像素没对齐。每个挪歪的形状报一次，和对齐得多的那个比。"""
    roles = {}
    for sh in _placed(slide):
        m = _NUMBERED.match(sh.name)
        if m and not sh.is_placeholder:
            roles.setdefault(m.group(1), []).append(sh)
    issues = []
    for group in roles.values():
        for axis, edge in (("row", "上沿"), ("col", "左沿")):
            score = {id(s): sum(_aligned(s, t, axis) for t in group if t is not s) for s in group}
            for s in group:
                for t in group:
                    diff = None if t is s else _near_miss(s, t, axis)
                    if diff is None or score[id(s)] > score[id(t)]:
                        continue
                    want = t.top if axis == "row" else t.left
                    issues.append(("错位", place,
                                   f"形状「{s.name}」和「{t.name}」差 {diff / PX_EMU:.1f} 像素没对齐",
                                   f"把「{s.name}」的{edge}对齐到 {_inches(want)}（和「{t.name}」一致）"))
                    break
    return issues


# 文字溢出：行高按字号 × 1.2 估算（和各版式警告用的 LINE_SPACING 同一口径），字宽用
# 生成器的 text_width_in。估算高度超出文本框可用高度（去掉内边距）OVERFLOW_TOL 以上才报：
# 正常稿里最紧的大数字框估算高度恰好等于框高，0.05" 吸收估算与取整误差。
LINE_HEIGHT = 1.2
OVERFLOW_TOL = int(0.05 * EMU_PER_IN)
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _list_style(sh):
    """文本框自带 lstStyle 第一级（红条的字号、行距、缩进写在这里）；没有返回 None。"""
    return sh.text_frame._txBody.find(f"{_A}lstStyle/{_A}lvl1pPr")


def _para_metrics(para, lvl1):
    """一段的 (各 run 的 (文字, 磅)、行距倍数、段前磅、左缩进 EMU)；字号读不到返回 None。"""
    default_pt = None
    spacing, indent = 1.0, 0
    if lvl1 is not None:
        rpr = lvl1.find(f"{_A}defRPr")
        if rpr is not None and rpr.get("sz"):
            default_pt = int(rpr.get("sz")) / 100
        pct = lvl1.find(f"{_A}lnSpc/{_A}spcPct")
        if pct is not None:
            spacing = int(pct.get("val")) / 100000
        indent = int(lvl1.get("marL", 0))
    runs = []
    for run in para.runs:
        pt = run.font.size.pt if run.font.size is not None else default_pt
        if pt is None:
            return None
        runs.append((run.text, pt))
    if isinstance(para.line_spacing, float):
        spacing = para.line_spacing
    before = para.space_before.pt if para.space_before is not None else 0
    return runs, spacing, before, indent


def _text_height_in(sh):
    """估算文字占的高度（英寸）；字号继承模板（占位框）读不到时返回 None，不估。"""
    tf = sh.text_frame
    width = sh.width - tf.margin_left - tf.margin_right
    lvl1 = _list_style(sh)
    total = 0.0
    for para in tf.paragraphs:
        m = _para_metrics(para, lvl1)
        if m is None:
            return None
        runs, spacing, before, indent = m
        if not runs:
            continue
        pt = max(p for _, p in runs)
        line_w = (width - indent) / EMU_PER_IN
        text_w = sum(text_width_in(t, p) for t, p in runs)
        lines = 1 if tf.word_wrap is False else max(1, -(-text_w // line_w))
        total += lines * pt * LINE_HEIGHT * spacing / 72 + before / 72
    return total


def check_overflow(slide, place):
    """文字估计溢出文本框（自己写了字号的文本框和形状；占位框按模板排，不估）。"""
    issues = []
    for sh in _placed(slide):
        if not sh.has_text_frame or not sh.text_frame.text.strip() or sh.is_placeholder:
            continue
        need = _text_height_in(sh)
        if need is None:
            continue
        tf = sh.text_frame
        room = (sh.height - tf.margin_top - tf.margin_bottom) / EMU_PER_IN
        if (need - room) * EMU_PER_IN > OVERFLOW_TOL:
            issues.append(("文字溢出", place,
                           f"形状「{sh.name}」的文字估计要 {need:.2f}\"高，框只有 {room:.2f}\"",
                           "精简文稿里对应的文字后重新生成；不要缩字号或拉大框挤进去"))
    return issues


def _cell_height_in(cell, width_emu):
    """单元格文字估算高度（英寸，含上下内边距）；字号读不到返回 None。"""
    tf = cell.text_frame
    width = (width_emu - cell.margin_left - cell.margin_right) / EMU_PER_IN
    total = (cell.margin_top + cell.margin_bottom) / EMU_PER_IN
    for para in tf.paragraphs:
        m = _para_metrics(para, None)
        if m is None:
            return None
        runs, spacing, before, _ = m
        if not runs:
            continue
        pt = max(p for _, p in runs)
        lines = max(1, -(-sum(text_width_in(t, p) for t, p in runs) // width))
        total += lines * pt * LINE_HEIGHT * spacing / 72 + before / 72
    return total


def check_table_overflow(slide, place):
    """原生表格（table 版式的 Data Table）：某行文字估计高过行高。PowerPoint 会把行撑高、
    表格往下长，压到红条或页脚；按和文本框同一口径估算，超出 OVERFLOW_TOL 才报。"""
    issues = []
    for sh in _placed(slide):
        if not getattr(sh, "has_table", False):
            continue
        tbl = sh.table
        for r, row in enumerate(tbl.rows):
            need = [_cell_height_in(tbl.cell(r, c), col.width)
                    for c, col in enumerate(tbl.columns)]
            need = max((n for n in need if n is not None), default=0)
            room = row.height / EMU_PER_IN
            if (need - room) * EMU_PER_IN > OVERFLOW_TOL:
                issues.append(("文字溢出", place,
                               f"形状「{sh.name}」第 {r + 1} 行的文字估计要 {need:.2f}\"高，"
                               f"行高只有 {room:.2f}\"",
                               "精简文稿里对应的单元格后重新生成；不要缩字号或拉高行挤进去"))
    return issues


def review_geometry(doc, path):
    """几何检查（只用 python-pptx 和计算）：逐页查正文页。返回 [(规则, 位置, 问题, 怎么改)]。"""
    from pptx import Presentation
    prs = Presentation(path)
    slides = list(prs.slides)
    issues = []
    for n, (slide, page) in enumerate(zip(slides[1:], doc.pages), start=2):
        place = f"pptx 第 {n} 页（{where(page)}）"
        issues += check_bounds(slide, prs.slide_width, prs.slide_height, place)
        issues += check_overlap(slide, place)
        issues += check_alignment(slide, place)
        issues += check_overflow(slide, place)
        issues += check_table_overflow(slide, place)
    return issues


def main(argv):
    if len(argv) not in (1, 2):
        print("用法: python3 review_deck.py deck.md [输出.pptx]", file=sys.stderr)
        return 1
    try:
        doc = mdparse.parse(argv[0])      # 解析时已按注册表把各页交给版式模块
    except DeckError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    issues = review_md(doc)
    if len(argv) == 2:
        try:
            issues += review_pptx(doc, argv[1])
        except Exception as e:   # 文件不存在、不是 pptx：python-pptx 抛的异常种类不一
            print(f"错误: 读不了 pptx {argv[1]}: {e}", file=sys.stderr)
            return 1
        issues += review_geometry(doc, argv[1])
    for rule, place, problem, fix in issues:
        print(f"[{rule}] {place}：{problem} → {fix}")
    print(f"REVIEW: {len(issues)} 条问题" if issues else "REVIEW OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
