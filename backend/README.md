# 剧格 AI DramaType — Agent MVP

> 面向腾讯视频剧集内容的 AI 互动叙事内容生产系统。

## 项目定位

剧格 AI 不是人格测试，不是 MBTI，不是心理诊断，也不是 AI 改写剧情。

它是基于**授权原剧内容**的轻量 AI 互动叙事层：
- 将剧集关键剧情节点转化为用户可参与的**剧情选择题**
- 通过原剧切片反馈、角色人格光谱和好友对照
- 将长视频观看从"单向观看"升级为"可选择、可反馈、可分享"的互动体验

平台侧 Agent 的价值：将互动测试内容生产从"人工逐剧定制"升级为"AI 生成初稿 + 运营审核发布"的规模化生产流程。

## 为什么不是 MBTI

MBTI 是人格类型理论，用于心理学自我认知。剧格 AI 的"角色人格光谱"是**剧情选择倾向**——你在一个虚构故事中的行动偏好，不等于你的现实人格。我们不做心理学，做的是互动叙事。

## 为什么不是心理诊断

本产品不生成任何心理健康相关判定，不使用"诊断""抑郁""焦虑"等医疗术语，不将剧情选择映射到心理健康维度。所有输出均标注"AI 生成初稿，需运营审核"。

## 为什么不是 AI 改写剧情

剧格 AI 不改写原剧结局，不替角色生成新的正片台词，不声称 AI 生成内容是原剧内容。所有切片标注均为"候选"，不是真实视频解析结果。

## 为什么使用 RAG

- 剧集内容生产必须基于角色、剧情、场景和运营规则的**结构化知识**
- RAG 让生成结果**可追溯**——每个关键输出都能找到知识库依据
- RAG **降低幻觉**——LLM 不凭空编造角色设定和剧情节点
- RAG 支持**多剧集知识库扩展**——新剧只需新增知识库文件
- RAG 为平台侧 Agent Console 提供**可解释依据**

## 为什么使用 LangGraph

- 剧集内容生产不是单次 LLM 调用
- 它是一个**多步骤、可审核、可中断、可追踪**的工作流
- LangGraph 提供状态化 Agent workflow 编排
- 每个节点可独立测试、独立替换

## 为什么使用 LangChain

- LangChain 提供 **ChatAnthropic** 模型接入
- `with_structured_output` 保证 LLM 输出**严格符合 Pydantic 模型**
- LangChain 生态支持 Chroma 向量库集成
- 所有 LLM 输出再经过 JSON Schema 二次校验

## Agent MVP 工作流

```
输入 Markdown 素材
     ↓
读取素材 (read_material)
     ↓
解析素材 (parse_material)
     ↓
[RAG] 检索知识库 (retrieve_knowledge)  ← 可选
     ↓
分析角色 (generate_characters)
     ↓
抽取剧情节点 (extract_nodes)
     ↓
生成问题 (generate_questions)
     ↓
匹配切片候选 (attach_slice_candidates)
     ↓
生成结果文案 (generate_results)
     ↓
安全审核 (review_safety)
     ↓
组装内容包 (assemble_content_pack)
     ↓
Pydantic 校验 + JSON Schema 校验
     ↓
保存 JSON
```

## 项目结构

