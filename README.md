# Ask my CV

An AI assistant that answers recruiters' questions about my experience. It is grounded in my CV and project notes, and built the way I would build an LLM integration for a real product.

**Live:** https://mohamadnajjari.github.io/ask-my-cv/

```
 Recruiter's browser                      Backend (FastAPI, Docker)                 Anthropic
┌──────────────────────┐  POST /api/chat  ┌───────────────────────────────┐        ┌─────────────┐
│ docs/index.html      │ ───────────────▶ │ validation · CORS · rate limit │        │             │
│ static, GitHub Pages │                  │ Claude tool-use loop ─────────┼──────▶ │ Claude API  │
│ no secrets           │ ◀─────────────── │   └ search_profile (BM25 RAG) │ ◀───── │             │
└──────────────────────┘ answer + sources │   └ get_contact_options       │        └─────────────┘
                                          │ knowledge/*.md                │
                                          └───────────────────────────────┘
```

## How it works

- **Retrieval-augmented generation.** `knowledge/*.md` is split into sections by heading and ranked with Okapi BM25 (`backend/app/retrieval.py`), with simple German→English synonyms so German questions find English source text. No vector database is needed at this size, and the `Retriever.search()` interface is the place to plug in embeddings later.
- **Tool use (function calling).** Claude decides when to call `search_profile` and can search several times with different queries. `get_contact_options` returns contact details. The loop is capped at 3 tool rounds.
- **Grounding and guardrails.** The system prompt requires answers to be based on retrieved text, says to admit when something is unknown, answers in the visitor's language (EN/DE/FA), and resists prompt injection and off-topic requests. Sources are returned with every answer.
- **Security and cost control.** The API key exists only on the server. Requests are validated (length, roles, history size), CORS only allows the GitHub Pages origin, each IP gets a sliding-window rate limit and there is a global daily cap. Error details are never sent to the browser.
- **Quality.** `pytest` covers retrieval, the tool loop, rate limits and CORS with a fake Claude client. `evals/run_evals.py` checks real answers against known facts and red-team questions.

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

Edit the Markdown in `knowledge/`. Lines starting with `> TODO` or `<!--` are private notes and are never sent to the model. `_summary.md` is always included in the prompt, and `_contact.md` is what the contact tool returns.
