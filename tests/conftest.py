
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest

# Ensure core runtime deps are present; skip whole test suite early if not.
pytest.importorskip("pydantic_settings")
pytest.importorskip("pydantic")
pytest.importorskip("fakeredis")

REPO_ROOT = Path(__file__).resolve().parents[1]

# Minimal environment keys used during tests to avoid loading project .env
DEFAULT_ENV = {
    "TELEGRAM_BOT_TOKEN": "dummy-token",
    "TOKEN_SECRET": "dummy-secret",
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_PASSWORD": "test-password",
    "XMIN": "-9400",
    "XMAX": "8000",
    "YMIN": "-8500",
    "YMAX": "8500",
    "CELLS": "32",
    "INFERENCE_INPUT_QUEUE": "inference:input",
    "INFERENCE_OUTPUT_QUEUE": "inference:output",
    "HEATMAP_RESULT_KEY": "heat_map",
    "REQUEST_TIMEOUT_SECONDS": "1.0",
    "INFERENCE_SERVICE_URL": "http://localhost:8000",
}


@pytest.fixture(autouse=True)
def required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # gsi_processor settings are validated on module import.
    defaults = {
        "TELEGRAM_BOT_TOKEN": "dummy-token",
        "TOKEN_SECRET": "dummy-secret",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_PASSWORD": "test-password",
        "XMIN": "-9400",
        "XMAX": "8000",
        "YMIN": "-8500",
        "YMAX": "8500",
        "CELLS": "32",
        "INFERENCE_INPUT_QUEUE": "inference:input",
        "INFERENCE_OUTPUT_QUEUE": "inference:output",
        "HEATMAP_RESULT_KEY": "heat_map",
        "REQUEST_TIMEOUT_SECONDS": "1.0",
        "INFERENCE_SERVICE_URL": "http://localhost:8000",
    }
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)


def _clear_scr_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "scr" or module_name.startswith("scr."):
            del sys.modules[module_name]


@contextmanager
def import_service_scr(service_path: Path) -> Iterator[None]:
    original_sys_path = list(sys.path)
    original_cwd = Path.cwd()
    _clear_scr_modules()
    sys.path.insert(0, str(service_path))
    # Temporarily reduce environment so pydantic-settings does not read project .env
    old_env = os.environ.copy()
    allowed_preserve = {
        "PATH",
        "HOME",
        "USER",
        "SHELL",
        "TERM",
        "PYTEST_CURRENT_TEST",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PWD",
        "LANG",
        "LC_ALL",
    }
    new_env = {k: v for k, v in old_env.items() if k in allowed_preserve}
    new_env.update(DEFAULT_ENV)
    os.environ.clear()
    os.environ.update(new_env)
    try:
        os.chdir(service_path)
        yield
    finally:
        # restore environment
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(old_env)
        _clear_scr_modules()
        sys.path[:] = original_sys_path


@pytest.fixture
def gsi_service_path() -> Path:
    return REPO_ROOT / "services" / "gsi_processor"


@pytest.fixture
def inference_service_path() -> Path:
    return REPO_ROOT / "services" / "inference"


@pytest.fixture
def web_service_path() -> Path:
    return REPO_ROOT / "services" / "web"
