"""Extract narrative nodes from parsed material."""

# ── Rule-based nodes (《雾港来信》) ────────────────────

_RULE_NODES = [
    {
        "id": "node_001",
        "title": "被藏起的来信",
        "episode": "第1集",
        "time_range": "00:12:10-00:14:30",
        "scene_summary": "你发现朋友偷偷藏起了一封关键来信，而这封信可能和十年前的旧案有关。",
        "conflict_type": "信任与怀疑",
        "spoiler_level": "看前无剧透",
        "why_interactive": "用户可以代入发现朋友隐瞒真相后的第一反应。",
    },
    {
        "id": "node_002",
        "title": "信任的人背叛你",
        "episode": "第2集",
        "time_range": "00:18:40-00:22:15",
        "scene_summary": "你发现最信任的人对你撒了谎，但他曾经在你最危险的时候救过你。",
        "conflict_type": "关系保护与真相追问",
        "spoiler_level": "看前无剧透",
        "why_interactive": "用户需要在情感信任和事实怀疑之间做选择。",
    },
    {
        "id": "node_003",
        "title": "救人还是保住证据",
        "episode": "第3集",
        "time_range": "00:27:00-00:31:20",
        "scene_summary": "一个人被困在码头仓库里，而能证明真相的录音也可能被销毁。",
        "conflict_type": "生命优先与证据优先",
        "spoiler_level": "看后深度复盘",
        "why_interactive": "用户需要在即时救援和长期正义之间做选择。",
    },
    {
        "id": "node_004",
        "title": "是否公开真相",
        "episode": "第5集",
        "time_range": "00:35:10-00:39:00",
        "scene_summary": "你掌握了足以推翻所有人关系的真相。但一旦公开，一个无辜的人也会被舆论伤害。",
        "conflict_type": "公开真相与保护无辜者",
        "spoiler_level": "看后深度复盘",
        "why_interactive": "用户需要判断真相是否应该被立即公开。",
    },
    {
        "id": "node_005",
        "title": "最后的选择",
        "episode": "第6集",
        "time_range": "00:41:30-00:45:00",
        "scene_summary": "真相即将揭开，但你发现自己也曾间接造成了这场悲剧。所有人都在等你开口。",
        "conflict_type": "自我承担与完成目标",
        "spoiler_level": "看后深度复盘",
        "why_interactive": "用户需要在承担责任和继续行动之间做最终选择。",
    },
]


def extract_narrative_nodes(parsed_material: dict, mode: str = "rule_based") -> list[dict]:
    """
    Return narrative nodes.

    rule_based → hardcoded 《雾港来信》 nodes.
    llm mode → handled by langchain_generator.
    """
    if mode == "llm":
        raise RuntimeError(
            "llm mode node extraction should be done by langchain_generator, "
            "not by node_extractor. Use mode='rule_based' here."
        )
    return [dict(n) for n in _RULE_NODES]
