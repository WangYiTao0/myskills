"""End-to-end fill_html.py output assertions.

Validates that a minimal content.yaml produces a well-formed deck folder
with all required artifacts and CSS variable injection.
"""
import json
import re
from pathlib import Path

import pytest

from fill_html import build_css, fill, find_html_ppt_dir


SKILL_DIR = Path(__file__).resolve().parent.parent
TOKENS = json.loads((SKILL_DIR / "assets" / "tokens.json").read_text())


def test_build_css_injects_primary_color():
    css = build_css(TOKENS)
    assert "--mw-primary: #DB011C;" in css


def test_build_css_injects_pt_to_px_conversion():
    css = build_css(TOKENS)
    # title 24pt * 1.3333 = 32.00px (matches PPT master titleStyle)
    assert re.search(r"--mw-title-size:\s*32\.00px", css)
    # banner_height = 96 (px directly, no conversion)
    assert "--mw-banner-h: 96px;" in css


def test_fill_writes_all_artifacts(tmp_path):
    content = SKILL_DIR / "sample" / "content.yaml"
    if not content.exists():
        pytest.skip("sample/content.yaml not yet written (Task 5)")
    out = tmp_path / "deck"
    fill(content, out, html_ppt_dir=None)
    assert (out / "index.html").exists()
    assert (out / "theme.css").exists()
    assert (out / "logo.png").exists()
    # runtime.js / base.css get stubs when html-ppt not found
    assert (out / "runtime.js").exists()
    assert (out / "base.css").exists()


def test_fill_output_has_correct_slide_count(tmp_path):
    content = SKILL_DIR / "sample" / "content.yaml"
    if not content.exists():
        pytest.skip("sample/content.yaml not yet written (Task 5)")
    import yaml
    expected = len(yaml.safe_load(content.read_text())["slides"])
    out = tmp_path / "deck"
    fill(content, out, html_ppt_dir=None)
    html = (out / "index.html").read_text()
    assert html.count('<section class="slide"') == expected


def test_find_html_ppt_dir_returns_none_when_explicit_missing():
    assert find_html_ppt_dir("/nonexistent/path/12345") is None
