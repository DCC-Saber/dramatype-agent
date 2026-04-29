from typing import Literal

from pydantic import BaseModel, Field


# ── Drama ──────────────────────────────────────────────

class DramaInfo(BaseModel):
    title: str
    type: str
    description: str


# ── Characters ─────────────────────────────────────────

class CharacterProfile(BaseModel):
    id: str
    name: str
    archetype: str
    keywords: list[str]
    description: str
    action_logic: str


# ── Narrative Nodes ────────────────────────────────────

class NarrativeNode(BaseModel):
    id: str
    title: str
    episode: str
    time_range: str
    scene_summary: str
    conflict_type: str
    spoiler_level: Literal["看前无剧透", "轻微剧透", "看后深度复盘"]
    why_interactive: str


# ── Questions ──────────────────────────────────────────

class CharacterMapping(BaseModel):
    character_id: str
    score: int


class SliceCandidate(BaseModel):
    episode: str
    time: str
    title: str
    scene: str
    subtitle: str


class QuestionOption(BaseModel):
    label: str
    text: str
    character_mapping: list[CharacterMapping]
    action_logic: str
    feedback_character: str
    slice_candidate: SliceCandidate
    ai_analysis: str


class Question(BaseModel):
    id: str
    node_id: str
    background: str
    question: str
    options: list[QuestionOption] = Field(min_length=2)


# ── Results ────────────────────────────────────────────

class ResultProfile(BaseModel):
    character_id: str
    title: str
    main_quote: str
    explanation: str
    fate_hint: str
    recommended_scenes: list[str]


# ── Evidence Refs ──────────────────────────────────────

class EvidenceRef(BaseModel):
    source: str
    doc_type: str | None = None
    section: str | None = None
    snippet: str
    reason: str


# ── Review ─────────────────────────────────────────────

class SpoilerFlag(BaseModel):
    node_id: str
    level: str
    reason: str


class ReviewInfo(BaseModel):
    risk_flags: list[str] = Field(default_factory=list)
    spoiler_flags: list[SpoilerFlag] = Field(default_factory=list)
    needs_human_review: bool


# ── Agent Meta ─────────────────────────────────────────

class AgentMeta(BaseModel):
    input_material_length: int = 0
    pipeline_version: str = "0.2.0"
    generation_mode: str = "rule_based"
    llm_provider: str | None = None
    schema_validated: bool = False
    human_review_required: bool = True
    note: str = ""


# ── Content Pack (root) ───────────────────────────────

class ContentPack(BaseModel):
    drama: DramaInfo
    characters: list[CharacterProfile] = Field(min_length=1)
    nodes: list[NarrativeNode] = Field(min_length=1)
    questions: list[Question] = Field(min_length=1)
    results: list[ResultProfile] = Field(min_length=1)
    review: ReviewInfo
    agent_meta: AgentMeta


# ── API Request / Response ────────────────────────────

class GenerateRequest(BaseModel):
    mode: str = "rule_based"


class GenerateResponse(BaseModel):
    success: bool
    message: str
    data: ContentPack | None = None
    error: str | None = None
