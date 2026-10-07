import json
from pathlib import Path

import pytest

from app.cache import AnswerCache
from app.prepared import LANGS, PreparedAnswers, detect_lang
from app.retrieval import tokenize

KB = Path(__file__).resolve().parents[1] / "knowledge"
RAW = json.loads((KB / "answers.json").read_text(encoding="utf-8"))
P = PreparedAnswers(KB / "answers.json")


def test_every_answer_exists_in_every_language_with_phrases():
    assert "about" in P.by_id_map  # the fallback of last resort
    ids = [item["id"] for item in RAW]
    assert len(ids) == len(set(ids))
    for item in RAW:
        for lang in LANGS:
            assert item["a"][lang].strip(), (item["id"], lang)
            assert item["q"][lang], (item["id"], lang)


def test_no_phrase_is_only_stop_words_or_one_vague_word():
    vague = {"why", "good", "work", "project", "learn", "how", "his", "him"}
    for item in RAW:
        for lang in LANGS:
            for phrase in item["q"][lang]:
                words = tokenize(phrase)
                assert words and set(words) - vague, (item["id"], lang, phrase)


@pytest.mark.parametrize("item", RAW, ids=lambda i: i["id"])
def test_each_first_phrase_finds_its_own_answer(item):
    for lang in LANGS:
        found = P.match(item["q"][lang][0], lang)
        assert found is not None and found[0] == item["id"], (lang, item["q"][lang][0], found)


def test_language_detection():
    assert detect_lang("Where did he study?") == "en"
    assert detect_lang("Wo hat er studiert?") == "de"
    assert detect_lang("Spricht er Französisch?") == "de"
    assert detect_lang("\u06a9\u062c\u0627 \u062f\u0631\u0633 \u062e\u0648\u0627\u0646\u062f\u0647\u061f") == "fa"


def test_the_fallback_is_the_closest_topic_or_the_introduction():
    assert P.fallback("what is his salary expectation", "en")[0] == "salary"
    assert P.fallback("qwertz zzz", "en")[0] == "about"
    assert P.fallback("", "fa")[0] == "about"


def test_the_hint_gives_english_words_for_other_languages_only():
    assert "thesis" in P.hint("Erzähl mir von der Masterarbeit bei BHS", "de")
    assert P.hint("Tell me about the thesis", "en") == ""


def test_the_cache_expires_and_keeps_only_the_newest():
    now = [1000.0]
    cache = AnswerCache(None, ttl_days=1, max_entries=2, clock=lambda: now[0])
    cache.put("Docker skills?", "en", "Yes.", [])
    assert cache.get("skills docker", "en")["answer"] == "Yes."
    assert cache.get("skills docker", "de") is None  # another language, another answer
    now[0] += 86_401
    assert cache.get("skills docker", "en") is None
    for q in ("one thing", "two things", "three things"):
        now[0] += 1
        cache.put(q, "en", q, [])
    assert cache.get("one thing", "en") is None and cache.get("three things", "en") is not None


def test_a_broken_cache_file_starts_empty(tmp_path):
    (tmp_path / "c.json").write_text("{not json")
    assert AnswerCache(tmp_path / "c.json").get("x y", "en") is None
