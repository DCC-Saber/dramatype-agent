"""Tests for schema validation."""

import pytest
from app.agent.pipeline import run_pipeline
from app.agent.schema_validator import validate_content_pack, validate_with_pydantic


def test_valid_content_pack_passes():
    result = run_pipeline()
    cp = validate_with_pydantic(result)
    assert cp.drama.title == "雾港来信"


def test_missing_drama_fails():
    result = run_pipeline()
    del result["drama"]
    with pytest.raises(Exception):
        validate_with_pydantic(result)


def test_missing_characters_fails():
    result = run_pipeline()
    result["characters"] = []
    with pytest.raises(Exception):
        validate_with_pydantic(result)


def test_missing_questions_fails():
    result = run_pipeline()
    result["questions"] = []
    with pytest.raises(Exception):
        validate_with_pydantic(result)


def test_invalid_spoiler_level_fails():
    result = run_pipeline()
    result["nodes"][0]["spoiler_level"] = "invalid_level"
    with pytest.raises(Exception):
        validate_with_pydantic(result)


def test_missing_needs_human_review_fails():
    result = run_pipeline()
    del result["review"]["needs_human_review"]
    with pytest.raises(Exception):
        validate_with_pydantic(result)
