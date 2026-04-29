"""Safety review for generated content packs."""

# Terms that must NOT appear in the content pack
_BANNED_TERMS = [
    "MBTI",
    "mbti",
    "心理诊断",
    "诊断",
    "抑郁",
    "焦虑症",
    "焦虑障碍",
    "人格障碍",
    "真实人格",
    "改写剧情",
    "改写结局",
]

# Nodes that need spoiler flags
_SPOILER_NODE_FLAGS = {
    "node_003": ("medium", "涉及第3集关键证据与救援冲突，建议仅用于看后复盘模式。"),
    "node_004": ("high", "涉及第5集真相公开节点，建议仅用于看后深度复盘。"),
    "node_005": ("high", "涉及第6集最终责任选择，必须运营审核后发布。"),
}


def _walk_strings(obj) -> list[str]:
    """Recursively collect all string values from a nested structure."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        result = []
        for v in obj.values():
            result.extend(_walk_strings(v))
        return result
    if isinstance(obj, list):
        result = []
        for item in obj:
            result.extend(_walk_strings(item))
        return result
    return []


def review_content_pack(content_pack: dict) -> dict:
    """
    Review content pack for safety violations.

    Returns a review dict:
      - risk_flags: list of found violations
      - spoiler_flags: list of spoiler warnings per node
      - needs_human_review: always True
    """
    risk_flags: list[str] = []

    all_text = " ".join(_walk_strings(content_pack))
    for term in _BANNED_TERMS:
        if term in all_text:
            risk_flags.append(f"检测到禁用词: {term}")

    # Build spoiler flags from nodes
    spoiler_flags: list[dict] = []
    for node in content_pack.get("nodes", []):
        node_id = node.get("id", "")
        if node_id in _SPOILER_NODE_FLAGS:
            level, reason = _SPOILER_NODE_FLAGS[node_id]
            spoiler_flags.append({
                "node_id": node_id,
                "level": level,
                "reason": reason,
            })

    return {
        "risk_flags": risk_flags,
        "spoiler_flags": spoiler_flags,
        "needs_human_review": True,
    }
