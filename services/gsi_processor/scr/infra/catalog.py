from pathlib import Path
from typing import Any, Union
import json

JSONType = Union[dict, list]

class JsonCatalog:
    def __init__(self, path: str):
        self._path = Path(path)

        with self._path.open("r", encoding="utf-8") as f:
            self._data: JSONType = json.load(f)

    def as_dict(self) -> dict:
        if not isinstance(self._data, dict):
            raise TypeError("JSON is not a dict")
        return self._data

    def as_list(self) -> list:
        if not isinstance(self._data, list):
            raise TypeError("JSON is not a list")
        return self._data