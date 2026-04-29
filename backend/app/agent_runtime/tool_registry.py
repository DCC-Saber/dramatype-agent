"""
Tool registry: wraps existing pipeline modules as callable tools.

Each tool function takes a dict of arguments and returns (data, error).
"""

import json
import copy
from pathlib import Path

from app.core.config import settings
from app.core.paths import DEFAULT_OUTPUT_PATH


# ── helpers ────────────────────────────────────────────

def _summarize_cp(cp: dict) -> dict:
    """Return a compact summary of a content pack (no full text)."""
    if not cp:
        return {}
    return {
        "drama_title": cp.get("drama", {}).get("title", ""),
        "questions_count": len(cp.get("questions", [])),
        "characters_count": len(cp.get("characters", [])),
        "nodes_count": len(cp.get("nodes", [])),
        "results_count": len(cp.get("results", [])),
        "generation_mode": cp.get("agent_meta", {}).get("generation_mode", ""),
    }


def _calc_evidence_coverage(cp: dict) -> float:
    """
    evidence_coverage = questions with evidence_refs / total questions.
    Returns 0.0 if no questions.
    """
    questions = cp.get("questions", [])
    if not questions:
        return 0.0
    with_refs = sum(1 for q in questions if q.get("evidence_refs"))
    return round(with_refs / len(questions), 2)


def _extract_keywords(text: str, max_keywords: int = 5) -> str:
    """
    Extract short searchable keywords from Chinese text.
    Splits on punctuation and common separators, returns space-joined short terms.
    """
    import re
    # Split on Chinese/English punctuation and whitespace
    parts = re.split(r'[，。！？、；：\s,\.!\?;:\"\'\(\)（）]+', text)
    # Keep parts with 2-6 chars (good keyword length for Chinese)
    keywords = [p.strip() for p in parts if 2 <= len(p.strip()) <= 6]
    if not keywords:
        # Fallback: take first 4 chars
        keywords = [text[:4].strip()] if text.strip() else []
    return " ".join(keywords[:max_keywords])


def _build_question_query(q: dict, cp: dict) -> str:
    """Build a short searchable query for a question."""
    parts = []
    # Node title (short, meaningful)
    node_id = q.get("node_id", "")
    for node in cp.get("nodes", []):
        if node.get("id") == node_id:
            title = node.get("title", "")
            if title:
                parts.append(title)
            summary = node.get("scene_summary", "")
            if summary:
                parts.append(_extract_keywords(summary, 2))
            break
    # Question text keywords
    q_text = q.get("question", "")
    if q_text:
        parts.append(_extract_keywords(q_text, 2))
    # Character names from mappings
    for opt in q.get("options", []):
        for cm in opt.get("character_mapping", []):
            char_id = cm.get("character_id", "")
            for ch in cp.get("characters", []):
                if ch.get("id") == char_id and ch.get("name"):
                    parts.append(ch["name"])
                    break
    # Drama title
    drama_title = cp.get("drama", {}).get("title", "")
    if drama_title:
        parts.append(drama_title)
    return " ".join(dict.fromkeys(p for p in parts if p))


def _build_node_query(node: dict, cp: dict) -> str:
    """Build a short searchable query for a node."""
    parts = []
    title = node.get("title", "")
    if title:
        parts.append(title)
    summary = node.get("scene_summary", "")
    if summary:
        parts.append(_extract_keywords(summary, 2))
    conflict = node.get("conflict_type", "")
    if conflict:
        parts.append(_extract_keywords(conflict, 2))
    drama_title = cp.get("drama", {}).get("title", "")
    if drama_title:
        parts.append(drama_title)
    return " ".join(dict.fromkeys(p for p in parts if p))


def _refs_to_dicts(refs: list) -> list[dict]:
    """Convert evidence refs to plain dicts."""
    return [
        {
            "source_file": r.get("source", ""),
            "doc_type": r.get("doc_type", ""),
            "section": r.get("section", ""),
            "quote": r.get("snippet", "")[:200],
            "relevance": r.get("reason", ""),
        }
        for r in refs
    ]


def _search_and_attach_evidence(cp: dict) -> dict:
    """
    Search knowledge base and attach evidence_refs to questions, nodes, options.
    Uses short extracted keywords for Chinese text compatibility.
    """
    from app.agent.rag_retriever import retrieve_knowledge

    cp = copy.deepcopy(cp)

    # Attach evidence to questions
    for q in cp.get("questions", []):
        if not q.get("evidence_refs"):
            query = _build_question_query(q, cp)
            _, refs = retrieve_knowledge(query, top_k=3)
            q["evidence_refs"] = _refs_to_dicts(refs)

        # Attach evidence to options
        for opt in q.get("options", []):
            if not opt.get("evidence_refs"):
                opt_query = _extract_keywords(
                    opt.get("text", "") + " " + opt.get("action_logic", ""), 3
                )
                _, opt_refs = retrieve_knowledge(opt_query, top_k=2)
                opt["evidence_refs"] = _refs_to_dicts(opt_refs)

    # Attach evidence to nodes
    for node in cp.get("nodes", []):
        if not node.get("evidence_refs"):
            node_query = _build_node_query(node, cp)
            _, node_refs = retrieve_knowledge(node_query, top_k=3)
            node["evidence_refs"] = _refs_to_dicts(node_refs)

    return cp


