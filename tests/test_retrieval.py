from pathlib import Path

from app.retrieval import Retriever, load_chunks, tokenize

KB = Path(__file__).resolve().parents[1] / "knowledge"


def test_private_notes_are_never_loaded():
    chunks = load_chunks(KB)
    assert chunks
    assert not any("TODO" in c.text for c in chunks)
    assert not any(c.source.startswith("_") for c in chunks)


def test_thesis_question_finds_thesis():
    r = Retriever(load_chunks(KB))
    top = r.search("master thesis F1 score", k=3)
    assert any("thesis" in c.heading.lower() for c in top)


def test_german_question_maps_to_english_text():
    r = Retriever(load_chunks(KB))
    top = r.search("Welche Erfahrung hat er mit Bildverarbeitung und Kamera?", k=3)
    assert any("BHS" in c.heading for c in top)


def test_tokenize_drops_stopwords():
    assert tokenize("What is the thesis about?") == ["thesis"]


def test_onsorex_status_is_stated_honestly():
    r = Retriever(load_chunks(KB))
    text = " ".join(c.text for c in r.search("Onsorex alerts AI status production", k=4))
    assert "not built yet" in text or "not active in production" in text
