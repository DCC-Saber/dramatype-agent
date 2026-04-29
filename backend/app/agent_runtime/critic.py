"""Critic: evaluates whether a content_pack is deliverable."""


def _calc_evidence_coverage(cp: dict) -> float:
    """questions with evidence_refs / total questions."""
    questions = cp.get("questions", [])
    if not questions:
        return 0.0
    with_refs = sum(1 for q in questions if q.get("evidence_refs"))
    return round(with_refs / len(questions), 2)


def evaluate(
    content_pack: dict | None,
    safety_result: dict | None,
    require_evidence: bool = True,
) -> dict:
    """
    Evaluate a content pack for delivery readiness.

    Returns:
        {
            "qualified": bool,
            "reasons": list[str],
            "next_action": str | None
        }
    """
    reasons: list[str] = []
    qualified = True

    if content_pack is None:
        return {
            "qualified": False,
            "reasons": ["content_pack 不存在"],
            "next_action": "fallback_to_rule_based",
        }

    # Check questions
    questions = content_pack.get("questions", [])
    if len(questions) < 5:
        qualified = False
        reasons.append(f"questions 数量不足 5 (当前 {len(questions)})")
    else:
        for i, q in enumerate(questions):
            opts = q.get("options", [])
            if len(opts) < 4:
                qualified = False
                reasons.append(f"Question {q.get('id', i)} options 不足 4")

    # Check evidence coverage
    coverage = _calc_evidence_coverage(content_pack)
    if require_evidence:
        if coverage < 1.0:
            qualified = False
            reasons.append(f"evidence_coverage={coverage}，不足 1.0")
        # Check each question has evidence_refs
        for q in questions:
            if not q.get("evidence_refs"):
                qualified = False
                reasons.append(f"Question {q.get('id', '?')} 缺少 evidence_refs")
                break  # one is enough to trigger repair

    # Check nodes have evidence_refs
    nodes = content_pack.get("nodes", [])
    for node in nodes:
        if not node.get("evidence_refs"):
            qualified = False
            reasons.append(f"Node {node.get('id', '?')} 缺少 evidence_refs")
            break

    # Check schema validation
    meta = content_pack.get("agent_meta", {})
    schema_ok = meta.get("schema_validated", False)
    if not schema_ok:
        qualified = False
        reasons.append("schema_validated 不为 True")

    # Check safety
    if safety_result and safety_result.get("risk_flags"):
        qualified = False
        reasons.append(f"安全审核发现风险: {len(safety_result['risk_flags'])} 项")

    # Check needs_human_review
    review = content_pack.get("review", {})
    if not review.get("needs_human_review", False):
        qualified = False
        reasons.append("needs_human_review 不为 True")

    # Determine next action
    next_action = None
    if not qualified:
        reason_str = " ".join(reasons)
        if "evidence" in reason_str:
            next_action = "repair_content_pack"
        elif "schema_validated" in reason_str:
            next_action = "repair_content_pack"
        elif "安全审核" in reason_str:
            next_action = "repair_content_pack"
        elif "questions" in reason_str or "options" in reason_str:
            next_action = "fallback_to_rule_based"
        else:
            next_action = "repair_content_pack"

    return {
        "qualified": qualified,
        "reasons": reasons,
        "next_action": next_action,
        "evidence_coverage": coverage,
    }
