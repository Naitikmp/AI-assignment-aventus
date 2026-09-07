import logging

from src.policy_agent.config import AgentConfig
from src.policy_agent.providers.base import BasePolicyProvider
from src.policy_agent.providers.local_engine import LocalPolicyProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory pattern for creating policy answer synthesis providers."""

    @staticmethod
    def create(provider_name: str = None) -> tuple[BasePolicyProvider, str]:
        target = (provider_name or AgentConfig.get_effective_provider()).strip().lower()

        if target == "openrouter":
            try:
                from src.policy_agent.providers.openrouter_provider import OpenRouterProvider
                return OpenRouterProvider(), "openrouter"
            except Exception as e:
                logger.warning(f"Could not initialize OpenRouter ({e}). Using LocalPolicyProvider.")
                return LocalPolicyProvider(), "local"

        elif target == "openai":
            try:
                from src.policy_agent.providers.openai_provider import OpenAIProvider
                return OpenAIProvider(), "openai"
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI ({e}). Using LocalPolicyProvider.")
                return LocalPolicyProvider(), "local"
        return LocalPolicyProvider(), "local"
