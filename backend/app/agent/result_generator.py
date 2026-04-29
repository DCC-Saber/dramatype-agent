"""Generate result profile texts for each character."""

_RULE_RESULTS = [
    {
        "character_id": "lin_che",
        "title": "你是冷静观察者",
        "main_quote": "你不急着选择立场，你先确认真相在哪里。",
        "explanation": "你的剧情选择倾向更接近林澈：克制、观察、延迟判断、证据优先。你在面对困境时不会急于表态，而是先收集信息、分析局势，再做出最理性的判断。",
        "fate_hint": "在雾港的故事里，这种冷静让你更接近真相，也更容易独自承担秘密。",
        "recommended_scenes": ["第1集 00:14:05", "第2集 00:21:10", "第3集 00:30:15"],
    },
    {
        "character_id": "xu_zhixia",
        "title": "你是共情守护者",
        "main_quote": "你先看见人的伤口，再判断事情的对错。",
        "explanation": "你的剧情选择倾向更接近许知夏：保护关系、理解他人、愿意承担。你在每一个选择中都优先考虑人的感受和安全，即使真相很近，你也不愿踩着别人走过去。",
        "fate_hint": "这种选择让你更容易守住关系，也可能让你背负更多沉默。",
        "recommended_scenes": ["第1集 00:13:48", "第2集 00:21:10", "第5集 00:36:50"],
    },
    {
        "character_id": "zhou_ye",
        "title": "你是冒险破局者",
        "main_quote": "你不等待答案，你会直接把门撞开。",
        "explanation": "你的剧情选择倾向更接近周野：行动、突破、直觉、打破僵局。你不愿意在僵局中等待，会用行动制造变化，即使结果不一定完美。",
        "fate_hint": "你的行动可能带来转机，也可能让局面提前失控。",
        "recommended_scenes": ["第1集 00:13:02", "第3集 00:29:00", "第6集 00:44:30"],
    },
    {
        "character_id": "gu_chen",
        "title": "你是秩序裁决者",
        "main_quote": "你相信边界，因为没有边界的善意也会伤人。",
        "explanation": "你的剧情选择倾向更接近顾沉：规则、公正、理性、风险控制。你在面对复杂局面时会守住原则，即使这意味着承担不近人情的评价。",
        "fate_hint": "你会努力守住秩序，但也可能因此显得不近人情。",
        "recommended_scenes": ["第1集 00:14:20", "第3集 00:28:20", "第5集 00:35:40"],
    },
]


def generate_results(characters: list[dict], mode: str = "rule_based") -> list[dict]:
    """
    Return result profiles for each character.

    rule_based → hardcoded results.
    llm mode → handled by langchain_generator.
    """
    if mode == "llm":
        raise RuntimeError(
            "llm mode result generation should be done by langchain_generator, "
            "not by result_generator. Use mode='rule_based' here."
        )
    return [dict(r) for r in _RULE_RESULTS]
