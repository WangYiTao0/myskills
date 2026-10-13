#!/usr/bin/env python3
"""现生成示例文稿用的示意图（色块 + 框 + 英文标签），不含任何真实截图。

用法：python3 make_images.py        # 写到同目录 img/ 下，已存在则覆盖
需要 Pillow。图是 16:9 的 1600×900（竖图 900×1200），调色板模式保存，体积小。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "img"

WHITE, PAPER, LINE = (255, 255, 255), (245, 245, 245), (208, 208, 208)
INK, MUTED, DARK = (26, 26, 26), (107, 107, 107), (51, 51, 51)
RED = (219, 1, 28)


def font(size):
    return ImageFont.load_default(size=size)


def canvas(size=(1600, 900), bg=WHITE):
    im = Image.new("RGB", size, bg)
    return im, ImageDraw.Draw(im)


def save(im, name):
    OUT.mkdir(exist_ok=True)
    im.convert("P", palette=Image.ADAPTIVE, colors=16).save(OUT / name, optimize=True)


def paper_log():
    """纸质登记本：表头 + 若干手写行，几行留空、一行划掉。"""
    im, d = canvas(bg=PAPER)
    d.rectangle([200, 80, 1400, 820], fill=WHITE, outline=LINE, width=4)
    d.text((240, 110), "TOOL CHECK-OUT LOG (paper)", font=font(44), fill=INK)
    cols = [240, 520, 860, 1120]
    for x, head in zip(cols, ["Date", "Tool", "Borrower", "Returned"]):
        d.text((x, 200), head, font=font(30), fill=MUTED)
    for i in range(9):
        y = 260 + i * 58
        d.line([240, y + 44, 1360, y + 44], fill=LINE, width=2)
        if i in (2, 5, 6):          # 空行：没登记归还
            continue
        for x, w in zip(cols, [160, 220, 180, 120]):
            d.rounded_rectangle([x, y + 10, x + w, y + 32], radius=8, fill=(190, 190, 190))
    d.line([520, 260 + 4 * 58 + 22, 1300, 260 + 4 * 58 + 22], fill=DARK, width=4)
    save(im, "paper-log.png")


def online_form():
    """线上借还表单：扫码框 + 三个字段 + 提交按钮。"""
    im, d = canvas()
    d.rectangle([0, 0, 1600, 90], fill=DARK)
    d.text((40, 24), "Tool Check-out  |  demo app", font=font(40), fill=WHITE)
    d.rectangle([80, 160, 620, 700], outline=LINE, width=4, fill=PAPER)
    d.rectangle([230, 310, 470, 550], outline=DARK, width=8)
    d.text((215, 600), "Scan tool QR", font=font(36), fill=MUTED)
    for i, label in enumerate(["Tool ID", "Borrower", "Due date"]):
        y = 170 + i * 170
        d.text((720, y), label, font=font(32), fill=MUTED)
        d.rectangle([720, y + 50, 1500, y + 120], outline=LINE, width=3)
        d.rounded_rectangle([740, y + 72, 740 + 260 - i * 50, y + 98], radius=8,
                            fill=(190, 190, 190))
    d.rectangle([720, 700, 1060, 790], fill=DARK)
    d.text((800, 725), "Submit", font=font(36), fill=WHITE)
    save(im, "online-form.png")


def dashboard():
    """借还看板：左侧柱状图 + 右侧三张数字卡，只有一处用红。"""
    im, d = canvas()
    d.text((60, 40), "Tool Usage Dashboard (mock)", font=font(44), fill=INK)
    d.rectangle([60, 130, 1000, 840], outline=LINE, width=3)
    for i, h in enumerate([260, 340, 300, 420, 380, 460]):
        x = 120 + i * 145
        d.rectangle([x, 800 - h, x + 90, 800], fill=(140, 140, 140) if i < 5 else DARK)
    d.line([100, 800, 980, 800], fill=MUTED, width=3)
    for i, (label, color) in enumerate([("On loan", INK), ("Overdue", RED), ("Idle", INK)]):
        y = 130 + i * 245
        d.rectangle([1060, y, 1540, y + 215], fill=PAPER)
        d.text((1090, y + 25), label, font=font(30), fill=MUTED)
        d.rounded_rectangle([1090, y + 90, 1090 + 200, y + 170], radius=10, fill=color)
    save(im, "dashboard.png")


def main():
    paper_log()
    online_form()
    dashboard()
    print(f"已生成示意图: {OUT}")


if __name__ == "__main__":
    main()
