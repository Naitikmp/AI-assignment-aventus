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

    # Provider settings: 'local', 'openrouter', 'openai'
    DEFAULT_PROVIDER: str = os.getenv("LLM_PROVIDER", "local").strip().lower()

    # OpenRouter Settings (OpenAI-compatible - supports free models)
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @classmethod
    def get_effective_provider(cls) -> str:
        """
        Determines the active provider based on environment credentials.
        If a remote provider is requested but credentials are missing,
        it automatically falls back to 'local' to ensure zero crash.
        """
        provider = cls.DEFAULT_PROVIDER
        if provider == "openrouter":
            if not cls.OPENROUTER_API_KEY:
                return "local"
            return "openrouter"
        elif provider == "openai":
            if not cls.OPENAI_API_KEY:
                return "local"
            return "openai"
        elif provider == "openrouter":
            if not cls.OPENROUTER_API_KEY:
                return "local"
            return "openrouter"
        return "local"
