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
            return NS(stop_reason="tool_use", content=[block])
        assert last[0]["type"] == "tool_result"
        return NS(stop_reason="end_turn", content=[NS(type="text", text="F1 rose from 0.41 to 0.85.")])


def make(**overrides):
    s = Settings(knowledge_dir=KB, llm_mode="test", **overrides)
    fake = FakeClaude()
    return TestClient(build_app(s, client=fake)), fake


def ask(client, text, origin="https://mohamadnajjari.github.io"):
    return client.post("/api/chat", json={"messages": [{"role": "user", "content": text}]},
                       headers={"Origin": origin})


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
