# DramaType Agent

面向长视频平台的可追溯互动内容生产 Agent。

系统可以基于剧集知识库，自动生成互动剧情测试内容包，并完成 LLM 生成、RAG 检索、Evidence 补全、Schema 校验、安全审核和人工审核报告。

## 项目亮点

- **用户端互动剧情测试** — 基于剧集角色人格的选择题，生成光谱画像和推荐片段
- **Agent Runtime** — 自然语言 goal → plan → tool calls → observation → repair → delivery
- **RAG 检索** — 基于《雾港来信》知识库检索素材依据
- **Evidence Refs** — 每道题可追溯到知识库片段，证据覆盖率可量化
- **多 LLM Provider** — 支持 DeepSeek / Xiaomi MiMo / OpenAI / Anthropic / Qwen / Kimi / Zhipu / SiliconFlow / custom OpenAI-compatible
- **Repair Loop** — 证据不足或结构错误时自动修复
- **Safety Review** — 剧透风险和安全风险审核
- **Schema Validation** — Pydantic + JSON Schema 双重校验
- **Frontend Demo** — 精致互动体验 + Agent Drawer 可视化执行过程
- **Fallback 机制** — LLM 失败时自动 fallback 到 RAG / rule_based

## 技术栈

**Backend:**
- FastAPI
- Pydantic v2
- LangChain
- LangGraph
- ChromaDB / keyword fallback
- pytest

**Frontend:**
- Single-file HTML
- React 18 (CDN)
- Babel (CDN)
- Tailwind CSS (CDN)
- Vanilla fetch API

## 项目结构

```
dramatype-agent/
├── backend/
│   ├── app/
│   │   ├── agent/              # Pipeline, generator, repair, schema, safety
│   │   ├── agent_runtime/      # Agent loop: planner, executor, critic, memory
│   │   ├── core/               # Config, settings, provider management
│   │   └── services/           # Content pack service
│   ├── data/
│   │   ├── input/              # 原始剧集素材
│   │   ├── knowledge/          # 知识库文档
│   │   └── output/             # 生成的内容包 (gitignored)
│   ├── schemas/                # JSON Schema
│   ├── scripts/                # 诊断脚本
│   ├── tests/                  # pytest 测试
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py
├── frontend/
│   ├── fusion-demo/
│   │   └── index.html          # 融合版：精致体验 + Agent Console
│   └── agent-console/
│       └── index.html          # Agent Console 独立版
├── scripts/
├── README.md
└── .gitignore
```

## 快速开始

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置（不要提交真实 API Key）
copy .env.example .env

# 启动服务
uvicorn app.main:app --reload
```

后端运行在 http://127.0.0.1:8000

### 前端

```bash
cd frontend/fusion-demo
python -m http.server 5501
```

浏览器打开 http://127.0.0.1:5501/index.html

### Swagger 文档

http://127.0.0.1:8000/docs

## .env 配置

**重要：不要提交包含真实 API Key 的 .env 文件。**

`.env.example` 提供了完整的配置模板。复制为 `.env` 后填入你的 API Key。

### DeepSeek

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=your-key-here
```

### Xiaomi MiMo

```env
LLM_PROVIDER=xiaomi
LLM_MODEL=mimo-v2.5-pro
LLM_BASE_URL=https://api.mimo-v2.com/v1
XIAOMI_API_KEY=your-key-here
```

### Custom OpenAI-compatible

```env
LLM_PROVIDER=custom_openai_compatible
LLM_MODEL=your-model
LLM_BASE_URL=https://your-provider/v1
LLM_API_KEY=your-key-here
```

### 通用 fallback key

如果不想为每个 provider 单独配置 key，可以使用 `LLM_API_KEY` 作为通用 key：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your-deepseek-key
```

### 所有支持的 Provider

| Provider | Key 环境变量 | 默认 Model |
|----------|-------------|-----------|
| anthropic | ANTHROPIC_API_KEY | claude-sonnet-4-20250514 |
| openai | OPENAI_API_KEY | gpt-4o |
| deepseek | DEEPSEEK_API_KEY | deepseek-chat |
| qwen | DASHSCOPE_API_KEY | qwen-plus |
| kimi | MOONSHOT_API_KEY | kimi-k2.5 |
| zhipu | ZHIPUAI_API_KEY | glm-5.1 |
| siliconflow | SILICONFLOW_API_KEY | Qwen/Qwen3-8B |
| xiaomi (alias: mimo) | XIAOMI_API_KEY | mimo-v2.5-pro |
| custom_openai_compatible | LLM_API_KEY | (必须指定 LLM_MODEL) |

## LLM 诊断

### CLI 诊断脚本

```bash
cd backend
python scripts/check_llm.py
```

输出当前 provider、model、base_url、key 状态，以及可选的 LLM 测试调用。

### API 诊断

```bash
# 查看当前 LLM 配置状态
GET http://127.0.0.1:8000/api/llm/status

