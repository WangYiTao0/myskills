"""验证模板 assets/MS_Template.pptx 的版式契约（票 #13）。

- 共 8 个 layout；0–2 与基线（git e2cbdea，追加新版式之前）逐项一致；前 3 张样例页不动。
- 3 是 Before / After：按内部月报的 Before/After 排布改过几何（票 #14 后续修正）——
  对比框缩矮、caption 紧贴框下、给底部结论条留位置；第 4 张样例页随之更新。
- 4–7 是 Process / Stats / Timeline / Image + Text：idx 0/10 与 layout 0 同位置，
  命名 BODY 槽位在 banner 以下、红条最高位以上，左右边距不小于 0.5 英寸。
- 新 layout 不预画形状（只有占位框），banner 以外没有新增红色。

运行：python3 skills/milwaukee-ppt/tests/test_template_layouts.py
"""
import io
import re
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.util import Emu

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "MS_Template.pptx"
REPO = SKILL.parent.parent
BASELINE_REV = "e2cbdea"
BASELINE_PATH = "skills/milwaukee-ppt/assets/MS_Template.pptx"

EMU_IN = 914400
SLIDE_W_IN = 13.333
BANNER_BOTTOM_IN = 1.0
SLOT_BOTTOM_LIMIT_IN = 5.6  # 证据页红条最高位（=图片区底缘），槽位不能压到它下面
MIN_MARGIN_IN = 0.5

# layout 3「Before / After」的几何（英寸，L / T / W / H），见 references/before-after.md
LAYOUT3_PLACEHOLDERS = {
    0: None, 10: None,                       # 沿用 layout 0
    11: ("Before Title", (2.035, 1.80, 2.90, 0.42)),
    12: ("After Title", (8.395, 1.80, 2.90, 0.42)),
    13: ("Before Content", (0.66, 2.42, 5.65, 2.99)),
    14: ("After Content", (7.02, 2.42, 5.65, 2.99)),
    15: ("Before Caption", (0.61, 5.57, 5.80, 0.58)),
    16: ("After Caption", (6.97, 5.57, 5.80, 0.58)),
}
LAYOUT3_SHAPES = {
    "Before Frame": (0.56, 2.32, 5.85, 3.19),
    "After Frame": (6.92, 2.32, 5.85, 3.19),
    "Conversion": (6.43, 3.665, 0.47, 0.50),
}
CONCLUSION_BAR_IN = (0.56, 6.43, 12.21, 0.55)   # 结论条（生成器画，样例页同位置）
FOOTER_TOP_IN = 7.25

# index -> (名字, {idx: 槽位名})
NEW_LAYOUTS = {
    4: ("Process", {17: "Process Area"}),
    5: ("Stats", {18: "Stats Area"}),
    6: ("Timeline", {19: "Timeline Area"}),
    7: ("Image + Text", {20: "Image Frame", 21: "Text Area"}),
}

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def geom(shape):
    return (shape.left, shape.top, shape.width, shape.height)


def describe_layout(layout):
    return (layout.name, sorted(
        (ph.placeholder_format.idx, ph.name, geom(ph)) for ph in layout.placeholders))


def load_baseline():
    blob = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{BASELINE_REV}:{BASELINE_PATH}"],
        check=True, capture_output=True).stdout
    return Presentation(io.BytesIO(blob))


def is_grey(hex6):
    r, g, b = hex6[0:2], hex6[2:4], hex6[4:6]
    return r == g == b


base = load_baseline()
prs = Presentation(str(TEMPLATE))
layouts = list(prs.slide_layouts)

# 1. 一共 8 个 layout
check(len(layouts) == 8, f"layout 数应为 8，实际 {len(layouts)}")

# 2. layout 0–2 与基线一致
for i, old in enumerate(base.slide_layouts):
    if i >= len(layouts) or i == 3:
        continue
    check(describe_layout(layouts[i]) == describe_layout(old),
          f"layout {i} 与基线不一致：{describe_layout(layouts[i])} != {describe_layout(old)}")

