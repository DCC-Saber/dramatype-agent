"""FastAPI application entry point for DramaType Agent."""

import time

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.content_pack_service import (
    get_agent_status,
    read_generated_content_pack,
    generate_new_content_pack,
)
from app.agent.schema_validator import validate_with_pydantic, validate_with_json_schema
from app.agent.knowledge_ingestor import rebuild_index, get_knowledge_stats
from app.agent.rag_retriever import retrieve_knowledge
from app.agent_runtime.schemas import AgentRunRequest
from app.agent_runtime.agent import run_agent, get_last_run

app = FastAPI(
    title="剧格 AI DramaType Agent API",
    description="面向腾讯视频剧集内容的 AI 互动叙事内容生产 Agent（RAG + LangGraph + Autonomous Agent）",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────

class GenerateRequest(BaseModel):
    mode: str = "rule_based"


# ── Endpoints ──────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "name": "剧格 AI DramaType Agent",
        "version": "0.2.0",
        "status": "running",
        "supported_modes": ["rule_based", "llm", "rag"],
        "message": "DramaType Agent 后端服务运行中。",
    }


@app.get("/api/agent/status")
def agent_status():
    return get_agent_status()


@app.get("/api/content-pack")
def get_content_pack():
    return read_generated_content_pack()


@app.post("/api/generate-content-pack")
def generate_content_pack(req: GenerateRequest = GenerateRequest()):
    return generate_new_content_pack(mode=req.mode)


@app.post("/api/validate-content-pack")
def validate_endpoint():
    """Validate the current output JSON against Pydantic + JSON Schema."""
    result = read_generated_content_pack()
    if not result["success"]:
        return {"success": False, "message": result["message"]}

    try:
        validate_with_pydantic(result["data"])
        validate_with_json_schema(result["data"])
        return {"success": True, "message": "内容包校验通过。"}
    except Exception as exc:
        return {"success": False, "message": f"校验失败: {exc}"}


@app.post("/api/knowledge/rebuild-index")
def rebuild_knowledge_index():
    """Rebuild the knowledge base vector store index."""
    try:
        result = rebuild_index()
        return result
    except Exception as exc:
        return {
            "success": False,
            "message": f"索引重建失败: {exc}",
            "docs_ingested": 0,
        }


@app.get("/api/knowledge/search")
def search_knowledge(q: str = Query(..., description="搜索关键词")):
    """Search the knowledge base."""
    try:
        context, refs = retrieve_knowledge(q, top_k=5)
        return {
            "success": True,
            "message": f"找到 {len(refs)} 条相关知识。",
            "data": {
                "query": q,
                "context": context,
                "evidence_refs": refs,
            },
        }
    except Exception as exc:
        return {
            "success": False,
            "message": f"搜索失败: {exc}",
        }


@app.get("/api/knowledge/stats")
def knowledge_stats():
    """Return knowledge base statistics."""
    return {
        "success": True,
        "message": "知识库统计信息。",
        "data": get_knowledge_stats(),
    }


# ── Agent Runtime Endpoints ────────────────────────────

@app.post("/api/agent/run")
def agent_run(req: AgentRunRequest):
    """Run the autonomous Agent with a natural language goal."""
    try:
        result = run_agent(req)
        return result.model_dump()
    except Exception as exc:
        return {
            "success": False,
            "goal": req.goal,
            "plan": {"goal": req.goal, "steps": [], "expected_output": ""},
            "steps": [],
            "final_content_pack_path": None,
            "final_content_pack": None,
            "review_report": None,
            "errors": [str(exc)],
            "needs_human_review": True,
        }


@app.get("/api/agent/last-run")
def agent_last_run():
    """Return the most recent Agent run trace."""
    last = get_last_run()
    if last is None:
        return {
            "success": False,
            "message": "还没有 Agent 执行记录。请先调用 POST /api/agent/run。",
        }
    return last.model_dump()


# ── LLM Diagnostic Endpoints ─────────────────────────────

@app.get("/api/llm/status")
def llm_status():
    """Return current LLM provider configuration status."""
    from app.core.config import settings, _resolve_provider
    provider = _resolve_provider(settings.LLM_PROVIDER)
    return {
        "provider": provider,
        "model": settings.llm_model_name,
        "base_url": settings.llm_base_url,
        "has_api_key": settings.has_llm_key,
        "api_key_source": settings.get_key_source(provider),
        "is_openai_compatible": settings.is_openai_compatible,
        "warnings": settings.get_warnings(provider),
    }


class LLMTestRequest(BaseModel):
    message: str = "只回复 OK"


@app.post("/api/llm/test")
def llm_test(req: LLMTestRequest):
    """Send a minimal test message to the configured LLM provider."""
    from app.core.config import settings, _resolve_provider
    from langchain_core.messages import HumanMessage

    provider = _resolve_provider(settings.LLM_PROVIDER)
    model = settings.llm_model_name

    if not settings.has_llm_key:
        return {
            "success": False,
            "provider": provider,
            "model": model,
            "error_type": "config_error",
            "error_message": f"API key 未配置。请设置 {settings.get_key_source(provider)}。",
        }

    try:
        from app.agent.langchain_generator import _get_llm
        llm = _get_llm(settings)
    except RuntimeError as exc:
        return {
            "success": False,
            "provider": provider,
            "model": model,
            "error_type": "config_error",
            "error_message": str(exc)[:200],
        }
    except ImportError as exc:
        return {
            "success": False,
            "provider": provider,
            "model": model,
            "error_type": "config_error",
            "error_message": str(exc)[:200],
        }

    start = time.time()
    try:
        response = llm.invoke([HumanMessage(content=req.message)])
        text = response.content if hasattr(response, "content") else str(response)
        latency = int((time.time() - start) * 1000)
        return {
            "success": True,
            "provider": provider,
            "model": model,
            "response_preview": str(text)[:200],
            "latency_ms": latency,
        }
    except Exception as exc:
        latency = int((time.time() - start) * 1000)
        err_str = str(exc)
        # Classify error type
        if "401" in err_str or "unauthorized" in err_str.lower() or "auth" in err_str.lower():
            error_type = "auth_error"
        elif "400" in err_str or "invalid" in err_str.lower():
            error_type = "request_error"
        elif "timeout" in err_str.lower():
            error_type = "request_error"
        else:
            error_type = "request_error"
        # Strip any potential key content from error
        safe_err = err_str[:200]
        return {
            "success": False,
            "provider": provider,
            "model": model,
            "error_type": error_type,
            "error_message": safe_err,
            "latency_ms": latency,
        }
