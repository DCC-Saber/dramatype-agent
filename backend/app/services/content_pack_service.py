"""Service layer: bridges API endpoints and the agent pipeline."""

import json
from pathlib import Path

from app.core.config import settings
from app.core.paths import DEFAULT_INPUT_PATH, DEFAULT_OUTPUT_PATH
from app.agent.pipeline import run_pipeline


def get_agent_status() -> dict:
    """Return current agent status and capabilities."""
    return {
        "success": True,
        "message": "DramaType Agent is ready.",
        "data": {
            "agent_name": "DramaType Agent",
            "version": "0.2.0",
            "agent_mode": settings.AGENT_MODE,
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.llm_model_name,
            "has_llm_key": settings.has_llm_key,
            "has_any_llm_key": settings.has_any_llm_key,
            "supported_modes": ["rule_based", "llm", "rag"],
            "input_material_exists": DEFAULT_INPUT_PATH.exists(),
            "content_pack_exists": DEFAULT_OUTPUT_PATH.exists(),
            "needs_human_review": True,
            "description": (
                "DramaType Agent 生成结构化互动叙事内容包。"
                "支持 rule_based（无需 API Key）、llm（需要 API Key）和 rag（知识库检索）三种模式。"
                "LLM 支持 Anthropic 和 OpenAI 两个 provider。"
            ),
        },
    }


def read_generated_content_pack() -> dict:
    """Read the previously generated content pack from disk."""
    if not DEFAULT_OUTPUT_PATH.exists():
        return {
            "success": False,
            "message": "内容包尚未生成。请先调用 POST /api/generate-content-pack。",
            "data": None,
        }

    try:
        content = json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "success": False,
            "message": f"读取内容包失败: {exc}",
            "data": None,
        }

    return {
        "success": True,
        "message": "内容包加载成功。",
        "data": content,
    }


def generate_new_content_pack(mode: str | None = None) -> dict:
    """
    Run the full pipeline and return the result.

    Args:
        mode: "rule_based" or "llm". Defaults to settings.AGENT_MODE.
    """
    effective_mode = mode or settings.AGENT_MODE

    try:
        content_pack = run_pipeline(mode=effective_mode)
        return {
            "success": True,
            "message": f"内容包生成成功（模式: {effective_mode}）。",
            "data": content_pack,
        }
    except Exception as exc:
        return {
            "success": False,
            "message": f"内容包生成失败: {exc}",
            "error": str(exc),
        }