# 3. 前 3 张样例页不动（版式名与 XML 完全一致）；第 4 张见下方 layout 3 检查
check(len(prs.slides) == len(base.slides), f"样例页数应为 {len(base.slides)}，实际 {len(prs.slides)}")
for i, (new_s, old_s) in enumerate(list(zip(prs.slides, base.slides))[:3]):
    check(new_s.slide_layout.name == old_s.slide_layout.name, f"样例页 {i} 版式变了")
    check(new_s.part.blob == old_s.part.blob, f"样例页 {i} 内容变了")

# 3b. layout 3 Before / After：新几何
def inch(v):
    return round(v / EMU_IN, 3)


def ginch(shape):
    return tuple(inch(v) for v in geom(shape))


lay3 = layouts[3]
check(lay3.name == "Before / After", f"layout 3 名字是 {lay3.name!r}")
ref0 = {ph.placeholder_format.idx: geom(ph) for ph in layouts[0].placeholders}
phs3 = {ph.placeholder_format.idx: ph for ph in lay3.placeholders}
check(set(phs3) == set(LAYOUT3_PLACEHOLDERS), f"layout 3 占位框 idx：{sorted(phs3)}")
for idx, spec in LAYOUT3_PLACEHOLDERS.items():
    ph = phs3.get(idx)
    if ph is None:
        continue
    if spec is None:
        check(geom(ph) == ref0[idx], f"layout 3 idx {idx} 与 layout 0 位置不同")
        continue
    name, box = spec
    check(ph.name == name, f"layout 3 idx {idx} 名字是 {ph.name!r}，应为 {name!r}")
    check(ginch(ph) == box, f"layout 3 {name} 几何 {ginch(ph)} != {box}")
shapes3 = {s.name: s for s in lay3.shapes if not s.is_placeholder}
check(set(shapes3) == set(LAYOUT3_SHAPES), f"layout 3 预画形状：{sorted(shapes3)}")
for name, box in LAYOUT3_SHAPES.items():
    if name in shapes3:
        check(ginch(shapes3[name]) == box, f"layout 3 {name} 几何 {ginch(shapes3[name])} != {box}")
for name in ("Before Frame", "After Frame"):
    ln = shapes3[name]._element.find(".//{*}spPr/{*}ln") if name in shapes3 else None
    clr = ln.find("./{*}solidFill/{*}srgbClr") if ln is not None else None
    check(ln is not None and ln.get("w") == "9525" and clr is not None
          and clr.get("val") == "000000", f"layout 3 {name} 不是黑色 0.75pt 细框")
# caption 紧贴框下、最多两行（槽内换行，顶对齐），结论条在 caption 之下、页脚之上
for idx in (15, 16):
    body = phs3[idx]._element.find(".//{*}txBody/{*}bodyPr")
    check(body is not None and body.get("wrap") == "square" and body.get("anchor") == "t",
          f"layout 3 idx {idx} caption 应换行且顶对齐")
cap_bottom = max(inch(phs3[i].top + phs3[i].height) for i in (15, 16))
frame_bottom = max(inch(s.top + s.height) for n, s in shapes3.items() if "Frame" in n)
check(0 <= phs3[15].top / EMU_IN - frame_bottom <= 0.1, "caption 没有紧贴对比框下方")
l, t, w, h = CONCLUSION_BAR_IN
check(cap_bottom < t and t + h < FOOTER_TOP_IN, "结论条位置压 caption 或页脚")

# 3c. 第 4 张样例页：用 layout 3，槽位与 layout 同位置，填写提示干净，结论条在新位置
s4 = prs.slides[3]
check(s4.slide_layout.name == "Before / After", "样例页 4 不是 Before / After")
for ph in s4.placeholders:
    idx = ph.placeholder_format.idx
    if idx in phs3:
        check(geom(ph) == geom(phs3[idx]), f"样例页 4 idx {idx} 与 layout 3 位置不同")
sample = {s.name: s for s in s4.shapes if not s.is_placeholder}
check(set(sample) == {"Lead", "Conclusion"}, f"样例页 4 文本框：{sorted(sample)}")
if "Conclusion" in sample:
    c = sample["Conclusion"]
    check(ginch(c) == CONCLUSION_BAR_IN, f"样例页 4 结论条几何 {ginch(c)}")
    fill = c._element.find("./{*}spPr/{*}solidFill/{*}srgbClr")
    check(fill is not None and fill.get("val") == "DB011C", "样例页 4 结论条不是品牌红底")
    check("占位" in c.text_frame.text, f"样例页 4 结论条不是填写提示：{c.text_frame.text!r}")

