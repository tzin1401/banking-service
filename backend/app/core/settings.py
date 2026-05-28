"""Application configuration loaded from environment variables.

Adapted from Lab 3 for the microservice architecture. Intent detection is now
delegated to the Intent Service via gRPC, so Unsloth/mock settings are removed.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. All fields can be overridden via env vars."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Ollama (response drafting LLM) ---
    ollama_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
        description="Base URL of the Ollama HTTP server.",
    )
    ollama_model: str = Field(
        default="gpt-oss:20b",
        description="Model tag served by Ollama for drafting.",
    )
    ollama_timeout: float = Field(
        default=600.0,
        description="Per-request timeout in seconds.",
    )
    llm_max_tokens: int = Field(default=2048, ge=64)
    llm_reasoning_effort: str = Field(default="low")

    # --- Intent Service (gRPC) ---
    intent_service_host: str = Field(
        default="intent-service",
        description="Hostname of the Intent gRPC service.",
    )
    intent_service_port: int = Field(
        default=50051,
        description="Port of the Intent gRPC service.",
    )

    # --- Behaviour toggles ---
    mock_llm: bool = Field(
        default=False,
        description="If True, skip Ollama and return a canned draft.",
    )

    # --- Validation thresholds ---
    min_draft_length: int = Field(default=20, ge=1)
    intent_confidence_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (env is read only once)."""
    return Settings()