```
backend/
  app/
    __init__.py
    main.py                    # FastAPI 入口
    models.py                  # Pydantic 数据模型

    core/
      __init__.py
      config.py                # 配置管理 (dotenv)
      paths.py                 # 路径管理 (pathlib)

    agent/
      __init__.py
      pipeline.py              # 编排器 (rule_based / llm / rag)
      graph.py                 # LangGraph workflow
      state.py                 # LangGraph 状态定义
      material_parser.py       # 素材解析器
      character_analyzer.py    # 角色分析器
      node_extractor.py        # 剧情节点抽取器
      conflict_classifier.py   # 冲突分类器
      question_generator.py    # 问题生成器
      slice_matcher.py         # 切片候选匹配器
      result_generator.py      # 结果文案生成器
      safety_reviewer.py       # 安全审核器
      schema_validator.py      # Pydantic + JSON Schema 校验
      llm_client.py            # LLM 客户端封装
      prompts.py               # Prompt 模板
      langchain_generator.py   # LangChain structured output 生成器
      knowledge_ingestor.py    # 知识库索引构建
      vector_store.py          # Chroma 向量库管理
      rag_retriever.py         # RAG 检索器 (keyword / semantic)

    services/
      __init__.py
      content_pack_service.py  # 服务层

  data/
    input/
      wugang_letters_material.md       # 输入素材
    output/
      wugang_letters_content_pack.json # 生成输出
    knowledge/
      wugang_letters/                  # 知识库
        series_bible.md
        characters.md
        episodes.md
        scenes.md
        safety_rules.md
        interaction_rules.md
    vector_store/
      chroma/                          # Chroma 持久化目录

  schemas/
    content_pack.schema.json           # JSON Schema

  tests/
    __init__.py
    test_pipeline.py
    test_schema_validation.py
    test_knowledge.py
    test_graph_pipeline.py

  .env.example
  requirements.txt
  README.md
```

## 如何安装

```bash
cd backend
pip install -r requirements.txt
```

如有 .env 需求：
```bash
cp .env.example .env
# 编辑 .env，按需填写 ANTHROPIC_API_KEY
```

## 如何启动后端

```bash
cd backend
uvicorn app.main:app --reload
```

服务默认运行在 http://127.0.0.1:8000

## 如何生成内容包

### 方式一：通过 API

```bash
# rule_based 模式（无需 API Key）
curl -X POST http://127.0.0.1:8000/api/generate-content-pack \
  -H "Content-Type: application/json" \
  -d '{"mode": "rule_based"}'

# rag 模式（知识库检索 + rule_based 生成）
curl -X POST http://127.0.0.1:8000/api/generate-content-pack \
  -H "Content-Type: application/json" \
  -d '{"mode": "rag"}'

# llm 模式（需要 ANTHROPIC_API_KEY）
curl -X POST http://127.0.0.1:8000/api/generate-content-pack \
  -H "Content-Type: application/json" \
  -d '{"mode": "llm"}'
```

### 方式二：通过 Python

```python
from app.agent.pipeline import run_pipeline
result = run_pipeline(mode="rule_based")
```

### 方式三：通过 LangGraph

```python
from app.agent.graph import run_graph_pipeline
result = run_graph_pipeline(mode="rag")
```

## API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务状态 |
| GET | `/api/agent/status` | Agent 状态 |
| GET | `/api/content-pack` | 读取已生成内容包 |
| POST | `/api/generate-content-pack` | 生成内容包 |
| POST | `/api/validate-content-pack` | 校验当前内容包 |
| POST | `/api/knowledge/rebuild-index` | 重建知识库索引 |
| GET | `/api/knowledge/search?q=...` | 搜索知识库 |
| GET | `/api/knowledge/stats` | 知识库统计 |
| POST | `/api/agent/run` | 运行自主 Agent |
| GET | `/api/agent/last-run` | 查看最近 Agent 执行轨迹 |

## JSON Schema 校验

所有内容包生成后经过两层校验：

1. **Pydantic 校验**：类型、字段、枚举值、嵌套结构
2. **JSON Schema 校验**：基于 `schemas/content_pack.schema.json` 的结构校验

校验不通过时会抛出明确错误。

## 如何运行测试

```bash
cd backend
python -m pytest tests/ -v
```

## 三种模式对比

| 模式 | 需要 API Key | 需要知识库 | 稳定性 | 智能程度 |
|------|-------------|-----------|--------|---------|
| rule_based | 否 | 否 | 最稳定 | 规则模板 |
| rag | 否 | 是（内置） | 稳定 | 检索增强 |
| llm | 是 | 否 | 取决于模型 | 最智能 |

