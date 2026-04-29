"""Analyze characters from parsed material."""

from app.core.config import settings

# ── Rule-based character data (《雾港来信》) ──────────

_RULE_CHARACTERS = [
    {
        "id": "lin_che",
        "name": "林澈",
        "archetype": "冷静观察者",
        "keywords": ["克制", "观察", "延迟判断", "证据优先"],
        "description": "他不急于摊牌，总是在别人忽略的细节里寻找真相。",
        "action_logic": "先观察，再判断；先找证据，再行动。",
    },
    {
        "id": "xu_zhixia",
        "name": "许知夏",
        "archetype": "共情守护者",
        "keywords": ["关系", "保护", "共情", "承担"],
        "description": "她总是先看见人的伤口，再判断事情的对错。",
        "action_logic": "优先保护关系和无辜者，再追问真相。",
    },
    {
        "id": "zhou_ye",
        "name": "周野",
        "archetype": "冒险破局者",
        "keywords": ["行动", "冲动", "突破", "直觉"],
        "description": "他不喜欢等待答案，会直接把门撞开。",
        "action_logic": "先行动打破僵局，再在变化中寻找答案。",
    },
    {
        "id": "gu_chen",
        "name": "顾沉",
        "archetype": "秩序裁决者",
        "keywords": ["规则", "边界", "公正", "理性"],
        "description": "他相信边界，因为没有边界的善意也会伤人。",
        "action_logic": "用规则和边界控制风险，优先维护公正。",
    },
]


def analyze_characters(parsed_material: dict, mode: str = "rule_based") -> list[dict]:
    """
    Return character profiles.

    rule_based → hardcoded 《雾港来信》 characters.
    llm mode → handled by langchain_generator, not here.
    """
    if mode == "llm":
        raise RuntimeError(
            "llm mode character analysis should be done by langchain_generator, "
            "not by character_analyzer. Use mode='rule_based' here."
        )

    return [dict(c) for c in _RULE_CHARACTERS]
