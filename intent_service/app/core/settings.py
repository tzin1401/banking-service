"""Intent Service configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Intent gRPC service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Ollama (used for intent prediction) ---
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL of the Ollama HTTP server.",
    )
    intent_model_name: str = Field(
        default="gpt-oss:20b",
        description="Model tag served by Ollama for intent prediction.",
    )
    ollama_timeout: float = Field(
        default=120.0,
        description="Per-request timeout in seconds for Ollama calls.",
    )

    # --- gRPC ---
    grpc_port: int = Field(
        default=50051,
        description="Port the gRPC server listens on.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
