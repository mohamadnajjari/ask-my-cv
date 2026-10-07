"""Runtime settings, read once from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("MODEL", "claude-haiku-4-5-20251001"))
    llm_mode: str = field(default_factory=lambda: os.getenv("LLM_MODE", "anthropic").lower())
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.getenv("ALLOWED_ORIGINS", "https://mohamadnajjari.github.io").split(",")
            if o.strip()
        )
    )
    rate_limit_per_ip: int = field(default_factory=lambda: _int("RATE_LIMIT_PER_IP", 20))
    rate_limit_window: int = field(default_factory=lambda: _int("RATE_LIMIT_WINDOW_SECONDS", 600))
    daily_cap: int = field(default_factory=lambda: _int("DAILY_REQUEST_CAP", 400))
    trust_proxy: bool = field(
        default_factory=lambda: os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
    )
    knowledge_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("KNOWLEDGE_DIR", Path(__file__).resolve().parents[2] / "knowledge")
        )
    )
    max_message_chars: int = 600
    max_history_turns: int = 8
    max_output_tokens: int = 700
    max_tool_rounds: int = 3


def get_settings() -> Settings:
    return Settings()
