"""
RAG retriever for DramaType knowledge base.

Supports two modes:
  - Chroma semantic retriever (when vector store is available)
  - Simple keyword retriever (fallback, always works)
"""

from pathlib import Path

from app.core.paths import DATA_DIR


_KNOWLEDGE_DIR = DATA_DIR / "knowledge" / "wugang_letters"


class EvidenceRef:
    """A reference to a piece of evidence from the knowledge base."""

    def __init__(self, source: str, doc_type: str, snippet: str, reason: str,
                 section: str | None = None):
        self.source = source
        self.doc_type = doc_type
        self.section = section
        self.snippet = snippet
        self.reason = reason

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "doc_type": self.doc_type,
            "section": self.section,
            "snippet": self.snippet,
            "reason": self.reason,
        }


def _keyword_search(query: str, top_k: int = 5) -> list[EvidenceRef]:
    """
    Simple keyword-based search over knowledge base files.
    Always works, no dependencies needed.
    """
    results: list[EvidenceRef] = []

    type_map = {
        "series_bible.md": ("series_bible", "剧集概要"),
        "characters.md": ("characters", "角色设定"),
        "episodes.md": ("episodes", "分集概要"),
        "scenes.md": ("scenes", "场景参考"),
        "safety_rules.md": ("safety_rules", "安全审核规则"),
        "interaction_rules.md": ("interaction_rules", "互动内容生成规则"),
    }

    if not _KNOWLEDGE_DIR.exists():
        return results

    # Split query into keywords
    keywords = [kw.strip() for kw in query.split() if len(kw.strip()) >= 2]

    for md_file in sorted(_KNOWLEDGE_DIR.glob("*.md")):
        doc_type, section = type_map.get(
            md_file.name, ("unknown", md_file.stem)
        )
        text = md_file.read_text(encoding="utf-8")

        # Score by keyword matches
        score = 0
        matched_lines = []
        for line in text.splitlines():
            line_score = sum(1 for kw in keywords if kw in line)
            if line_score > 0:
                score += line_score
                matched_lines.append(line.strip())

        if score > 0 and matched_lines:
            snippet = " | ".join(matched_lines[:3])
            results.append(EvidenceRef(
                source=md_file.name,
                doc_type=doc_type,
                snippet=snippet[:300],
                reason=f"关键词匹配 ({score} hits)",
                section=section,
            ))

    # Sort by relevance
    results.sort(key=lambda r: len(r.snippet), reverse=True)
    return results[:top_k]


def _chroma_search(query: str, top_k: int = 5) -> list[EvidenceRef]:
    """Semantic search using Chroma vector store."""
    from app.agent.vector_store import get_vector_store

    store = get_vector_store()
    docs = store.similarity_search(query, k=top_k)

    results = []
    for doc in docs:
        meta = doc.metadata or {}
        results.append(EvidenceRef(
            source=meta.get("source", "unknown"),
            doc_type=meta.get("doc_type", "unknown"),
            snippet=doc.page_content[:300],
            reason="语义检索匹配",
            section=meta.get("section"),
        ))
    return results


def retrieve_knowledge(
    query: str, top_k: int = 5, use_vector: bool = False
) -> tuple[str, list[dict]]:
    """
    Retrieve relevant knowledge for a query.

    Args:
        query: The search query.
        top_k: Maximum number of results.
        use_vector: If True, try Chroma semantic search. Falls back to keyword.

    Returns:
        (context_text, evidence_refs) tuple.
    """
    if use_vector:
        try:
            from app.agent.vector_store import is_chroma_available
            if is_chroma_available():
                refs = _chroma_search(query, top_k)
                if refs:
                    context = "\n\n---\n\n".join(
                        f"[{r.doc_type}] {r.snippet}" for r in refs
                    )
                    return context, [r.to_dict() for r in refs]
        except Exception:
            pass  # Fall back to keyword search

    # Keyword fallback (always works)
    refs = _keyword_search(query, top_k)
    context = "\n\n---\n\n".join(
        f"[{r.doc_type}] {r.snippet}" for r in refs
    )
    return context, [r.to_dict() for r in refs]
