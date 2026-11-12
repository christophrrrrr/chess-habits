# Kiebitz games service
FROM python:3.12.16-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first (pinned) so this layer is cached between code changes.
COPY requirements.txt ./
RUN pip install --no-deps -r requirements.txt

# Only what the service needs at runtime; no tests, no local files.
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY app/ ./app/

RUN useradd --create-home --uid 10001 kiebitz
USER kiebitz

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
