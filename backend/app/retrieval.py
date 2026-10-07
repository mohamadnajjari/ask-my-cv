"""Lightweight retrieval over the Markdown knowledge base.

Chunks every Markdown file by heading and ranks chunks with Okapi BM25.
No external services or vector database are needed, which keeps the server
small and cheap. The `Retriever` interface (`search(query, k)`) is the seam
for swapping in embedding-based search later.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

# Latin with German letters, and Persian letters (U+0600-U+06FF) for Persian questions.
_TOKEN = re.compile(r"[a-zA-Z0-9äöüßÄÖÜ\u0600-\u06ff+#.\-]+")
# Persian typed on different keyboards: Arabic yeh/kaf become the Persian forms; the zero-width
# non-joiner is dropped, so "می\u200cکند" and "میکند" are the same word.
_PERSIAN = str.maketrans({"\u064a": "\u06cc", "\u0643": "\u06a9", "\u0629": "\u0647", "\u200c": None})
_STOP = {
    # English
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was",
    "were", "be", "by", "at", "as", "it", "this", "that", "what", "which", "who", "how", "does",
    "do", "did", "has", "have", "he", "his", "him", "about", "from", "can", "you", "me", "tell",
    # German
    "der", "die", "das", "und", "oder", "ein", "eine", "ist", "sind", "war", "mit", "von", "zu",
    "im", "in", "auf", "für", "er", "sein", "seine", "was", "wie", "hat", "über", "den", "dem",
    "hat", "kann", "welche", "welcher", "wann", "wo", "ihn", "ihm", "es", "sie",
    # Persian (normalised: no zero-width non-joiner)
    "او", "از", "در", "به", "را", "که", "و", "با", "این", "آن", "است", "چه", "چی", "آیا",
    "برای", "ها", "های", "می", "میکند", "دارد", "چگونه", "چطور", "کدام", "هست", "ایشان", "یک",
}
# A few bilingual synonyms so German questions find English source text.
_SYNONYMS = {
    "erfahrung": "experience", "ausbildung": "education", "studium": "education",
    "kenntnisse": "skills", "fähigkeiten": "skills", "sprachen": "languages",
    "deutsch": "german", "englisch": "english", "projekt": "project", "projekte": "projects",
    "masterarbeit": "thesis", "abschluss": "degree", "werkstudent": "working student",
    "kontakt": "contact", "verfügbarkeit": "availability", "arbeitserlaubnis": "work permit",
    "bildverarbeitung": "computer vision", "ki": "ai", "kamera": "camera", "sensoren": "sensor",
}


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for tok in _TOKEN.findall(text.lower().translate(_PERSIAN)):
        tok = tok.strip(".-")
        if not tok or tok in _STOP:
            continue
        out.extend(_SYNONYMS.get(tok, tok).split())
    return out


@dataclass(frozen=True)
class Chunk:
    source: str
    heading: str
    text: str

    def render(self) -> str:
        return f"[{self.source} › {self.heading}]\n{self.text}"


def load_chunks(knowledge_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(knowledge_dir.glob("*.md")):
        if path.name.startswith("_"):  # summary/contact are injected directly
            continue
        heading, buf = path.stem, []

        def flush() -> None:
            body = "\n".join(buf).strip()
            if body:
                chunks.append(Chunk(path.stem, heading, body))

        for line in path.read_text(encoding="utf-8").splitlines():
            # Private notes for the owner are never shown to the model.
            if line.lstrip().startswith(("> TODO", "<!--")):
                continue
            if line.startswith("#"):
                flush()
                heading, buf = line.lstrip("#").strip(), []
            else:
                buf.append(line)
        flush()
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.2, b: float = 0.5) -> None:
        self.chunks = chunks
        self.k1, self.b = k1, b
        # Headings count double: they say what a section is about.
        self.docs = [tokenize(c.heading) * 2 + tokenize(c.text) for c in chunks]
        self.tf = [Counter(d) for d in self.docs]
        self.avgdl = sum(map(len, self.docs)) / max(len(self.docs), 1)
        df: Counter[str] = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 4) -> list[Chunk]:
        q = tokenize(query)
        scored = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return [self.chunks[i] for _, i in scored[:k]]
