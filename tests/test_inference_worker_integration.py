from __future__ import annotations

import json
from pathlib import Path

import pytest

# Require fakeredis for Redis emulation in tests
fakeredis = pytest.importorskip("fakeredis")
import fakeredis.aioredis

from conftest import import_service_scr


class DummyPredictor:
    backend_name = "dummy"

    def predict_proba(self, features: list[dict]) -> list[float]:
        return [0.77 for _ in features]


@pytest.mark.asyncio
async def test_inference_worker_reads_acks_writes_and_updates_heatmap(inference_service_path: Path) -> None:
    with import_service_scr(inference_service_path):
        from scr.infra.redis import InferenceRedisRepository, RedisClient
        from scr.services.batch import BatchBuilder
        from scr.services.worker import InferenceWorkerService, WorkerSettings

        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        redis_client = RedisClient(client=fake_redis)
        repository = InferenceRedisRepository(
            client=redis_client,
            input_queue_name="inference:input",
            output_queue_name="inference:output",
            consumer_name="test-consumer",
        )

        valid_message = {
            "record_id": "m1:a1:10",
            "payload": {"square": 5, "health": 300, "mana": 100},
        }
        await fake_redis.xadd("inference:input", {"data": json.dumps(valid_message)})
        await fake_redis.xadd("inference:input", {"data": "{not-json"})

        worker = InferenceWorkerService(
            redis_repository=repository,
            predictor=DummyPredictor(),
            batch_builder=BatchBuilder(),
            worker_settings=WorkerSettings(
                batch_size=10,
                poll_interval_seconds=0.01,
                cells=4,
                heatmap_result_key="heat_map",
            ),
        )

        response = await worker.process_once()
        assert response.processed_items == 1
        assert response.enqueued_results == 1

        input_entries = await fake_redis.xrange("inference:input", min="-", max="+")
        assert len(input_entries) == 1
        assert input_entries[0][1]["data"] == "{not-json"

        output_entries = await fake_redis.xrange("inference:output", min="-", max="+")
        assert len(output_entries) == 1
        output_payload = json.loads(output_entries[0][1]["data"])
        assert output_payload["record_id"] == "m1:a1:10"
        assert output_payload["death_probability"] == pytest.approx(0.77)
        assert output_payload["metadata"]["square"] == 5

        heatmap_raw = await fake_redis.get("heat_map")
        assert heatmap_raw is not None
        heatmap = json.loads(heatmap_raw)
        assert heatmap[1][1] == pytest.approx(0.77)


@pytest.mark.asyncio
async def test_inference_worker_replaces_single_square_heatmap_between_ticks(inference_service_path: Path) -> None:
    with import_service_scr(inference_service_path):
        from scr.infra.redis import InferenceRedisRepository, PredictionConfigRepository, RedisClient
        from scr.schemas.prediction_config import PredictionConfig
        from scr.services.batch import BatchBuilder
        from scr.services.model import ModelRegistry
        from scr.services.worker import InferenceWorkerService, WorkerSettings

        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        redis_client = RedisClient(client=fake_redis)
        repository = InferenceRedisRepository(
            client=redis_client,
            input_queue_name="inference:input",
            output_queue_name="inference:output",
            consumer_name="test-consumer",
        )
        config_repository = PredictionConfigRepository(client=redis_client)
        await config_repository.set_for_token(
            "token-a",
            PredictionConfig(model="boosting", time=10, interval=1, full_map=False),
        )

        model_registry = ModelRegistry(
            predictors={("boosting", 10): TokenPredictor("boosting", 0.55)}
        )

        first_message = {
            "record_id": "a1",
            "payload": {
                "square": 0,
                "health": 300,
                "mana": 100,
                "is_radiant": True,
                "x": 0,
                "y": 0,
                "enemy_1_last_seen_x": 100,
                "enemy_1_last_seen_y": 100,
                "enemy_1_last_seen_distance": 0,
                "nearest_ally_tower_distance": 0,
                "nearest_enemy_tower_distance": 0,
                "hero_id": 1,
                "enemy_1_name": "npc_dota_hero_axe",
                "enemy_2_name": "",
                "enemy_3_name": "",
                "enemy_4_name": "",
                "enemy_5_name": "",
                "__meta__": {"token": "token-a"},
            },
        }
        second_message = {
            "record_id": "a2",
            "payload": {
                "square": 5,
                "health": 300,
                "mana": 100,
                "is_radiant": True,
                "x": 0,
                "y": 0,
                "enemy_1_last_seen_x": 100,
                "enemy_1_last_seen_y": 100,
                "enemy_1_last_seen_distance": 0,
                "nearest_ally_tower_distance": 0,
                "nearest_enemy_tower_distance": 0,
                "hero_id": 1,
                "enemy_1_name": "npc_dota_hero_axe",
                "enemy_2_name": "",
                "enemy_3_name": "",
                "enemy_4_name": "",
                "enemy_5_name": "",
                "__meta__": {"token": "token-a"},
            },
        }
        await fake_redis.xadd("inference:input", {"data": json.dumps(first_message)})
        await fake_redis.xadd("inference:input", {"data": json.dumps(second_message)})

        worker = InferenceWorkerService(
            redis_repository=repository,
            predictor=None,
            batch_builder=BatchBuilder(),
            worker_settings=WorkerSettings(
                batch_size=10,
                poll_interval_seconds=0.01,
                cells=4,
                heatmap_result_key="heat_map",
            ),
            config_repository=config_repository,
            model_registry=model_registry,
        )

        first_response = await worker.process_once()
        assert first_response.processed_items == 1

        first_heatmap_raw = await fake_redis.get("heat_map:token-a")
        assert first_heatmap_raw is not None
        first_heatmap = json.loads(first_heatmap_raw)
        assert first_heatmap[0][0] == pytest.approx(0.55)

        second_response = await worker.process_once()
        assert second_response.processed_items == 1

        second_heatmap_raw = await fake_redis.get("heat_map:token-a")
        assert second_heatmap_raw is not None
        second_heatmap = json.loads(second_heatmap_raw)
        assert second_heatmap[0][0] == pytest.approx(0.0)
        assert second_heatmap[1][1] == pytest.approx(0.55)


