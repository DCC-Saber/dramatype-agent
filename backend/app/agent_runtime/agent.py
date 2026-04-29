"""
Agent main loop: plan -> execute -> observe -> decide -> repair -> deliver.

The autonomous Agent runtime for DramaType content production.
Users input a natural language goal, the Agent plans, calls tools,
observes results, repairs errors, and delivers with full trace.
"""

from app.core.config import settings, _resolve_provider
from app.core.paths import DEFAULT_OUTPUT_PATH
from app.agent_runtime.schemas import (
    AgentRunRequest,
    AgentRunResult,
    AgentPlan,
)
from app.agent_runtime.memory import AgentMemory
from app.agent_runtime.trace import TraceRecorder
from app.agent_runtime.planner import create_plan
from app.agent_runtime.executor import execute_step


_last_run: AgentRunResult | None = None


def get_last_run() -> AgentRunResult | None:
    return _last_run


def run_agent(request: AgentRunRequest) -> AgentRunResult:
    global _last_run

    trace = TraceRecorder()
    memory = AgentMemory()
    errors: list[str] = []

    plan = create_plan(
        goal=request.goal,
        series_id=request.series_id,
        preferred_mode=request.preferred_mode,
    )

    queue = _plan_to_queue(plan)
    report_generated = False

    # Track LLM attempt if preferred_mode is llm
    if request.preferred_mode == "llm":
        memory.llm_attempted = True
        memory.llm_provider_attempted = _resolve_provider(settings.LLM_PROVIDER)
        memory.llm_model_attempted = settings.llm_model_name

    step_count = 0
    max_steps = request.max_steps

    while step_count < max_steps and queue:
        step_count += 1
        tool_name, phase, summary = queue.pop(0)

        arguments = _build_compact_arguments(tool_name, memory)

        data, error = execute_step(
            tool_name=tool_name,
            arguments=arguments,
            phase=phase,
            decision_summary=summary,
            trace=trace,
            memory=memory,
        )

        if error:
            errors.append(f"Step {step_count} ({tool_name}): {error}")

        _post_step_react(
            tool_name, data, error, memory, queue, request,
        )

    # Final validation check
    final_cp = memory.content_pack
    validation_ok = True
    if final_cp:
        try:
            from app.agent.schema_validator import validate_content_pack
            validate_content_pack(final_cp)
        except Exception:
            validation_ok = False

    # Generate review report (only once, at the very end)
    review_report = None
    if final_cp and not report_generated:
        report_data, _ = call_tool_quiet("generate_review_report", {
            "content_pack": final_cp,
            "safety_result": memory.safety_result,
            "validation_ok": validation_ok,
        })
        if report_data:
            review_report = report_data

            # Add LLM attempt info to review report
            if memory.llm_attempted:
                review_report["llm_attempted"] = True
                review_report["llm_provider_attempted"] = memory.llm_provider_attempted
                review_report["llm_model_attempted"] = memory.llm_model_attempted
                review_report["llm_call_status"] = memory.llm_call_status or "unknown"
                review_report["fallback_used"] = memory.fallback_used
                review_report["fallback_reason"] = memory.fallback_reason
                review_report["final_generation_mode"] = (
                    memory.generation_mode_used or "rag"
                )

            trace.record(
                phase="deliver",
                tool_name="generate_review_report",
                arguments={"summary_only": True},
                success=True,
                data={
                    "evidence_coverage": report_data.get("evidence_coverage", 0),
                    "total_evidence_refs": report_data.get("total_evidence_refs", 0),
                },
                decision_summary="生成运营审核报告，确认内容包可交付。",
                status="completed",
            )

    # Write fallback info to final content_pack agent_meta
    if final_cp and memory.llm_attempted and memory.fallback_used:
        if "agent_meta" not in final_cp:
            final_cp["agent_meta"] = {}
        final_cp["agent_meta"]["llm_attempted"] = True
        final_cp["agent_meta"]["llm_provider_attempted"] = memory.llm_provider_attempted
        final_cp["agent_meta"]["llm_model_attempted"] = memory.llm_model_attempted
        final_cp["agent_meta"]["fallback_from_llm"] = True
        final_cp["agent_meta"]["fallback_reason"] = memory.fallback_reason

    # Determine success
    evidence_ok = True
    if request.require_evidence and review_report:
        evidence_ok = review_report.get("evidence_coverage", 0) >= 1.0

    success = (
        final_cp is not None
        and len(final_cp.get("questions", [])) >= 5
        and validation_ok
        and evidence_ok
    )

    result = AgentRunResult(
        success=success,
        goal=request.goal,
        plan=plan,
        steps=trace.to_list(),
        final_content_pack_path=str(DEFAULT_OUTPUT_PATH) if final_cp else None,
        final_content_pack=final_cp,
        review_report=review_report,
        errors=errors,
        needs_human_review=True,
    )

    _last_run = result
    return result


def call_tool_quiet(tool_name: str, arguments: dict) -> tuple:
    """Call a tool without recording to trace (for final report)."""
    from app.agent_runtime.tool_registry import call_tool
    return call_tool(tool_name, arguments)


# -- Plan -> Queue --

