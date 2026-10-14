"""自检：确认当前环境能用本技能包生成 pptx。

运行：python scripts/check_env.py（在技能目录下）
逐项打印 Python 版本、python-pptx、Pillow、公司模板，再用一份两页的小文稿实际生成一次；
全部通过时最后一行打印 OK，否则以非零退出码结束。
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "MS_Template.pptx")
SMOKE = """---
title: 自检文稿
---

# 自检 / CHECK
## 生成脚本可以运行
Layout: process
1. 读取文稿 | 解析 md
2. 套用模板 | 打开公司模板
3. 写出文件 | 保存 pptx
自检通过
"""


def main():
    ok = True
    print(f"Python {sys.version.split()[0]}")
    try:
        import pptx
        print(f"python-pptx {pptx.__version__}")
    except ImportError:
        print("python-pptx 不可用：当前环境不能生成 pptx")
        ok = False
    try:
        import PIL
        print(f"Pillow {PIL.__version__}")
    except ImportError:
        print("Pillow 不可用：多张图片按等宽排列（不影响生成）")
    if os.path.exists(TEMPLATE):
        print("公司模板 assets/MS_Template.pptx 存在")
    else:
        print("找不到公司模板 assets/MS_Template.pptx")
        ok = False
    if ok:
        work = tempfile.mkdtemp(prefix="milwaukee-ppt-check-")
        deck, out = os.path.join(work, "deck.md"), os.path.join(work, "check.pptx")
        with open(deck, "w", encoding="utf-8") as f:
            f.write(SMOKE)
        r = subprocess.run([sys.executable, os.path.join(HERE, "generate_ppt.py"), deck, "-o", out],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(out):
            print("试生成一份 2 页的 pptx：成功")
        else:
            print("试生成失败：" + (r.stderr.strip() or r.stdout.strip()))
            ok = False
    print("OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