# 发送测试消息
POST http://127.0.0.1:8000/api/llm/test
Content-Type: application/json
{"message": "只回复 OK"}
```

## Agent API

### 运行 Agent

```bash
POST http://127.0.0.1:8000/api/agent/run
Content-Type: application/json
```

请求示例：

```json
{
  "goal": "请基于《雾港来信》知识库生成一个可审核、可追溯、无剧透的互动内容包。",
  "series_id": "wugang_letters",
  "preferred_mode": "llm",
  "max_steps": 12,
  "require_evidence": true,
  "require_human_review": true
}
```

返回中的重点字段：

| 字段 | 说明 |
|------|------|
| `final_content_pack` | 生成的互动内容包（drama / characters / questions / results） |
| `review_report` | 审核报告（evidence coverage、validation、safety flags） |
| `steps` | Agent 执行步骤的完整 trace |
| `review_report.llm_attempted` | 是否尝试了 LLM 调用 |
| `review_report.fallback_used` | 是否 fallback 到 RAG/rule_based |
| `review_report.evidence_coverage` | 证据覆盖率 (0.0 ~ 1.0) |
| `review_report.schema_validation_passed` | Schema 校验是否通过 |
| `review_report.final_generation_mode` | 最终使用的生成模式 (llm / rag / rule_based) |

### 查看上次执行

```bash
GET http://127.0.0.1:8000/api/agent/last-run
```

## 前端演示

打开 http://127.0.0.1:5501/index.html 后：

### 顶部控制栏

- **Check LLM** — 调用 `GET /api/llm/status`，显示当前 provider/model/key 状态
- **Goal** — 展开可编辑的 Agent 目标输入框
- **Run Agent** — 调用 `POST /api/agent/run`，执行真实 Agent
- **体验模式 / Agent 模式** — 切换页面信息密度
- **查看 Agent 过程** — 打开右侧 Agent Drawer

### 右侧 Agent Drawer

- **Provider 状态** — provider、model、base_url、key 来源
- **Test LLM** — 调用 `POST /api/llm/test` 测试大模型连通性
- **LLM 调用追踪** — llm_attempted、provider、model、call_status、fallback_used、fallback_reason、final_generation_mode
- **Review Report** — evidence_coverage、total_evidence_refs、schema_validation、needs_human_review、safety_flags
- **Agent Steps Timeline** — 真实的 steps trace，显示 tool_name、status、observation
- **Evidence Refs** — 当前题目对应的知识库引用

### 交互流程

1. 点击 **Run Agent** → 后端执行 Agent
2. 右侧 Drawer 实时显示 steps 和 review report
3. 如果 LLM fallback → 显示黄色 fallback 提示
4. 生成完成后 → 答题内容自动更新为 Agent 生成的内容
5. 用户正常答题 → 结果页展示 Agent 生成的画像

## 测试

```bash
cd backend
python -m pytest tests/ -v
```

当前测试状态：**91 tests passed**

测试覆盖：
- Pipeline 生成（结构完整性、字段数量）
- Schema 校验（Pydantic + JSON Schema）
- LLM 配置（provider 解析、key 解析、fallback、所有 provider 默认值）
- Agent Runtime（plan 生成、fallback 行为、LLM 追踪）
- Tool Registry（错误处理、key 泄露防护）
- LangChain Generator（无 key 报错）

## 常见问题

### 页面打不开

确保前端和后端都在运行：

```bash
# 终端 1: 后端
cd backend && uvicorn app.main:app --reload

# 终端 2: 前端
cd frontend/fusion-demo && python -m http.server 5501
```

浏览器访问 http://127.0.0.1:5501/index.html

### Check LLM 显示 key 未配置

编辑 `backend/.env`，设置对应的 API Key：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
```

然后重启后端。

### Run Agent 后 generation_mode 是 rag

说明 LLM 调用失败，Agent fallback 到了 RAG。打开右侧 Drawer 查看：
- `llm_attempted` 是否为 true
- `fallback_reason` 是什么
- 常见原因：API Key 未配置、Key 无效、网络问题、余额不足

### LLM attempted 但 fallback_used=true

查看 `fallback_reason` 字段，常见原因：
- `DEEPSEEK_API_KEY 未配置` — 需要在 .env 中设置 key
- `401 Unauthorized` — key 无效
- `Rate limit exceeded` — 请求频率过高
- `Connection error` — 网络不通

### CORS 或 file:// 问题

推荐通过 `python -m http.server` 打开前端，不要直接双击 `index.html`（file:// 协议下 fetch 会被浏览器阻止）。

后端已配置 `allow_origins=["*"]`，支持所有来源。

### 不要提交 .env

`.gitignore` 已配置忽略 `.env` 文件。如果你的 API Key 意外提交到了 git：

```bash
git rm --cached backend/.env
git commit -m "Remove .env from tracking"
```

然后更改你的 API Key（因为已经暴露）。

## 项目演示话术

> DramaType Agent 不是简单的剧情测试网页，而是一个内容生产 Agent。它接收自然语言目标，自动检查知识库、调用 LLM 或 RAG 生成内容、补齐 evidence_refs、执行 Schema 校验和安全审核，并输出可人工审核的互动内容包。整个过程可追溯、可审计、可修复。

## License

MIT