没有 API Key 时：rule_based 和 rag 模式完全可用，llm 模式返回明确错误。

## 当前 Agent 智能在哪里

1. **结构化 Pipeline**：不是单次 LLM 调用，而是可审核、可替换的多步骤流程
2. **Pydantic 强校验**：所有输出严格符合预定义模型，不输出无法控制的自由文本
3. **JSON Schema 双重校验**：Pydantic + JSON Schema 两层保障
4. **RAG 检索增强**：生成结果可追溯到知识库依据
5. **LangGraph 状态流**：每个节点可独立测试、独立替换
6. **安全审核自动化**：自动检测禁用词和剧透风险
7. **多模式支持**：rule_based / rag / llm 三种模式灵活切换
8. **自主 Agent Runtime**：用户输入自然语言目标，Agent 自行规划、调用工具、修复错误

## From Workflow to Agent Runtime

当前系统不仅有固定 pipeline，还提供了一个 **tool-using autonomous Agent runtime**。

用户不再需要手动选择 mode。只需输入自然语言目标：

```bash
curl -X POST http://127.0.0.1:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "请基于《雾港来信》知识库生成一个可审核、可追溯、无剧透的互动内容包。",
    "series_id": "wugang_letters",
    "preferred_mode": "rag",
    "max_steps": 12,
    "require_evidence": true,
    "require_human_review": true
  }'
```

Agent 会自行：
1. **检查知识库状态** — 调用 `knowledge_stats`
2. **重建索引** — 如果索引为空，调用 `rebuild_knowledge_index`
3. **生成内容包** — 根据目标选择 rag / llm / rule_based
4. **Schema 校验** — Pydantic + JSON Schema 双重校验
5. **安全审核** — 自动检测禁用词和剧透风险
6. **自动修复** — 校验失败时调用 `repair_content_pack`
7. **保存并生成报告** — 保存 JSON，生成运营审核报告

每次执行生成完整的 `steps trace`，可查看 `/api/agent/last-run`。

### Agent 与旧 Pipeline 的区别

| | 固定 Pipeline | Agent Runtime |
|---|---|---|
| 输入 | 用户选择 mode | 自然语言目标 |
| 流程 | 线性固定 | 自适应 |
| 错误处理 | 抛出异常 | 自动修复 + fallback |
| 可追溯性 | 无 trace | 完整 steps trace |
| 适合 | 稳定批量生成 | 探索性内容生产 |

### Agent 执行轨迹示例

```json
{
  "step_index": 3,
  "phase": "generate",
  "tool_call": {
    "tool_name": "generate_content_pack_rag",
    "arguments": {"series_id": "wugang_letters"}
  },
  "observation": {
    "success": true,
    "data": {
      "questions_count": 5,
      "characters_count": 4
    }
  },
  "decision_summary": "使用 rag 模式生成内容包。",
  "status": "completed"
}
```

### Agent 可用工具

| 工具 | 说明 |
|------|------|
| `knowledge_stats` | 检查知识库状态 |
| `rebuild_knowledge_index` | 重建知识库向量索引 |
| `search_knowledge` | 搜索知识库 |
| `generate_content_pack_rule_based` | 规则模板生成 |
| `generate_content_pack_rag` | RAG 检索增强生成 |
| `generate_content_pack_llm` | LLM 结构化输出生成 |
| `validate_content_pack` | Pydantic + JSON Schema 校验 |
| `review_safety` | 安全审核 |
| `repair_content_pack` | 确定性修复 |
| `save_content_pack` | 保存到磁盘 |
| `load_content_pack` | 读取已有内容包 |
| `generate_review_report` | 生成运营审核报告 |

## 后续路线

- 接入真实 LLM（Claude / Anthropic structured output）
- 前端迁移 Vite + React
- Agent Console 展示真实 pipeline 状态
- 多剧集内容包管理
- 向量数据库语义检索
- 后续再做视频切片/字幕对齐
