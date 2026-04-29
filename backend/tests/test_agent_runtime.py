"""Tests for the autonomous Agent runtime."""

from app.agent_runtime.schemas import AgentRunRequest, AgentRunResult
from app.agent_runtime.agent import run_agent, get_last_run
from app.agent_runtime.planner import create_plan
from app.agent_runtime.tool_registry import call_tool
from app.agent_runtime.critic import evaluate
from app.agent_runtime.memory import AgentMemory
from app.agent_runtime.trace import TraceRecorder


# ── Helpers ────────────────────────────────────────────

def _make_minimal_cp(**overrides) -> dict:
    """Build a minimal valid content pack for testing."""
    cp = {
        "drama": {"title": "test", "type": "test", "description": "test"},
        "characters": [
            {"id": "c1", "name": "c", "archetype": "a", "keywords": [],
             "description": "d", "action_logic": "a"}
        ],
        "nodes": [
            {"id": "n1", "title": "n", "episode": "1", "time_range": "00:00",
             "scene_summary": "s", "conflict_type": "c",
             "spoiler_level": "看前无剧透", "why_interactive": "w",
             "evidence_refs": [{"source_file": "test.md", "doc_type": "test",
                                "section": "test", "quote": "q", "relevance": "r"}]}
        ],
        "questions": [
            {
                "id": f"q{i}", "node_id": "n1", "background": "b", "question": "q",
                "options": [
                    {"label": l, "text": "t",
                     "character_mapping": [{"character_id": "c1", "score": 1}],
                     "action_logic": "a", "feedback_character": "f",
                     "slice_candidate": {"episode": "1", "time": "00:00",
                                         "title": "t", "scene": "s", "subtitle": "s"},
                     "ai_analysis": "a"}
                    for l in ["A", "B", "C", "D"]
                ],
                "evidence_refs": [
                    {"source_file": "test.md", "doc_type": "test",
                     "section": "test", "quote": "q", "relevance": "r"}
                ],
            }
            for i in range(5)
        ],
        "results": [
            {"character_id": "c1", "title": "t", "main_quote": "q",
             "explanation": "e", "fate_hint": "f", "recommended_scenes": []}
        ],
        "review": {"risk_flags": [], "spoiler_flags": [], "needs_human_review": True},
        "agent_meta": {
            "input_material_length": 100, "pipeline_version": "0.2.0",
            "generation_mode": "test", "llm_provider": None,
            "schema_validated": True, "human_review_required": True,
            "note": "test",
        },
    }
    cp.update(overrides)
    return cp


# ── Plan tests ─────────────────────────────────────────

def test_agent_creates_plan():
    plan = create_plan("请生成一个可审核的内容包")
    assert plan.goal == "请生成一个可审核的内容包"
    assert len(plan.steps) > 0
    assert "knowledge_stats" in plan.steps
    assert "save_content_pack" in plan.steps
    # generate_review_report is handled by agent.py at the end, not in plan
    assert "generate_review_report" not in plan.steps


def test_plan_infers_rag_from_keywords():
    plan = create_plan("请基于知识库生成可追溯的内容包", preferred_mode=None)
    assert any("rag" in s for s in plan.steps)


def test_plan_prefers_llm_when_key_exists():
    from app.core.config import settings
    if not settings.has_llm_key:
        plan = create_plan("请用 Claude 生成", preferred_mode="llm")
        assert any("rag" in s or "rule_based" in s for s in plan.steps)
    else:
        plan = create_plan("请用 Claude 生成", preferred_mode="llm")
        assert any("llm" in s for s in plan.steps)


def test_plan_does_not_always_include_rebuild():
    plan = create_plan("生成内容包", preferred_mode="rule_based")
    assert "rebuild_knowledge_index" not in plan.steps


# ── Tool registry tests ───────────────────────────────

def test_knowledge_stats_tool():
    data, error = call_tool("knowledge_stats")
    assert error is None
    assert data is not None
    assert "file_count" in data


def test_unknown_tool():
    data, error = call_tool("nonexistent_tool")
    assert data is None
    assert "Unknown tool" in error


def test_search_knowledge_tool():
    data, error = call_tool("search_knowledge", {"query": "林澈", "top_k": 3})
    assert error is None
    assert "evidence_refs" in data
    assert data["ref_count"] > 0


# ── Agent run tests ────────────────────────────────────

def test_agent_accepts_natural_language_goal():
    req = AgentRunRequest(goal="请基于《雾港来信》知识库生成一个可审核的内容包。")
    result = run_agent(req)
    assert isinstance(result, AgentRunResult)
    assert result.goal == "请基于《雾港来信》知识库生成一个可审核的内容包。"


def test_agent_generates_plan():
    req = AgentRunRequest(goal="生成内容包")
    result = run_agent(req)
    assert len(result.plan.steps) > 0


