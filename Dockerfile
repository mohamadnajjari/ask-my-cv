FROM python:3.12-slim
WORKDIR /srv
# Exact versions with checksums (backend/requirements.lock, made with `uv pip compile
# --generate-hashes`, releases at least 7 days old): a changed or compromised package can't slip in.
COPY backend/requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY backend/app ./app
COPY knowledge ./knowledge
# DATA_DIR keeps the budget's totals across restarts (mount a volume there).
ENV KNOWLEDGE_DIR=/srv/knowledge PORT=8080 DATA_DIR=/data PYTHONDONTWRITEBYTECODE=1
RUN useradd -m bot && mkdir /data && chown -R bot /srv /data
USER bot
# No --proxy-headers: uvicorn must not trust X-Forwarded-For from anyone; the app reads
# Cloudflare's CF-Connecting-IP itself when TRUST_PROXY_HEADERS=true.
CMD ["sh", "-c", "exec uvicorn --factory app.main:create_app --host 0.0.0.0 --port ${PORT}"]
