#!/usr/bin/env python3
"""检查 pptx：按页列出每个形状的名字、类型、位置大小（英寸）和文字前约 30 字。

用法：python3 inspect_ppt.py deck.pptx
输出：每页一个标题行 `== 第 N 页 | layout: <模板 layout 名> | 版式: <生成器版式名>`，
其下每个形状一行 `名字 | 类型 | L= T= W= H= | 文字`；占位框的类型写成 `PLACEHOLDER idx=N`。

生成器版式名不写进成稿（写进去会改动月报和旧写法的输出），而是从模板 layout 推断：
一个模板 layout 只对应一个版式时直接得出；stats / stats-side、timeline / timeline-phase
共用模板 layout，靠版式模块的 MARK_SHAPE（如 `Side Card 1`）区分。封面、收尾等非正文页为 `-`。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

EMU = 914400
TEXT_LEN = 30


def fail(msg):
    print(f"错误：{msg}", file=sys.stderr)
    sys.exit(1)


def inches(v):
    return "-" if v is None else f"{v / EMU:.2f}"


def shape_type(sh):
    try:
        t = sh.shape_type
    except Exception:
        t = None
    if t is None:
        return "PLACEHOLDER" if sh.is_placeholder else "UNKNOWN"
    return t.name if hasattr(t, "name") else str(t)


def shape_kind(sh):
    """类型列：占位框附上 idx（细调时按 idx 取占位框）。"""
    t = shape_type(sh)
    return f"{t} idx={sh.placeholder_format.idx}" if sh.is_placeholder else t


def generator_layout(prs, slide):
    """推断生成器版式名；认不出（封面、收尾、模板里没有对应版式的页）为 "-"。"""
    import layouts
    try:
        index = list(prs.slide_layouts).index(slide.slide_layout)
    except ValueError:
        return "-"
    candidates = [m for m in layouts.REGISTRY.values() if m.LAYOUT_INDEX == index]
    names = {sh.name for sh in slide.shapes}
    marked = [m for m in candidates if getattr(m, "MARK_SHAPE", None) in names]
    plain = [m for m in candidates if not getattr(m, "MARK_SHAPE", None)]
    found = marked or plain
    return found[0].NAME if len(found) == 1 else "-"


def shape_text(sh):
    if not getattr(sh, "has_text_frame", False):
        return ""
    return " ".join(sh.text_frame.text.split())[:TEXT_LEN]


def main(argv):
    if len(argv) != 2:
        fail("用法：inspect_ppt.py <deck.pptx>")
    path = Path(argv[1])
    if not path.is_file():
        fail(f"文件不存在：{path}")
    from pptx import Presentation
    try:
        prs = Presentation(str(path))
    except Exception as e:
        fail(f"不是有效的 pptx 文件：{path}（{type(e).__name__}）")
    for n, slide in enumerate(prs.slides, 1):
        print(f"== 第 {n} 页 | layout: {slide.slide_layout.name} "
              f"| 版式: {generator_layout(prs, slide)}")
        for sh in slide.shapes:
            print(f"{sh.name} | {shape_kind(sh)} | L={inches(sh.left)} "
                  f"T={inches(sh.top)} W={inches(sh.width)} H={inches(sh.height)} "
                  f"| {shape_text(sh)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
