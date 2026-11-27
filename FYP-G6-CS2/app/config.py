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
    llm_model: str = "gemma4:latest"
    llm_timeout_s: float = 180
    cors_origins: str = "http://localhost:5173"
    rate_limit_per_min: int = 30
    log_retention_days: int = 90
    help_search_ttl_days: int = 30
    help_search_max_results: int = 5
    help_search_prefer_domains: str = "gov,gov.in,nhs.uk,who.int,findahelpline.com"
    embed_model: str = "hashing-n-gram-v1"
    index_version: str = "current"
    index_dir: str = "models_store/index"
    allow_peer_reviewed_non_clinical: bool = False
    ram_budget_mb: int = 256
    page_size: int = 256
    top_k: int = 8
    min_similarity: float = 0.12
    level_high_threshold: float = 0.58
    level_critical_threshold: float = 0.76
    level_confidence_threshold: float = 0.55
    level_decay: float = 0.8
    hysteresis_turns: int = 3
    prefetch_neighbours: int = 2
    mood_smoothing: float = 0.55

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
