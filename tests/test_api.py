import json
import logging
from pathlib import Path
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import build_app

KB = Path(__file__).resolve().parents[1] / "knowledge"


class FakeClaude:
    """Mimics the Anthropic Messages API: one call, one answer."""

    def __init__(self, stop_reason="end_turn"):
        self.calls = []
        self.stop_reason = stop_reason

    def create(self, **kw):
        self.calls.append(kw)
        return NS(stop_reason=self.stop_reason,
                  content=[NS(type="text", text="F1 rose from 0.41 to 0.85.")],
                  usage=NS(input_tokens=1200, output_tokens=150))


def make(fake=None, **overrides):
    s = Settings(knowledge_dir=KB, llm_mode="test", **overrides)
    fake = fake or FakeClaude()
    return TestClient(build_app(s, client=fake)), fake


def ask(client, text, origin="https://mohamadnajjari.github.io", **headers):
    return client.post("/api/chat", json={"messages": [{"role": "user", "content": text}]},
                       headers={"Origin": origin, **headers})


def test_one_lean_call_with_retrieved_passages_and_sources():
    client, fake = make()
    r = ask(client, "How many annotated images did the BHS thesis use?")
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "ai" and "0.85" in body["answer"]
    assert any("thesis" in s.lower() or "bhs" in s.lower() for s in body["sources"])
    [call] = fake.calls  # one call, no tool loop
    assert "tools" not in call and call["max_tokens"] == 350
    assert "5,886" in call["system"]  # the passage travelled with the question
    # The API key never appears in what the model or browser sees.
    assert "sk-ant" not in str(fake.calls)


def test_system_prompt_contains_summary_not_todos():
    client, fake = make()
    ask(client, "Tell me something surprising about his hobbies")
    system = fake.calls[0]["system"]
    assert "Deggendorf" in system and "TODO" not in system


def test_only_the_newest_messages_reach_the_model():
    client, fake = make()
    history = []
    for i in range(6):
        history += [{"role": "user", "content": f"question {i}"},
                    {"role": "assistant", "content": f"answer {i}"}]
    history.append({"role": "user", "content": "And what about Docker?"})
    assert client.post("/api/chat", json={"messages": history}).status_code == 200
    sent = fake.calls[0]["messages"]
    assert sent[0]["role"] == "user" and sent[-1]["content"] == "And what about Docker?"
    assert len(sent) <= 5 and "question 0" not in str(sent)


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
    r = ask(client, "What did he run on Hetzner with Docker Compose?")
    assert r.status_code == 200 and "mock" in r.json()["answer"]


# One answer: 1200 input + 150 output tokens = 1200 x 1 + 150 x 5 = 1950 micro-dollars.
ANSWER_MICRO = 1950


def kinds(client, *questions, **headers):
    return [ask(client, q, **headers).json()["kind"] for q in questions]


def test_the_daily_budget_stops_ai_answers_by_real_cost():
    client, fake = make(daily_budget_usd=0.003)  # room for two answers (3900 > 3000)
    assert kinds(client, "Kubernetes?", "Terraform?", "Rust?") == ["ai", "ai", "limited"]
    assert len(fake.calls) == 2  # the third question never reached the model


def test_the_monthly_budget_is_kept_across_restarts(tmp_path):
    client, _ = make(data_dir=tmp_path, monthly_budget_usd=0.003)
    assert kinds(client, "Kubernetes?") == ["ai"]  # 1950 of 3000
    saved = json.loads((tmp_path / "usage.json").read_text())
    assert saved["month_micro"] == ANSWER_MICRO
    restarted, fake = make(data_dir=tmp_path, monthly_budget_usd=0.003)
    assert kinds(restarted, "Terraform?", "Rust?") == ["ai", "limited"]  # 3900: now over
    assert len(fake.calls) == 1


def test_usage_is_logged_without_question_answer_or_address(caplog):
    client, _ = make(trust_proxy=True)
    with caplog.at_level(logging.INFO, logger="ask-my-cv"):
        ask(client, "What about his secret Kubernetes cluster?", **{"CF-Connecting-IP": "198.51.100.7"})
    [line] = [r.getMessage() for r in caplog.records if '"usage"' in r.getMessage()]
    usage = json.loads(line)
    assert (usage["input_tokens"], usage["output_tokens"]) == (1200, 150)
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


def test_a_failing_model_gives_a_readable_503():
    class Broken:
        def create(self, **kw):
            raise RuntimeError("provider down")

    s = Settings(knowledge_dir=KB, llm_mode="test")
    client = TestClient(build_app(s, client=Broken()))
    r = ask(client, "hi")
    assert r.status_code == 503
    assert "temporarily unavailable" in r.json()["detail"]


# ---- prepared answers, cache and AI quota ----------------------------------------------------

def test_a_suggestion_button_gets_its_prepared_answer_without_the_model():
    client, fake = make()
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "Languages?"}],
                                       "lang": "de", "prepared_id": "languages"})
    assert r.json() == {"answer": r.json()["answer"], "sources": [], "kind": "prepared"}
    assert "Deutsch B1" in r.json()["answer"] and fake.calls == []


def test_unknown_or_malformed_prepared_ids_are_refused():
    client, _ = make()
    msg = [{"role": "user", "content": "x"}]
    assert client.post("/api/chat", json={"messages": msg, "prepared_id": "nope"}).status_code == 404
    bad = client.post("/api/chat", json={"messages": msg, "prepared_id": "../etc"})
    assert bad.status_code == 422


