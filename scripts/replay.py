#!/usr/bin/env python3
# Проигрывает .jsonl-дамп GSI на эндпоинт gsi_processor.
# Подменяет auth.token (в дампах он "секретный_токен") на переданный --token,
# выдерживает паузы между событиями по provider.timestamp * 1/speed.
import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--token", required=True)
    p.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="множитель к реальному времени (0 = слать без пауз)",
    )
    p.add_argument("--timeout", type=float, default=5.0)
    args = p.parse_args()

    sent = ok = skipped_422 = skipped_bad = failed = 0
    prev_ts: float | None = None
    started = time.monotonic()

    with open(args.file, "rb") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                skipped_bad += 1
                continue

            payload.setdefault("auth", {})["token"] = args.token

            ts = payload.get("provider", {}).get("timestamp")
            if (
                args.speed > 0
                and isinstance(ts, (int, float))
                and prev_ts is not None
            ):
                delta = (ts - prev_ts) / args.speed
                if delta > 0:
                    time.sleep(delta)
            if isinstance(ts, (int, float)):
                prev_ts = float(ts)

            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                args.url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            sent += 1
            try:
                with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                    if 200 <= resp.status < 300:
                        ok += 1
                    else:
                        failed += 1
            except urllib.error.HTTPError as e:
                # 422 — кадр не подходит под GSIRequest (меню/загрузка). Это норма.
                # 403 — токен не активирован: критично, печатаем.
                if e.code == 422:
                    skipped_422 += 1
                else:
                    failed += 1
                    if failed <= 5:
                        msg = e.read()[:200]
                        print(
                            f"[!] HTTP {e.code} на кадре #{sent}: {msg!r}",
                            file=sys.stderr,
                        )
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"[!] кадр #{sent}: {e!r}", file=sys.stderr)

            if sent % 200 == 0:
                el = time.monotonic() - started
                print(
                    f"[*] sent={sent} ok={ok} 422_skipped={skipped_422} "
                    f"failed={failed} elapsed={el:.1f}s",
                    flush=True,
                )

    el = time.monotonic() - started
    print(
        f"[*] done. sent={sent} ok={ok} 422_skipped={skipped_422} "
        f"bad_json={skipped_bad} failed={failed} elapsed={el:.1f}s"
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
