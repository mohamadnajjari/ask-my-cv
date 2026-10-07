"""HTTP API for the CV assistant.

The Anthropic API key lives only here, on the server. The static chat page
(GitHub Pages) calls POST /api/chat and never sees the key.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .assistant import AnthropicClient, CVAssistant, MockClient
from .budget import Budget
from .cache import AnswerCache
from .config import Settings, get_settings
from .prepared import PreparedAnswers, detect_lang
from .ratelimit import DailyQuota, RateLimiter
from .retrieval import Retriever, load_chunks

log = logging.getLogger("ask-my-cv")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=40)
    # The page's language; without it, the question's own language is detected.
    lang: Literal["en", "de", "fa"] | None = None
    # A suggestion button asks for its prepared answer directly (0 tokens).
    prepared_id: str | None = Field(default=None, pattern=r"^[a-z0-9-]{1,40}$")

    @field_validator("messages")
    @classmethod
    def last_is_user(cls, v: list[Message]) -> list[Message]:
        if v[-1].role != "user":
            raise ValueError("last message must be from the user")
        return v


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    # Where the answer came from: "prepared" and "cached" cost nothing, "ai" called the model,
    # "limited" is a prepared answer given because a limit was reached (the page says so).
    kind: Literal["prepared", "cached", "ai", "limited"]


def build_app(settings: Settings | None = None, client=None) -> FastAPI:
    settings = settings or get_settings()
    chunks = load_chunks(settings.knowledge_dir)
    retriever = Retriever(chunks)
    summary = (settings.knowledge_dir / "_summary.md").read_text(encoding="utf-8")
    contact = (settings.knowledge_dir / "_contact.md").read_text(encoding="utf-8")

    if client is None:
        if settings.llm_mode == "mock":
            client = MockClient()
        else:
            if not settings.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not set (or use LLM_MODE=mock)")
            client = AnthropicClient(settings.api_key)

    assistant = CVAssistant(retriever, summary, contact, client, settings.model,
                            settings.max_output_tokens, settings.max_history_messages)
    prepared = PreparedAnswers(settings.knowledge_dir / "answers.json")
    # Fingerprint of everything the answers come from: a CV change empties the cache.
    knowledge = hashlib.sha256()
    for path in sorted(settings.knowledge_dir.iterdir()):
        if path.suffix in (".md", ".json"):
            knowledge.update(path.name.encode() + b"\0" + path.read_bytes())
    cache = AnswerCache(settings.data_dir / "answers-cache.json" if settings.data_dir else None,
                        version=knowledge.hexdigest()[:16])
    limiter = RateLimiter(settings.rate_limit_per_ip, settings.rate_limit_window, settings.daily_cap)
    quota = DailyQuota(settings.ai_quota_per_ip, settings.ai_answers_per_day)
    budget = Budget(
        settings.data_dir / "usage.json" if settings.data_dir else None,
        settings.daily_budget_usd,
        settings.monthly_budget_usd,
        settings.usd_per_mtok_in,
        settings.usd_per_mtok_out,
    )

    app = FastAPI(title="Ask my CV", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type"],
        max_age=3600,
    )

    def client_ip(request: Request) -> str:
        # Behind Cloudflare (TRUST_PROXY_HEADERS=true): Cloudflare writes the visitor's address
        # into CF-Connecting-IP and overwrites any value a visitor sends, unlike X-Forwarded-For,
        # whose first entry anyone can fake. The origin accepts only Cloudflare's addresses.
        raw = request.headers.get("cf-connecting-ip", "") if settings.trust_proxy else ""
        raw = raw or (request.client.host if request.client else "")
        try:
            return str(ipaddress.ip_address(raw.strip()))
        except ValueError:
            return "unknown"  # one shared bucket, never unlimited

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "chunks": str(len(chunks))}

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, request: Request) -> ChatResponse:
        question = body.messages[-1].content
        if len(question) > settings.max_message_chars:
            raise HTTPException(413, f"Please keep questions under {settings.max_message_chars} characters.")
        history = [m.model_dump() for m in body.messages][-settings.max_history_messages:]
        if sum(len(m["content"]) for m in history) > settings.max_conversation_chars:
            raise HTTPException(413, "This conversation is too long. Please start a new one.")
        ip = client_ip(request)
        if limiter.check(ip) is not None:  # a flood, whatever it asks for
            raise HTTPException(429, "Too many questions in a short time. Please try again in a few minutes.")
        lang = body.lang or detect_lang(question)

        # 1. A suggestion button: its prepared answer (0 tokens).
        if body.prepared_id is not None:
            answer = prepared.by_id(body.prepared_id, lang)
            if answer is None:
                raise HTTPException(404, "Unknown suggestion.")
            return ChatResponse(answer=answer, sources=[], kind="prepared")
        # 2. A single question (not a follow-up, which depends on its conversation): a prepared
        #    answer that clearly fits, or the same question answered before (0 tokens).
        if len(body.messages) == 1:
            match = prepared.match(question, lang)
            if match is not None:
                return ChatResponse(answer=match[1], sources=[], kind="prepared")
            hit = cache.get(question, lang)
            if hit is not None:
                return ChatResponse(answer=hit["answer"], sources=hit["sources"], kind="cached")
        # 3. The model, within the money budget and the AI quotas; otherwise the closest prepared
        #    answer, so overuse costs nothing and the visitor still gets something useful.
        reason = budget.check() or quota.take(ip)
        if reason is not None:
            log.info(json.dumps({"event": "limited", "reason": reason}))
            return ChatResponse(answer=prepared.fallback(question, lang)[1], sources=[], kind="limited")
        try:
            result = assistant.answer(history, hint=prepared.hint(question, lang))
        except Exception as error:  # never leak internals to the browser
            # The error's type only: provider messages can repeat parts of the request.
            log.error("chat failed: %s", type(error).__name__)
            # 503, not 502: Cloudflare replaces a 502 with its own error page, which the chat page
            # can't read, so visitors would see "couldn't reach" instead of this message.
            raise HTTPException(503, "The assistant is temporarily unavailable. Please try again later.")
        usage = result["usage"]
        totals = budget.add(usage["input_tokens"], usage["output_tokens"])
        # One line per answer for monitoring (`docker logs ask-my-cv | grep usage`):
        # tokens, cost and totals only; never the question, the answer or the address.
        log.info(json.dumps({"event": "usage", **usage, **totals}))
        if len(body.messages) == 1 and result["complete"]:
            cache.put(question, lang, result["answer"], result["sources"])
        return ChatResponse(answer=result["answer"], sources=result["sources"], kind="ai")

    return app


def create_app() -> FastAPI:  # uvicorn factory entry point
    logging.basicConfig(level=logging.INFO)
    return build_app()