# ── 1. knowledge_stats ─────────────────────────────────

def tool_knowledge_stats(args: dict) -> tuple[dict | None, str | None]:
    try:
        from app.agent.knowledge_ingestor import get_knowledge_stats
        stats = get_knowledge_stats()
        # Return compact version
        return {
            "file_count": stats.get("file_count", 0),
            "total_chars": stats.get("total_chars", 0),
            "has_files": stats.get("file_count", 0) > 0,
        }, None
    except Exception as exc:
        return None, f"knowledge_stats failed: {exc}"


# ── 2. rebuild_knowledge_index ─────────────────────────

def tool_rebuild_knowledge_index(args: dict) -> tuple[dict | None, str | None]:
    try:
        from app.agent.knowledge_ingestor import rebuild_index
        result = rebuild_index()
        return {
            "success": result.get("success", False),
            "docs_ingested": result.get("docs_ingested", 0),
            "message": result.get("message", ""),
        }, None
    except Exception as exc:
        return None, f"rebuild_knowledge_index failed: {exc}"


# ── 3. search_knowledge ────────────────────────────────

def tool_search_knowledge(args: dict) -> tuple[dict | None, str | None]:
    try:
        from app.agent.rag_retriever import retrieve_knowledge
        query = args.get("query", "")
        top_k = args.get("top_k", 5)
        context, refs = retrieve_knowledge(query, top_k=top_k)
        return {"evidence_refs": refs, "ref_count": len(refs)}, None
    except Exception as exc:
        return None, f"search_knowledge failed: {exc}"


# ── 4. generate_content_pack_rule_based ────────────────

def tool_generate_rule_based(args: dict) -> tuple[dict | None, str | None]:
    try:
        from app.agent.pipeline import run_pipeline
        cp = run_pipeline(mode="rule_based")
        return cp, None
    except Exception as exc:
        return None, f"generate_rule_based failed: {exc}"


# ── 5. generate_content_pack_rag ───────────────────────

def tool_generate_rag(args: dict) -> tuple[dict | None, str | None]:
    try:
        from app.agent.pipeline import run_pipeline
        cp = run_pipeline(mode="rag")
        return cp, None
    except Exception as exc:
        return None, f"generate_rag failed: {exc}"


# ── 6. generate_content_pack_llm ──────────────────────

def tool_generate_llm(args: dict) -> tuple[dict | None, str | None]:
    if not settings.has_llm_key:
        pcfg = settings.current_provider_config
        key_name = pcfg.key_env_var if pcfg else "API_KEY"
        return None, (
            f"LLM key 未配置 (provider={settings.LLM_PROVIDER})。"
            f"请设置 {key_name}，或使用 rule_based / rag 模式。"
        )
    try:
        from app.agent.pipeline import run_pipeline
        cp = run_pipeline(mode="llm")
        return cp, None
    except Exception as exc:
        return None, f"generate_llm failed: {exc}"


# ── 7. validate_content_pack ──────────────────────────

def tool_validate(args: dict) -> tuple[dict | None, str | None]:
    cp = args.get("content_pack")
    if not cp:
        return None, "No content_pack provided for validation."
    try:
        from app.agent.schema_validator import validate_content_pack
        validate_content_pack(cp)
        return {"valid": True}, None
    except Exception as exc:
        return {"valid": False}, str(exc)


# ── 8. review_safety ──────────────────────────────────

def tool_review_safety(args: dict) -> tuple[dict | None, str | None]:
    cp = args.get("content_pack")
    if not cp:
        return None, "No content_pack provided for safety review."
    try:
        from app.agent.safety_reviewer import review_content_pack
        result = review_content_pack(cp)
        return result, None
    except Exception as exc:
        return None, f"review_safety failed: {exc}"


# ── 9. repair_content_pack ────────────────────────────

def tool_repair(args: dict) -> tuple[dict | None, str | None]:
    cp = args.get("content_pack")
    if not cp:
        return None, "No content_pack provided for repair."
    try:
        repaired = _deterministic_repair(cp)
        return repaired, None
    except Exception as exc:
        return None, f"repair_content_pack failed: {exc}"


