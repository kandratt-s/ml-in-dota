FROM python:3.12-slim

# install uv
RUN pip install --no-cache-dir uv==0.10.9

WORKDIR /app

# 1. Копируем корневые файлы workspace
COPY pyproject.toml uv.lock ./

# 2. Копируем только pyproject.toml сервиса (для кеша зависимостей)
COPY services/bot/pyproject.toml ./services/bot/

# 3. Установка зависимостей (кешируется при изменении только кода)
RUN uv sync --package bot --no-dev --frozen

# 4. Копируем весь код сервиса
COPY services/bot/ ./services/bot/

WORKDIR /app/services/bot

CMD ["uv", "run", "python", "main.py"]