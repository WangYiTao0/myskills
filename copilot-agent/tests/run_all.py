"""跑 tests 目录下所有 test_*.py（各自是独立脚本），任一失败则非零退出。

运行：python3 copilot-agent/tests/run_all.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    failed = []
    for test in sorted(HERE.glob("test_*.py")):
        print(f"=== {test.name}", flush=True)
        r = subprocess.run([sys.executable, str(test)], cwd=HERE)
        if r.returncode != 0:
            failed.append(test.name)
    print()
    if failed:
        print("失败：" + ", ".join(failed))
        sys.exit(1)
    print("所有检查通过")


if __name__ == "__main__":
    main()
