from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsightForge AI"
    environment: str = "development"
    frontend_origin: str = "http://localhost:5173"
    ai_provider: str = "local"
    ai_provider_strategy: str = "fallback"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    huggingface_api_key: str | None = None
    huggingface_model: str = "Qwen/Qwen2.5-7B-Instruct"
    huggingface_provider: str = "auto"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "datasets"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
