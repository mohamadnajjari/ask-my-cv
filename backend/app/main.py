"""HTTP API for the CV assistant.

The Anthropic API key lives only here, on the server. The static chat page
(GitHub Pages) calls POST /api/chat and never sees the key.
"""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .assistant import AnthropicClient, CVAssistant, MockClient
from .config import Settings, get_settings
from .ratelimit import RateLimiter
from .retrieval import Retriever, load_chunks

log = logging.getLogger("ask-my-cv")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=40)

    @field_validator("messages")
    @classmethod
    def last_is_user(cls, v: list[Message]) -> list[Message]:
        if v[-1].role != "user":
            raise ValueError("last message must be from the user")
        return v


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


def build_app(settings: Settings | None = None, client=None) -> FastAPI:
    settings = settings or get_settings()
    chunks = load_chunks(settings.knowledge_dir)
    retriever = Retriever(chunks)
    summary = (settings.knowledge_dir / "_summary.md").read_text(encoding="utf-8")
    contact = (settings.knowledge_dir / "_contact.md").read_text(encoding="utf-8")

    if client is None:
        if settings.llm_mode == "mock":
            client = MockClient(retriever)
        else:
            if not settings.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not set (or use LLM_MODE=mock)")
            client = AnthropicClient(settings.api_key)

    assistant = CVAssistant(retriever, summary, contact, client, settings.model,
                            settings.max_output_tokens, settings.max_tool_rounds)
    limiter = RateLimiter(settings.rate_limit_per_ip, settings.rate_limit_window, settings.daily_cap)

    app = FastAPI(title="Ask my CV", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type"],
        max_age=3600,
    )

    def client_ip(request: Request) -> str:
        if settings.trust_proxy:
            fwd = request.headers.get("x-forwarded-for", "")
            if fwd:
                return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "chunks": str(len(chunks))}

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, request: Request) -> ChatResponse:
        if len(body.messages[-1].content) > settings.max_message_chars:
            raise HTTPException(413, f"Please keep questions under {settings.max_message_chars} characters.")
        reason = limiter.check(client_ip(request))
        if reason == "rate_limited":
            raise HTTPException(429, "Too many questions in a short time. Please try again in a few minutes.")
        if reason == "daily_cap":
            raise HTTPException(429, "The assistant has reached today's limit. Please contact Mohammad directly.")

        history = [m.model_dump() for m in body.messages][-(settings.max_history_turns * 2 + 1):]
        if history[0]["role"] != "user":
            history = history[1:]
        try:
            result = assistant.answer(history)
        except Exception:  # never leak internals to the browser
            log.exception("chat failed")
            raise HTTPException(502, "The assistant is temporarily unavailable. Please try again later.")
        return ChatResponse(**result)

    return app


def create_app() -> FastAPI:  # uvicorn factory entry point
    logging.basicConfig(level=logging.INFO)
    return build_app()
