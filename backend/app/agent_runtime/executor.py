"""Executor: runs a single tool call and records the result."""

from app.agent_runtime.tool_registry import call_tool
from app.agent_runtime.trace import TraceRecorder
from app.agent_runtime.memory import AgentMemory


def _compact_arguments(arguments: dict | None) -> dict:
    """Strip full content_pack from trace arguments, keep summary only."""
    if not arguments:
        return {}
    result = {}
    for k, v in arguments.items():
        if k == "content_pack" and isinstance(v, dict):
            result["content_pack_summary"] = {
                "drama_title": v.get("drama", {}).get("title", ""),
                "questions_count": len(v.get("questions", [])),
                "characters_count": len(v.get("characters", [])),
                "nodes_count": len(v.get("nodes", [])),
            }
        else:
            result[k] = v
    return result


def _compact_observation(data) -> dict | list | str | None:
    """Strip full content_pack from observation data, keep summary only."""
    if isinstance(data, dict) and "drama" in data:
        return {
            "questions_count": len(data.get("questions", [])),
            "characters_count": len(data.get("characters", [])),
            "nodes_count": len(data.get("nodes", [])),
            "results_count": len(data.get("results", [])),
            "generation_mode": data.get("agent_meta", {}).get("generation_mode", ""),
        }
    return data


def execute_step(
    tool_name: str,
    arguments: dict | None,
    phase: str,
    decision_summary: str,
    trace: TraceRecorder,
    memory: AgentMemory,
) -> tuple:
    """Execute one tool call, record trace, update memory, return (data, error)."""

    data, error = call_tool(tool_name, arguments)
    success = error is None

    # Update memory
    if success and data is not None:
        if tool_name == "knowledge_stats":
            memory.knowledge_stats = data
        elif tool_name in (
            "generate_content_pack_rule_based",
            "generate_content_pack_rag",
            "generate_content_pack_llm",
        ):
            if isinstance(data, dict) and "drama" in data:
                memory.content_pack = data
                memory.generation_mode_used = tool_name.replace(
                    "generate_content_pack_", ""
                )
        elif tool_name == "validate_content_pack":
            if isinstance(data, dict) and not data.get("valid", True):
                memory.validation_errors.append(
                    data.get("error", "Validation failed")
                )
        elif tool_name == "review_safety":
            memory.safety_result = data
        elif tool_name == "repair_content_pack":
            if isinstance(data, dict):
                memory.content_pack = data
                memory.repair_count += 1
                memory.validation_errors = []

    # Record compact trace
    trace.record(
        phase=phase,
        tool_name=tool_name,
        arguments=_compact_arguments(arguments),
        success=success,
        data=_compact_observation(data),
        error=error,
        decision_summary=decision_summary,
        status="completed" if success else "failed",
    )

    return data, error