def _plan_to_queue(plan: AgentPlan) -> list[tuple[str, str, str]]:
    queue = []
    for step_name in plan.steps:
        if "generate" in step_name:
            mode = step_name.replace("generate_content_pack_", "")
            queue.append((step_name, "generate",
                          f"Agent 选择 {mode} 模式生成内容包。"))
        elif step_name == "knowledge_stats":
            queue.append((step_name, "inspect",
                          "检查知识库状态和索引可用性。"))
        elif step_name == "rebuild_knowledge_index":
            queue.append((step_name, "inspect",
                          "知识库索引为空，正在重建。"))
        elif step_name == "validate_content_pack":
            queue.append((step_name, "validate",
                          "内容包已生成，开始 Schema 校验。"))
        elif step_name == "review_safety":
            queue.append((step_name, "safety",
                          "Schema 校验通过，进入安全审核。"))
        elif step_name == "save_content_pack":
            queue.append((step_name, "save",
                          "内容包已通过校验和安全审核，准备保存。"))
        elif step_name == "generate_review_report":
            queue.append((step_name, "deliver",
                          "生成运营审核报告。"))
        else:
            queue.append((step_name, "other", f"执行 {step_name}。"))
    return queue


# -- Compact Arguments --

def _build_compact_arguments(tool_name: str, memory: AgentMemory) -> dict:
    """Build compact arguments -- never dump full content_pack into trace."""
    if tool_name == "validate_content_pack":
        return {"content_pack": memory.content_pack}
    if tool_name == "review_safety":
        return {"content_pack": memory.content_pack}
    if tool_name == "save_content_pack":
        return {"content_pack": memory.content_pack}
    if tool_name == "repair_content_pack":
        return {"content_pack": memory.content_pack}
    return {}


# -- Post-Step Reactions --

def _post_step_react(
    tool_name: str,
    data,
    error: str | None,
    memory: AgentMemory,
    queue: list[tuple[str, str, str]],
    request: AgentRunRequest,
):
    """React to step results by inserting corrective actions."""

    # After knowledge_stats: conditionally rebuild index
    if tool_name == "knowledge_stats" and data:
        file_count = data.get("file_count", 0)
        has_files = data.get("has_files", False)
        if has_files:
            pass
        else:
            queue.insert(0, (
                "rebuild_knowledge_index", "inspect",
                "知识库索引为空或文件不存在，正在重建。",
            ))
        return

    # LLM failed -> fallback to rag
    if tool_name == "generate_content_pack_llm" and error:
        memory.llm_call_status = "failed"
        memory.llm_error = error
        memory.fallback_used = True
        memory.fallback_reason = f"LLM 调用失败: {error[:200]}"
        queue.insert(0, (
            "generate_content_pack_rag", "generate",
            f"LLM ({memory.llm_provider_attempted}) 调用失败，fallback 到 RAG。原因: {error[:100]}",
        ))
        return

    # LLM succeeded
    if tool_name == "generate_content_pack_llm" and not error:
        memory.llm_call_status = "completed"
        return

    # RAG failed -> fallback to rule_based
    if tool_name == "generate_content_pack_rag" and error:
        if memory.llm_attempted and not memory.fallback_reason:
            memory.fallback_reason = f"RAG 也失败了: {error[:200]}"
        queue.insert(0, (
            "generate_content_pack_rule_based", "generate",
            "RAG 生成失败，fallback 到 rule_based 兜底。",
        ))
        return

    # Generate failed entirely
    if "generate" in tool_name and error and "rule_based" not in tool_name:
        queue.insert(0, (
            "generate_content_pack_rule_based", "generate",
            "生成失败，尝试 rule_based 兜底。",
        ))
        return

    # After generate: check evidence coverage before validate
    if "generate" in tool_name and not error and memory.content_pack:
        coverage = _calc_coverage(memory.content_pack)
        if request.require_evidence and coverage < 1.0:
            queue.insert(0, (
                "repair_content_pack", "repair",
                f"evidence_coverage={coverage}，不足 1.0，进入自动修复补充证据。",
            ))
            return

    # Validation failed -> repair
    if tool_name == "validate_content_pack" and memory.validation_errors:
        queue.insert(0, (
            "repair_content_pack", "repair",
            f"Schema 校验发现 {len(memory.validation_errors)} 个错误，正在修复。",
        ))
        return

    # After repair -> re-validate and re-check evidence
    if tool_name == "repair_content_pack" and not error:
        queue.insert(0, (
            "validate_content_pack", "validate",
            "修复完成，重新校验内容包结构。",
        ))
        return

    # Safety review found risk flags -> repair
    if tool_name == "review_safety" and memory.safety_result:
        risk_flags = memory.safety_result.get("risk_flags", [])
        if risk_flags and memory.repair_count < 3:
            queue.insert(0, (
                "repair_content_pack", "repair",
                f"安全审核发现 {len(risk_flags)} 个风险标记，正在修复。",
            ))
            return


def _calc_coverage(cp: dict) -> float:
    questions = cp.get("questions", [])
    if not questions:
        return 0.0
    with_refs = sum(1 for q in questions if q.get("evidence_refs"))
    return round(with_refs / len(questions), 2)