def test_agent_calls_knowledge_stats():
    req = AgentRunRequest(goal="检查知识库并生成内容包", max_steps=3)
    result = run_agent(req)
    tool_names = [s.tool_call.tool_name for s in result.steps if s.tool_call]
    assert "knowledge_stats" in tool_names


def test_agent_rag_mode_produces_content_pack():
    req = AgentRunRequest(
        goal="请基于知识库生成一个可审核的内容包。",
        preferred_mode="rag",
        max_steps=15,
    )
    result = run_agent(req)
    assert result.final_content_pack is not None
    assert "drama" in result.final_content_pack
    assert len(result.final_content_pack.get("questions", [])) == 5


def test_agent_llm_fallback_when_no_key():
    from app.core.config import settings
    if settings.has_llm_key:
        return
    req = AgentRunRequest(
        goal="请用 Claude 生成内容包。",
        preferred_mode="llm",
        max_steps=15,
    )
    result = run_agent(req)
    assert result.final_content_pack is not None
    tool_names = [s.tool_call.tool_name for s in result.steps if s.tool_call]
    assert "generate_content_pack_llm" in tool_names or "generate_content_pack_rag" in tool_names


def test_agent_returns_steps_trace():
    req = AgentRunRequest(goal="生成内容包", max_steps=8)
    result = run_agent(req)
    assert len(result.steps) > 0
    for step in result.steps:
        assert step.step_index >= 1
        assert step.status in ("completed", "failed")


def test_agent_needs_human_review():
    req = AgentRunRequest(goal="生成内容包")
    result = run_agent(req)
    assert result.needs_human_review is True


def test_agent_last_run_is_stored():
    req = AgentRunRequest(goal="测试存储 trace", max_steps=3)
    result = run_agent(req)
    last = get_last_run()
    assert last is not None
    assert last.goal == "测试存储 trace"


# ── Evidence tests (NEW) ──────────────────────────────

def test_evidence_coverage_not_zero():
    """require_evidence=true → evidence_coverage must not be 0."""
    req = AgentRunRequest(
        goal="请基于《雾港来信》知识库生成一个可追溯的内容包。",
        preferred_mode="rag",
        require_evidence=True,
        max_steps=15,
    )
    result = run_agent(req)
    if result.review_report:
        assert result.review_report["evidence_coverage"] > 0
        assert result.review_report["total_evidence_refs"] > 0


def test_every_question_has_evidence_refs():
    """Every question must have evidence_refs after agent run."""
    req = AgentRunRequest(
        goal="请基于知识库生成可追溯的内容包。",
        preferred_mode="rag",
        max_steps=15,
    )
    result = run_agent(req)
    if result.final_content_pack:
        for q in result.final_content_pack.get("questions", []):
            assert q.get("evidence_refs"), f"Question {q.get('id')} missing evidence_refs"
            assert len(q["evidence_refs"]) > 0


def test_every_node_has_evidence_refs():
    """Every node must have evidence_refs after agent run."""
    req = AgentRunRequest(
        goal="请基于知识库生成可追溯的内容包。",
        preferred_mode="rag",
        max_steps=15,
    )
    result = run_agent(req)
    if result.final_content_pack:
        for node in result.final_content_pack.get("nodes", []):
            assert node.get("evidence_refs"), f"Node {node.get('id')} missing evidence_refs"


def test_evidence_triggers_repair():
    """Missing evidence_refs should trigger repair_content_pack."""
    req = AgentRunRequest(
        goal="请基于知识库生成可追溯的内容包。",
        preferred_mode="rag",
        require_evidence=True,
        max_steps=15,
    )
    result = run_agent(req)
    tool_names = [s.tool_call.tool_name for s in result.steps if s.tool_call]
    # Should have gone through repair to attach evidence
    assert "repair_content_pack" in tool_names


def test_report_not_duplicated():
    """generate_review_report should appear exactly once in steps."""
    req = AgentRunRequest(
        goal="生成内容包",
        preferred_mode="rag",
        max_steps=15,
    )
    result = run_agent(req)
    tool_names = [s.tool_call.tool_name for s in result.steps if s.tool_call]
    report_count = sum(1 for t in tool_names if t == "generate_review_report")
    assert report_count == 1, f"generate_review_report called {report_count} times"


def test_steps_no_full_content_pack():
    """Tool call arguments in trace should NOT contain full content_pack."""
    req = AgentRunRequest(
        goal="生成内容包",
        preferred_mode="rag",
        max_steps=15,
    )
    result = run_agent(req)
    for step in result.steps:
        if step.tool_call:
            args = step.tool_call.arguments
            # Should never have full "content_pack" key with drama etc.
            if "content_pack" in args:
                cp = args["content_pack"]
                assert "drama" not in cp, (
                    f"Step {step.step_index} has full content_pack in arguments"
                )
            # content_pack_summary is OK
            if "content_pack_summary" in args:
                assert "drama_title" in args["content_pack_summary"]


