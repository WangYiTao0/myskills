"""milwaukee-ppt 测试共用辅助：所有测试只走“md 进、pptx 出”这一个切入点。

各版式测试文件（test_<版式>.py）都 `from deckcheck import *` 后使用：

- generate(md, images=...)      写文稿 + 现生成纯色图 → 调生成器 → Result
                                （probe=True 额外注册测试专用版式 _probe，见 probe_layout.py）
- open_pptx(path)               打开生成结果
- placeholder(slide, idx)       按 idx 取占位框（没有返回 None）
- out_of_bounds(prs, slides)    超出页面 / 压 banner / 压页脚的形状
- red_elements(slide)           用了红色（填充、描边、文字）的形状名
- body_slide / pictures / shapes_named / run_style / run_styles / emu_rect
- caption_bar / tag_texts / paragraphs / caption_style_problems / warnings
- runs(shape, para)             一段里每个 run 的 (文字, 字号, 粗体, 颜色)，查数字 / 单位拆分
- fill_color / line_color / geometry(shape)   纯色填充 / 描边 hex、预设几何名（ellipse、diamond…）
- inside(shape, rect_in)        形状落在英寸矩形（如 CONTENT_SLOT_IN）内
- inside_shape(inner, outer)    形状整个落在另一个形状里
- center_x / center_y / bottom(shape)   中心横 / 纵坐标、底边（EMU）
- named(slide, name)            名字恰为 name 的全部形状；one(slide, name) 恰好一个时返回它，否则 None
- slide_xmls(path)              各页 slide XML 字节，和改动前的输出逐字节比较
- deck_error(r, title, *needles) 报错退出且信息含页标题（和 needles）
- review(md, pptx=None)         调审核脚本 review_deck.py → (退出码, stdout, stderr)
- registered_layouts()          生成器注册表里的全部版式名（从未知版式的报错信息里读）
- 常量：STATUS_COLORS / DONE_GREEN / DOING_AMBER / DOING_INK、UNIT_PT / UNIT_COLOR
- check(name, ok, detail) 记录结果；finish() 打印汇总并按结果退出
"""
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

SKILL = Path(__file__).resolve().parent.parent
GENERATOR = SKILL / "scripts" / "generate_ppt.py"
REVIEWER = SKILL / "scripts" / "review_deck.py"
TEMPLATE = SKILL / "assets" / "MS_Template.pptx"

EMU = 914400
BANNER_BOTTOM = EMU            # 母版红 banner 占顶部 1.0"
FOOTER_TOP = int(7.25 * EMU)   # 母版页脚文本框上沿

# 原月报红条：底边固定在 5379048 + 1097952 EMU，最小高度 1097952，左 155575，宽 11874874
CAPTION_BOTTOM = 6477000
CAPTION_MIN_CY = 1097952

BRAND_RED = "DB011C"
# 视为“红色”的颜色：品牌红 + 常见纯红/深红，防止有人另起一个红
RED_COLORS = {BRAND_RED, "FF0000", "C00000", "E3000F", "D0021B", "CC0000"}

# 时间线状态色（spec #20）：未完成用品牌红，只描边、不实心填充
DONE_GREEN, DOING_AMBER, DOING_INK = "2E7D32", "F2A900", "1A1A1A"
STATUS_COLORS = {"done": DONE_GREEN, "doing": DOING_AMBER, "todo": BRAND_RED}
UNIT_PT, UNIT_COLOR = 28, "6B6B6B"   # 数字后的单位：28pt 灰色、不加粗

LAYOUT_INDEX = {"evidence": 0, "before-after": 3, "process": 4, "stats": 5,
                "stats-side": 5, "timeline": 6, "timeline-phase": 6, "image-text": 7}

# 模板槽位（英寸，L / T / W / H；#13 定稿）
CONTENT_SLOT_IN = (0.56, 1.30, 12.21, 4.30)   # process 17 / stats 18 / timeline 19
IMAGE_FRAME_IN = (0.56, 1.30, 7.64, 4.30)     # image-text 20（16:9 图框）

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

FAILS = []


