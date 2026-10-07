# Project – Ask my CV (this assistant)
An AI assistant that answers recruiters' questions about Mohammad. Source code: https://github.com/mohamadnajjari/ask-my-cv
- Cost-aware design: common questions get prepared answers in English, German and Persian and repeated questions come from a shared cache, both without any model call; other questions get one lean Claude call with the three best passages (retrieval-augmented generation, BM25). The first version used tool use (function calling); one call with server-side retrieval costs about half.
- FastAPI backend keeps the API key on the server; the chat page is a static site on GitHub Pages.
- Guardrails against prompt injection and off-topic use, a money budget, per-visitor AI quotas (beyond them visitors get prepared answers, so overuse costs nothing), automated tests and an evaluation script that checks answers against known facts.

# Project – Damage Depth Determination (summary)
See the BHS master's thesis section: ResNet-50 classifier, F1-score 0.41 → 0.85, Top-1 error 50% → 23%, 5,886 annotated industrial images.

# Project – Onsorex (summary)
Live multilingual market-explanation web app (Next.js, FastAPI, PostgreSQL/TimescaleDB) with a guarded LLM layer that is built and tested but not yet active in production. See the Onsorex sections.
