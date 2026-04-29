import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parents[2]


def _ensure_env_file():
    """Auto-create .env from .env.example if .env doesn't exist."""
    env_path = _backend_dir / ".env"
    example_path = _backend_dir / ".env.example"
    if not env_path.exists() and example_path.exists():
        shutil.copy2(example_path, env_path)


_ensure_env_file()
load_dotenv(_backend_dir / ".env", override=False)


@dataclass(frozen=True)
class ProviderConfig:
    """Immutable config for a single LLM provider."""
    name: str
    key_env_var: str
    default_base_url: str | None
    default_model: str
    is_openai_compatible: bool = True


_PROVIDER_ALIASES: dict[str, str] = {
    "mimo": "xiaomi",
}

_PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    "anthropic": ProviderConfig(
        name="anthropic",
        key_env_var="ANTHROPIC_API_KEY",
        default_base_url=None,
        default_model="claude-sonnet-4-20250514",
        is_openai_compatible=False,
    ),
    "openai": ProviderConfig(
        name="openai",
        key_env_var="OPENAI_API_KEY",
        default_base_url=None,
        default_model="gpt-4o",
        is_openai_compatible=True,
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        key_env_var="DEEPSEEK_API_KEY",
        default_base_url="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
    ),
    "qwen": ProviderConfig(
        name="qwen",
        key_env_var="DASHSCOPE_API_KEY",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
    ),
    "kimi": ProviderConfig(
        name="kimi",
        key_env_var="MOONSHOT_API_KEY",
        default_base_url="https://api.moonshot.cn/v1",
        default_model="kimi-k2.5",
    ),
    "zhipu": ProviderConfig(
        name="zhipu",
        key_env_var="ZHIPUAI_API_KEY",
        default_base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-5.1",
    ),
    "siliconflow": ProviderConfig(
        name="siliconflow",
        key_env_var="SILICONFLOW_API_KEY",
        default_base_url="https://api.siliconflow.cn/v1",
        default_model="Qwen/Qwen3-8B",
    ),
    "custom_openai_compatible": ProviderConfig(
        name="custom_openai_compatible",
        key_env_var="LLM_API_KEY",
        default_base_url=None,
        default_model="",
    ),
    "xiaomi": ProviderConfig(
        name="xiaomi",
        key_env_var="XIAOMI_API_KEY",
        default_base_url="https://api.mimo-v2.com/v1",
        default_model="mimo-v2.5-pro",
    ),
}


def _resolve_provider(provider: str) -> str:
    return _PROVIDER_ALIASES.get(provider, provider)


def _get_provider_config(provider: str) -> ProviderConfig | None:
    canonical = _resolve_provider(provider)
    return _PROVIDER_CONFIGS.get(canonical)


