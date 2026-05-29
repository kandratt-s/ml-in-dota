from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request
import sys
from pathlib import Path


DEFAULT_URL = "http://localhost:8001/gsi-input"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a JSONL file to the GSI collector line by line with a fixed delay between requests.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to the JSONL file to stream.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Delay in seconds between sending lines. Default: 1.0.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Collector URL. Default: {DEFAULT_URL}",
    )
    return parser.parse_args()


def send_json(url: str, payload: str) -> tuple[bool, str | None]:
    body = payload.encode("utf-8")

    
    request = urllib.request.Request(
        url=url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return False, str(exc)

    return True, None


def main() -> None:
    args = parse_args()

    if not args.path.exists():
        raise SystemExit(f"File not found: {args.path}")

    try:
        lines = [line.strip() for line in args.path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except UnicodeDecodeError:
        lines = [line.strip() for line in args.path.read_text(encoding="cp1251").splitlines() if line.strip()]


    sent_count = 0
    rejected_count = 0

    for index, payload in enumerate(lines, start=1):
        sent, error = send_json(args.url, payload)
        if sent:
            print(f"sent line {index}")
            sent_count += 1
        else:
            print(f"line {index} was rejected and skipped: {error}", file=sys.stderr)
            rejected_count += 1

        if index != len(lines):
            time.sleep(args.interval)

    print(f"done: sent={sent_count}, rejected={rejected_count}, total={len(lines)}")


if __name__ == "__main__":
    main()