"""
Orchestrator for DramaType content pack generation.

Supports three modes:
  - rule_based: stable, no API key needed
  - llm: uses LangChain + Anthropic structured output (requires API key)
  - rag: uses knowledge base retrieval + rule-based generation
"""

import json
from pathlib import Path

from app.core.config import settings, _resolve_provider
from app.core.paths import DEFAULT_INPUT_PATH, DEFAULT_OUTPUT_PATH
from app.agent.material_parser import read_material, parse_material_sections
from app.agent.character_analyzer import analyze_characters
from app.agent.node_extractor import extract_narrative_nodes
from app.agent.question_generator import generate_questions
from app.agent.slice_matcher import attach_slice_candidates
from app.agent.result_generator import generate_results
from app.agent.safety_reviewer import review_content_pack
from app.agent.schema_validator import validate_content_pack


def _build_content_pack(
    material_text: str,
    characters: list[dict],
    nodes: list[dict],
    questions: list[dict],
    results: list[dict],
    review: dict,
    mode: str,
    evidence_refs: list[dict] | None = None,
) -> dict:
    """Assemble the final content pack dict."""
    note = "AI 生成初稿，需运营审核后发布。"
    if mode == "rule_based":
        note = "当前版本为规则模板生成，后续可接入 LLM Agent 生成。"
    if evidence_refs:
        note += f" RAG 检索证据 {len(evidence_refs)} 条。"

    return {
        "drama": {
            "title": "雾港来信",
            "type": "悬疑 / 群像 / 情感抉择 / 6集短剧",
            "description": "十年前，雾港发生一起未解旧案。十年后，一封没有署名的来信寄到四位故人手中。每个人都知道一部分真相，也都在隐瞒一部分过去。随着调查深入，他们必须在保护关系、追求真相、遵守规则和打破僵局之间做出选择。",
        },
        "characters": characters,
        "nodes": nodes,
        "questions": questions,
        "results": results,
        "review": review,
        "agent_meta": {
            "input_material_length": len(material_text),
            "pipeline_version": "0.2.0",
            "generation_mode": mode,
            "llm_provider": (
                _resolve_provider(settings.LLM_PROVIDER)
                if mode == "llm" else None
            ),
            "llm_model": settings.llm_model_name if mode == "llm" else None,
            "llm_base_url_masked": settings.llm_base_url if mode == "llm" else None,
            "schema_validated": False,
            "human_review_required": True,
            "note": note,
        },
    }


def _run_rule_based(material_text: str) -> dict:
    """Full rule-based pipeline: no LLM, no API key needed."""
    parsed = parse_material_sections(material_text)
    characters = analyze_characters(parsed, mode="rule_based")
    nodes = extract_narrative_nodes(parsed, mode="rule_based")
    questions = generate_questions(nodes, characters, mode="rule_based")
    questions = attach_slice_candidates(questions, nodes)
    results = generate_results(characters, mode="rule_based")
    content_pack = _build_content_pack(
        material_text, characters, nodes, questions, results,
        review={}, mode="rule_based",
    )
    return content_pack


def _run_rag(material_text: str) -> dict:
    """RAG pipeline: retrieve knowledge, then generate with rule-based + evidence refs."""
    from app.agent.rag_retriever import retrieve_knowledge

    parsed = parse_material_sections(material_text)

    # Retrieve relevant knowledge
    query_parts = []
    for key in ("basic_info", "characters", "nodes"):
        if key in parsed:
            query_parts.append(parsed[key])
    query = " ".join(query_parts) if query_parts else material_text

    context, evidence_refs = retrieve_knowledge(query, top_k=8, use_vector=False)

    # Generate using rule-based (but with evidence context available)
    characters = analyze_characters(parsed, mode="rule_based")
    nodes = extract_narrative_nodes(parsed, mode="rule_based")
    questions = generate_questions(nodes, characters, mode="rule_based")
    questions = attach_slice_candidates(questions, nodes)
    results = generate_results(characters, mode="rule_based")

    content_pack = _build_content_pack(
        material_text, characters, nodes, questions, results,
        review={}, mode="rag", evidence_refs=evidence_refs,
    )
    return content_pack


def _run_llm(material_text: str) -> dict:
    """LLM pipeline: retrieves evidence context, then generates via LLM."""
    from app.agent.langchain_generator import generate_content_pack_with_langchain
    from app.agent.rag_retriever import retrieve_knowledge

    # Retrieve evidence context for the LLM prompt
    parsed = parse_material_sections(material_text)
    query_parts = []
    for key in ("basic_info", "characters", "nodes"):
        if key in parsed:
            query_parts.append(parsed[key])
    query = " ".join(query_parts) if query_parts else material_text

    context, evidence_refs = retrieve_knowledge(query, top_k=8, use_vector=False)

    # Generate via LLM with evidence context
    content_pack = generate_content_pack_with_langchain(
        material_text,
        evidence_context=context if context else None,
    )

    # Attach evidence_refs to the generated content pack
    if evidence_refs:
        from app.agent_runtime.tool_registry import _search_and_attach_evidence
        content_pack = _search_and_attach_evidence(content_pack)

    return content_pack


def run_pipeline(
    input_path: Path | None = None,
    output_path: Path | None = None,
    mode: str | None = None,
) -> dict:
    """
    Main pipeline entry point.

    Args:
        input_path: Path to material markdown. Defaults to wugang_letters_material.md
        output_path: Path to write output JSON. Defaults to wugang_letters_content_pack.json
        mode: "rule_based", "llm", or "rag". Defaults to settings.AGENT_MODE.

    Returns:
        The generated content pack as a dict.
    """
    mode = mode or settings.AGENT_MODE
    inp = input_path or DEFAULT_INPUT_PATH
    out = output_path or DEFAULT_OUTPUT_PATH

    # 1. Read material
    material_text = read_material(inp)

    # 2. Generate content pack
    if mode == "llm":
        content_pack = _run_llm(material_text)
    elif mode == "rag":
        content_pack = _run_rag(material_text)
    else:
        content_pack = _run_rule_based(material_text)

    # 3. Safety review
    review = review_content_pack(content_pack)
    content_pack["review"] = review

    # 4. Validate with Pydantic + JSON Schema
    validate_content_pack(content_pack)

    # 5. Mark as validated
    content_pack["agent_meta"]["schema_validated"] = True
    content_pack["agent_meta"]["human_review_required"] = review["needs_human_review"]

    # 6. Save JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(content_pack, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return content_pack
