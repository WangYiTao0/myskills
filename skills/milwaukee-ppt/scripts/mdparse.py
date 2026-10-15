"""解析层：md 文稿 → 文档模型（frontmatter + 页列表）。

本模块只切页、取通用字段（主标题 #、action title ##、Layout:、Tag:、PDCA:、Next:/下一步：），
其余正文行原样放进 page.lines，再交给 layouts 里对应的版式模块解析成
page.fields（本版式字段）和 page.conclusion（底部红条结论）。
新增版式不用改这里。
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
    pdca: list = field(default_factory=list)         # 项目汇报模式的 PDCA 阶段，如 ["D", "C"]
    conclusion: list = field(default_factory=list)   # 普通文字行 → 底部红条（版式模块填）
    next: str = ""
    next_label: str = "Next"
    fields: dict = field(default_factory=dict)       # 本版式字段（版式模块填）
    lines: list = field(default_factory=list)        # 通用字段以外的原始正文行，空行为 ""
    indents: list = field(default_factory=list)      # 与 lines 一一对应：行首缩进宽度（tab 算 4）


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


def is_monthly(meta):
    """月报模式：有 month 且没有 title。写了 title 就是通用模式。"""
    return not meta.get("title") and bool(meta.get("month"))


def uses_lead(meta):
    """方向 C（结论画成标题下的 lead、Next 画在页底一行）：通用模式和项目汇报模式都是；
    月报模式仍画底部红条。"""
    return not is_monthly(meta)


PROJECT_REPORT = "project"
PDCA_LETTERS = ("P", "D", "C", "A")


def is_project(meta):
    """项目汇报模式：frontmatter 写了 report: project，各页才能写 PDCA:。"""
    return meta.get("report", "").strip().lower() == PROJECT_REPORT


def _parse_pdca(text, title):
    """「D」「D/C」→ ["D", "C"]：字母只认 P / D / C / A（不区分大小写），用 / 分隔，不重复。"""
    letters = [part.strip().upper() for part in text.split("/")]
    bad = [part for part in letters if part not in PDCA_LETTERS]
    if bad:
        raise DeckError(f"页「{title}」的 PDCA 写错: {text!r}, "
                        f"只认 P / D / C / A，组合用 / 分隔，如 PDCA: D/C")
    if len(set(letters)) != len(letters):
        raise DeckError(f"页「{title}」的 PDCA 有重复字母: {text!r}")
    return letters


def _validate_meta(meta):
    report = meta.get("report", "").strip()
    if report and report.lower() != PROJECT_REPORT:
        raise DeckError(f"frontmatter 的 report 只认 {PROJECT_REPORT}（项目汇报模式）, "
                        f"实际: {report!r}")
    if meta.get("title"):
        return                                   # 通用模式：只要 title
    if not meta.get("month"):
        raise DeckError("frontmatter 缺少必填项: title（通用模式）"
                        "或 month + author（月报模式）")
    for req in ("month", "author"):
        if not meta.get(req):
            raise DeckError(f"frontmatter 缺少必填项: {req}")
    if not re.match(r"^\d{4}-\d{1,2}$", meta["month"]):
        raise DeckError(f"month 格式应为 YYYY-MM, 实际: {meta['month']!r}")
    if not 1 <= int(meta["month"].split("-")[1]) <= 12:
        raise DeckError(f"month 月份应为 01-12, 实际: {meta['month']!r}")


def _indent(raw):
    """行首空白的宽度：空格算 1，tab 按 4 列对齐（markdown 习惯）。"""
    expanded = raw.expandtabs(4)
    return len(expanded) - len(expanded.lstrip())


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
        if line.startswith("# "):
            cur = Page(title=line[2:].strip())
            pages.append(cur)
            continue
        if cur is None:        # 第一个 # 之前的内容忽略
            continue
        if line.startswith("## "):
            cur.action_title = line[3:].strip()
            continue
        mlayout = re.match(r"(?i)^layout\s*[:：]\s*(.+)$", line)
        if mlayout:
            cur.layout = mlayout.group(1).strip().lower()
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
        mpdca = re.match(r"(?i)^pdca\s*[:：]\s*(.+)$", line)
        if mpdca:
            cur.pdca = _parse_pdca(mpdca.group(1), cur.title)
            continue
        cur.lines.append(line)
        cur.indents.append(_indent(raw) if line else 0)

    if not pages:
        raise DeckError("md 中没有找到任何页 (以 '# ' 开头的标题)")
    if not is_project(meta):
        for page in pages:
            if page.pdca:
                raise DeckError(f"页「{page.title}」写了 PDCA:，但 frontmatter 没写 "
                                f"report: {PROJECT_REPORT}；PDCA 图标只在项目汇报模式下使用")
    import layouts            # 延迟导入：layouts 依赖本模块的 Page / DeckError
    for page in pages:
        layouts.parse_page(page)
    return Document(meta=meta, pages=pages,
                    source_dir=os.path.dirname(os.path.abspath(path)))
