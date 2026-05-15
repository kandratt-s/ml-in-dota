FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN useradd -m appuser
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/gsi_processor/pyproject.toml ./services/gsi_processor/

RUN uv sync --package gsi_processor --no-dev --frozen && \
    chown -R appuser:appuser /app
    
COPY --chown=appuser:appuser services/gsi_processor/ ./services/gsi_processor/

USER appuser
WORKDIR /app/services/gsi_processor


CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${GSI_PROCESSOR_PORT:-8001}"]