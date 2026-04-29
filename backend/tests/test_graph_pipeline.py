"""Tests for LangGraph pipeline."""

import pytest


def test_graph_build():
    """Test that the graph can be built."""
    try:
        from app.agent.graph import build_graph
        graph = build_graph()
        assert graph is not None
    except (ImportError, ModuleNotFoundError):
        pytest.skip("langgraph not installed")


def test_graph_rule_based():
    """Test running graph in rule_based mode."""
    try:
        from app.agent.graph import run_graph_pipeline
        result = run_graph_pipeline(mode="rule_based")
    except (ImportError, ModuleNotFoundError):
        pytest.skip("langgraph not installed")

    assert isinstance(result, dict)
    assert "drama" in result
    assert "characters" in result
    assert "questions" in result
    assert len(result["characters"]) == 4
    assert len(result["questions"]) == 5


def test_graph_rag_mode():
    """Test running graph in rag mode."""
    try:
        from app.agent.graph import run_graph_pipeline
        result = run_graph_pipeline(mode="rag")
    except (ImportError, ModuleNotFoundError):
        pytest.skip("langgraph not installed")

    assert isinstance(result, dict)
    assert "drama" in result
