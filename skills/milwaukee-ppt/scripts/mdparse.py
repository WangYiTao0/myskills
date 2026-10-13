"""解析层：md 文稿 → 文档模型（frontmatter + 页列表）。

每页是一个 Page：通用字段（主标题、action title、版式名、Tag、结论、Next）
加上 fields（各版式自己的字段；evidence 版式为 images）。
"""
import os
import re
from dataclasses import dataclass, field


class DeckError(Exception):
    """文稿有错：生成器以非零退出并打印这条信息。"""


@dataclass
class Page:
    title: str
    action_title: str = ""
    layout: str = "evidence"
    tag: str = ""
    conclusion: list = field(default_factory=list)   # 普通文字行 → 底部红条
    next: str = ""
    next_label: str = "Next"
    fields: dict = field(default_factory=dict)


@dataclass
class Document:
    meta: dict
    pages: list
    source_dir: str


def _parse_frontmatter(text):
    meta = {}
    m = re.match(r"\s*---\n(.*?)\n---\n", text, re.S)
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]            # 去掉成对引号（YAML 习惯）
            meta[k.strip()] = v
    return meta, text[m.end():]


def _validate_meta(meta):
    for req in ("month", "author"):
        if not meta.get(req):
            raise DeckError(f"frontmatter 缺少必填项: {req}")
    if not re.match(r"^\d{4}-\d{1,2}$", meta["month"]):
        raise DeckError(f"month 格式应为 YYYY-MM, 实际: {meta['month']!r}")
    if not 1 <= int(meta["month"].split("-")[1]) <= 12:
        raise DeckError(f"month 月份应为 01-12, 实际: {meta['month']!r}")


def _strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def parse(path):
    if not os.path.exists(path):
        raise DeckError(f"找不到输入文件: {path}")
    with open(path, encoding="utf-8-sig") as f:   # utf-8-sig: 透明去掉 BOM
        text = f.read()
    meta, body = _parse_frontmatter(text)
    _validate_meta(meta)

    pages, cur = [], None
    for raw in _strip_comments(body).splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            cur = Page(title=line[2:].strip(), fields={"images": []})
            pages.append(cur)
            continue
        if cur is None:        # 第一个 # 之前的内容忽略
            continue
        if line.startswith("## "):
            cur.action_title = line[3:].strip()
            continue
        img = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line)
        if img:
            cur.fields["images"].append(img.group(1).strip())
            continue
        mnext = re.match(r"(?i)^(next|下一步)\s*[:：]\s*(.+)$", line)
        if mnext:
            cur.next = mnext.group(2).strip()
            # 保留作者写的前缀：中文稿写「下一步」就别显示成 "Next"
            cur.next_label = "下一步" if mnext.group(1) == "下一步" else "Next"
            continue
        mtag = re.match(r"(?i)^tag\s*[:：]\s*(.+)$", line)
        if mtag:
            cur.tag = mtag.group(1).strip()
            continue
        cur.conclusion.append(line)

    if not pages:
        raise DeckError("md 中没有找到任何页 (以 '# ' 开头的标题)")
    return Document(meta=meta, pages=pages,
                    source_dir=os.path.dirname(os.path.abspath(path)))