class Settings:
    """DramaType Agent configuration. All values read from env with safe defaults."""

    AGENT_MODE: str = os.getenv("DRAMATYPE_AGENT_MODE", "rule_based")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")
    LLM_MODEL: str | None = os.getenv("LLM_MODEL") or None
    LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL") or None
    LLM_API_KEY: str | None = os.getenv("LLM_API_KEY") or None

    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY") or None
    DEEPSEEK_API_KEY: str | None = os.getenv("DEEPSEEK_API_KEY") or None
    DASHSCOPE_API_KEY: str | None = os.getenv("DASHSCOPE_API_KEY") or None
    MOONSHOT_API_KEY: str | None = os.getenv("MOONSHOT_API_KEY") or None
    ZHIPUAI_API_KEY: str | None = os.getenv("ZHIPUAI_API_KEY") or None
    SILICONFLOW_API_KEY: str | None = os.getenv("SILICONFLOW_API_KEY") or None
    XIAOMI_API_KEY: str | None = os.getenv("XIAOMI_API_KEY") or None

    RAG_ENABLED: bool = os.getenv("RAG_ENABLED", "true").lower() == "true"
    VECTOR_STORE_PROVIDER: str = os.getenv("VECTOR_STORE_PROVIDER", "chroma")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "keyword")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "data/vector_store/chroma")

    @property
    def env_file_path(self) -> str:
        return str(_backend_dir / ".env")

    def _get_key_for_provider(self, provider: str) -> str | None:
        """Get API key for a provider. Falls back to LLM_API_KEY if provider key is empty."""
        pcfg = _get_provider_config(provider)
        if pcfg is None:
            return None
        env_map = {
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "DEEPSEEK_API_KEY": self.DEEPSEEK_API_KEY,
            "DASHSCOPE_API_KEY": self.DASHSCOPE_API_KEY,
            "MOONSHOT_API_KEY": self.MOONSHOT_API_KEY,
            "ZHIPUAI_API_KEY": self.ZHIPUAI_API_KEY,
            "SILICONFLOW_API_KEY": self.SILICONFLOW_API_KEY,
            "LLM_API_KEY": self.LLM_API_KEY,
            "XIAOMI_API_KEY": self.XIAOMI_API_KEY,
        }
        key = env_map.get(pcfg.key_env_var)
        if key:
            return key
        # Fallback to LLM_API_KEY if provider-specific key is empty
        if pcfg.key_env_var != "LLM_API_KEY" and self.LLM_API_KEY:
            return self.LLM_API_KEY
        return None

    def get_key_source(self, provider: str) -> str:
        """Return which env var provided the key for a provider."""
        pcfg = _get_provider_config(provider)
        if pcfg is None:
            return "none"
        env_map = {
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "DEEPSEEK_API_KEY": self.DEEPSEEK_API_KEY,
            "DASHSCOPE_API_KEY": self.DASHSCOPE_API_KEY,
            "MOONSHOT_API_KEY": self.MOONSHOT_API_KEY,
            "ZHIPUAI_API_KEY": self.ZHIPUAI_API_KEY,
            "SILICONFLOW_API_KEY": self.SILICONFLOW_API_KEY,
            "LLM_API_KEY": self.LLM_API_KEY,
            "XIAOMI_API_KEY": self.XIAOMI_API_KEY,
        }
        if env_map.get(pcfg.key_env_var):
            return pcfg.key_env_var
        if pcfg.key_env_var != "LLM_API_KEY" and self.LLM_API_KEY:
            return "LLM_API_KEY"
        return "none"

    def get_warnings(self, provider: str) -> list[str]:
        """Return warnings for current provider config."""
        warnings = []
        source = self.get_key_source(provider)
        pcfg = _get_provider_config(provider)
        if pcfg and source == "LLM_API_KEY" and pcfg.key_env_var != "LLM_API_KEY":
            warnings.append(
                f"使用 LLM_API_KEY 作为 {provider} 的 key。"
                f"建议改用 {pcfg.key_env_var}。"
            )
        if provider == "custom_openai_compatible" and not self.LLM_BASE_URL:
            warnings.append("custom_openai_compatible 需要设置 LLM_BASE_URL。")
        return warnings

    @property
    def current_provider_config(self) -> ProviderConfig | None:
        return _get_provider_config(self.LLM_PROVIDER)

    @property
    def has_llm_key(self) -> bool:
        return bool(self._get_key_for_provider(self.LLM_PROVIDER))

    @property
    def has_any_llm_key(self) -> bool:
        for name in _PROVIDER_CONFIGS:
            if self._get_key_for_provider(name):
                return True
        return False

    @property
    def llm_model_name(self) -> str:
        if self.LLM_MODEL:
            return self.LLM_MODEL
        pcfg = _get_provider_config(self.LLM_PROVIDER)
        if pcfg:
            return pcfg.default_model
        return "claude-sonnet-4-20250514"

    @property
    def llm_base_url(self) -> str | None:
        if self.LLM_BASE_URL:
            return self.LLM_BASE_URL
        pcfg = _get_provider_config(self.LLM_PROVIDER)
        if pcfg:
            return pcfg.default_base_url
        return None

    @property
    def llm_api_key(self) -> str | None:
        return self._get_key_for_provider(self.LLM_PROVIDER)

    @property
    def is_openai_compatible(self) -> bool:
        pcfg = _get_provider_config(self.LLM_PROVIDER)
        return pcfg.is_openai_compatible if pcfg else False

    @property
    def is_rule_based(self) -> bool:
        return self.AGENT_MODE == "rule_based"


settings = Settings()
