"""YAML schema validation tests for content.yaml.

The validator must accept all 9 slide types and reject malformed input
with a clear error message naming the offending slide and field.
"""
import pytest

from fill_html import validate_content  # imported via conftest sys.path


def test_minimal_valid_deck():
    content = {
        "meta": {"title": "T"},
        "slides": [{"type": "title", "title": "X"}],
    }
    validate_content(content)  # should not raise


def test_all_9_types_valid():
    content = {
        "meta": {"title": "T"},
        "slides": [
            {"type": "title", "title": "A"},
            {"type": "text", "title": "T", "blocks": [{"text": "x"}]},
            {"type": "bullets", "title": "B", "items": ["a"]},
            {"type": "table", "title": "T", "rows": [["a"]]},
            {"type": "kpi", "title": "K", "value": "1", "label": "x"},
            {"type": "quote", "title": "Q", "text": "x"},
            {"type": "section", "title": "S", "text": "x"},
            {"type": "image", "title": "I", "path": "x.png"},
            {"type": "columns", "title": "C", "columns": [{"head": "h", "body": "b"}]},
        ],
    }
    validate_content(content)


def test_missing_slides_key_rejected():
    with pytest.raises(ValueError, match="missing 'slides'"):
        validate_content({"meta": {"title": "x"}})


def test_unknown_type_rejected():
    content = {"slides": [{"type": "rocketship", "title": "x"}]}
    with pytest.raises(ValueError, match="slide #1.*unknown type.*rocketship"):
        validate_content(content)


def test_bullets_missing_items_rejected():
    content = {"slides": [{"type": "bullets", "title": "x"}]}
    with pytest.raises(ValueError, match="slide #1.*bullets.*missing.*items"):
        validate_content(content)


def test_kpi_missing_value_rejected():
    content = {"slides": [{"type": "kpi", "title": "x", "label": "y"}]}
    with pytest.raises(ValueError, match="slide #1.*kpi.*missing.*value"):
        validate_content(content)
