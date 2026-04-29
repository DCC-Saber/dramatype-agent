"""
Ingest knowledge base markdown files into vector store.

Splits documents with RecursiveCharacterTextSplitter and adds metadata.
Falls back gracefully when Chroma is not available.
"""

from pathlib import Path

from app.core.paths import DATA_DIR


_KNOWLEDGE_DIR = DATA_DIR / "knowledge" / "wugang_letters"


def _collect_markdown_files() -> list[tuple[Path, str, str]]:
    """
    Collect markdown files with their doc_type.

    Returns list of (path, doc_type, section) tuples.
    """
    type_map = {
        "series_bible.md": ("series_bible", "剧集概要"),
        "characters.md": ("characters", "角色设定"),
        "episodes.md": ("episodes", "分集概要"),
        "scenes.md": ("scenes", "场景参考"),
        "safety_rules.md": ("safety_rules", "安全审核规则"),
        "interaction_rules.md": ("interaction_rules", "互动内容生成规则"),
    }

    files = []
    if not _KNOWLEDGE_DIR.exists():
        return files

    for md_file in sorted(_KNOWLEDGE_DIR.glob("*.md")):
        doc_type, section = type_map.get(
            md_file.name, ("unknown", md_file.stem)
        )
        files.append((md_file, doc_type, section))

    return files


def rebuild_index() -> dict:
    """
    Rebuild the vector store index from knowledge base files.

    Returns:
        dict with success status and doc count.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        raise ImportError(
            "langchain is not installed. Run: pip install langchain"
        )

    from app.agent.vector_store import is_chroma_available, get_vector_store

    if not is_chroma_available():
        return {
            "success": False,
            "message": "ChromaDB is not installed. Cannot rebuild index.",
            "docs_ingested": 0,
        }

    files = _collect_markdown_files()
    if not files:
        return {
            "success": False,
            "message": f"No knowledge files found in {_KNOWLEDGE_DIR}",
            "docs_ingested": 0,
        }

    # Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )

    all_docs = []
    for path, doc_type, section in files:
        text = path.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            all_docs.append({
                "text": chunk,
                "metadata": {
                    "source": path.name,
                    "doc_type": doc_type,
                    "section": section,
                    "chunk_index": i,
                },
            })

    # Ingest into Chroma
    store = get_vector_store()

    texts = [d["text"] for d in all_docs]
    metadatas = [d["metadata"] for d in all_docs]

    store.add_texts(texts=texts, metadatas=metadatas)

    return {
        "success": True,
        "message": f"索引重建完成。共处理 {len(files)} 个知识库文件，{len(all_docs)} 个文本块。",
        "docs_ingested": len(all_docs),
    }


def get_knowledge_stats() -> dict:
    """Return stats about the knowledge base."""
    files = _collect_markdown_files()
    total_chars = 0
    for path, _, _ in files:
        total_chars += len(path.read_text(encoding="utf-8"))

    return {
        "knowledge_dir": str(_KNOWLEDGE_DIR),
        "file_count": len(files),
        "total_chars": total_chars,
        "files": [
            {"name": f.name, "doc_type": dt, "section": sec}
            for f, dt, sec in files
        ],
    }
