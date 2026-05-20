#!/usr/bin/env bash
# Тестовый запуск: поднимает стек и проигрывает записанный GSI-дамп
# в gsi_processor с фиксированным токеном из дампов ("секретный_токен").
# Никакая Dota и фронт-кнопка Start не нужны.
#
# Переменные окружения (необязательные):
#   TEST_TOKEN    — токен для активации в Redis. По умолчанию "секретный_токен"
#                   (именно с этим значением записаны .jsonl-дампы).
#   JSONL_FILE    — путь к конкретному .jsonl. По умолчанию первый файл из
#                   scripts/gsi_jsonl, отсортированный по имени.
#   SPEED         — множитель скорости. 1.0 — реальное время, 10 — x10,
#                   0 — слать без пауз. По умолчанию 1.0.
#   MODEL/TIME/INTERVAL — параметры предсказания, передаваемые в /api/start.
#                   По умолчанию boosting / time=20 / interval=5 — даёт
#                   заметную «тепловую» область вокруг героя. На interval=1
#                   красится только одна клетка, time=5 на ранней игре даёт
#                   <2% вероятности — визуально почти не видно.
#   FULL_MAP=1    — считать предсказания для всех 32*32 клеток. Медленнее,
#                   но карта покрывается целиком (полезно для дебага).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

TOKEN="${TEST_TOKEN:-секретный_токен}"
JSONL_DIR="$SCRIPT_DIR/gsi_jsonl"
SPEED="${SPEED:-0.1}"
MODEL="${MODEL:-boosting}"
PRED_TIME="${TIME:-20}"
PRED_INTERVAL="${INTERVAL:-5}"
case "${FULL_MAP:-1}" in 1|true|TRUE|yes) FULL_MAP_JSON=true;; *) FULL_MAP_JSON=false;; esac
FRONT_PORT="${FRONT_EXTERNAL_PORT:-3000}"
GSI_PORT="${GSI_PROCESSOR_PORT:-8001}"
BASE_URL="http://localhost:${FRONT_PORT}"
GSI_HEALTH="http://localhost:${GSI_PORT}/health"

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

JSONL_FILE="${JSONL_FILE:-}"
if [[ -z "$JSONL_FILE" ]]; then
  JSONL_FILE="$(ls "$JSONL_DIR"/*.jsonl 2>/dev/null | sort | head -n1 || true)"
fi
if [[ -z "$JSONL_FILE" || ! -f "$JSONL_FILE" ]]; then
  echo "[!] Не нашёл .jsonl в $JSONL_DIR. Положи туда дамп(ы) и повтори." >&2
  exit 1
fi

for tool in docker curl jq python3; do
  command -v "$tool" >/dev/null 2>&1 || { echo "[!] нужен $tool" >&2; exit 1; }
done

echo "[*] docker compose up --build -d"
compose up --build -d

echo "[*] Жду gsi_processor на $GSI_HEALTH ..."
for i in $(seq 1 120); do
  if curl -fsS "$GSI_HEALTH" >/dev/null 2>&1; then
    echo "[+] gsi_processor готов"
    break
  fi
  sleep 1
  if [[ $i -eq 120 ]]; then
    echo "[!] gsi_processor не поднялся за 120s" >&2
    compose ps
    exit 1
  fi
done

echo "[*] Жду bff (через front-прокси $BASE_URL/api/start) ..."
for i in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/api/start" \
    -H 'Content-Type: application/json' --data '{}' || true)"
  # 400 (invalid json/token) означает что bff отвечает — этого достаточно.
  if [[ "$code" =~ ^(200|400)$ ]]; then
    echo "[+] bff отвечает (code=$code)"
    break
  fi
  sleep 1
  if [[ $i -eq 60 ]]; then
    echo "[!] bff не отвечает через nginx-прокси" >&2
    compose ps
    exit 1
  fi
done

echo "[*] Активирую тестовый токен в Redis через /api/start"
body="$(jq -n \
  --arg t "$TOKEN" \
  --arg m "$MODEL" \
  --argjson ti "$PRED_TIME" \
  --argjson iv "$PRED_INTERVAL" \
  --argjson fm "$FULL_MAP_JSON" \
  '{token:$t, config:{model:$m, time:$ti, interval:$iv, full_map:$fm}}')"
curl -sS -X POST "$BASE_URL/api/start" \
  -H 'Content-Type: application/json' \
  --data "$body"
echo

TOKEN_URL_ENC="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$TOKEN")"
FRONT_URL="$BASE_URL/?token=$TOKEN_URL_ENC"
echo "[*] Проигрываю $(basename "$JSONL_FILE") (SPEED=$SPEED) → $BASE_URL/gsi-input"
echo "    Открой в браузере (НЕ ЖМИ Start, токен уже активен):"
echo "      $FRONT_URL"
python3 "$SCRIPT_DIR/replay.py" \
  --file "$JSONL_FILE" \
  --url "$BASE_URL/gsi-input" \
  --token "$TOKEN" \
  --speed "$SPEED"

echo "[*] Replay завершён. Стек продолжает работать."
echo "    Heatmap:  $FRONT_URL"
echo "    Останов:  docker compose down"
