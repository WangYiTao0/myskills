"""手工快测文件夹（runs/<轮次>/）里要粘贴的文件和源文件保持一致。

运行：python3 copilot-agent/tests/test_runs.py
"""
from contract import AGENT, check, finish, test_no_private_paths

RUNS = AGENT / "runs"
STEP1 = "1-先发-指令.txt"     # 第一条消息：指令全文 + 一句说明
STEP2 = "2-再发-题目.txt"     # 第二条消息：题目
SUFFIX = "\n\n以下对话按这份说明回答。\n"


def test_step_files():
    instructions = (AGENT / "instructions.md").read_text(encoding="utf-8")
    rounds = sorted(p.parent for p in RUNS.glob(f"*/{STEP1}"))
    check("至少有一轮手工快测文件夹", bool(rounds), rounds)
    for d in rounds:
        step1 = (d / STEP1).read_text(encoding="utf-8")
        check(f"{d.name}：{STEP1} = 当前 instructions.md + 说明句",
              step1 == instructions.rstrip("\n") + SUFFIX, d.name)
        step2 = d / STEP2
        check(f"{d.name}：有 {STEP2}", step2.exists() and step2.read_text(encoding="utf-8").strip())
        check(f"{d.name}：有步骤说明 README.md", (d / "README.md").exists())


if __name__ == "__main__":
    test_step_files()
    test_no_private_paths()
    finish()
