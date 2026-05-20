#!/usr/bin/env bash
# Поднимает весь стек (redis, inference, gsi_processor, bff, front) через docker compose.
# Использование: ./scripts/run.sh [доп. аргументы для docker compose up]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

compose() {
	if docker compose version >/dev/null 2>&1; then
		docker compose "$@"
		return
	fi

	if command -v docker-compose >/dev/null 2>&1; then
		docker-compose "$@"
		return
	fi

	echo "[!] нужен docker compose или docker-compose" >&2
	exit 1
}

exec compose up --build "$@"
