# Project – Ask my CV (this assistant)
An AI assistant that answers recruiters' questions about Mohammad. Source code: https://github.com/mohamadnajjari/ask-my-cv
- Retrieval-augmented generation: the CV and project notes are split into sections and ranked with BM25; Claude decides when to search via tool use (function calling).
- FastAPI backend keeps the API key on the server; the chat page is a static site on GitHub Pages.
- Guardrails against prompt injection and off-topic use, per-visitor rate limits and a daily cost cap, automated tests and an evaluation script that checks answers against known facts.

# Project – Damage Depth Determination (summary)
See the BHS master's thesis section: ResNet-50 classifier, F1-score 0.41 → 0.85, Top-1 error 50% → 23%, 5,886 annotated industrial images.

# Project – Onsorex (summary)
Live multilingual market-explanation web app (Next.js, FastAPI, PostgreSQL/TimescaleDB) with a guarded LLM layer that is built and tested but not yet active in production. See the Onsorex sections.
