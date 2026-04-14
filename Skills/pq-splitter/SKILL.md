---
name: pq-splitter
description: >
  将 Power BI 中复制出的合并 Power Query 代码拆分为多个独立的 .m 文件。
  当用户提到"拆分PQ"、"拆分Power Query"、"PQ代码拆分"、"split pq"、
  "把PQ拆成多个文件"、"从Power BI复制的代码"、"合并的M代码"、"拆分query"，
  或上传了包含多个 `// QueryName` 块的文本文件时，使用此 skill。
  即使用户只是说"拆分这个文件"而文件内容看起来像合并的 Power Query 代码，也应触发此 skill。
---

# Power Query Splitter

将 Power BI Query 界面"复制所有查询"导出的合并代码拆分为多个独立 `.m` 文件。

## 输入格式

Power BI 复制出的合并代码格式：

```
// QueryName1
let
    Source = ...
in
    Result

// QueryName2
"= some expression" meta [...]
```

每个 query 以 `// QueryName` 注释行开头，代码紧随其后。

## 脚本位置

- `scripts/split_pq.py` — 手动拆分（无外部依赖）
- `scripts/watch_pq.py` — 自动监听文件变更并拆分（需 `pip install watchdog`）

## 使用方式

### 手动拆分

```bash
python scripts/split_pq.py <输入文件> -o <输出目录>
```

示例：
```bash
python scripts/split_pq.py AllQueries.txt -o ./queries
# 输出:
#   ✅ Source.m  (236 chars)
#   ✅ workpc.m  (163 chars)
#   ✅ MPS Loading.m  (37 chars)
#   🎉 共拆分出 3 个 query 文件 → ./queries
```

### 自动监听（文件保存时自动拆分）

```bash
pip install watchdog
python scripts/watch_pq.py AllQueries.txt -o ./queries
# 👀 正在监听 AllQueries.txt 的变更...
#    按 Ctrl+C 停止
```

每次文件保存后自动重新拆分，适合搭配 Power BI 导出工作流使用。

### Claude Code 中使用

用户只需说"拆分这个 PQ 文件"或类似指令，Claude 应：

1. 确定输入来源（文件路径或聊天中粘贴的代码）
2. 如果是粘贴的代码，先保存为临时文件
3. 运行 `split_pq.py` 拆分
4. 告诉用户生成了哪些文件

```bash
# 从文件拆分
python /path/to/scripts/split_pq.py ./AllQueries.txt -o ./pq_output

# 从粘贴内容拆分（先写入临时文件）
cat > /tmp/pq_input.txt << 'PQEOF'
...粘贴的代码...
PQEOF
python /path/to/scripts/split_pq.py /tmp/pq_input.txt -o ./pq_output
```

## 输出规则

- 每个 query → `QueryName.m`
- 保留原始名称（含中文），特殊字符 `<>:"/\|?*` 替换为 `_`
- UTF-8 编码
- 参数查询（非 let...in）同样正常拆分

## 0 个 query 时的处理

提示用户确认格式：每个 query 需以 `// QueryName` 开头。
