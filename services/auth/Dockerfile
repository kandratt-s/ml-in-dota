FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.10.9

RUN useradd -m appuser

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/auth/pyproject.toml ./services/auth/

RUN uv sync --package auth --no-dev --frozen

COPY services/auth/ ./services/auth/

ENV PATH="/app/.venv/bin:$PATH"

RUN chown -R appuser:appuser /app
USER appuser

WORKDIR /app/services/auth

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]