"""Typed settings loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration; secrets must be provided by the environment."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "local"
    database_url: str = ""
    database_url_direct: str = ""
    jwt_secret: str = ""
    access_ttl_min: int = 15
    refresh_ttl_days: int = 14
    field_encryption_key: str = ""
    ollama_host: str = "http://127.0.0.1:8001"
    ollama_api_key: str = ""
    llm_model: str = "gemma3:270m"
    llm_timeout_s: float = 180
    cors_origins: str = "http://localhost:5173"
    rate_limit_per_min: int = 30
    log_retention_days: int = 90
    help_search_ttl_days: int = 30
    help_search_max_results: int = 5
    help_search_prefer_domains: str = "gov,gov.in,nhs.uk,who.int,findahelpline.com"

    @property
    def preferred_help_domains(self) -> list[str]:
        return [x.strip().lower() for x in self.help_search_prefer_domains.split(",") if x.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [v.strip() for v in self.cors_origins.split(",") if v.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings. Incoming: none. Outgoing: Settings."""
    return Settings()
