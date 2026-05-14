from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def flatten_mapping(data: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flat_mapping: dict[str, Any] = {}
    for key, value in data.items():
        nested_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            flat_mapping.update(flatten_mapping(value, nested_key))
            continue
        if isinstance(value, list):
            for index, item in enumerate(value):
                list_key = f"{nested_key}.{index}"
                if isinstance(item, Mapping):
                    flat_mapping.update(flatten_mapping(item, list_key))
                else:
                    flat_mapping[list_key] = item
            continue
        flat_mapping[nested_key] = value
    return flat_mapping