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


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("MODEL", "claude-haiku-4-5"))
    llm_mode: str = field(default_factory=lambda: os.getenv("LLM_MODE", "anthropic").lower())
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.getenv("ALLOWED_ORIGINS", "https://mohamadnajjari.github.io").split(",")
            if o.strip()
        )
    )
    # Flood limit, every kind of answer: beyond it a visitor gets 429 (no human asks that fast).
    rate_limit_per_ip: int = field(default_factory=lambda: _int("RATE_LIMIT_PER_IP", 20))
    rate_limit_window: int = field(default_factory=lambda: _int("RATE_LIMIT_WINDOW_SECONDS", 600))
    daily_cap: int = field(default_factory=lambda: _int("DAILY_REQUEST_CAP", 2000))
    # AI answers (the only ones that cost money) per visitor and in total per UTC day; beyond
    # them, visitors get the closest prepared answer instead.
    ai_quota_per_ip: int = field(default_factory=lambda: _int("AI_QUOTA_PER_IP_PER_DAY", 10))
    ai_answers_per_day: int = field(default_factory=lambda: _int("AI_ANSWERS_PER_DAY", 150))
    trust_proxy: bool = field(
        default_factory=lambda: os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
    )
    # Money (USD): the day's and the month's budget, and the model's price per million tokens
    # (Claude Haiku 4.5: $1 input, $5 output). Change the prices with the model.
    daily_budget_usd: float = field(default_factory=lambda: _float("DAILY_BUDGET_USD", 0.50))
    monthly_budget_usd: float = field(default_factory=lambda: _float("MONTHLY_BUDGET_USD", 5.0))
    usd_per_mtok_in: float = field(default_factory=lambda: _float("INPUT_USD_PER_MTOK", 1.0))
    usd_per_mtok_out: float = field(default_factory=lambda: _float("OUTPUT_USD_PER_MTOK", 5.0))
    # Where the budget's totals survive restarts; unset: memory only (tests, local runs).
    data_dir: Path | None = field(
        default_factory=lambda: Path(os.environ["DATA_DIR"]) if os.getenv("DATA_DIR") else None
    )
    knowledge_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("KNOWLEDGE_DIR", Path(__file__).resolve().parents[2] / "knowledge")
        )
    )
    max_message_chars: int = 600  # the visitor's newest question
    max_conversation_chars: int = 6000  # everything sent along: no huge fake histories
    max_history_messages: int = 5  # sent to the model: the question and the two turns before it
    max_output_tokens: int = 350  # about 250 words: enough for 2-4 sentences in any language


def get_settings() -> Settings:
    return Settings()