def check(name, ok, detail=""):
    print(("✓ " if ok else "✗ ") + name + ("" if ok else f"  —— {detail}"))
    if not ok:
        FAILS.append(name)


def finish():
    print()
    if FAILS:
        print(f"{len(FAILS)} 项失败")
        sys.exit(1)
    print("全部通过")


def make_image(path, size=(1600, 900), color=(120, 120, 120)):
    from PIL import Image
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


@dataclass
class Result:
    rc: int
    stdout: str
    stderr: str
    prs: object        # Presentation 或 None（失败 / 没指定 -o）
    path: Path         # 输出文件路径（-o 时）
    workdir: Path

    @property
    def slides(self):
        return list(self.prs.slides) if self.prs is not None else []


# probe=True 时用它代替直接跑生成器：argv = [scripts 目录, tests 目录, 生成器参数...]
_PROBE_RUNNER = """
import sys
scripts, tests = sys.argv[1], sys.argv[2]
sys.path[:0] = [scripts, tests]
import layouts, probe_layout, generate_ppt
layouts.REGISTRY[probe_layout.NAME] = probe_layout
sys.exit(generate_ppt.main(sys.argv[3:]))
"""
HERE = Path(__file__).resolve().parent


def generate(md_text, workdir=None, images=None, out_name="out.pptx", use_o=True,
             env=None, probe=False):
    """写文稿 deck.md → 调生成器 → Result。

    images: {相对路径: (宽, 高)} 或 {相对路径: ((宽, 高), (r, g, b))}，现生成纯色图。
    workdir 不传时用一个新临时目录（进程结束前不清理，便于调试）。
    env: 追加给生成器进程的环境变量（如 MILWAUKEE_PPT_CACHE）。
    probe: True 时额外注册测试专用版式 `_probe`（tests/probe_layout.py），只给
           test_common_parts.py 测共用部件用。
    """
    workdir = Path(workdir or tempfile.mkdtemp(prefix="mppt-test-"))
    for rel, spec in (images or {}).items():
        size, color = (spec if isinstance(spec[0], tuple)
                       else (spec, (120, 120, 120)))
        make_image(workdir / rel, size, color)
    md = workdir / "deck.md"
    md.write_text(textwrap.dedent(md_text).lstrip(), encoding="utf-8")
    cmd = ([sys.executable, "-c", _PROBE_RUNNER, str(GENERATOR.parent), str(HERE)]
           if probe else [sys.executable, str(GENERATOR)]) + [str(md)]
    out = workdir / out_name
    if use_o:
        cmd += ["-o", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       env={**os.environ, **env} if env else None)
    prs = open_pptx(out) if use_o and out.exists() else None
    return Result(r.returncode, r.stdout, r.stderr, prs, out, workdir)


def open_pptx(path):
    return Presentation(str(path))


def placeholder(slide, idx):
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    return None


def body_slide(r, n=1):
    """第 n 页（默认封面后的第一页正文）；没有就返回 None。"""
    return r.slides[n] if len(r.slides) > n else None


def pictures(slide):
    return [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]


def shapes_named(slide, prefix):
    """名字为「prefix N」的形状，按 N 排序（如 "Stat Card" → Stat Card 1, 2, …）。"""
    found = []
    for sh in slide.shapes:
        m = re.fullmatch(re.escape(prefix) + r" (\d+)", sh.name)
        if m:
            found.append((int(m.group(1)), sh))
    return [sh for _, sh in sorted(found, key=lambda x: x[0])]


def emu_rect(rect_in):
    """英寸的 (L, T, W, H) → EMU 整数。"""
    return tuple(int(v * EMU) for v in rect_in)


def _font_style(run):
    f = run.font
    color = str(f.color.rgb) if f.color and f.color.type is not None else None
    return (f.size.pt if f.size else None, bool(f.bold), color)


def run_style(shape, para=0):
    """第 para 段第一个 run 的 (字号 pt, 是否粗体, 颜色 hex)。"""
    return _font_style(shape.text_frame.paragraphs[para].runs[0])