def _deterministic_repair(cp: dict) -> dict:
    """Deterministic repair: fix structural issues AND attach evidence_refs."""
    cp = copy.deepcopy(cp)

    # 1. Ensure needs_human_review = True
    if "review" not in cp:
        cp["review"] = {}
    cp["review"]["needs_human_review"] = True
    cp["review"].setdefault("risk_flags", [])
    cp["review"].setdefault("spoiler_flags", [])

    # 2. Ensure agent_meta
    if "agent_meta" not in cp:
        cp["agent_meta"] = {}
    cp["agent_meta"]["human_review_required"] = True
    cp["agent_meta"]["schema_validated"] = False

    # 3. Ensure structural fields
    cp.setdefault("drama", {
        "title": "雾港来信", "type": "悬疑", "description": "待补充",
    })
    cp.setdefault("characters", [])
    cp.setdefault("nodes", [])
    cp.setdefault("results", [])
    cp.setdefault("questions", [])

    # 4. Ensure options structure
    for q in cp.get("questions", []):
        q.setdefault("options", [])
        for opt in q["options"]:
            opt.setdefault("label", "A")
            opt.setdefault("text", "待补充")
            opt.setdefault("character_mapping", [])
            opt.setdefault("action_logic", "待补充")
            opt.setdefault("feedback_character", "待补充")
            opt.setdefault("slice_candidate", {
                "episode": "未知", "time": "00:00:00",
                "title": "待匹配", "scene": "待补充", "subtitle": "待补充",
            })
            opt.setdefault("ai_analysis", "待补充")

    # 5. Attach evidence_refs via knowledge search
    cp = _search_and_attach_evidence(cp)

    # 6. Clean banned terms
    banned = ["MBTI", "mbti", "心理诊断", "诊断", "抑郁", "焦虑症",
              "焦虑障碍", "人格障碍", "真实人格", "改写剧情", "改写结局"]

    def _clean(obj):
        if isinstance(obj, str):
            for term in banned:
                obj = obj.replace(term, "")
            return obj
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(item) for item in obj]
        return obj

    return _clean(cp)


# ── 10. save_content_pack ─────────────────────────────

def tool_save(args: dict) -> tuple[dict | None, str | None]:
    cp = args.get("content_pack")
    if not cp:
        return None, "No content_pack provided for save."
    path = args.get("path", str(DEFAULT_OUTPUT_PATH))
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(cp, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"path": str(p), "size_bytes": p.stat().st_size}, None
    except Exception as exc:
        return None, f"save_content_pack failed: {exc}"


# ── 11. load_content_pack ─────────────────────────────

def tool_load(args: dict) -> tuple[dict | None, str | None]:
    path = args.get("path", str(DEFAULT_OUTPUT_PATH))
    try:
        p = Path(path)
        if not p.exists():
            return None, f"File not found: {p}"
        cp = json.loads(p.read_text(encoding="utf-8"))
        return cp, None
    except Exception as exc:
        return None, f"load_content_pack failed: {exc}"


# ── 12. generate_review_report ────────────────────────

def tool_generate_review_report(args: dict) -> tuple[dict | None, str | None]:
    cp = args.get("content_pack")
    safety = args.get("safety_result") or {}
    validation_ok = args.get("validation_ok", False)

    if not cp:
        return None, "No content_pack for review report."

    meta = cp.get("agent_meta", {})
    questions = cp.get("questions", [])
    nodes = cp.get("nodes", [])

    # Calculate evidence coverage properly
    evidence_coverage = _calc_evidence_coverage(cp)

    # Count total evidence refs
    total_evidence = 0
    for q in questions:
        total_evidence += len(q.get("evidence_refs", []))
        for opt in q.get("options", []):
            total_evidence += len(opt.get("evidence_refs", []))
    for node in nodes:
        total_evidence += len(node.get("evidence_refs", []))

    report = {
        "generation_mode": meta.get("generation_mode", "unknown"),
        "pipeline_version": meta.get("pipeline_version", "unknown"),
        "evidence_coverage": evidence_coverage,
        "total_evidence_refs": total_evidence,
        "questions_with_evidence": sum(1 for q in questions if q.get("evidence_refs")),
        "nodes_with_evidence": sum(1 for n in nodes if n.get("evidence_refs")),
        "schema_validation_passed": validation_ok,
        "safety_risk_flags": safety.get("risk_flags", []),
        "safety_spoiler_flags": safety.get("spoiler_flags", []),
        "needs_human_review": True,
        "questions_count": len(questions),
        "characters_count": len(cp.get("characters", [])),
        "nodes_count": len(nodes),
        "recommended_next_action": (
            "内容包已通过校验和安全审核，建议运营人员进行人工审核后发布。"
            if validation_ok and not safety.get("risk_flags") and evidence_coverage >= 1.0
            else "内容包存在待修复项，建议运营人员重点审核后决定是否发布。"
        ),
    }
    return report, None


# ── Registry ───────────────────────────────────────────

TOOLS: dict[str, callable] = {
    "knowledge_stats": tool_knowledge_stats,
    "rebuild_knowledge_index": tool_rebuild_knowledge_index,
    "search_knowledge": tool_search_knowledge,
    "generate_content_pack_rule_based": tool_generate_rule_based,
    "generate_content_pack_rag": tool_generate_rag,
    "generate_content_pack_llm": tool_generate_llm,
    "validate_content_pack": tool_validate,
    "review_safety": tool_review_safety,
    "repair_content_pack": tool_repair,
    "save_content_pack": tool_save,
    "load_content_pack": tool_load,
    "generate_review_report": tool_generate_review_report,
}


def call_tool(tool_name: str, arguments: dict | None = None) -> tuple:
    """Look up and call a tool by name."""
    fn = TOOLS.get(tool_name)
    if fn is None:
        return None, f"Unknown tool: {tool_name}"
    return fn(arguments or {})