def test_skip_rebuild_when_index_exists():
    """When index exists, rebuild_knowledge_index should be skipped."""
    req = AgentRunRequest(
        goal="基于知识库生成内容包",
        preferred_mode="rag",
        max_steps=15,
    )
    result = run_agent(req)
    tool_names = [s.tool_call.tool_name for s in result.steps if s.tool_call]
    # If index has files, rebuild should NOT be in the steps
    # (it's only inserted when knowledge_stats reports has_files=False)
    if result.review_report and result.review_report.get("evidence_coverage", 0) > 0:
        # Evidence was found from existing index, so rebuild was skipped
        assert "rebuild_knowledge_index" not in tool_names


def test_success_requires_evidence_and_safety():
    """Final success must check evidence coverage AND schema AND safety."""
    req = AgentRunRequest(
        goal="请基于知识库生成可追溯的内容包。",
        preferred_mode="rag",
        require_evidence=True,
        max_steps=15,
    )
    result = run_agent(req)
    if result.success:
        # If success, evidence coverage must be >= 1.0
        if result.review_report:
            assert result.review_report["evidence_coverage"] >= 1.0


# ── Critic tests ───────────────────────────────────────

def test_critic_rejects_none_cp():
    result = evaluate(None, None)
    assert result["qualified"] is False
    assert result["next_action"] == "fallback_to_rule_based"


def test_critic_accepts_valid_cp():
    cp = _make_minimal_cp()
    result = evaluate(cp, {"risk_flags": [], "spoiler_flags": []})
    assert result["qualified"] is True
    assert result["evidence_coverage"] == 1.0


def test_critic_rejects_missing_evidence():
    cp = _make_minimal_cp()
    # Remove evidence_refs from questions
    for q in cp["questions"]:
        del q["evidence_refs"]
    result = evaluate(cp, {"risk_flags": [], "spoiler_flags": []})
    assert result["qualified"] is False
    assert result["next_action"] == "repair_content_pack"


# ── Trace tests ────────────────────────────────────────

def test_trace_recorder():
    trace = TraceRecorder()
    trace.record(
        phase="test", tool_name="test_tool", arguments={"a": 1},
        success=True, data={"result": "ok"}, decision_summary="测试",
        status="completed",
    )
    assert len(trace.steps) == 1
    assert trace.steps[0].step_index == 1
    assert trace.steps[0].tool_call.tool_name == "test_tool"


# ── Repair tests ──────────────────────────────────────

def test_deterministic_repair():
    data, error = call_tool("repair_content_pack", {
        "content_pack": {
            "drama": {"title": "t", "type": "t", "description": "d"},
            "characters": [],
            "nodes": [],
            "questions": [],
            "results": [],
            "review": {"needs_human_review": False},
            "agent_meta": {},
        }
    })
    assert error is None
    assert data["review"]["needs_human_review"] is True
    assert data["agent_meta"]["human_review_required"] is True


def test_repair_attaches_evidence():
    """Repair should attach evidence_refs to questions."""
    data, error = call_tool("repair_content_pack", {
        "content_pack": {
            "drama": {"title": "雾港来信", "type": "悬疑", "description": "d"},
            "characters": [{"id": "c1", "name": "林澈", "archetype": "a",
                            "keywords": [], "description": "d", "action_logic": "a"}],
            "nodes": [{"id": "n1", "title": "被藏起的来信", "episode": "1",
                       "time_range": "00:00", "scene_summary": "发现来信",
                       "conflict_type": "c", "spoiler_level": "看前无剧透",
                       "why_interactive": "w"}],
            "questions": [
                {"id": "q1", "node_id": "n1", "background": "发现朋友藏信",
                 "question": "你会怎么做？",
                 "options": [
                     {"label": "A", "text": "质问他", "character_mapping": [],
                      "action_logic": "a", "feedback_character": "f",
                      "slice_candidate": {"episode": "1", "time": "00:00",
                                          "title": "t", "scene": "s", "subtitle": "s"},
                      "ai_analysis": "a"}
                 ]}
            ],
            "results": [],
            "review": {"needs_human_review": True, "risk_flags": [], "spoiler_flags": []},
            "agent_meta": {"pipeline_version": "0.2.0", "generation_mode": "test",
                           "schema_validated": False, "human_review_required": True},
        }
    })
    assert error is None
    assert len(data["questions"][0].get("evidence_refs", [])) > 0
    assert len(data["nodes"][0].get("evidence_refs", [])) > 0
