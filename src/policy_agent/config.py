import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    pass


class AgentConfig:
    """Central configuration for travel policy agent."""
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_PATH: Path = (
        BASE_DIR / "data" / "travel_expense_policy.csv"
        if (BASE_DIR / "data" / "travel_expense_policy.csv").exists()
        else BASE_DIR / "travel_expense_policy.csv"
    )

    # Provider settings: 'local', 'azure_openai', 'openai'
    DEFAULT_PROVIDER: str = os.getenv("LLM_PROVIDER", "local").strip().lower()

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Azure OpenAI Settings
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    # OpenRouter Settings (OpenAI-compatible)
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    @classmethod
    def get_effective_provider(cls) -> str:
        """
        Determines the active provider based on environment credentials.
        If a remote provider is requested but credentials are missing,
        it automatically falls back to 'local' to ensure zero crash.
        """
        provider = cls.DEFAULT_PROVIDER
        if provider == "azure_openai":
            if not cls.AZURE_OPENAI_API_KEY or not cls.AZURE_OPENAI_ENDPOINT:
                return "local"
            return "azure_openai"
        elif provider == "openai":
            if not cls.OPENAI_API_KEY:
                return "local"
            return "openai"
        elif provider == "openrouter":
            if not cls.OPENROUTER_API_KEY:
                return "local"
            return "openrouter"
        return "local"
