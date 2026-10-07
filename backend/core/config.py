"""Pydantic Settings — 12-factor app configuration from env vars / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "VishwasEdge"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Security
    secret_key: str = "change-me-in-production-32-char-minimum-please"
    api_key_header: str = "X-API-Key"
    access_token_expire_minutes: int = 30
    default_admin_username: str = "operator"
    default_admin_password: str = "changeme123"
    default_api_key: str = "dev-local-api-key"
    jwt_algorithm: str = "HS256"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/vishwasedge.db"

    # Cache
    redis_url: str = ""

    # Models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    chroma_persist_dir: str = "./data/processed/chroma"

    # AQR / LLM
    anthropic_api_key: str = ""
    llm_fast_model: str = "claude-haiku-4-5-20251001"
    llm_heavy_model: str = "claude-sonnet-5"

    # Edge constraints
    max_memory_mb: int = 4096
    max_cpu_percent: int = 80
    cache_size_mb: int = 512
    offline_mode: bool = False

    # Monitoring
    enable_metrics: bool = True
    jaeger_endpoint: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
