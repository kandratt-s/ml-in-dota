FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
COPY services/inference/pyproject.toml /app/services/inference/pyproject.toml
COPY services/inference/main.py /app/services/inference/main.py
COPY services/inference/scr /app/services/inference/scr
COPY data/models/artifacts/boosting/catboost_dota_model_5s.cbm /app/services/inference/model.cbm

RUN uv sync --package inference --no-dev --frozen

EXPOSE 8000

WORKDIR /app/services/inference

CMD ["uv", "run", "python", "main.py"]
