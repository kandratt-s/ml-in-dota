# FROM python:3.12-slim

# RUN pip install --no-cache-dir uv==0.10.9

# WORKDIR /app

# COPY pyproject.toml uv.lock ./

# COPY services/gsi_processor/pyproject.toml ./services/gsi_processor/

# RUN uv sync --package gsi_processor --no-dev --frozen

# COPY services/gsi_processor/ ./services/gsi_processor/

# WORKDIR /app/services/gsi_processor

# CMD ["python", "main.py"]


FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.10.9

RUN useradd -m appuser

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/gsi_processor/pyproject.toml ./services/gsi_processor/

RUN uv sync --package gsi_processor --no-dev --frozen

COPY services/gsi_processor/ ./services/gsi_processor/

ENV PATH="/app/.venv/bin:$PATH"

RUN chown -R appuser:appuser /app
USER appuser

WORKDIR /app/services/gsi_processor

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]