def run_styles(shape):
    """文本框里所有 run 的 (字号 pt, 是否粗体, 颜色 hex) 集合，便于断言“全部一致”。"""
    return {_font_style(r) for p in shape.text_frame.paragraphs for r in p.runs}


def runs(shape, para=0):
    """第 para 段每个 run 的 (文字, 字号 pt, 是否粗体, 颜色 hex)，按顺序（查数字 / 单位拆分）。"""
    return [(r.text, *_font_style(r)) for r in shape.text_frame.paragraphs[para].runs]


def fill_color(shape):
    """形状自身 spPr 的纯色填充 hex；无填充 / 非纯色返回 None。"""
    el = shape._element.find(f".//{P}spPr/{A}solidFill/{A}srgbClr")
    return el.get("val").upper() if el is not None else None


def line_color(shape):
    """形状描边的纯色 hex；没写描边颜色或 noFill 返回 None。"""
    ln = shape._element.find(f".//{P}spPr/{A}ln")
    if ln is None:
        return None
    el = ln.find(f"{A}solidFill/{A}srgbClr")
    return el.get("val").upper() if el is not None else None


def geometry(shape):
    """预设几何名，如 "ellipse"、"diamond"、"rect"、"homePlate"、"chevron"；没有返回 None。"""
    el = shape._element.find(f".//{A}prstGeom")
    return el.get("prst") if el is not None else None


def inside(shape, rect_in, tol_in=0.01):
    """形状整个落在英寸矩形 (L, T, W, H) 内（容差 tol_in 英寸），如槽位 CONTENT_SLOT_IN。"""
    l, t, w, h = (v * EMU for v in rect_in)
    tol = tol_in * EMU
    return (shape.left >= l - tol and shape.top >= t - tol
            and shape.left + shape.width <= l + w + tol
            and shape.top + shape.height <= t + h + tol)


def inside_shape(inner, outer):
    """inner 整个落在 outer 的外框里（如卡片里的数字框）。"""
    return (inner.left >= outer.left and inner.top >= outer.top
            and inner.left + inner.width <= outer.left + outer.width
            and inner.top + inner.height <= outer.top + outer.height)


def center_x(sh):
    return sh.left + sh.width // 2


def center_y(sh):
    return sh.top + sh.height // 2


def bottom(sh):
    return sh.top + sh.height


def named(slide, name):
    """名字恰为 name 的全部形状（不带编号的名字，如 "Current Tag"）。"""
    return [sh for sh in slide.shapes if sh.name == name]


def one(slide, name):
    """名字恰为 name 的形状恰好一个时返回它，否则 None。"""
    found = named(slide, name)
    return found[0] if len(found) == 1 else None


def texts(slide):
    return [sh.text_frame.text for sh in slide.shapes if sh.has_text_frame]


def warnings(stderr):
    return [ln for ln in stderr.splitlines() if ln.startswith("警告")]


def out_of_bounds(prs, slides, skip_title_placeholders=True):
    """所有形状须在页面内、不压 banner（顶部 1.0"）和页脚。返回违规的 "第N页 形状名"。

    slides 是 (页码, slide) 序列或 slide 列表；banner 里的 idx 0/10 标题占位框默认跳过。
    """
    bad = []
    for n, s in (slides if slides and isinstance(slides[0], tuple)
                 else enumerate(slides, start=1)):
        for sh in s.shapes:
            if (skip_title_placeholders and sh.is_placeholder
                    and sh.placeholder_format.idx in (0, 10)):
                continue
            if not (sh.left >= 0 and sh.left + sh.width <= prs.slide_width
                    and sh.top >= BANNER_BOTTOM
                    and sh.top + sh.height <= FOOTER_TOP):
                bad.append(f"第{n}页 {sh.name}")
    return bad


def red_elements(slide):
    """用了红色的形状名（看形状自身 XML 里的 srgbClr：填充、描边、文字都算）。"""
    out = []
    for sh in slide.shapes:
        vals = {e.get("val", "").upper() for e in sh._element.iter(f"{A}srgbClr")}
        if vals & RED_COLORS:
            out.append(sh.name)
    return out


