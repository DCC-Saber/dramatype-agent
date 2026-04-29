"""Tests for the rule-based pipeline."""

from app.agent.pipeline import run_pipeline


def test_pipeline_returns_dict():
    result = run_pipeline()
    assert isinstance(result, dict)


def test_pipeline_has_required_keys():
    result = run_pipeline()
    for key in ["drama", "characters", "nodes", "questions", "results", "review", "agent_meta"]:
        assert key in result, f"Missing key: {key}"


def test_pipeline_characters_count():
    result = run_pipeline()
    assert len(result["characters"]) == 4


def test_pipeline_questions_count():
    result = run_pipeline()
    assert len(result["questions"]) == 5


def test_pipeline_questions_have_four_options():
    result = run_pipeline()
    for q in result["questions"]:
        assert len(q["options"]) == 4, f"Question {q['id']} should have 4 options"


def test_pipeline_nodes_count():
    result = run_pipeline()
    assert len(result["nodes"]) == 5


def test_pipeline_results_count():
    result = run_pipeline()
    assert len(result["results"]) == 4


def test_pipeline_needs_human_review():
    result = run_pipeline()
    assert result["review"]["needs_human_review"] is True


def test_pipeline_agent_meta():
    result = run_pipeline()
    meta = result["agent_meta"]
    assert meta["pipeline_version"] == "0.2.0"
    assert meta["schema_validated"] is True
    assert meta["human_review_required"] is True
    assert meta["input_material_length"] > 0


def test_pipeline_spoiler_flags():
    result = run_pipeline()
    spoiler_flags = result["review"]["spoiler_flags"]
    spoiler_node_ids = {f["node_id"] for f in spoiler_flags}
    assert "node_003" in spoiler_node_ids
    assert "node_004" in spoiler_node_ids
    assert "node_005" in spoiler_node_ids


def test_pipeline_no_banned_terms():
    result = run_pipeline()
    assert result["review"]["risk_flags"] == [], (
        f"Safety review found banned terms: {result['review']['risk_flags']}"
    )