def test_common_questions_get_prepared_answers_in_their_language():
    client, fake = make()
    en = ask(client, "Does he have a work permit?").json()
    de = ask(client, "Hat er eine Arbeitserlaubnis?").json()
    fa = ask(client, "\u0622\u06cc\u0627 \u0627\u062c\u0627\u0632\u0647 \u06a9\u0627\u0631 \u062f\u0627\u0631\u062f\u061f").json()
    assert [en["kind"], de["kind"], fa["kind"]] == ["prepared"] * 3
    assert "allowed to work" in en["answer"] and "darf" in de["answer"]
    assert "\u0627\u062c\u0627\u0632\u0647 \u06a9\u0627\u0631" in fa["answer"]
    assert fake.calls == []


def test_a_question_about_something_else_still_goes_to_the_model():
    client, fake = make()
    # Mentions "work permit" but is mostly about other things.
    r = ask(client, "Which Python libraries did he use for image augmentation in the work permit era?")
    assert r.json()["kind"] == "ai" and len(fake.calls) == 1


def test_the_same_question_is_answered_from_the_cache(tmp_path):
    client, fake = make(data_dir=tmp_path)
    assert kinds(client, "Which Docker Compose setups did he build?") == ["ai"]
    # Other order, case and punctuation: the same content words.
    assert kinds(client, "which setups, Docker Compose, did he build") == ["cached"]
    restarted, fake2 = make(data_dir=tmp_path)
    assert kinds(restarted, "Which Docker Compose setups did he build?") == ["cached"]
    assert len(fake.calls) == 1 and fake2.calls == []


def test_a_cut_off_answer_is_not_cached():
    client, fake = make(fake=FakeClaude(stop_reason="max_tokens"))
    assert kinds(client, "Kubernetes?", "Kubernetes?") == ["ai", "ai"]
    assert len(fake.calls) == 2


def test_follow_ups_are_never_served_from_prepared_answers_or_the_cache():
    client, fake = make()
    history = [{"role": "user", "content": "Tell me about BHS"},
               {"role": "assistant", "content": "He worked there."},
               {"role": "user", "content": "Does he have a work permit?"}]
    r = client.post("/api/chat", json={"messages": history})
    assert r.json()["kind"] == "ai" and len(fake.calls) == 1


def test_a_visitor_over_the_ai_quota_gets_prepared_answers_free():
    client, fake = make(trust_proxy=True, ai_quota_per_ip=2)
    ip = {"CF-Connecting-IP": "198.51.100.7"}
    assert kinds(client, "Kubernetes?", "Terraform?", "Which TensorFlow version?", **ip) == \
        ["ai", "ai", "limited"]
    limited = ask(client, "What grade did he get in the master?", **ip).json()
    assert limited["kind"] == "limited" and "2.1" in limited["answer"]  # the closest topic
    # Prepared answers still work for this visitor, and others still get AI answers.
    assert kinds(client, "Does he have a work permit?", **ip) == ["prepared"]
    assert kinds(client, "Rust?", **{"CF-Connecting-IP": "203.0.113.9"}) == ["ai"]
    assert len(fake.calls) == 3


def test_the_global_ai_cap_protects_against_many_addresses():
    client, fake = make(trust_proxy=True, ai_answers_per_day=2)
    got = [ask(client, f"Kubernetes version {i}?", **{"CF-Connecting-IP": f"198.51.100.{i}"}).json()["kind"]
           for i in range(1, 5)]
    assert got == ["ai", "ai", "limited", "limited"] and len(fake.calls) == 2


def test_a_german_question_finds_english_passages_through_its_topic():
    client, fake = make()
    assert kinds(client, "Was hat er in seiner Masterarbeit konkret erreicht?") == ["ai"]
    assert "5,886" in fake.calls[0]["system"]


def test_a_cv_change_empties_the_answer_cache(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    for f in KB.iterdir():
        if f.is_file():
            (kb / f.name).write_bytes(f.read_bytes())
    data = tmp_path / "data"
    data.mkdir()
    first = TestClient(build_app(Settings(knowledge_dir=kb, llm_mode="test", data_dir=data), client=FakeClaude()))
    assert kinds(first, "Which Docker Compose setups did he build?") == ["ai"]
    (kb / "projects.md").write_text((kb / "projects.md").read_text() + "\n# New project\nA new thing.\n")
    fake = FakeClaude()
    updated = TestClient(build_app(Settings(knowledge_dir=kb, llm_mode="test", data_dir=data), client=fake))
    assert kinds(updated, "Which Docker Compose setups did he build?") == ["ai"]  # not the old answer
    assert len(fake.calls) == 1


def test_answers_with_private_details_never_reach_the_visitor():
    class Leaky(FakeClaude):
        def __init__(self, text):
            super().__init__()
            self.text = text

        def create(self, **kw):
            resp = super().create(**kw)
            resp.content = [NS(type="text", text=self.text)]
            return resp

    for leak in ("Call him at +49 151 23456789.", "His number is 0151 2345678.",
                 "Write to someone.else@example.com."):
        client, _ = make(fake=Leaky(leak))
        body = ask(client, "What is his private Kubernetes number?").json()
        assert body["kind"] == "prepared" and "linkedin" in body["answer"].lower(), leak
    # Dates, scores and his listed address are fine.
    client, _ = make(fake=Leaky("03/2023 - 03/2026, F1 0.41 -> 0.85, 5,886 images; mohamad.najjari.a.e@gmail.com"))
    assert ask(client, "Kubernetes?").json()["kind"] == "ai"


def test_the_prompt_forbids_personal_details():
    client, fake = make()
    ask(client, "Kubernetes?")
    assert "Never give personal details" in fake.calls[0]["system"]


def test_the_knowledge_holds_no_private_documents():
    text = " ".join(f.read_text(encoding="utf-8").lower() for f in KB.iterdir() if f.is_file())
    for word in ("police", "clearance", "job-seeker", "job seekers", "passport", "date of birth", "+49"):
        assert word not in text, word