# 4. 新 layout
ref = {ph.placeholder_format.idx: geom(ph) for ph in layouts[0].placeholders}
for index, (name, slots) in NEW_LAYOUTS.items():
    if index >= len(layouts):
        failures.append(f"缺少 layout {index}（{name}）")
        continue
    lay = layouts[index]
    tag = f"layout {index}（{name}）"
    check(lay.name == name, f"{tag} 名字是 {lay.name!r}")

    phs = {ph.placeholder_format.idx: ph for ph in lay.placeholders}
    for idx in (0, 10):
        check(idx in phs and geom(phs[idx]) == ref[idx], f"{tag} idx {idx} 与 layout 0 位置不同")
    check(set(phs) == {0, 10, *slots}, f"{tag} 占位框 idx 应为 {{0, 10, {sorted(slots)}}}，实际 {sorted(phs)}")

    # 不预画形状：layout 上只有占位框
    extra = [s.name for s in lay.shapes if not s.is_placeholder]
    check(not extra, f"{tag} 预画了非占位框形状：{extra}")

    for idx, slot_name in slots.items():
        ph = phs.get(idx)
        if ph is None:
            continue
        check(ph.name == slot_name, f"{tag} idx {idx} 名字是 {ph.name!r}，应为 {slot_name!r}")
        check(ph.placeholder_format.type == PP_PLACEHOLDER.BODY, f"{tag} idx {idx} 不是 BODY")
        l, t, w, h = (v / EMU_IN for v in geom(ph))
        check(t >= BANNER_BOTTOM_IN, f"{tag} {slot_name} 顶边 {t:.3f} 压 banner")
        check(t + h <= SLOT_BOTTOM_LIMIT_IN + 1e-6, f"{tag} {slot_name} 底边 {t + h:.3f} 超过 {SLOT_BOTTOM_LIMIT_IN}")
        check(l >= MIN_MARGIN_IN, f"{tag} {slot_name} 左边距 {l:.3f} < 0.5")
        check(SLIDE_W_IN - (l + w) >= MIN_MARGIN_IN, f"{tag} {slot_name} 右边距 {SLIDE_W_IN - (l + w):.3f} < 0.5")

        # 槽位文字必须自带非红色：母版正文默认是红色 Wingdings 项目符号
        lvl1 = ph._element.find(".//{*}lstStyle/{*}lvl1pPr")
        check(lvl1 is not None, f"{tag} {slot_name} 没有 lvl1pPr 样式")
        if lvl1 is not None:
            fill = lvl1.find("./{*}defRPr/{*}solidFill/{*}srgbClr")
            check(fill is not None and is_grey(fill.get("val")), f"{tag} {slot_name} 文字没有显式灰阶颜色")
            sz = lvl1.find("./{*}defRPr")
            check(sz is not None and int(sz.get("sz", "0")) >= 1200, f"{tag} {slot_name} 字号 < 12pt")
            bu_none = lvl1.find("./{*}buNone") is not None
            bu_clr = lvl1.find("./{*}buClr/{*}srgbClr")
            check(bu_none or (bu_clr is not None and is_grey(bu_clr.get("val"))),
                  f"{tag} {slot_name} 项目符号会继承母版红色")

    # banner 以外没有新增红色：整份 layout XML 只允许灰阶 srgb 与 bg1/tx1（白/黑）
    xml = lay.part.blob.decode("utf-8")
    colors = set(re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', xml))
    check(all(is_grey(c) for c in colors), f"{tag} 出现非灰阶颜色：{sorted(colors)}")
    schemes = set(re.findall(r'schemeClr val="(\w+)"', xml))
    check(schemes <= {"bg1", "tx1"}, f"{tag} 引用了主题色：{sorted(schemes)}")

if failures:
    print("FAIL")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("OK：8 个 layout，0–2 与前 3 张样例页未变，layout 3 新几何与样例页 4、4 个新 layout 契约满足")
