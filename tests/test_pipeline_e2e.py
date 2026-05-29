from __future__ import annotations

import json
from pathlib import Path

import fakeredis
import fakeredis.aioredis
import pytest

from conftest import import_service_scr
from test_gsi_processor_integration import _build_payload


class DummyPredictor:
    backend_name = "dummy"

    def predict_proba(self, features: list[dict]) -> list[float]:
        return [0.66 for _ in features]


@pytest.mark.asyncio
async def test_e2e_gsi_to_inference_to_web(
    gsi_service_path: Path,
    inference_service_path: Path,
    web_service_path: Path,
    monkeypatch,
) -> None:
    server = fakeredis.FakeServer()
    fake_async_redis = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)
    fake_sync_redis = fakeredis.FakeRedis(server=server, decode_responses=True)

    with import_service_scr(gsi_service_path):
        from scr.infra.catalog import JsonCatalog
        from scr.infra.redis import ActiveTokensRepository, EnemyStateRepository, InferenceQueueRepository, SnapshotStateRepository
        from scr.schemas.dota_input import GSIRequest
        from scr.services.process import GSIProcessorService

        class FakeRedisClient:
            def __init__(self, raw):
                self.raw = raw

        gsi_service = GSIProcessorService(
            abilities_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "abilities.json")),
            hero_stats_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "heroes.json")),
            items_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "items.json")),
            enemy_state_repo=EnemyStateRepository(client=FakeRedisClient(fake_async_redis)),
            active_token_repo=ActiveTokensRepository(client=FakeRedisClient(fake_async_redis)),
            inference_queue_repo=InferenceQueueRepository(client=FakeRedisClient(fake_async_redis), queue_name="inference:input"),
            snapshot_state_repo=SnapshotStateRepository(client=FakeRedisClient(fake_async_redis)),
        )

        request_payload = _build_payload(
            token="token-e2e",
            game_time=500,
            minimap={
                "1": {"xpos": 1800, "ypos": 900, "unitname": "npc_dota_hero_axe", "team": 3},
                "2": {"xpos": 1700, "ypos": 800, "unitname": "npc_dota_badguys_tower1_mid", "team": 3},
                "3": {"xpos": 1200, "ypos": 600, "unitname": "npc_dota_goodguys_tower1_mid", "team": 2},
            },
        )
        result = await gsi_service.process_gsi_data(GSIRequest.model_validate(request_payload))
        assert result.game_time == 500

    with import_service_scr(inference_service_path):
        from scr.infra.redis import InferenceRedisRepository, RedisClient
        from scr.services.batch import BatchBuilder
        from scr.services.worker import InferenceWorkerService, WorkerSettings

        repository = InferenceRedisRepository(
            client=RedisClient(client=fake_async_redis),
            input_queue_name="inference:input",
            output_queue_name="inference:output",
            consumer_name="e2e-consumer",
        )
        worker = InferenceWorkerService(
            redis_repository=repository,
            predictor=DummyPredictor(),
            batch_builder=BatchBuilder(),
            worker_settings=WorkerSettings(
                batch_size=16,
                poll_interval_seconds=0.01,
                cells=32,
                heatmap_result_key="heat_map",
            ),
        )
        process_response = await worker.process_once()
        assert process_response.processed_items == 1
        assert process_response.enqueued_results == 1

    output_entries = await fake_async_redis.xrange("inference:output", min="-", max="+")
    assert len(output_entries) == 1
    output_payload = json.loads(output_entries[0][1]["data"])
    assert output_payload["record_id"].endswith(":500")

    with import_service_scr(web_service_path):
        from scr.api.heatmap_client import InferenceClient

        import redis

        monkeypatch.setattr(redis, "Redis", lambda *args, **kwargs: fake_sync_redis)

        web_client = InferenceClient(inference_service_url="http://localhost:8000")
        heatmap = web_client.get_current_heatmap()
        assert heatmap is not None
        assert web_client.get_current_heatmap() is None
