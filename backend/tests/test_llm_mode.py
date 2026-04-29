"""Tests for LLM mode configuration, fallback, and multi-provider support.

No real API keys are used — all tests verify behavior WITHOUT calling LLM APIs.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.config import Settings, _PROVIDER_CONFIGS, _resolve_provider


def _make_settings(provider: str, **keys) -> Settings:
    """Helper to create a Settings instance with specific values."""
    s = Settings.__new__(Settings)
    s.LLM_PROVIDER = provider
    s.LLM_MODEL = None
    s.LLM_BASE_URL = None
    s.LLM_API_KEY = None
    s.ANTHROPIC_API_KEY = None
    s.OPENAI_API_KEY = None
    s.DEEPSEEK_API_KEY = None
    s.DASHSCOPE_API_KEY = None
    s.MOONSHOT_API_KEY = None
    s.ZHIPUAI_API_KEY = None
    s.SILICONFLOW_API_KEY = None
    s.XIAOMI_API_KEY = None
    for k, v in keys.items():
        setattr(s, k, v)
    return s


# ── Provider resolution ──────────────────────────────────

class TestProviderResolution:
    def test_mimo_resolves_to_xiaomi(self):
        assert _resolve_provider("mimo") == "xiaomi"

    def test_xiaomi_stays(self):
        assert _resolve_provider("xiaomi") == "xiaomi"

    def test_unknown_stays(self):
        assert _resolve_provider("foo") == "foo"


# ── Config: key resolution ───────────────────────────────

class TestConfigKeyResolution:
    """Test _get_key_for_provider with primary and fallback keys."""

    def test_deepseek_uses_primary_key(self):
        s = _make_settings("deepseek", DEEPSEEK_API_KEY="sk-ds")
        assert s._get_key_for_provider("deepseek") == "sk-ds"

    def test_deepseek_fallback_to_llm_api_key(self):
        s = _make_settings("deepseek", LLM_API_KEY="sk-fallback")
        assert s._get_key_for_provider("deepseek") == "sk-fallback"

    def test_deepseek_primary_overrides_fallback(self):
        s = _make_settings("deepseek", DEEPSEEK_API_KEY="sk-primary", LLM_API_KEY="sk-fb")
        assert s._get_key_for_provider("deepseek") == "sk-primary"

    def test_xiaomi_uses_primary_key(self):
        s = _make_settings("xiaomi", XIAOMI_API_KEY="xm-key")
        assert s._get_key_for_provider("xiaomi") == "xm-key"

    def test_xiaomi_fallback_to_llm_api_key(self):
        s = _make_settings("xiaomi", LLM_API_KEY="xm-fallback")
        assert s._get_key_for_provider("xiaomi") == "xm-fallback"

    def test_key_source_primary(self):
        s = _make_settings("deepseek", DEEPSEEK_API_KEY="sk-ds")
        assert s.get_key_source("deepseek") == "DEEPSEEK_API_KEY"

    def test_key_source_fallback(self):
        s = _make_settings("deepseek", LLM_API_KEY="sk-fb")
        assert s.get_key_source("deepseek") == "LLM_API_KEY"

    def test_key_source_none(self):
        s = _make_settings("deepseek")
        assert s.get_key_source("deepseek") == "none"

    def test_fallback_warning(self):
        s = _make_settings("deepseek", LLM_API_KEY="sk-fb")
        warnings = s.get_warnings("deepseek")
        assert len(warnings) > 0
        assert "LLM_API_KEY" in warnings[0]
        assert "DEEPSEEK_API_KEY" in warnings[0]


# ── Config: all providers ────────────────────────────────

class TestAllProviderConfigs:
    """Test default models, base URLs, and key checks for all providers."""

    def test_deepseek_defaults(self):
        s = _make_settings("deepseek")
        assert s.llm_model_name == "deepseek-chat"
        assert s.llm_base_url == "https://api.deepseek.com/v1"
        assert s.has_llm_key is False
        assert s.is_openai_compatible is True

    def test_qwen_defaults(self):
        s = _make_settings("qwen")
        assert s.llm_model_name == "qwen-plus"
        assert "dashscope" in (s.llm_base_url or "")

    def test_kimi_defaults(self):
        s = _make_settings("kimi")
        assert s.llm_model_name == "kimi-k2.5"
        assert s.llm_base_url == "https://api.moonshot.cn/v1"

    def test_zhipu_defaults(self):
        s = _make_settings("zhipu")
        assert s.llm_model_name == "glm-5.1"

    def test_siliconflow_defaults(self):
        s = _make_settings("siliconflow")
        assert "Qwen" in s.llm_model_name

    def test_xiaomi_defaults(self):
        s = _make_settings("xiaomi")
        assert s.llm_model_name == "mimo-v2.5-pro"
        assert s.llm_base_url == "https://api.mimo-v2.com/v1"

    def test_mimo_alias_defaults(self):
        s = _make_settings("mimo", XIAOMI_API_KEY="k")
        assert s.has_llm_key is True
        assert s.llm_model_name == "mimo-v2.5-pro"

    def test_custom_requires_base_url(self):
        s = _make_settings("custom_openai_compatible", LLM_API_KEY="k")
        warnings = s.get_warnings("custom_openai_compatible")
        assert any("LLM_BASE_URL" in w for w in warnings)


# ── Config: overrides ────────────────────────────────────

class TestConfigOverrides:
    def test_model_override(self):
        s = _make_settings("xiaomi", XIAOMI_API_KEY="k")
        s.LLM_MODEL = "mimo-v2-flash"
        assert s.llm_model_name == "mimo-v2-flash"

    def test_model_override_any_string(self):
        s = _make_settings("xiaomi", XIAOMI_API_KEY="k")
        s.LLM_MODEL = "my-custom-v3-model"
        assert s.llm_model_name == "my-custom-v3-model"

    def test_base_url_override(self):
        s = _make_settings("xiaomi", XIAOMI_API_KEY="k")
        s.LLM_BASE_URL = "https://custom.mimo.com/v1"
        assert s.llm_base_url == "https://custom.mimo.com/v1"

    def test_has_any_llm_key(self):
        s = _make_settings("anthropic", XIAOMI_API_KEY="xm")
        assert s.has_any_llm_key is True

    def test_has_any_llm_key_false(self):
        s = _make_settings("anthropic")
        assert s.has_any_llm_key is False


# ── Tool registry LLM error ──────────────────────────────

class TestToolRegistryLLM:
    def test_error_without_key(self):
        from app.agent_runtime.tool_registry import call_tool
        with patch("app.agent_runtime.tool_registry.settings") as mock_s:
            mock_s.has_llm_key = False
            mock_s.LLM_PROVIDER = "deepseek"
            mock_s.current_provider_config = _PROVIDER_CONFIGS["deepseek"]
            data, error = call_tool("generate_content_pack_llm", {})
            assert data is None
            assert "LLM key" in error
            assert "DEEPSEEK_API_KEY" in error

    def test_error_with_mimo_alias(self):
        from app.agent_runtime.tool_registry import call_tool
        pcfg = _PROVIDER_CONFIGS["xiaomi"]
        with patch("app.agent_runtime.tool_registry.settings") as mock_s:
            mock_s.has_llm_key = False
            mock_s.LLM_PROVIDER = "mimo"
            mock_s.current_provider_config = pcfg
            _, error = call_tool("generate_content_pack_llm", {})
            assert "XIAOMI_API_KEY" in error


# ── Agent fallback ────────────────────────────────────────

class TestAgentFallback:
    def test_llm_fallback_deepseek(self):
        from app.agent_runtime.agent import run_agent
        from app.agent_runtime.schemas import AgentRunRequest
        with patch("app.agent_runtime.tool_registry.settings") as mock_s:
            mock_s.has_llm_key = False
            mock_s.LLM_PROVIDER = "deepseek"
            result = run_agent(AgentRunRequest(
                goal="请用 DeepSeek 生成内容包。",
                preferred_mode="llm",
                max_steps=15,
            ))
            assert result.final_content_pack is not None

    def test_llm_fallback_tracks_attempt(self):
        """When preferred_mode=llm, memory should track the attempt."""
        from app.agent_runtime.agent import run_agent
        from app.agent_runtime.schemas import AgentRunRequest
        with patch("app.agent_runtime.tool_registry.settings") as mock_s:
            mock_s.has_llm_key = False
            mock_s.LLM_PROVIDER = "deepseek"
            result = run_agent(AgentRunRequest(
                goal="请用 DeepSeek 生成内容包。",
                preferred_mode="llm",
                max_steps=15,
            ))
            # Check review_report has LLM tracking info
            if result.review_report:
                assert result.review_report.get("llm_attempted") is True
                assert result.review_report.get("fallback_used") is True
                assert result.review_report.get("final_generation_mode") in ("rag", "rule_based")

    def test_llm_fallback_agent_meta(self):
        """Fallback content_pack.agent_meta should record LLM attempt."""
        from app.agent_runtime.agent import run_agent
        from app.agent_runtime.schemas import AgentRunRequest
        with patch("app.agent_runtime.tool_registry.settings") as mock_s:
            mock_s.has_llm_key = False
            mock_s.LLM_PROVIDER = "deepseek"
            result = run_agent(AgentRunRequest(
                goal="请用 DeepSeek 生成。",
                preferred_mode="llm",
                max_steps=15,
            ))
            if result.final_content_pack:
                meta = result.final_content_pack.get("agent_meta", {})
                assert meta.get("llm_attempted") is True
                assert meta.get("llm_provider_attempted") == "deepseek"
                assert meta.get("fallback_from_llm") is True
                assert meta.get("fallback_reason") is not None

    def test_llm_fallback_reason_not_empty(self):
        from app.agent_runtime.agent import run_agent
        from app.agent_runtime.schemas import AgentRunRequest
        with patch("app.agent_runtime.tool_registry.settings") as mock_s:
            mock_s.has_llm_key = False
            mock_s.LLM_PROVIDER = "xiaomi"
            result = run_agent(AgentRunRequest(
                goal="请用 MiMo 生成。",
                preferred_mode="llm",
                max_steps=15,
            ))
            if result.review_report:
                reason = result.review_report.get("fallback_reason", "")
                assert len(reason) > 0, "fallback_reason should not be empty"

    def test_rag_mode_no_llm_tracking(self):
        """When preferred_mode=rag, no LLM tracking should appear."""
        from app.agent_runtime.agent import run_agent
        from app.agent_runtime.schemas import AgentRunRequest
        result = run_agent(AgentRunRequest(
            goal="基于知识库生成内容包",
            preferred_mode="rag",
            max_steps=15,
        ))
        if result.review_report:
            assert result.review_report.get("llm_attempted") is not True


# ── LangChain generator errors ──────────────────────────

class TestLangchainGeneratorErrors:
    def test_deepseek_raises_without_key(self):
        from app.agent.langchain_generator import generate_content_pack_with_langchain
        with patch("app.core.config.settings") as mock_s:
            mock_s.LLM_PROVIDER = "deepseek"
            mock_s.llm_model_name = "deepseek-chat"
            mock_s.llm_base_url = "https://api.deepseek.com/v1"
            mock_s.llm_api_key = None
            mock_s.current_provider_config = _PROVIDER_CONFIGS["deepseek"]
            with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
                generate_content_pack_with_langchain("test")

    def test_xiaomi_raises_without_key(self):
        from app.agent.langchain_generator import generate_content_pack_with_langchain
        with patch("app.core.config.settings") as mock_s:
            mock_s.LLM_PROVIDER = "xiaomi"
            mock_s.llm_model_name = "mimo-v2.5-pro"
            mock_s.llm_base_url = "https://api.mimo-v2.com/v1"
            mock_s.llm_api_key = None
            mock_s.current_provider_config = _PROVIDER_CONFIGS["xiaomi"]
            with pytest.raises(RuntimeError, match="XIAOMI_API_KEY"):
                generate_content_pack_with_langchain("test")

    def test_custom_raises_without_base_url(self):
        from app.agent.langchain_generator import generate_content_pack_with_langchain
        with patch("app.core.config.settings") as mock_s:
            mock_s.LLM_PROVIDER = "custom_openai_compatible"
            mock_s.llm_model_name = "my-model"
            mock_s.llm_base_url = None
            mock_s.llm_api_key = "some-key"
            mock_s.current_provider_config = _PROVIDER_CONFIGS["custom_openai_compatible"]
            with pytest.raises(RuntimeError, match="LLM_BASE_URL"):
                generate_content_pack_with_langchain("test")


# ── Key leak prevention ──────────────────────────────────

class TestKeyLeakPrevention:
    def test_error_does_not_contain_key(self):
        from app.agent_runtime.tool_registry import call_tool
        with patch("app.agent_runtime.tool_registry.settings") as mock_s:
            mock_s.has_llm_key = False
            mock_s.LLM_PROVIDER = "deepseek"
            mock_s.current_provider_config = _PROVIDER_CONFIGS["deepseek"]
            _, error = call_tool("generate_content_pack_llm", {})
            assert "sk-" not in (error or "")

    def test_masked_url_no_key(self):
        s = _make_settings("xiaomi", XIAOMI_API_KEY="k")
        assert "key" not in s.llm_base_url.lower()
        assert "token" not in s.llm_base_url.lower()
