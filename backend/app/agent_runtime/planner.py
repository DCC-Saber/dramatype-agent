"""Planner: creates an execution plan from a natural language goal."""

from app.core.config import settings
from app.agent_runtime.schemas import AgentPlan


def create_plan(
    goal: str,
    series_id: str = "wugang_letters",
    preferred_mode: str | None = None,
) -> AgentPlan:
    """
    Create an execution plan based on the goal and preferences.

    Rules:
    - If goal mentions knowledge/RAG, prefer rag mode.
    - If goal mentions LLM/Claude, prefer llm mode.
    - If no API key and llm requested, plan fallback to rag.
    - Rebuild is NOT always in the plan; agent checks stats first.
    """
    mode = _decide_mode(goal, preferred_mode)

    steps = [
        "knowledge_stats",
        f"generate_content_pack_{mode}",
        "validate_content_pack",
        "review_safety",
        "save_content_pack",
        # generate_review_report is handled by agent.py at the end (not queued)
    ]

    expected_output = (
        f"使用 {mode} 模式生成一个通过 Schema 校验和安全审核的 content_pack.json，"
        f"需人工审核后发布。"
    )

    return AgentPlan(goal=goal, steps=steps, expected_output=expected_output)


def _decide_mode(goal: str, preferred: str | None) -> str:
    """Decide generation mode from goal text and preference."""
    if preferred == "llm":
        if settings.has_llm_key:
            return "llm"
        return "rag"

    if preferred == "rag":
        return "rag"

    if preferred == "rule_based":
        return "rule_based"

    # Infer from goal text
    goal_lower = goal.lower()
    rag_keywords = ["知识库", "依据", "可追溯", "rag", "检索"]
    llm_keywords = ["真实 llm", "claude", "自然生成", "llm"]

    for kw in llm_keywords:
        if kw in goal_lower:
            if settings.has_llm_key:
                return "llm"
            return "rag"

    for kw in rag_keywords:
        if kw in goal_lower:
            return "rag"

    return "rag"
