"""Attach and validate slice candidates on question options."""


_DEFAULT_SLICE = {
    "episode": "未知集数",
    "time": "00:00:00",
    "title": "待匹配切片",
    "scene": "切片候选待生成",
    "subtitle": "（切片候选待补充）",
}


def attach_slice_candidates(
    questions: list[dict], nodes: list[dict]
) -> list[dict]:
    """
    Ensure every option has a complete slice_candidate.
    Fills in defaults for any missing fields.

    Note: slice_candidates are simulated candidates, not real video parses.
    """
    for q in questions:
        for opt in q.get("options", []):
            sc = opt.get("slice_candidate")
            if not isinstance(sc, dict):
                sc = dict(_DEFAULT_SLICE)
            else:
                for key in _DEFAULT_SLICE:
                    sc.setdefault(key, _DEFAULT_SLICE[key])
            opt["slice_candidate"] = sc
    return questions
