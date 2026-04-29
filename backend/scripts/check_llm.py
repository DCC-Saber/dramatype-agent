#!/usr/bin/env python3
"""
LLM configuration diagnostic script.

Usage:
    python scripts/check_llm.py

Checks current .env LLM configuration and optionally sends a test message.
"""

import sys
import os
import time

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from app.core.config import settings, _resolve_provider, _PROVIDER_CONFIGS

    print("=" * 60)
    print("DramaType Agent - LLM Configuration Diagnostic")
    print("=" * 60)

    # Env file
    print(f"\n.env 路径:      {settings.env_file_path}")
    env_exists = os.path.exists(settings.env_file_path)
    print(f".env 存在:       {'是' if env_exists else '否 (将从 .env.example 自动创建)'}")

    # Provider
    provider = _resolve_provider(settings.LLM_PROVIDER)
    print(f"\nLLM_PROVIDER:   {settings.LLM_PROVIDER}")
    if provider != settings.LLM_PROVIDER:
        print(f"  -> 解析为:     {provider}")

    # Model
    print(f"LLM_MODEL:      {settings.LLM_MODEL or '(使用默认)'}")
    print(f"  -> 实际模型:   {settings.llm_model_name}")

    # Base URL
    print(f"LLM_BASE_URL:   {settings.LLM_BASE_URL or '(使用默认)'}")
    print(f"  -> 实际 URL:   {settings.llm_base_url or '(无)'}")

    # API Key
    has_key = settings.has_llm_key
    key_source = settings.get_key_source(provider)
    print(f"\nAPI Key 状态:   {'已配置' if has_key else '未配置'}")
    print(f"API Key 来源:   {key_source}")

    if has_key:
        key = settings.llm_api_key
        masked = f"{key[:4]}...{key[-4:]}" if key and len(key) >= 12 else "***"
        print(f"API Key 掩码:   {masked}")

    # Warnings
    warnings = settings.get_warnings(provider)
    if warnings:
        print(f"\n警告:")
        for w in warnings:
            print(f"  - {w}")

    # OpenAI compatible
    print(f"\nOpenAI 兼容:    {'是' if settings.is_openai_compatible else '否'}")

    # All providers summary
    print(f"\n{'─' * 60}")
    print("所有 Provider Key 状态:")
    for name, pcfg in _PROVIDER_CONFIGS.items():
        key_val = settings._get_key_for_provider(name)
        status = "已配置" if key_val else "未配置"
        source = settings.get_key_source(name)
        print(f"  {name:30s} {status:6s}  来源: {source}")

    # Test LLM call
    print(f"\n{'─' * 60}")
    if not has_key:
        print("跳过 LLM 测试: API Key 未配置。")
        print("请在 .env 中设置对应的 API Key 后重新运行。")
        return

    print(f"正在测试 LLM 调用 ({provider}/{settings.llm_model_name})...")

    try:
        from app.agent.langchain_generator import _get_llm
        from langchain_core.messages import HumanMessage

        llm = _get_llm(settings)
        start = time.time()
        response = llm.invoke([HumanMessage(content="只回复 OK")])
        latency = int((time.time() - start) * 1000)
        text = response.content if hasattr(response, "content") else str(response)
        print(f"LLM 调用成功!")
        print(f"  响应: {str(text)[:100]}")
        print(f"  延迟: {latency}ms")
    except Exception as exc:
        print(f"LLM 调用失败!")
        print(f"  错误: {str(exc)[:200]}")

    print(f"\n{'=' * 60}")
    print("诊断完成。")


if __name__ == "__main__":
    main()
