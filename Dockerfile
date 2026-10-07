FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY knowledge ./knowledge
ENV KNOWLEDGE_DIR=/srv/knowledge PORT=8080
RUN useradd -m bot && chown -R bot /srv
USER bot
CMD ["sh", "-c", "uvicorn --factory app.main:create_app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
