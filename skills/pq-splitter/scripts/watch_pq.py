#!/usr/bin/env python3
"""
Power Query Watcher - 监听指定文件，变更时自动拆分 PQ 代码

用法：
    python watch_pq.py myqueries.txt -o ./pq_output
    python watch_pq.py myqueries.txt                   # 默认输出到 ./pq_output/

依赖：
    pip install watchdog
"""

import argparse
import sys
import time
import os

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ 需要安装 watchdog: pip install watchdog")
    sys.exit(1)

from split_pq import split_pq


class PQFileHandler(FileSystemEventHandler):
    def __init__(self, target_file: str, output_dir: str):
        self.target_file = os.path.abspath(target_file)
        self.output_dir = output_dir

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == self.target_file:
            print(f"\n🔄 检测到文件变更: {event.src_path}")
            print(f"   {time.strftime('%H:%M:%S')} 重新拆分中...")
            try:
                split_pq(self.target_file, self.output_dir)
            except Exception as e:
                print(f"   ❌ 拆分失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='监听 PQ 文件变更并自动拆分')
    parser.add_argument('input', help='要监听的合并 PQ 代码文件')
    parser.add_argument('-o', '--output', default='./pq_output',
                        help='输出目录（默认: ./pq_output）')
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)

    # Run once immediately
    print(f"👀 首次拆分 {args.input} ...")
    split_pq(args.input, args.output)

    # Start watching
    watch_dir = os.path.dirname(os.path.abspath(args.input))
    handler = PQFileHandler(args.input, args.output)
    observer = Observer()
    observer.schedule(handler, watch_dir, recursive=False)
    observer.start()

    print(f"\n👀 正在监听 {args.input} 的变更...")
    print("   按 Ctrl+C 停止\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 已停止监听")
    observer.join()


if __name__ == '__main__':
    main()
