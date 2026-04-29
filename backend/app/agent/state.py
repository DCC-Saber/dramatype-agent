"""LangGraph state definition for DramaType Agent workflow."""

from typing import TypedDict


class DramaTypeAgentState(TypedDict, total=False):
    """State object for the DramaType LangGraph workflow."""

    # Configuration
    mode: str  # "rule_based" | "llm" | "rag"

    # Input
    material_text: str
    parsed_material: dict

    # RAG context
    retrieved_context: str
    evidence_refs: list[dict]

    # Generation outputs
    characters: list[dict]
    nodes: list[dict]
    questions: list[dict]
    results: list[dict]

    # Assembly
    content_pack: dict

    # Validation
    validation_errors: list[str]
    review: dict

    # Output
    output_path: str
