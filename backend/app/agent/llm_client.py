"""LLM client wrapper supporting all configured providers."""

from app.core.config import settings, _get_provider_config, _resolve_provider


class LLMClient:
    """
    Thin wrapper around LLM providers.
    is_available() returns False when no API key is configured,
    so rule_based mode always works.
    """

    def __init__(self, provider: str | None = None):
        raw = provider or settings.LLM_PROVIDER
        self.provider = _resolve_provider(raw)
        self._config = _get_provider_config(self.provider)

    def is_available(self) -> bool:
        """Check if the current provider's API key is configured."""
        return bool(settings._get_key_for_provider(self.provider))

    @property
    def model_name(self) -> str:
        return settings.llm_model_name

    @property
    def base_url(self) -> str | None:
        if settings.LLM_BASE_URL:
            return settings.LLM_BASE_URL
        return self._config.default_base_url if self._config else None

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Placeholder for direct LLM JSON generation.
        For structured output, prefer langchain_generator instead.
        """
        if not self.is_available():
            key_name = (
                self._config.key_env_var if self._config else "API_KEY"
            )
            raise RuntimeError(
                f"No {key_name} configured for provider '{self.provider}'. "
                "Please use mode='rule_based' or add your API key to .env"
            )

        raise NotImplementedError(
            "Direct LLM JSON generation is not implemented. "
            "Use langchain_generator for structured output with LangChain."
        )
