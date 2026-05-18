"""Render a content.yaml into a portable Milwaukee-branded HTML deck.

Outputs an independent folder containing:
  index.html   -- deck rendered from deck.html.j2
  theme.css    -- milwaukee.css with :root vars injected from tokens.json
  logo.png     -- copied from milwaukee-ppt/assets/
  runtime.js   -- copied from html-ppt skill (if found)
  base.css     -- copied from html-ppt skill (if found)

Usage:
    python fill_html.py content.yaml --out ~/talks/q2/
    python fill_html.py content.yaml --out ~/talks/q2/ --html-ppt-dir <path>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

SKILL_DIR = Path(__file__).resolve().parent.parent
TOKENS_PATH = SKILL_DIR / "assets" / "tokens.json"
TEMPLATE_DIR = SKILL_DIR / "assets" / "html-template"
LOGO_PATH = SKILL_DIR / "assets" / "logo.png"

PT_TO_PX = 96.0 / 72.0  # 1.3333

# Required keys per slide type. Empty list = only `type` and `title` required.
REQUIRED_FIELDS = {
    "title":   [],
    "text":    ["blocks"],
    "bullets": ["items"],
    "table":   ["rows"],
    "kpi":     ["value", "label"],
    "quote":   ["text"],
    "section": [],  # "text" optional (falls back to title)
    "image":   ["path"],
    "columns": ["columns"],
}


def validate_content(content: dict) -> None:
    """Raise ValueError with a clear message if content fails schema check."""
    if "slides" not in content:
        raise ValueError("content.yaml missing 'slides' key")
    slides = content["slides"]
    if not isinstance(slides, list):
        raise ValueError("'slides' must be a list")
    for i, slide in enumerate(slides, start=1):
        if "type" not in slide:
            raise ValueError(f"slide #{i} missing 'type' field")
        t = slide["type"]
        if t not in REQUIRED_FIELDS:
            raise ValueError(
                f"slide #{i} unknown type {t!r}; allowed: {sorted(REQUIRED_FIELDS)}"
            )
        for field in REQUIRED_FIELDS[t]:
            if field not in slide:
                raise ValueError(
                    f"slide #{i} type={t} missing required field {field!r}"
                )


def find_html_ppt_dir(explicit: str | None) -> Path | None:
    """Resolve html-ppt skill root. Returns None if not found."""
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if (p / "assets" / "runtime.js").exists():
            return p
        return None
    if env := os.environ.get("HTML_PPT_SKILL_DIR"):
        p = Path(env).expanduser().resolve()
        if (p / "assets" / "runtime.js").exists():
            return p
    candidates = [
        Path.home() / "Repo" / "myskills" / ".claude" / "skills" / "html-ppt",
    ]
    for c in candidates:
        if (c / "assets" / "runtime.js").exists():
            return c
    for c in (Path.home() / ".claude" / "plugins" / "cache").glob(
        "*/skills/html-ppt"
    ):
        if (c / "assets" / "runtime.js").exists():
            return c
    return None


def build_css(tokens: dict) -> str:
    """Read milwaukee.css and inject :root from tokens.

    The replacement regex assumes :root has no nested braces. milwaukee.css
    keeps :root as flat key:value pairs only — do not add @supports, @media,
    or nested rules inside :root or the regex will silently misreplace.
    """
    css = (TEMPLATE_DIR / "milwaukee.css").read_text()
    colors = tokens["colors"]
    fonts = tokens["fonts"]
    sizes = tokens["sizes_pt"]
    chrome = tokens["chrome"]
    canvas = tokens["canvas"]
    logo = chrome["logo"]

    lines = [
        ":root {",
        f"  --mw-primary: {colors['primary']};",
        f"  --mw-text-dark: {colors['text_dark']};",
        f"  --mw-text-mid: {colors['text_mid']};",
        f"  --mw-bg-light: {colors['bg_light']};",
        f"  --mw-white: {colors['white']};",
        "",
        f"  --mw-font-en: {fonts['en_sans']}, sans-serif;",
        '  --mw-font-cjk: "'
        + fonts["cjk_sans"]
        + '", '
        + ", ".join(f'"{f}"' for f in fonts["fallback_cjk"])
        + ", sans-serif;",
        "",
        f"  --mw-title-size: {sizes['title'] * PT_TO_PX:.2f}px;",
        f"  --mw-subtitle-size: {sizes['subtitle'] * PT_TO_PX:.2f}px;",
        f"  --mw-body-size: {sizes['body'] * PT_TO_PX:.2f}px;",
        f"  --mw-body-dense-size: {sizes['body_dense'] * PT_TO_PX:.2f}px;",
        f"  --mw-kpi-size: {sizes['kpi'] * PT_TO_PX:.2f}px;",
        f"  --mw-quote-size: {sizes['quote'] * PT_TO_PX:.2f}px;",
        f"  --mw-section-size: {sizes['section'] * PT_TO_PX:.2f}px;",
        "",
        f"  --mw-canvas-w: {canvas['width_px']}px;",
        f"  --mw-canvas-h: {canvas['height_px']}px;",
        f"  --mw-banner-h: {chrome['banner_height_px']}px;",
        f"  --mw-logo-w: {logo['width']}px;",
        f"  --mw-logo-h: {logo['height']}px;",
        f"  --mw-logo-left: {logo['left']}px;",
        f"  --mw-logo-top: {logo['top']}px;",
        f"  --mw-footer-h: {chrome['footer_height_px']}px;",
        f"  --mw-content-top: {chrome['content_top_px']}px;",
        f"  --mw-content-bottom: {chrome['content_bottom_px']}px;",
        "}",
    ]
    injected = "\n".join(lines)

    pattern = re.compile(r":root\s*\{[^}]*\}", re.DOTALL)
    if pattern.search(css):
        return pattern.sub(injected, css, count=1)
    return injected + "\n" + css


def render_html(content: dict, tokens: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template("deck.html.j2")
    return tpl.render(
        meta=content.get("meta", {}),
        slides=content["slides"],
        chrome=tokens["chrome"],
    )


def fill(content_path: Path, out_dir: Path, html_ppt_dir: Path | None) -> Path:
    content = yaml.safe_load(content_path.read_text())
    validate_content(content)
    tokens = json.loads(TOKENS_PATH.read_text())

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "theme.css").write_text(build_css(tokens))
    (out_dir / "index.html").write_text(render_html(content, tokens))
    shutil.copyfile(LOGO_PATH, out_dir / "logo.png")

    if html_ppt_dir:
        for fn in ("runtime.js", "base.css"):
            src = html_ppt_dir / "assets" / fn
            if src.exists():
                shutil.copyfile(src, out_dir / fn)
            else:
                print(f"warning: {src} not found", file=sys.stderr)
    else:
        print(
            "\n"
            "⚠️  html-ppt skill not found — milwaukee-ppt requires it for HTML preview.\n"
            "    Install it (one-time):\n"
            "      npx skills add lewislulu/html-ppt-skill\n"
            "    Or, if already installed in a non-standard location:\n"
            "      python fill_html.py <yaml> --out <dir> --html-ppt-dir <path>\n"
            "      (or set environment variable HTML_PPT_SKILL_DIR=<path>)\n"
            "\n"
            "    Continuing with stub runtime.js / base.css — the static HTML will\n"
            "    render correctly but keyboard navigation and presenter mode will\n"
            "    not work.\n",
            file=sys.stderr,
        )
        # Write a stub base.css and empty runtime.js so the HTML still loads
        (out_dir / "runtime.js").write_text("// html-ppt runtime not available\n")
        (out_dir / "base.css").write_text("/* html-ppt base.css not available */\n")

    return out_dir / "index.html"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Milwaukee YAML → HTML deck")
    p.add_argument("content", help="path to content.yaml")
    p.add_argument("--out", required=True, help="output directory")
    p.add_argument("--html-ppt-dir", default=None, help="html-ppt skill root")
    args = p.parse_args(argv)

    out = fill(
        content_path=Path(args.content),
        out_dir=Path(args.out),
        html_ppt_dir=find_html_ppt_dir(args.html_ppt_dir),
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
