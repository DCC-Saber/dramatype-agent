"""Tests for knowledge base and RAG retriever."""

from app.agent.rag_retriever import retrieve_knowledge, _keyword_search
from app.agent.knowledge_ingestor import get_knowledge_stats


def test_knowledge_stats():
    stats = get_knowledge_stats()
    assert stats["file_count"] >= 6
    assert stats["total_chars"] > 0


def test_keyword_search_lin_che():
    refs = _keyword_search("林澈 行动逻辑", top_k=3)
    assert len(refs) > 0
    # Should find characters.md
    sources = [r.source for r in refs]
    assert "characters.md" in sources


def test_keyword_search_safety():
    refs = _keyword_search("MBTI 禁止", top_k=3)
    assert len(refs) > 0
    # Should find safety_rules.md
    sources = [r.source for r in refs]
    assert "safety_rules.md" in sources


def test_retrieve_knowledge_returns_tuple():
    context, refs = retrieve_knowledge("雾港来信 角色", top_k=3)
    assert isinstance(context, str)
    assert isinstance(refs, list)
    if refs:
        assert "source" in refs[0]
        assert "doc_type" in refs[0]
        assert "snippet" in refs[0]


def test_retrieve_knowledge_empty_query():
    context, refs = retrieve_knowledge("", top_k=3)
    # Empty query may return no results
    assert isinstance(context, str)
    assert isinstance(refs, list)
