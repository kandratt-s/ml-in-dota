from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import redis

# Попытка загрузить .env файл (если установлен python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # ищет .env в корне проекта
except ImportError:
    pass  # dotenv не установлен — используем только системные env-переменные


# Дефолты из env-переменных (если не заданы — используются локальные значения)
# DEFAULT_REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DEFAULT_REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # None, если не задано
DEFAULT_ACTIVE_PREFIX = "active:"
DEFAULT_CONFIG_PREFIX = "prediction-config:"
DEFAULT_COLLECTOR_URL = "http://localhost:8001/gsi-input"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write active token + per-token prediction config to Redis, "
            "then stream a JSONL file to gsi_processor via send_jsonl_to_gsi_collector.py"
        )
    )
    parser.add_argument(
        "jsonl_path",
        type=Path,
        help="Path to JSONL file for send_jsonl_to_gsi_collector.py",
    )
    parser.add_argument(
        "--token",
        default="секретный_токен",
        help="Token used for active and config keys. Default: test-token",
    )
    
    # Redis connection args — с приоритетом: CLI > ENV > defaults
    parser.add_argument(
        "--redis-host",
        default=DEFAULT_REDIS_HOST,
        help=f"Redis host. Default: {DEFAULT_REDIS_HOST}",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=DEFAULT_REDIS_PORT,
        help=f"Redis port. Default: {DEFAULT_REDIS_PORT}",
    )
    parser.add_argument(
        "--redis-password",
        default=DEFAULT_REDIS_PASSWORD,
        help="Redis password. Default: value from REDIS_PASSWORD env var",
    )
    parser.add_argument(
        "--redis-db",
        type=int,
        default=int(os.getenv("REDIS_DB", 0)),
        help="Redis database number. Default: 0",
    )

    parser.add_argument(
        "--active-prefix",
        default=DEFAULT_ACTIVE_PREFIX,
        help=f"Redis key prefix for active tokens. Default: {DEFAULT_ACTIVE_PREFIX}",
    )
    parser.add_argument(
        "--config-prefix",
        default=DEFAULT_CONFIG_PREFIX,
        help=f"Redis key prefix for prediction config. Default: {DEFAULT_CONFIG_PREFIX}",
    )
    parser.add_argument(
        "--active-ttl",
        type=int,
        default=5400,
        help="TTL for active token key (seconds). Default: 5400",
    )

    parser.add_argument(
        "--model",
        choices=["boosting", "logreg"],
        default="boosting",
        help="Prediction model config. Default: boosting",
    )
    parser.add_argument(
        "--time",
        type=int,
        choices=[1, 5, 10, 15, 20],
        default=10,
        help="Prediction horizon config. Default: 10",
    )
    parser.add_argument(
        "--predict-interval",
        type=int,
        choices=[1, 3, 5],
        default=1,
        help="Prediction config interval. Default: 1",
    )
    parser.add_argument(
        "--full-map",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use full-map mode in prediction config (default: true)",
    )

    parser.add_argument(
        "--send-interval",
        type=float,
        default=0.01,
        help="Delay between JSONL lines for send_jsonl_to_gsi_collector.py. Default: 0.01",
    )
    parser.add_argument(
        "--collector-url",
        default=DEFAULT_COLLECTOR_URL,
        help=f"Collector URL for sender script. Default: {DEFAULT_COLLECTOR_URL}",
    )
    parser.add_argument(
        "--sender-script",
        type=Path,
        default=Path(__file__).resolve().parent / "send_jsonl_to_gsi_collector.py",
        help="Path to send_jsonl_to_gsi_collector.py",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to run sender script. Default: current interpreter",
    )

    return parser.parse_args()


def write_active_and_config(
    redis_host: str,
    redis_port: int,
    redis_password: str | None,
    redis_db: int,
    active_prefix: str,
    config_prefix: str,
    token: str,
    active_ttl: int,
    model: str,
    time_value: int,
    predict_interval: int,
    full_map: bool,
) -> None:
    # Собираем kwargs для Redis-клиента
    client_kwargs: dict[str, object] = {
        "host": redis_host,
        "port": redis_port,
        "db": redis_db,
        "decode_responses": True,
    }
    
    # Добавляем пароль ТОЛЬКО если он явно задан (не None)
    if redis_password is not None:
        client_kwargs["password"] = redis_password

    client = redis.Redis(**client_kwargs)
    
    try:
        # prefixes already include a trailing colon by default (e.g. "active:")
        active_key = f"{active_prefix}{token}"
        config_key = f"{config_prefix}{token}"

        config_payload = {
            "model": model,
            "time": time_value,
            "interval": predict_interval,
            "full_map": full_map,
        }

        client.set(active_key, "1", ex=active_ttl)
        client.set(config_key, json.dumps(config_payload, ensure_ascii=False))

        print(f"✓ active key set: {active_key} (ttl={active_ttl}s)")
        print(f"✓ config key set: {config_key} -> {config_payload}")
    finally:
        client.close()


def run_sender(
    python_executable: str,
    sender_script: Path,
    jsonl_path: Path,
    send_interval: float,
    collector_url: str,
) -> int:
    cmd = [
        python_executable,
        str(sender_script),
        str(jsonl_path),
        "--interval",
        str(send_interval),
        "--url",
        collector_url,
    ]
    print("running sender:", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    return int(result.returncode)


def main() -> None:
    args = parse_args()

    if not args.jsonl_path.exists():
        raise SystemExit(f"JSONL file not found: {args.jsonl_path}")
    if not args.sender_script.exists():
        raise SystemExit(f"Sender script not found: {args.sender_script}")
    if args.active_ttl <= 0:
        raise SystemExit("--active-ttl must be > 0")

    write_active_and_config(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        redis_password=args.redis_password,
        redis_db=args.redis_db,
        active_prefix=args.active_prefix,
        config_prefix=args.config_prefix,
        token=args.token,
        active_ttl=args.active_ttl,
        model=args.model,
        time_value=args.time,
        predict_interval=args.predict_interval,
        full_map=args.full_map,
    )
    # verify keys were written
    client = redis.Redis(host=args.redis_host, port=args.redis_port, db=args.redis_db, password=args.redis_password, decode_responses=True)
    try:
        active_key = f"{args.active_prefix}{args.token}"
        config_key = f"{args.config_prefix}{args.token}"
        if not client.exists(active_key):
            print(f"ERROR: active key {active_key} not present in Redis")
        else:
            print(f"OK: active key present: {active_key}")
        if not client.exists(config_key):
            print(f"ERROR: config key {config_key} not present in Redis")
        else:
            print(f"OK: config key present: {config_key}")
    finally:
        client.close()

    exit_code = run_sender(
        python_executable=args.python,
        sender_script=args.sender_script,
        jsonl_path=args.jsonl_path,
        send_interval=args.send_interval,
        collector_url=args.collector_url,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()