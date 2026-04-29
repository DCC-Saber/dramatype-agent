"""Generate interactive questions for narrative nodes."""

# ── Rule-based question data (《雾港来信》5 道剧情选择题) ─

_RULE_QUESTIONS = [
    {
        "id": "q_001",
        "node_id": "node_001",
        "background": "你发现朋友偷偷藏起了一封关键来信，而这封信可能和十年前的旧案有关。他没有发现你看见了这一幕。",
        "question": "你会怎么做？",
        "options": [
            {
                "label": "A",
                "text": "当场质问他，逼他说出真相",
                "character_mapping": [
                    {"character_id": "zhou_ye", "score": 2},
                    {"character_id": "gu_chen", "score": 1},
                ],
                "action_logic": "直接打破僵局，用压力逼近真相。",
                "feedback_character": "周野",
                "slice_candidate": {
                    "episode": "第1集",
                    "time": "00:13:02",
                    "title": "来信被藏起",
                    "scene": "角色在走廊转角发现朋友藏信。",
                    "subtitle": "有些事，不问就永远不会有人说。",
                },
                "ai_analysis": "这个选择更接近周野的行动逻辑：先行动，再让局面发生变化。",
            },
            {
                "label": "B",
                "text": "假装没看见，之后暗中调查",
                "character_mapping": [
                    {"character_id": "lin_che", "score": 3},
                ],
                "action_logic": "延迟判断，优先收集证据。",
                "feedback_character": "林澈",
                "slice_candidate": {
                    "episode": "第1集",
                    "time": "00:14:05",
                    "title": "沉默的观察",
                    "scene": "林澈没有开口，只是记下信封上的水渍。",
                    "subtitle": "现在问，得到的未必是真话。",
                },
                "ai_analysis": "这个选择体现出林澈式的克制和证据优先。",
            },
            {
                "label": "C",
                "text": "先替他隐瞒，等他主动解释",
                "character_mapping": [
                    {"character_id": "xu_zhixia", "score": 3},
                ],
                "action_logic": "优先保护关系，给对方留下解释空间。",
                "feedback_character": "许知夏",
                "slice_candidate": {
                    "episode": "第1集",
                    "time": "00:13:48",
                    "title": "没有说出口的怀疑",
                    "scene": "许知夏看见异常，却选择先保护对方。",
                    "subtitle": "也许他不是不想说，只是不知道怎么说。",
                },
                "ai_analysis": "这个选择更接近许知夏的共情守护倾向。",
            },
            {
                "label": "D",
                "text": "把信交给更可靠的人处理",
                "character_mapping": [
                    {"character_id": "gu_chen", "score": 3},
                ],
                "action_logic": "把风险交给更稳定的规则系统处理。",
                "feedback_character": "顾沉",
                "slice_candidate": {
                    "episode": "第1集",
                    "time": "00:14:20",
                    "title": "边界内的处理",
                    "scene": "顾沉提出将证据转交给可信渠道。",
                    "subtitle": "不是所有真相都适合被情绪处理。",
                },
                "ai_analysis": "这个选择体现出顾沉的规则意识和风险控制。",
            },
        ],
    },
    {
        "id": "q_002",
        "node_id": "node_002",
        "background": "你发现最信任的人对你撒了谎，但他曾经在你最危险的时候救过你。",
        "question": "面对这个曾经救过你的人，你会怎么做？",
        "options": [
            {
                "label": "A",
                "text": "立刻断开关系，不再给第二次机会",
                "character_mapping": [
                    {"character_id": "gu_chen", "score": 2},
                    {"character_id": "zhou_ye", "score": 1},
                ],
                "action_logic": "用边界保护自己，拒绝容忍欺骗。",
                "feedback_character": "顾沉",
                "slice_candidate": {
                    "episode": "第2集",
                    "time": "00:19:15",
                    "title": "信任断裂",
                    "scene": "顾沉转身离开，没有给对方解释的机会。",
                    "subtitle": "救过我是一回事，骗我是另一回事。",
                },
                "ai_analysis": "这个选择体现出顾沉的边界感：规则面前，感情不能成为借口。",
            },
            {
                "label": "B",
                "text": "给他一次解释机会，但不完全相信",
                "character_mapping": [
                    {"character_id": "lin_che", "score": 2},
                    {"character_id": "xu_zhixia", "score": 1},
                ],
                "action_logic": "保持距离地观察，既不封闭也不盲信。",
                "feedback_character": "林澈",
                "slice_candidate": {
                    "episode": "第2集",
                    "time": "00:20:30",
                    "title": "半信半疑",
                    "scene": "林澈听着对方解释，手里转着打火机。",
                    "subtitle": "你说，我听。但信不信，是我的事。",
                },
                "ai_analysis": "这个选择体现出林澈的延迟判断——不急于下结论。",
            },
            {
                "label": "C",
                "text": "先保护他，再查清楚他为什么撒谎",
                "character_mapping": [
                    {"character_id": "xu_zhixia", "score": 3},
                ],
                "action_logic": "优先保护关系，真相可以之后再找。",
                "feedback_character": "许知夏",
                "slice_candidate": {
                    "episode": "第2集",
                    "time": "00:21:10",
                    "title": "保护优先",
                    "scene": "许知夏挡在对方面前，不让别人靠近。",
                    "subtitle": "不管他做了什么，我先要确认他是安全的。",
                },
                "ai_analysis": "这个选择最接近许知夏的共情守护——她先看见人，再判断事。",
            },
            {
                "label": "D",
                "text": "利用他的隐瞒反向试探幕后的人",
                "character_mapping": [
                    {"character_id": "lin_che", "score": 3},
                ],
                "action_logic": "把对方的隐瞒变成情报优势。",
                "feedback_character": "林澈",
                "slice_candidate": {
                    "episode": "第2集",
                    "time": "00:22:05",
                    "title": "反向试探",
                    "scene": "林澈没有揭穿，而是顺着谎言引出更多线索。",
                    "subtitle": "他说谎是为了什么？这才是真正的问题。",
                },
                "ai_analysis": "这个选择体现出林澈的证据优先——谎言本身就是线索。",
            },
        ],
    },
    {
        "id": "q_003",
        "node_id": "node_003",
        "background": "你只有10分钟。一个人被困在码头仓库里，而能证明真相的录音也可能被销毁。",
        "question": "你会选择先做什么？",
        "options": [
            {
                "label": "A",
                "text": "先救人，证据以后再想办法",
                "character_mapping": [
                    {"character_id": "xu_zhixia", "score": 3},
                ],
                "action_logic": "人的生命高于一切，证据可以重建。",
                "feedback_character": "许知夏",
                "slice_candidate": {
                    "episode": "第3集",
                    "time": "00:27:45",
                    "title": "冲进仓库",
                    "scene": "许知夏不顾阻拦冲进浓烟中的仓库。",
                    "subtitle": "证据没了可以再找，人没了就什么都没了。",
                },
                "ai_analysis": "许知夏会毫不犹豫地选择救人——她优先看见的是人。",
            },
            {
                "label": "B",
                "text": "先保住证据，否则更多人会受害",
                "character_mapping": [
                    {"character_id": "gu_chen", "score": 3},
                ],
                "action_logic": "一个人的风险 vs 多数人的公正——选择更大的善。",
                "feedback_character": "顾沉",
                "slice_candidate": {
                    "episode": "第3集",
                    "time": "00:28:20",
                    "title": "选择证据",
                    "scene": "顾沉冲向录音设备，手在发抖。",
                    "subtitle": "如果真相没了，对不起的不只是一个人。",
                },
                "ai_analysis": "顾沉会选择保住证据——他的理性让他计算更大的后果。",
            },
            {
                "label": "C",
                "text": "自己去救人，同时让别人转移证据",
                "character_mapping": [
                    {"character_id": "zhou_ye", "score": 2},
                    {"character_id": "lin_che", "score": 1},
                ],
                "action_logic": "分头行动，两件事同时做。",
                "feedback_character": "周野",
                "slice_candidate": {
                    "episode": "第3集",
                    "time": "00:29:00",
                    "title": "分头行动",
                    "scene": "周野冲向仓库，同时喊人去拿录音。",
                    "subtitle": "两个都要，谁说只能选一个？",
                },
                "ai_analysis": "周野不愿意二选一——他会试图全都要。",
            },
            {
                "label": "D",
                "text": "判断现场风险后，选择成功率更高的一边",
                "character_mapping": [
                    {"character_id": "lin_che", "score": 3},
                ],
                "action_logic": "不被情绪驱动，用冷静判断最大化成功率。",
                "feedback_character": "林澈",
                "slice_candidate": {
                    "episode": "第3集",
                    "time": "00:30:15",
                    "title": "冷静判断",
                    "scene": "林澈站在原地，花了5秒评估烟雾方向和火势。",
                    "subtitle": "冲动不等于勇敢，判断才等于。",
                },
                "ai_analysis": "林澈会先评估——他的冷静让他做出最优判断，而不是最快的反应。",
            },
        ],
    },
    {
        "id": "q_004",
        "node_id": "node_004",
        "background": "你掌握了足以推翻所有人关系的真相。但一旦公开，一个无辜的人也会被舆论伤害。",
        "question": "你会怎么做？",
        "options": [
            {
                "label": "A",
                "text": "公开真相，所有后果都必须面对",
                "character_mapping": [
                    {"character_id": "gu_chen", "score": 3},
                ],
                "action_logic": "真相不应该被隐瞒，即使代价很大。",
                "feedback_character": "顾沉",
                "slice_candidate": {
                    "episode": "第5集",
                    "time": "00:35:40",
                    "title": "真相公开",
                    "scene": "顾沉把文件放在桌上，推到所有人面前。",
                    "subtitle": "真相不欠任何人情。",
                },
                "ai_analysis": "顾沉相信规则和公正——真相必须被知道，不管多痛。",
            },
            {
                "label": "B",
                "text": "暂缓公开，先保护无辜者",
                "character_mapping": [
                    {"character_id": "xu_zhixia", "score": 3},
                ],
                "action_logic": "不能让无辜者成为真相的代价。",
                "feedback_character": "许知夏",
                "slice_candidate": {
                    "episode": "第5集",
                    "time": "00:36:50",
                    "title": "暂缓公开",
                    "scene": "许知夏合上文件夹，眼眶泛红。",
                    "subtitle": "真相重要，但不能踩着无辜的人走过去。",
                },
                "ai_analysis": "许知夏会选择先保护无辜者——她把人的安全放在第一位。",
            },
            {
                "label": "C",
                "text": "只公开一部分，引出真正的幕后者",
                "character_mapping": [
                    {"character_id": "lin_che", "score": 3},
                ],
                "action_logic": "用部分真相做诱饵，引导真正的幕后人暴露。",
                "feedback_character": "林澈",
                "slice_candidate": {
                    "episode": "第5集",
                    "time": "00:37:30",
                    "title": "选择性公开",
                    "scene": "林澈只拿出三页纸，把剩下的藏在身后。",
                    "subtitle": "全说出去，就什么也钓不到了。",
                },
                "ai_analysis": "林澈会用策略——他不急于全盘托出，而是设计局面。",
            },
            {
                "label": "D",
                "text": "直接找幕后者摊牌，逼他自己露出破绽",
                "character_mapping": [
                    {"character_id": "zhou_ye", "score": 3},
                ],
                "action_logic": "不绕弯子，直接面对核心矛盾。",
                "feedback_character": "周野",
                "slice_candidate": {
                    "episode": "第5集",
                    "time": "00:38:20",
                    "title": "直接摊牌",
                    "scene": "周野推开门，直视对方的眼睛。",
                    "subtitle": "与其等人暴露，不如我来逼你暴露。",
                },
                "ai_analysis": "周野选择正面突破——他受不了等待，会直接撞门。",
            },
        ],
    },
    {
        "id": "q_005",
        "node_id": "node_005",
        "background": "真相即将揭开，但你发现自己也曾间接造成了这场悲剧。所有人都在等你开口。",
        "question": "你会怎么做？",
        "options": [
            {
                "label": "A",
                "text": "承认自己的责任，即使会失去一切",
                "character_mapping": [
                    {"character_id": "gu_chen", "score": 2},
                    {"character_id": "xu_zhixia", "score": 1},
                ],
                "action_logic": "面对自己的责任，不逃避。",
                "feedback_character": "顾沉",
                "slice_candidate": {
                    "episode": "第6集",
                    "time": "00:42:10",
                    "title": "承认责任",
                    "scene": "顾沉站起来，声音很轻但很清楚。",
                    "subtitle": "这件事里，我也有份。",
                },
                "ai_analysis": "顾沉会面对自己的责任——他的规则要求他对自己也公正。",
            },
            {
                "label": "B",
                "text": "先完成最后一步，再回来承担后果",
                "character_mapping": [
                    {"character_id": "lin_che", "score": 3},
                ],
                "action_logic": "先把该做的事做完，再处理个人的部分。",
                "feedback_character": "林澈",
                "slice_candidate": {
                    "episode": "第6集",
                    "time": "00:43:00",
                    "title": "延迟承担",
                    "scene": "林澈低头，把最后一页记录放进信封。",
                    "subtitle": "责任是你的，但不是现在。",
                },
                "ai_analysis": "林澈会先完成任务——他的冷静让他分清轻重缓急。",
            },
            {
                "label": "C",
                "text": "找到还能补救的人，不让悲剧继续扩大",
                "character_mapping": [
                    {"character_id": "xu_zhixia", "score": 2},
                    {"character_id": "zhou_ye", "score": 1},
                ],
                "action_logic": "过去的已经发生，现在要阻止更多伤害。",
                "feedback_character": "许知夏",
                "slice_candidate": {
                    "episode": "第6集",
                    "time": "00:43:45",
                    "title": "阻止扩大",
                    "scene": "许知夏拉住要离开的人，不肯放手。",
                    "subtitle": "过去的事改不了，但我不能让更多人受伤。",
                },
                "ai_analysis": "许知夏会选择止损——她最怕看见更多人受伤。",
            },
            {
                "label": "D",
                "text": "不解释，直接行动，用结果证明自己",
                "character_mapping": [
                    {"character_id": "zhou_ye", "score": 3},
                ],
                "action_logic": "用行动代替言语，结果比解释更有说服力。",
                "feedback_character": "周野",
                "slice_candidate": {
                    "episode": "第6集",
                    "time": "00:44:30",
                    "title": "行动证明",
                    "scene": "周野没有说话，转身走向码头。",
                    "subtitle": "说再多也没用，做了就知道。",
                },
                "ai_analysis": "周野不会停留在解释——他会用行动来证明自己。",
            },
        ],
    },
]


def generate_questions(
    nodes: list[dict],
    characters: list[dict],
    mode: str = "rule_based",
) -> list[dict]:
    """
    Return questions linked to narrative nodes.

    rule_based → hardcoded 5 questions for 《雾港来信》.
    llm mode → handled by langchain_generator.
    """
    if mode == "llm":
        raise RuntimeError(
            "llm mode question generation should be done by langchain_generator, "
            "not by question_generator. Use mode='rule_based' here."
        )
    return [dict(q) for q in _RULE_QUESTIONS]
