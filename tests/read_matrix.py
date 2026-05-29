from __future__ import annotations

import argparse
import os
import sys
import time
import json
from pathlib import Path

import redis

# ─────────────────────────────────────────────────────────────
# Загрузка .env (если установлен python-dotenv)
# ─────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass  # dotenv не установлен — используем только системные env


# ─────────────────────────────────────────────────────────────
# Конфиг из env-переменных
# ─────────────────────────────────────────────────────────────
# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_HOST = "localhost"
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # None, если не задано
REDIS_DB = int(os.getenv("REDIS_DB", 0))

STREAM_NAME = "inference:output"
BLOCK_TIMEOUT_MS = 5000  # сколько ждать новых сообщений (5 сек)
RECONNECT_DELAY_SEC = 2  # пауза при ошибке подключения
DEFAULT_HEATMAP_KEY = "heat_map:секретный_токен"  # базовый ключ для heatmap, к которому будет добавляться :<token


# ─────────────────────────────────────────────────────────────
# Создание Redis-клиента
# ─────────────────────────────────────────────────────────────
def make_redis_client() -> redis.Redis:
    kwargs = {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
        "db": REDIS_DB,
        "decode_responses": True,
        "socket_connect_timeout": 5,
    }
    if REDIS_PASSWORD and REDIS_PASSWORD.strip():
        kwargs["password"] = REDIS_PASSWORD.strip()
    return redis.Redis(**kwargs)


# ─────────────────────────────────────────────────────────────
# Форматированный вывод сообщения из стрима
# ─────────────────────────────────────────────────────────────
def print_stream_entry(stream: str, entry_id: str, fields: dict):
    timestamp = time.strftime("%H:%M:%S")
    print(f"\n[{timestamp}] � {stream}:{entry_id}")
    print("-" * 40)
    
    # Parse InferenceResult JSON from stream
    if "data" in fields:
        try:
            data = json.loads(fields["data"])
            # InferenceResult has: record_id, death_probability, model_backend, metadata
            record_id = data.get("record_id", "?")
            prob = data.get("death_probability", 0.0)
            backend = data.get("model_backend", "?")
            meta = data.get("metadata", {})

            print(f"record_id:         {record_id}")
            print(f"death_probability: {prob:.6f}")
            print(f"model_backend:     {backend}")
            if meta:
                print("metadata:")
                for k, v in meta.items():
                    if k in {"square", "token", "model", "time", "interval", "full_map"}:
                        print(f"  {k}: {v}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to parse JSON: {e}")
            print(fields["data"])
    else:
        # Print all fields if no "data" field
        for k, v in fields.items():
            print(f"{k}: {v}")
    print("-" * 40, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Monitor inference results and heatmap matrices. "
            "stream mode: read prediction results from inference:output stream; "
            "heatmap mode: read grid predictions from Redis heat_map key"
        )
    )
    parser.add_argument(
        "--mode",
        choices=["stream", "heatmap"],
        default="stream",
        help="Read mode: stream (results) or heatmap (32x32 grid). Default: stream",
    )
    parser.add_argument(
        "--token",
        default="",
        help="Token for token-scoped keys (e.g., heat_map:<token>). If empty, uses default key",
    )
    parser.add_argument(
        "--heatmap-key",
        default=DEFAULT_HEATMAP_KEY,
        help=f"Base heatmap key. Default: {DEFAULT_HEATMAP_KEY}",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="For heatmap mode: read once and exit (no polling)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="For stream mode: print summary stats every 10 results",
    )
    return parser.parse_args()


def print_heatmap_matrix(matrix: list) -> None:
    """Выводит все 32x32 значения из матрицы"""
    if not matrix or not isinstance(matrix[0], list):
        print("Invalid matrix format")
        return
    
    rows = len(matrix)
    cols = len(matrix[0])
    
    print(f"\n🗺️ Heatmap ({rows}x{cols}) - all values:")
    print("=" * 80)
    
    for row_idx, row in enumerate(matrix):
        line_parts = []
        for col_idx, cell in enumerate(row):
            try:
                val = float(cell)
                line_parts.append(f"{val:.4f}")
            except (TypeError, ValueError):
                line_parts.append("  N/A  ")
        print(f"[{row_idx:2d}] " + "  ".join(line_parts))
    
    print("=" * 80)


