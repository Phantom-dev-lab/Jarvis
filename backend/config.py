"""Zentrale Konfiguration – liest Werte aus der Umgebung bzw. der .env-Datei."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Claude / Anthropic
    anthropic_api_key: str = ""
    jarvis_model: str = "claude-opus-4-8"
    jarvis_language: str = "Deutsch"
    jarvis_user_name: str = "Sir"

    # Home Assistant
    home_assistant_url: str = ""
    home_assistant_token: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def claude_ready(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def home_assistant_ready(self) -> bool:
        return bool(self.home_assistant_url and self.home_assistant_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
