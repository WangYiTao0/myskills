#!/usr/bin/env python3
"""
Power Query Splitter - 将合并的 PQ 代码文件拆分为多个独立的 .m 文件

输入格式示例：
    // QueryName1
    let
        Source = ...
    in
        Result

    // QueryName2
    "= some expression" meta [...]

    // QueryName3
    let
        ...
    in
        ...

用法：
    python split_pq.py input.txt -o output_dir
    python split_pq.py input.txt                  # 默认输出到 ./pq_output/
"""

import argparse
import os
import re
import sys


def parse_pq_file(content: str) -> list[dict]:
    """
    解析合并的 PQ 文件，返回 [{name, code}, ...] 列表。

    识别规则：
    - 每个 query 以 `// QueryName` 行开头（name 可包含空格和中文）
    - query 的代码从注释行的下一行开始，到下一个 `// ...` 注释行之前结束
    """
    lines = content.replace('\r\n', '\n').split('\n')
    queries = []
    current_name = None
    current_lines = []

    # Pattern: line starts with // followed by the query name
    header_pattern = re.compile(r'^//\s+(.+)$')

    for line in lines:
        match = header_pattern.match(line)
        if match:
            # Save previous query if exists
            if current_name is not None:
                code = '\n'.join(current_lines).strip()
                if code:
                    queries.append({'name': current_name, 'code': code})
            current_name = match.group(1).strip()
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append(line)

    # Don't forget the last query
    if current_name is not None:
        code = '\n'.join(current_lines).strip()
        if code:
            queries.append({'name': current_name, 'code': code})

    return queries


def sanitize_filename(name: str) -> str:
    """将 query 名称转为安全的文件名（保留中文，替换特殊字符）"""
    # Replace characters that are invalid in filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Collapse multiple spaces/underscores
    sanitized = re.sub(r'[\s_]+', ' ', sanitized).strip()
    return sanitized


def split_pq(input_path: str, output_dir: str) -> list[str]:
    """
    主函数：读取输入文件，拆分并写出 .m 文件。
    返回生成的文件路径列表。
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return split_pq_from_text(content, output_dir)


def split_pq_from_text(content: str, output_dir: str) -> list[str]:
    """
    从文本内容拆分并写出 .m 文件。
    返回生成的文件路径列表。
    """
    queries = parse_pq_file(content)

    if not queries:
        print("⚠️  未检测到任何 Power Query 代码块。请确认格式：每个 query 以 '// QueryName' 开头。")
        return []

    os.makedirs(output_dir, exist_ok=True)

    created_files = []
    for q in queries:
        filename = sanitize_filename(q['name']) + '.m'
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(q['code'])
            f.write('\n')  # trailing newline

        created_files.append(filepath)
        print(f"  ✅ {filename}  ({len(q['code'])} chars)")

    print(f"\n🎉 共拆分出 {len(created_files)} 个 query 文件 → {output_dir}")
    return created_files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Power Query 代码拆分工具')
    parser.add_argument('input', help='合并的 PQ 代码文件路径')
    parser.add_argument('-o', '--output', default='./pq_output',
                        help='输出目录（默认: ./pq_output）')
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)

    split_pq(args.input, args.output)
