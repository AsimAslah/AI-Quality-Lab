from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    app_env: str = "development"
    database_url: str = f"sqlite:///{(ROOT / 'data' / 'ai_quality_lab.db').as_posix()}"
    session_secret: str = "local-development-only-change-me"
    cookie_name: str = "aql_owner"
    max_prompt_chars: int = 20_000
    max_response_chars: int = 50_000
    max_reference_chars: int = 30_000
    rate_limit_submissions_per_minute: int = 12
    enable_failure_testing: bool = False

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    provider_timeout_seconds: float = 8.0
    provider_max_attempts: int = 2
    allow_external_ai_with_pii: bool = False

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
