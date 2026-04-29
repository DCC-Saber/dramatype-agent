"""Classify conflict types from scene summaries."""

_CONFLICT_KEYWORDS: list[tuple[str, str]] = [
    ("信任", "怀疑", "信任与怀疑"),
    ("背叛", "隐瞒", "关系保护与真相追问"),
    ("救人", "证据", "生命优先与证据优先"),
    ("公开", "保护", "公开真相与保护无辜者"),
    ("责任", "行动", "自我承担与完成目标"),
    ("规则", "情感", "规则与情感"),
    ("等待", "行动", "行动与等待"),
]


def classify_conflict(scene_summary: str) -> str:
    """Return a conflict type string based on keyword matching. Defaults to '未分类冲突'."""
    for kw_a, kw_b, conflict_type in _CONFLICT_KEYWORDS:
        if kw_a in scene_summary and kw_b in scene_summary:
            return conflict_type
    # fallback: single keyword match
    for kw_a, _kw_b, conflict_type in _CONFLICT_KEYWORDS:
        if kw_a in scene_summary:
            return conflict_type
    return "未分类冲突"
