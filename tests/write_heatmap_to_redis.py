from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import redis


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a heatmap matrix to Redis in the format consumed by the web service.",
    )
    parser.add_argument("--redis-host", default=os.getenv("REDIS_HOST", "localhost"))
    parser.add_argument("--redis-port", type=int, default=int(os.getenv("REDIS_PORT", "6379")))
    parser.add_argument("--redis-password", default=os.getenv("REDIS_PASSWORD") or None)
    parser.add_argument("--key", default=os.getenv("HEATMAP_RESULT_KEY", "heat_map"))
    parser.add_argument("--cells", type=int, default=int(os.getenv("CELLS", "32")))
    parser.add_argument(
        "--points-json",
        type=Path,
        help="JSON file with either a list of {square, death_probability} points or an object with a points field.",
    )
    parser.add_argument(
        "--matrix-json",
        type=Path,
        help="JSON file containing a ready-made 2D heatmap matrix.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Read the key back after writing and validate that the stored matrix is usable by the web client.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_matrix(cells: int, points: list[dict[str, Any]] | None = None) -> list[list[float]]:
    matrix = [[0.0 for _ in range(cells)] for _ in range(cells)]
    if not points:
        # Default demo pattern: a diagonal gradient that is easy to see in the UI.
        for idx in range(cells):
            matrix[idx][idx] = round((idx + 1) / cells, 4)
        return matrix

    for point in points:
        square = point.get("square")
        value = point.get("death_probability", point.get("prediction"))
        if not isinstance(square, int):
            raise ValueError(f"Invalid square value: {square!r}")
        if not isinstance(value, (int, float)):
            raise ValueError(f"Invalid prediction value for square {square}: {value!r}")
        if square < 0 or square >= cells * cells:
            raise ValueError(f"Square index out of range for {cells}x{cells} heatmap: {square}")

        row = square // cells
        col = square % cells
        matrix[row][col] = float(value)

    return matrix


def _normalize_points(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        points = payload.get("points")
    else:
        points = payload

    if not isinstance(points, list):
        raise ValueError("points-json must contain a list of points or an object with a points list")

    normalized: list[dict[str, Any]] = []
    for item in points:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid point entry: {item!r}")
        normalized.append(item)
    return normalized


def main() -> int:
    args = _parse_args()

    if args.points_json and args.matrix_json:
        raise SystemExit("Use only one of --points-json or --matrix-json")

    if args.matrix_json:
        matrix = _load_json(args.matrix_json)
        if not isinstance(matrix, list):
            raise SystemExit("matrix-json must contain a 2D list")
    else:
        points = None
        if args.points_json:
            points = _normalize_points(_load_json(args.points_json))
        matrix = _build_matrix(args.cells, points)

    client = redis.Redis(
        host=args.redis_host,
        port=args.redis_port,
        password=args.redis_password,
        decode_responses=True,
    )

    payload = json.dumps(matrix, ensure_ascii=False)
    client.set(args.key, payload)

    rows = len(matrix)
    cols = len(matrix[0]) if rows and isinstance(matrix[0], list) else 0
    print(f"Stored heatmap in Redis key {args.key!r} at {args.redis_host}:{args.redis_port} with shape {rows}x{cols}")

    if args.verify:
        raw = client.get(args.key)
        if raw is None:
            raise SystemExit("Verification failed: heatmap key was not found after writing")

        restored = json.loads(raw)
        if not isinstance(restored, list) or not restored:
            raise SystemExit("Verification failed: restored heatmap is not a non-empty matrix")

        restored_rows = len(restored)
        restored_cols = len(restored[0]) if isinstance(restored[0], list) else 0
        if restored_rows != rows or restored_cols != cols:
            raise SystemExit(
                f"Verification failed: expected {rows}x{cols}, got {restored_rows}x{restored_cols}"
            )

        print("Verification passed: Redis value is readable by the web client format")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())