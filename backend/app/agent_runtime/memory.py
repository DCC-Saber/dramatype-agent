"""Agent runtime memory: stores intermediate state across steps."""

from dataclasses import dataclass, field


@dataclass
class AgentMemory:
    """Mutable state shared across agent steps."""

    content_pack: dict | None = None
    validation_errors: list[str] = field(default_factory=list)
    safety_result: dict | None = None
    evidence_refs: list[dict] = field(default_factory=list)
    knowledge_stats: dict | None = None
    generation_mode_used: str | None = None
    repair_count: int = 0

    # LLM attempt tracking
    llm_attempted: bool = False
    llm_provider_attempted: str | None = None
    llm_model_attempted: str | None = None
    llm_call_status: str | None = None  # "completed" | "failed"
    llm_error: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
