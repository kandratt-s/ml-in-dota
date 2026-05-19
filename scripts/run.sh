#!/usr/bin/env bash
# Поднимает весь стек (redis, inference, gsi_processor, bff, front) через docker compose.
# Использование: ./scripts/run.sh [доп. аргументы для docker compose up]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

exec docker-compose up --build "$@"
