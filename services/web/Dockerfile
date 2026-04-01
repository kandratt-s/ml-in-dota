FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.10.9

RUN useradd -m appuser

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/web/pyproject.toml ./services/web/

RUN uv sync --package web --no-dev --frozen

COPY services/web/ ./services/web/

ENV PATH="/app/.venv/bin:$PATH"

RUN chown -R appuser:appuser /app
USER appuser

WORKDIR /app/services/web

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
