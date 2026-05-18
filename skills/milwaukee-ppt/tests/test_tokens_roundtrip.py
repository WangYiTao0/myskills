"""Tokens.json structural + value tests.

These values must stay in lock-step with template.pptx — if you change
the template chrome, update tokens.json AND this test together.
"""
import json
import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
TOKENS_PATH = SKILL_DIR / "assets" / "tokens.json"


@pytest.fixture(scope="module")
def tokens():
    return json.loads(TOKENS_PATH.read_text())


def test_primary_color_matches_template(tokens):
    """Color must match template.pptx Rectangle 3 fill (extracted 2026-05-18)."""
    assert tokens["colors"]["primary"] == "#DB011C"


def test_all_colors_are_valid_hex(tokens):
    pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
    for name, value in tokens["colors"].items():
        assert pattern.match(value), f"colors.{name}={value} is not valid 6-digit hex"


def test_canvas_matches_template(tokens):
    """1280x720 @ 96 DPI = 13.333" x 7.5" — equals template slide size."""
    assert tokens["canvas"]["width_px"] == 1280
    assert tokens["canvas"]["height_px"] == 720
    assert tokens["canvas"]["dpi"] == 96


def test_chrome_geometry_matches_template(tokens):
    """All chrome px values were extracted from template.pptx slide_master."""
    chrome = tokens["chrome"]
    assert chrome["banner_height_px"] == 96   # Rectangle 3 height
    assert chrome["content_top_px"] == 96     # = banner bottom
    assert chrome["content_bottom_px"] == 696 # = footer top
    assert chrome["footer_height_px"] == 16
    logo = chrome["logo"]
    assert (logo["left"], logo["top"]) == (8, 8)
    assert (logo["width"], logo["height"]) == (176, 79)


def test_required_sizes_present(tokens):
    required = {"title", "subtitle", "body", "kpi", "quote", "section"}
    assert required.issubset(tokens["sizes_pt"].keys())
    for name, pt in tokens["sizes_pt"].items():
        assert pt > 0, f"sizes_pt.{name}={pt} must be positive"