class TokenPredictor:
    def __init__(self, backend_name: str, value: float) -> None:
        self.backend_name = backend_name
        self._value = value

    def predict_proba(self, features: list[dict]) -> list[float]:
        return [self._value for _ in features]


@pytest.mark.asyncio
async def test_inference_worker_uses_token_config_and_isolates_heatmaps(inference_service_path: Path) -> None:
    with import_service_scr(inference_service_path):
        from scr.infra.redis import InferenceRedisRepository, PredictionConfigRepository, RedisClient
        from scr.schemas.prediction_config import PredictionConfig
        from scr.services.batch import BatchBuilder
        from scr.services.model import ModelRegistry
        from scr.services.worker import InferenceWorkerService, WorkerSettings

        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        redis_client = RedisClient(client=fake_redis)
        repository = InferenceRedisRepository(
            client=redis_client,
            input_queue_name="inference:input",
            output_queue_name="inference:output",
            consumer_name="test-consumer",
        )
        config_repository = PredictionConfigRepository(client=redis_client)
        await config_repository.set_for_token("token-a", PredictionConfig(model="boosting", time=10, interval=1, full_map=True))
        await config_repository.set_for_token("token-b", PredictionConfig(model="logreg", time=5, interval=3, full_map=False))

        model_registry = ModelRegistry(
            predictors={
                ("boosting", 10): TokenPredictor("boosting", 0.10),
                ("logreg", 5): TokenPredictor("logreg", 0.90),
            }
        )

        valid_a = {
            "record_id": "a1",
            "payload": {
                "square": 0,
                "health": 300,
                "mana": 100,
                "is_radiant": True,
                "x": 0,
                "y": 0,
                "enemy_1_last_seen_x": 100,
                "enemy_1_last_seen_y": 100,
                "enemy_1_last_seen_distance": 0,
                "nearest_ally_tower_distance": 0,
                "nearest_enemy_tower_distance": 0,
                "hero_id": 1,
                "enemy_1_name": "npc_dota_hero_axe",
                "enemy_2_name": "",
                "enemy_3_name": "",
                "enemy_4_name": "",
                "enemy_5_name": "",
                "__meta__": {"token": "token-a"},
            },
        }
        valid_b = {
            "record_id": "b1",
            "payload": {
                "square": 5,
                "health": 300,
                "mana": 100,
                "is_radiant": False,
                "x": 0,
                "y": 0,
                "enemy_1_last_seen_x": 100,
                "enemy_1_last_seen_y": 100,
                "enemy_1_last_seen_distance": 0,
                "nearest_ally_tower_distance": 0,
                "nearest_enemy_tower_distance": 0,
                "hero_id": 1,
                "enemy_1_name": "npc_dota_hero_axe",
                "enemy_2_name": "",
                "enemy_3_name": "",
                "enemy_4_name": "",
                "enemy_5_name": "",
                "__meta__": {"token": "token-b"},
            },
        }
        await fake_redis.xadd("inference:input", {"data": json.dumps(valid_a)})
        await fake_redis.xadd("inference:input", {"data": json.dumps(valid_b)})

        worker = InferenceWorkerService(
            redis_repository=repository,
            predictor=None,
            batch_builder=BatchBuilder(),
            worker_settings=WorkerSettings(
                batch_size=10,
                poll_interval_seconds=0.01,
                cells=4,
                heatmap_result_key="heat_map",
            ),
            config_repository=config_repository,
            model_registry=model_registry,
        )

        response = await worker.process_once()
        assert response.processed_items == 2
        assert response.enqueued_results == 2

        heatmap_a_raw = await fake_redis.get("heat_map:token-a")
        heatmap_b_raw = await fake_redis.get("heat_map:token-b")
        assert heatmap_a_raw is not None
        assert heatmap_b_raw is not None
        heatmap_a = json.loads(heatmap_a_raw)
        heatmap_b = json.loads(heatmap_b_raw)
        assert heatmap_a[0][0] == pytest.approx(0.10)
        assert heatmap_b[1][1] == pytest.approx(0.90)

        output_entries = await fake_redis.xrange("inference:output", min="-", max="+")
        assert len(output_entries) == 2
        payloads = [json.loads(entry[1]["data"]) for entry in output_entries]
        assert {payload["metadata"]["token"] for payload in payloads} == {"token-a", "token-b"}
