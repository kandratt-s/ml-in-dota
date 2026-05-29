from __future__ import annotations

import json
from pathlib import Path

import pytest

# Require fakeredis in sync mode for web client tests
fakeredis = pytest.importorskip("fakeredis")
import fakeredis

from conftest import import_service_scr


def test_web_client_enqueues_requests_and_consumes_heatmap(web_service_path: Path, monkeypatch) -> None:
    with import_service_scr(web_service_path):
        from scr.api.heatmap_client import InferenceClient

        fake_sync_redis = fakeredis.FakeRedis(decode_responses=True)

        import redis

        monkeypatch.setattr(redis, "Redis", lambda *args, **kwargs: fake_sync_redis)

        client = InferenceClient(inference_service_url="http://localhost:8000")

        ok = client.enqueue_prediction_request("r1", {"square": 12, "hero_id": 1})
        assert ok is True

        input_entries = fake_sync_redis.xrange("inference:input", min="-", max="+")
        assert len(input_entries) == 1
        queued = json.loads(input_entries[0][1]["data"])
        assert queued["record_id"] == "r1"
        assert queued["payload"]["square"] == 12

        matrix = [[0.1, 0.2], [0.3, 0.4]]
        fake_sync_redis.set("heat_map", json.dumps(matrix))

        loaded_matrix = client.get_current_heatmap()
        assert loaded_matrix == matrix
        assert fake_sync_redis.get("heat_map") is None
