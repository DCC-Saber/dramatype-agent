"""Data models for the autonomous Agent runtime."""

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """User request to run the Agent."""
    goal: str
    series_id: str = "wugang_letters"
    preferred_mode: str | None = None
    max_steps: int = 12
    require_evidence: bool = True
    require_human_review: bool = True


class AgentPlan(BaseModel):
    """Plan created by the planner."""
    goal: str
    steps: list[str]
    expected_output: str


class ToolCall(BaseModel):
    """A tool invocation."""
    tool_name: str
    arguments: dict = Field(default_factory=dict)


class AgentObservation(BaseModel):
    """Result of a tool call."""
    success: bool
    data: dict | list | str | None = None
    error: str | None = None


class AgentStep(BaseModel):
    """A single step in the Agent execution trace."""
    step_index: int
    phase: str = ""
    tool_call: ToolCall | None = None
    observation: AgentObservation | None = None
    decision_summary: str = ""
    status: str = "pending"


class AgentRunResult(BaseModel):
    """Final result of an Agent run."""
    success: bool
    goal: str
    plan: AgentPlan
    steps: list[AgentStep] = Field(default_factory=list)
    final_content_pack_path: str | None = None
    final_content_pack: dict | None = None
    review_report: dict | None = None
    errors: list[str] = Field(default_factory=list)
    needs_human_review: bool = True
