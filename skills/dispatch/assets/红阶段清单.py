#!/usr/bin/env python3
"""红阶段清单：把测试函数的 docstring 原样抄成一张清单，给用户看「这些红测试在钉什么」。

⚠️ 抄，不是总结。agent 重写一遍会和 assert 慢慢对不上，而且没人查得出来；
docstring 长在 assert 旁边，审核员对得上。

用法：
    python 红阶段清单.py <测试目录或文件> ...              # 全部测试
    python 红阶段清单.py <目录> --红 <pytest 输出文件>       # 只挑 FAILED / ERROR 那些
        （先 `uv run pytest -q --tb=no > /tmp/红.txt`，再把 /tmp/红.txt 喂进来）

输出里 ⛔ 开头的是没写 docstring 的，红阶段不许留着交给用户。
退出码：有 ⛔ 则 1，全都有 docstring 则 0 —— 可以直接当闸门用。
"""
import argparse
import ast
import pathlib
import re
import sys


def 收测试(路径: pathlib.Path):
    """一个 .py 文件里所有 test_ 开头的函数 → [(函数名, docstring 或 None)]"""
    树 = ast.parse(路径.read_text(encoding="utf-8"), filename=str(路径))
    出 = []
    for 节点 in ast.walk(树):
        if isinstance(节点, (ast.FunctionDef, ast.AsyncFunctionDef)) and 节点.name.startswith("test_"):
            出.append((节点.name, ast.get_docstring(节点)))
    return 出


def 读红名单(报告: pathlib.Path):
    """从 pytest 输出里挑出 FAILED / ERROR 的函数名（去掉 parametrize 的 [...]）"""
    名字 = set()
    for 行 in 报告.read_text(encoding="utf-8").splitlines():
        配 = re.match(r"(?:FAILED|ERROR)\s+\S+::([\w一-鿿]+)", 行.strip())
        if 配:
            名字.add(配.group(1))
    return 名字


def 主():
    解析 = argparse.ArgumentParser()
    解析.add_argument("路径", nargs="+")
    解析.add_argument("--红", type=pathlib.Path, help="pytest -q --tb=no 的输出文件；给了就只列红的")
    参数 = 解析.parse_args()

    红名单 = 读红名单(参数.红) if 参数.红 else None
    缺 = 0
    总 = 0
    for 原始 in 参数.路径:
        起点 = pathlib.Path(原始)
        文件们 = sorted(起点.rglob("test_*.py")) if 起点.is_dir() else [起点]
        for 文件 in 文件们:
            条目 = [(名, 文档) for 名, 文档 in 收测试(文件)
                    if 红名单 is None or 名 in 红名单]
            if not 条目:
                continue
            print(f"\n## {文件}")
            for 名, 文档 in 条目:
                总 += 1
                if 文档:
                    第一段 = " ".join(行.strip() for 行 in 文档.strip().splitlines() if 行.strip())
                    print(f"- {第一段}\n  （{名}）")
                else:
                    缺 += 1
                    print(f"- ⛔ 没写这条钉住什么：{名}")

    print(f"\n合计 {总} 条，其中 {缺} 条没写 docstring。")
    return 1 if 缺 else 0


if __name__ == "__main__":
    sys.exit(主())
