import json
import logging
from pathlib import Path
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import build_app

KB = Path(__file__).resolve().parents[1] / "knowledge"


class FakeClaude:
    """Mimics the Anthropic Messages API: first asks for a search, then answers."""

    def __init__(self):
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        last = kw["messages"][-1]["content"]
        if isinstance(last, str):
            block = NS(type="tool_use", id="t1", name="search_profile", input={"query": "thesis"},
                       model_dump=lambda: {"type": "tool_use", "id": "t1",
                                           "name": "search_profile", "input": {"query": "thesis"}})
            return NS(stop_reason="tool_use", content=[block],
                      usage=NS(input_tokens=1000, output_tokens=50))
        assert last[0]["type"] == "tool_result"
        return NS(stop_reason="end_turn", content=[NS(type="text", text="F1 rose from 0.41 to 0.85.")],
                  usage=NS(input_tokens=1500, output_tokens=200))


def make(**overrides):
    s = Settings(knowledge_dir=KB, llm_mode="test", **overrides)
    fake = FakeClaude()
    return TestClient(build_app(s, client=fake)), fake


def ask(client, text, origin="https://mohamadnajjari.github.io", **headers):
    return client.post("/api/chat", json={"messages": [{"role": "user", "content": text}]},
                       headers={"Origin": origin, **headers})


def test_tool_use_loop_and_sources():
    client, fake = make()
    r = ask(client, "What was his thesis about?")
    assert r.status_code == 200
    body = r.json()
    assert "0.85" in body["answer"]
    assert any("thesis" in s.lower() for s in body["sources"])
    assert len(fake.calls) == 2
    # The API key never appears in what the model or browser sees.
    assert "sk-ant" not in str(fake.calls)


def test_system_prompt_contains_summary_not_todos():
    client, fake = make()
    ask(client, "hi")
    system = fake.calls[0]["system"]
    assert "Deggendorf" in system and "TODO" not in system


def test_rate_limit():
    client, _ = make(rate_limit_per_ip=2)
    assert ask(client, "a").status_code == 200
    assert ask(client, "b").status_code == 200
    assert ask(client, "c").status_code == 429


def test_daily_cap():
    client, _ = make(daily_cap=1)
    assert ask(client, "a").status_code == 200
    assert ask(client, "b").status_code == 429


def test_rejects_long_message_and_bad_roles():
    client, _ = make()
    assert ask(client, "x" * 601).status_code == 413
    r = client.post("/api/chat", json={"messages": [{"role": "assistant", "content": "hi"}]})
    assert r.status_code == 422


def test_cors_only_allows_configured_origin():
    client, _ = make()
    ok = ask(client, "hi")
    assert ok.headers.get("access-control-allow-origin") == "https://mohamadnajjari.github.io"
    bad = ask(client, "hi", origin="https://evil.example")
    assert "access-control-allow-origin" not in bad.headers


def test_mock_mode_runs_without_key():
    s = Settings(knowledge_dir=KB, llm_mode="mock", api_key="")
    client = TestClient(build_app(s))
    r = ask(client, "Onsorex")
    assert r.status_code == 200 and "mock" in r.json()["answer"]


# One answer: 2500 input + 250 output tokens = 2500 x 1 + 250 x 5 = 3750 micro-dollars.
ANSWER_MICRO = 3750


def test_the_daily_budget_stops_answers_by_real_cost():
    client, fake = make(daily_budget_usd=0.006)  # room for two answers (7500 > 6000)
    assert ask(client, "a").status_code == 200
    assert ask(client, "b").status_code == 200
    refused = ask(client, "c")
    assert refused.status_code == 429
    assert len(fake.calls) == 4  # the third question never reached the model


def test_the_monthly_budget_is_kept_across_restarts(tmp_path):
    client, _ = make(data_dir=tmp_path, monthly_budget_usd=0.005)
    assert ask(client, "a").status_code == 200  # 3750 of 5000
    saved = json.loads((tmp_path / "usage.json").read_text())
    assert saved["month_micro"] == ANSWER_MICRO
    restarted, fake = make(data_dir=tmp_path, monthly_budget_usd=0.005)
    assert ask(restarted, "b").status_code == 200  # 7500: now over
    assert ask(restarted, "c").status_code == 429
    assert len(fake.calls) == 2


def test_usage_is_logged_without_question_answer_or_address(caplog):
    client, _ = make(trust_proxy=True)
    with caplog.at_level(logging.INFO, logger="ask-my-cv"):
        ask(client, "What about his secret thesis?", **{"CF-Connecting-IP": "198.51.100.7"})
    [line] = [r.getMessage() for r in caplog.records if '"usage"' in r.getMessage()]
    usage = json.loads(line)
    assert (usage["input_tokens"], usage["output_tokens"]) == (2500, 250)
    assert usage["cost_micro_usd"] == ANSWER_MICRO and usage["day_answers"] == 1
    assert "secret" not in line and "0.85" not in line and "198.51.100.7" not in line


def test_a_faked_forwarded_address_gets_no_new_allowance():
    client, _ = make(trust_proxy=True, rate_limit_per_ip=1)
    assert ask(client, "a", **{"CF-Connecting-IP": "198.51.100.7"}).status_code == 200
    # X-Forwarded-For is ignored: anyone can write it.
    second = ask(client, "b", **{"CF-Connecting-IP": "198.51.100.7", "X-Forwarded-For": "1.2.3.4"})
    assert second.status_code == 429
    # Another real visitor (another CF-Connecting-IP) has their own allowance.
    assert ask(client, "c", **{"CF-Connecting-IP": "203.0.113.9"}).status_code == 200


def test_proxy_headers_count_only_when_trusted():
    client, _ = make(rate_limit_per_ip=1)  # not behind Cloudflare: the header means nothing
    assert ask(client, "a", **{"CF-Connecting-IP": "198.51.100.7"}).status_code == 200
    assert ask(client, "b", **{"CF-Connecting-IP": "203.0.113.9"}).status_code == 429


def test_a_huge_fake_history_is_refused_before_any_model_call():
    client, fake = make()
    history = [{"role": r, "content": "x" * 1900} for r in ["user", "assistant"] * 3]
    history.append({"role": "user", "content": "And?"})
    r = client.post("/api/chat", json={"messages": history})
    assert r.status_code == 413
    assert fake.calls == []