def caption_bar(slide):
    for sh in slide.shapes:
        if sh.name == "Caption Bar":
            return sh
    return None


def tag_shape(slide):
    for sh in slide.shapes:
        if sh.name == "Month Tag":
            return sh
    return None


def tag_texts(slide):
    """非占位框、非红条的文本框文字（证据页上只有月份标识会是这种）。"""
    return [sh.text_frame.text for sh in slide.shapes
            if sh.has_text_frame and not sh.is_placeholder
            and sh.name != "Caption Bar" and sh.text_frame.text]


def paragraphs(shape):
    return [p.text for p in shape.text_frame.paragraphs if p.text]


def caption_style_problems(sh):
    """红条与月报模板固定样式的差异；空列表表示一致。"""
    el = sh._element
    out = []
    if sh.left != 155575 or sh.width != 11874874:
        out.append(f"x/宽 {sh.left}/{sh.width}")
    if sh.top + sh.height != CAPTION_BOTTOM:
        out.append(f"底边 {sh.top + sh.height}")
    if sh.height < CAPTION_MIN_CY:
        out.append(f"高 {sh.height} 小于原版")
    fill = el.find(f".//{P}spPr/{A}solidFill/{A}srgbClr")
    if fill is None or fill.get("val") != BRAND_RED:
        out.append("底色不是 DB011C")
    ln = el.find(f".//{A}ln")
    if (ln is None or ln.get("w") != "9525"
            or ln.find(f"{A}solidFill/{A}schemeClr").get("val") != "tx1"):
        out.append("描边不是 0.75pt 黑")
    lvl1 = el.find(f".//{A}lstStyle/{A}lvl1pPr")
    if lvl1 is None:
        return out + ["缺 lvl1pPr"]
    if lvl1.find(f"{A}lnSpc/{A}spcPct").get("val") != "150000":
        out.append("行距不是 150%")
    if (lvl1.find(f"{A}buFont").get("typeface") != "Wingdings"
            or lvl1.find(f"{A}buChar").get("char") != "v"):
        out.append("项目符号不是 Wingdings ❖")
    rpr = lvl1.find(f"{A}defRPr")
    if (rpr.get("sz") != "1400"
            or rpr.find(f"{A}solidFill/{A}schemeClr").get("val") != "bg1"):
        out.append("文字不是白色 14pt")
    if el.find(f".//{A}bodyPr").get("anchor") != "ctr":
        out.append("不是垂直居中")
    return out


def slide_parts(pptx_path):
    import zipfile
    with zipfile.ZipFile(pptx_path) as z:
        return [n for n in z.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]


def slide_xmls(pptx_path):
    """{"ppt/slides/slideN.xml": 字节}，用来和改动前的输出逐字节比较。"""
    import zipfile
    with zipfile.ZipFile(pptx_path) as z:
        return {n: z.read(n) for n in slide_parts(pptx_path)}


def deck_error(r, title, *needles):
    """生成器报错退出，错误信息含页标题和 needles 里的每一段文字。"""
    return r.rc != 0 and title in r.stderr and all(s in r.stderr for s in needles)


def review(md, pptx=None):
    """跑审核脚本：md、pptx 为路径（pptx 可省略，只审文稿）→ CompletedProcess（rc / stdout / stderr）。"""
    cmd = [sys.executable, str(REVIEWER), str(md)] + ([str(pptx)] if pptx is not None else [])
    return subprocess.run(cmd, capture_output=True, text=True)


def registered_layouts():
    """生成器注册表里的全部版式名，按注册顺序。只走外部切入点：写一个未知版式，
    从报错信息「可选: a / b / …」里读出来；新版式登记进注册表后自动出现在这里。"""
    r = generate("""
        ---
        title: 注册表探测
        ---
        # 探测页
        Layout: __no_such_layout__
        """)
    m = re.search(r"可选: (.+)$", r.stderr, re.M)
    if r.rc == 0 or not m:
        raise RuntimeError(f"读不到注册表: {r.stderr}")
    return [name.strip() for name in m.group(1).split(" / ")]
