"""Prepared answers: the common questions answered without any model call (0 tokens).

`knowledge/answers.json` holds answers written in advance in English, German and Persian, each with
short keyword phrases per language. A question gets a prepared answer when one phrase appears in
it as whole words AND the phrase covers at least half of the question's content words, so a
question that is mostly about something else still goes to the assistant. The chat page's
suggestion buttons ask for an answer by its ID directly.

When a limit is reached (per visitor, per day, budget), the closest prepared answer is shown
instead of calling the model: visitors always get something useful, and abuse costs nothing.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .retrieval import tokenize

LANGS = ("en", "de", "fa")
_PERSIAN_LETTER = re.compile(r"[\u0600-\u06ff]")
_GERMAN = {"ist", "er", "sein", "seine", "hat", "wie", "was", "welche", "kann", "über", "für",
           "und", "nicht", "arbeit", "erfahrung", "warum", "wann", "wo", "gibt"}


@dataclass(frozen=True)
class Prepared:
    id: str
    phrases: dict[str, list[list[str]]]  # language -> phrases as words
    answers: dict[str, str]


def detect_lang(text: str) -> str:
    """The question's language: Persian by its letters, German by common words, else English."""
    if _PERSIAN_LETTER.search(text):
        return "fa"
    words = set(re.findall(r"[a-zäöüß]+", text.lower()))
    return "de" if len(words & _GERMAN) >= 2 or re.search(r"[äöüß]", text.lower()) else "en"


class PreparedAnswers:
    def __init__(self, path: Path) -> None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.items = [
            Prepared(
                item["id"],
                {lang: [tokenize(p) for p in item["q"].get(lang, [])] for lang in LANGS},
                item["a"],
            )
            for item in raw
        ]
        self.by_id_map = {item.id: item for item in self.items}

    def by_id(self, answer_id: str, lang: str) -> str | None:
        item = self.by_id_map.get(answer_id)
        return (item.answers.get(lang) or item.answers["en"]) if item else None

    def match(self, question: str, lang: str) -> tuple[str, str] | None:
        """(id, answer) when one prepared answer clearly fits the whole question, else None."""
        found = self._best(question, lang)
        if found is None or found[0] < 1.0:
            return None
        item = found[1]
        return item.id, item.answers.get(lang) or item.answers["en"]

    def fallback(self, question: str, lang: str) -> tuple[str, str]:
        """The closest prepared answer (or the short introduction), for when AI isn't allowed."""
        found = self._best(question, lang)
        item = found[1] if found and found[0] >= 0.5 else self.by_id_map["about"]
        return item.id, item.answers.get(lang) or item.answers["en"]

    def hint(self, question: str, lang: str) -> str:
        """English words of the closest topic, so a German or Persian question still finds its
        passages in the English knowledge files; empty when nothing is close."""
        if lang == "en":
            return ""
        found = self._best(question, lang)
        if found is None or found[0] < 0.5:
            return ""
        return " ".join(" ".join(p) for p in found[1].phrases["en"])

    def _best(self, question: str, lang: str) -> tuple[float, Prepared] | None:
        words = tokenize(question)
        if not words:
            return None
        said = set(words)
        best: tuple[float, Prepared] | None = None
        best_len = 0
        for item in self.items:
            # The question's language first; English phrases also count (codes, names, "AI").
            for phrase in item.phrases.get(lang, []) + item.phrases["en"]:
                if not phrase:
                    continue
                hit = sum(1 for w in phrase if w in said) / len(phrase)
                covers = len(set(phrase) & said) / len(said)
                score = hit if covers >= 0.5 else hit * 0.5
                # On a tie the longer phrase wins: "reference letter" beats "letter".
                if best is None or (score, len(phrase)) > (best[0], best_len):
                    best, best_len = (score, item), len(phrase)
        return best
