"""
LangChain-based structured content pack generator.

Supports all configured LLM providers via unified adapter.
Falls back to JSON parsing if structured output is not supported.
"""

import json
import re
import logging

from app.models import ContentPack
from app.agent.prompts import (
    SYSTEM_PROMPT_DRAMATYPE_AGENT,
    MATERIAL_TO_CONTENT_PACK_PROMPT,
)

logger = logging.getLogger(__name__)


def _mask_url(url: str | None) -> str | None:
    if not url:
        return None
    return url


def _mask_key(key: str | None) -> str | None:
    """Show first 4 and last 4 chars of key."""
    if not key or len(key) < 12:
        return None
    return f"{key[:4]}...{key[-4:]}"


def _get_llm(settings):
    """Create the appropriate LangChain LLM based on provider config."""
    from app.core.config import _resolve_provider

    provider = _resolve_provider(settings.LLM_PROVIDER)
    model = settings.llm_model_name
    base_url = settings.llm_base_url
    api_key = settings.llm_api_key

    if not api_key:
        pcfg = settings.current_provider_config
        key_name = pcfg.key_env_var if pcfg else "API_KEY"
        raise RuntimeError(
            f"LLM key 未配置 (provider={settings.LLM_PROVIDER})。"
            f"请设置 {key_name} 或 LLM_API_KEY。"
        )

    if provider == "custom_openai_compatible" and not base_url:
        raise RuntimeError(
            "custom_openai_compatible 需要设置 LLM_BASE_URL。"
        )

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic is not installed. "
                "Run: pip install langchain-anthropic"
            )
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0.3,
            max_tokens=8192,
        )

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is not installed. Run: pip install langchain-openai"
        )

    kwargs = {
        "model": model,
        "api_key": api_key,
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    if base_url:
        kwargs["base_url"] = base_url

    return ChatOpenAI(**kwargs)


def _parse_json_from_text(text: str) -> dict | None:
    """Try to extract and parse JSON from LLM text output."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except (json.JSONDecodeError, TypeError):
            pass

    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def generate_content_pack_with_langchain(
    material_text: str,
    content_pack_schema: type[ContentPack] = ContentPack,
    evidence_context: str | None = None,
) -> dict:
    """
    Generate a content pack using LangChain structured output.

    Supports all configured providers. Falls back to JSON parsing
    if structured output is not supported by the provider.

    Returns:
        dict: The generated content pack as a plain dict.

    Raises:
        RuntimeError: if generation or parsing fails.
        ImportError: if required packages are not installed.
    """
    from app.core.config import settings, _resolve_provider

    llm = _get_llm(settings)
    provider = _resolve_provider(settings.LLM_PROVIDER)
    model = settings.llm_model_name

    logger.info(
        f"LLM 生成开始: provider={provider}, model={model}, "
        f"base_url={settings.llm_base_url}"
    )

    # Build prompts
    user_prompt = MATERIAL_TO_CONTENT_PACK_PROMPT.format(
        material_text=material_text
    )

    if evidence_context:
        user_prompt += (
            f"\n\n以下是知识库检索到的相关证据，生成时请参考并确保内容有据可查：\n"
            f"{evidence_context}\n\n"
            f"请确保每个 question 和 node 都能在上述证据中找到对应来源。"
        )

    from langchain_core.messages import SystemMessage, HumanMessage

    system_prompt = SYSTEM_PROMPT_DRAMATYPE_AGENT
    if provider != "anthropic":
        system_prompt += (
            "\n\n请直接输出完整的 JSON 对象，不要包含任何其他文字、"
            "解释或 markdown 标记。输出必须是合法的 JSON。"
        )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    # Strategy 1: Try structured output
    cp = None
    structured_error = None
    try:
        logger.info("尝试 structured output 方式...")
        structured_llm = llm.with_structured_output(content_pack_schema)
        result: ContentPack = structured_llm.invoke(messages)
        cp = result.model_dump()
        logger.info("structured output 成功。")
    except Exception as exc:
        structured_error = str(exc)[:200]
        logger.warning(f"structured output 失败: {structured_error}")

    # Strategy 2: Fallback to raw text + JSON parse
    if cp is None:
        logger.info("尝试 raw text + JSON parse 方式...")
        try:
            response = llm.invoke(messages)
            text = response.content if hasattr(response, "content") else str(response)
            logger.info(f"LLM 原始输出长度: {len(text)} chars")

            parsed = _parse_json_from_text(text)
            if parsed:
                cp = content_pack_schema.model_validate(parsed).model_dump()
                logger.info("JSON parse + Pydantic 验证成功。")
            else:
                raise RuntimeError(
                    f"LLM 输出无法解析为 JSON。"
                    f"structured_output 错误: {structured_error}. "
                    f"原始输出前 300 字: {text[:300]}"
                )
        except Exception as json_exc:
            if structured_error:
                raise RuntimeError(
                    f"LLM ({provider}/{model}) 生成失败。"
                    f"structured_output: {structured_error}. "
                    f"JSON parse: {str(json_exc)[:200]}"
                )
            raise RuntimeError(
                f"LLM ({provider}/{model}) JSON parse 失败: {str(json_exc)[:200]}"
            )

    # Update agent_meta
    if "agent_meta" not in cp:
        cp["agent_meta"] = {}
    cp["agent_meta"]["llm_provider"] = settings.LLM_PROVIDER
    cp["agent_meta"].setdefault("llm_model", settings.llm_model_name)
    cp["agent_meta"]["llm_base_url_masked"] = _mask_url(settings.llm_base_url)

    logger.info(
        f"LLM 生成完成: provider={settings.LLM_PROVIDER}, "
        f"model={settings.llm_model_name}"
    )

    return cp
