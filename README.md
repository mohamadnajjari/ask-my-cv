# Ask my CV

An AI assistant that answers recruiters' questions about my experience. It is grounded in my CV and project notes, and built the way I would build an LLM integration for a real product.

**Live:** https://mohamadnajjari.github.io/ask-my-cv/

```
 Recruiter's browser                      Backend (FastAPI, Docker)                   Anthropic
┌──────────────────────┐  POST /api/chat  ┌─────────────────────────────────┐        ┌────────────┐
│ docs/index.html      │ ───────────────▶ │ validation · CORS · flood limit │        │            │
│ static, GitHub Pages │                  │ 1 prepared answer   (0 tokens)  │        │            │
│ no secrets           │                  │ 2 answer cache      (0 tokens)  │        │            │
│                      │                  │ 3 budget + AI quota ─ or ─ 1    │        │            │
│                      │ ◀─────────────── │ 4 BM25 passages + one call ─────┼──────▶ │ Claude API │
└──────────────────────┘ answer + kind    │ knowledge/*.md, answers.json    │ ◀───── │            │
                                          └─────────────────────────────────┘        └────────────┘
```

## How it works

Every question goes to the cheapest source that can answer it:

1. **Prepared answers (0 tokens).** `knowledge/answers.json` holds ~20 answers to the questions recruiters ask most (work permit, availability, location, strengths, contact…), written in English, German and Persian from the same facts as the knowledge files. A question gets one only when a keyword phrase covers most of it (`backend/app/prepared.py`); a question that is mostly about something else still goes to the model. The page's suggestion buttons ask for them by ID.
2. **Shared answer cache (0 tokens).** A question asked before, with the same content words in the same language, gets the stored answer (`backend/app/cache.py`; 30 days, 500 entries). Follow-ups and answers that were cut off are never cached.
3. **Limits that cost nothing.** Before any model call: the money budget (real token usage converted to micro-dollars, per day and month, kept across restarts), an AI quota per visitor per day and a total per day. When any is reached, the visitor gets the closest prepared answer instead of an error, so overuse costs nothing. A flood limit (all kinds of answers) answers 429; Cloudflare's edge rule stops floods before the server.
4. **One lean model call.** The server itself retrieves the three best passages with Okapi BM25 (`backend/app/retrieval.py`; German and Persian questions also search with the English words of their closest prepared topic) and sends them with a short prompt, the last two turns of the conversation and a 350-token answer cap: one call, no tool loop. A typical answer costs about $0.001–0.002 with Claude Haiku 4.5.

- **Grounding and guardrails.** The prompt allows only the given facts, says to admit when something is unknown, answers in the visitor's language (EN/DE/FA), and resists prompt injection and off-topic requests. Sources are returned with every AI answer.
- **Security.** The API key exists only on the server. Requests are validated (length, roles, history size, total conversation size, answer IDs), CORS only allows the GitHub Pages origin, and visitors are counted by Cloudflare's `CF-Connecting-IP`, which they can't fake. One log line per AI answer records tokens and cost, never the question or the address. Dependencies are pinned with hashes; the image is built in CI and pulled by digest. Error details are never sent to the browser.
- **Quality.** `pytest` covers retrieval, prepared answers in three languages, the cache, every limit and CORS with a fake Claude client. `evals/run_evals.py` checks real answers against known facts and red-team questions.

## Run locally

```bash
pip install -r requirements-dev.txt
pytest -q

# Without an API key (mock answers straight from retrieval)
cd backend && LLM_MODE=mock ALLOWED_ORIGINS=http://localhost:8080 uvicorn --factory app.main:create_app --port 8000
# In another terminal
cd docs && python -m http.server 8080
# Open http://localhost:8080/?api=http://localhost:8000
```

With a real key, copy `.env.example` to `.env`, fill it in, and run `set -a; source .env; set +a` before starting uvicorn.

## Deploy

**1. Backend on Google Cloud Run** (scales to zero, starts quickly, the free tier covers this traffic):

```bash
gcloud run deploy ask-my-cv-api --source . --region europe-west3 --allow-unauthenticated \
  --set-env-vars "MODEL=claude-haiku-4-5-20251001,ALLOWED_ORIGINS=https://mohamadnajjari.github.io,TRUST_PROXY_HEADERS=true" \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-key:latest" \
  --max-instances 2 --memory 512Mi
```

(First create the secret: `printf "sk-ant-..." | gcloud secrets create anthropic-key --data-file=-`.)

Alternative: run the Docker image on the server that already hosts Onsorex, behind nginx with HTTPS, e.g. at `cv-api.<your-domain>`. Set `TRUST_PROXY_HEADERS=true`.

**2. Frontend on GitHub Pages:** set `API_URL` near the top of the script in `docs/index.html` to the backend URL. Then go to *Settings → Pages → Deploy from branch → main / docs*.

**3. Cost safety:** set a monthly spend limit in the Anthropic Console. With Claude Haiku 4.5 a typical question costs well under one cent.

## Updating the content

Edit the Markdown in `knowledge/`. Lines starting with `> TODO` or `<!--` are private notes and are never sent to the model. `_summary.md` and `_contact.md` are always included in the prompt. After changing a fact, update `knowledge/answers.json` too (the same fact in all three languages).