def print_heatmap_stats(value: str, key: str) -> None:
    try:
        matrix = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        print(f"⚠️ Invalid JSON in key {key}")
        return

    if not isinstance(matrix, list) or not matrix or not isinstance(matrix[0], list):
        print(f"⚠️ Key {key} does not contain matrix-like data")
        return

    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    non_zero = 0
    total = 0
    for row in matrix:
        if not isinstance(row, list):
            continue
        for cell in row:
            try:
                val = float(cell)
            except (TypeError, ValueError):
                continue
            total += 1
            if val != 0.0:
                non_zero += 1

    print(f"[{time.strftime('%H:%M:%S')}] key={key} shape={rows}x{cols} non_zero={non_zero}/{total}")
    
    # Выводим матрицу
    print_heatmap_matrix(matrix)


# ─────────────────────────────────────────────────────────────
# Основной цикл чтения стрима
# ─────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    last_id = "$"  # start from end of stream (only new messages)
    print(f"🔌 Connecting to Redis: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    if args.mode == "stream":
        print(f"📡 Reading stream: {STREAM_NAME}")
        if args.stats:
            print("📊 Stats mode: will print summary every 10 results\n")
    else:
        heatmap_key = f"{args.heatmap_key}:{args.token}" if args.token else args.heatmap_key
        print(f"🗺️  Reading heatmap key: {heatmap_key}\n")
    print("Press Ctrl+C to exit\n")

    result_count = 0
    stats_interval = 10
    probs: list[float] = []

    while True:
        client = None
        try:
            client = make_redis_client()
            client.ping()  # connection check
            print(f"✓ Connected to Redis @ {time.strftime('%H:%M:%S')}\n")

            while True:
                if args.mode == "stream":
                    # Blocking read: wait for new messages
                    result = client.xread(
                        streams={STREAM_NAME: last_id},
                        block=BLOCK_TIMEOUT_MS,
                        count=10  # read in batches of 10
                    )

                    if result:
                        for stream_name, entries in result:
                            for entry_id, fields in entries:
                                print_stream_entry(stream_name, entry_id, fields)
                                result_count += 1

                                # extract probability for stats if available
                                if "data" in fields:
                                    try:
                                        data = json.loads(fields["data"])
                                        prob = data.get("death_probability", 0.0)
                                        if isinstance(prob, (int, float)):
                                            probs.append(float(prob))
                                    except Exception:
                                        pass

                                # print stats every N results
                                if args.stats and result_count > 0 and result_count % stats_interval == 0:
                                    if probs:
                                        avg_prob = sum(probs) / len(probs)
                                        min_prob = min(probs)
                                        max_prob = max(probs)
                                        print(f"\n📊 Stats: {result_count} results | "
                                              f"avg_prob={avg_prob:.4f} | "
                                              f"min={min_prob:.4f} | max={max_prob:.4f}\n")

                                last_id = entry_id
                else:
                    heatmap_key = f"{args.heatmap_key}:{args.token}" if args.token else args.heatmap_key
                    raw = client.get(heatmap_key)
                    if raw:
                        print_heatmap_stats(raw, heatmap_key)
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] key not found: {heatmap_key}")
                    if args.once:
                        return
                    time.sleep(1)

        except redis.AuthenticationError:
            print(f"\n❌ Authentication error. Check REDIS_PASSWORD='{REDIS_PASSWORD}'")
            time.sleep(RECONNECT_DELAY_SEC)
        except redis.ConnectionError as e:
            print(f"\n❌ Lost connection to Redis: {e}")
            print(f"🔄 Retrying in {RECONNECT_DELAY_SEC} sec...")
            time.sleep(RECONNECT_DELAY_SEC)
        except KeyboardInterrupt:
            print("\n👋 Shutdown")
            if result_count > 0 and args.stats:
                print(f"Final: processed {result_count} results")
            break
        except Exception as e:
            print(f"\n⚠️  Unexpected error: {type(e).__name__}: {e}")
            time.sleep(RECONNECT_DELAY_SEC)
        finally:
            if client:
                try:
                    client.close()
                except:
                    pass


if __name__ == "__main__":
    main()