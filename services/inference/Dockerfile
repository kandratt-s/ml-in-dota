FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN useradd -m appuser
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/inference/pyproject.toml ./services/inference/

RUN uv sync --package inference --no-dev --frozen && \
    chown -R appuser:appuser /app

COPY --chown=appuser:appuser services/inference/ ./services/inference/

USER appuser
WORKDIR /app/services/inference

CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${INFERENCE_PORT:-8000}"]