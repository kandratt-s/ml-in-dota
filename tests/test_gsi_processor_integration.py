from __future__ import annotations

import json
from pathlib import Path

import pytest

# Skip whole module if required runtime deps not installed in the test environment
pytest.importorskip("pydantic")
fakeredis = pytest.importorskip("fakeredis")
import fakeredis.aioredis
from pydantic import ValidationError

from conftest import import_service_scr


def _build_payload(*, token: str, game_time: int, minimap: dict[str, dict], hero_x: int = 1200, hero_y: int = 800) -> dict:
    return {
        "map": {
            "matchid": 8766917050,
            "game_time": game_time,
            "daytime": True,
            "radiant_score": 10,
            "dire_score": 12,
        },
        "player": {
            "accountid": 1001,
            "kills": 2,
            "deaths": 1,
            "assists": 3,
            "last_hits": 50,
            "denies": 5,
            "gold": 1200,
            "team_name": "radiant",
        },
        "hero": {
            "xpos": hero_x,
            "ypos": hero_y,
            "id": 1,
            "level": 8,
            "health": 700,
            "max_health": 1000,
            "mana": 350,
            "max_mana": 500,
            "xp": 2500,
        },
        "abilities": {
            "ability0": {"name": "", "level": 1, "cooldown": 0},
            "ability1": {"name": "", "level": 2, "cooldown": 5},
            "ability2": {"name": "", "level": 3, "cooldown": 8},
            "ability3": {"name": "", "level": 1, "cooldown": 0},
        },
        "items": {
            "slot0": {"name": "item_blink", "cooldown": 0},
            "slot1": {"name": "item_tpscroll", "cooldown": 0},
            "slot2": {"name": "item_phase_boots", "cooldown": 0},
        },
        "minimap": minimap,
        "auth": {"token": token},
    }


@pytest.mark.asyncio
async def test_gsi_updates_snapshot_and_enqueues_for_inference(gsi_service_path: Path) -> None:
    with import_service_scr(gsi_service_path):
        from scr.infra.catalog import JsonCatalog
        from scr.infra.redis import ActiveTokensRepository, EnemyStateRepository, InferenceQueueRepository, SnapshotStateRepository
        from scr.schemas.dota_input import GSIRequest
        from scr.schemas.inference_queue import InferenceRecord
        from scr.services.process import GSIProcessorService

        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

        class FakeRedisClient:
            def __init__(self, raw):
                self.raw = raw

        client = FakeRedisClient(fake_redis)

        service = GSIProcessorService(
            abilities_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "abilities.json")),
            hero_stats_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "heroes.json")),
            items_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "items.json")),
            enemy_state_repo=EnemyStateRepository(client=client),
            active_token_repo=ActiveTokensRepository(client=client),
            inference_queue_repo=InferenceQueueRepository(client=client, queue_name="inference:input"),
            snapshot_state_repo=SnapshotStateRepository(client=client),
        )

        token = "token-42"
        await service.active_token_repo.add(token)

        first_payload = _build_payload(
            token=token,
            game_time=100,
            minimap={
                "1": {"xpos": 1500, "ypos": 1000, "unitname": "npc_dota_hero_axe", "team": 3},
                "2": {"xpos": 1700, "ypos": 900, "unitname": "npc_dota_badguys_tower1_mid", "team": 3},
                "3": {"xpos": 1100, "ypos": 800, "unitname": "npc_dota_goodguys_tower1_mid", "team": 2},
            },
        )
        first = await service.process_gsi_data(GSIRequest.model_validate(first_payload))
        assert first.game_time == 100

        snapshot_raw = await fake_redis.get(f"snapshot:{token}:current")
        snapshot = json.loads(snapshot_raw)
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_time"] == 0
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_x"] == 1500
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_y"] == 1000

        second_payload = _build_payload(
            token=token,
            game_time=101,
            minimap={
                "2": {"xpos": 1700, "ypos": 900, "unitname": "npc_dota_badguys_tower1_mid", "team": 3},
                "3": {"xpos": 1100, "ypos": 800, "unitname": "npc_dota_goodguys_tower1_mid", "team": 2},
            },
        )
        second = await service.process_gsi_data(GSIRequest.model_validate(second_payload))
        assert second.game_time == 101

        snapshot_raw = await fake_redis.get(f"snapshot:{token}:current")
        snapshot = json.loads(snapshot_raw)
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_time"] == 1
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_x"] == 1500
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_y"] == 1000

        third_payload = _build_payload(
            token=token,
            game_time=102,
            minimap={
                "1": {"xpos": 1800, "ypos": 1400, "unitname": "npc_dota_hero_axe", "team": 3},
                "10": {"xpos": 2000, "ypos": 1450, "unitname": "npc_dota_hero_axe", "team": 3},
                "2": {"xpos": 1700, "ypos": 900, "unitname": "npc_dota_badguys_tower1_mid", "team": 3},
            },
        )
        third = await service.process_gsi_data(GSIRequest.model_validate(third_payload))
        assert third.game_time == 102

        snapshot_raw = await fake_redis.get(f"snapshot:{token}:current")
        snapshot = json.loads(snapshot_raw)
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_time"] == 0
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_x"] == 2000
        assert snapshot["enemies"]["npc_dota_hero_axe"]["enemy_last_seen_y"] == 1450

        stream_entries = await fake_redis.xrange("inference:input", min="-", max="+")
        assert len(stream_entries) == 3

        last_message = stream_entries[-1][1]["data"]
        parsed_record = InferenceRecord.model_validate_json(last_message)
        assert parsed_record.record_id.endswith(":102")
        assert parsed_record.payload["game_time"] == 102
        assert parsed_record.payload["enemy_1_last_seen_time"] == 0


@pytest.mark.asyncio
async def test_gsi_missing_required_fields_rejected_and_not_enqueued(gsi_service_path: Path) -> None:
    with import_service_scr(gsi_service_path):
        from scr.infra.catalog import JsonCatalog
        from scr.infra.redis import ActiveTokensRepository, EnemyStateRepository, InferenceQueueRepository, SnapshotStateRepository
        from scr.schemas.dota_input import GSIRequest
        from scr.services.process import GSIProcessorService

        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

        class FakeRedisClient:
            def __init__(self, raw):
                self.raw = raw

        client = FakeRedisClient(fake_redis)

        service = GSIProcessorService(
            abilities_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "abilities.json")),
            hero_stats_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "heroes.json")),
            items_catalog=JsonCatalog(str(gsi_service_path / "local_data" / "items.json")),
            enemy_state_repo=EnemyStateRepository(client=client),
            active_token_repo=ActiveTokensRepository(client=client),
            inference_queue_repo=InferenceQueueRepository(client=client, queue_name="inference:input"),
            snapshot_state_repo=SnapshotStateRepository(client=client),
        )

        payload = _build_payload(
            token="token-invalid",
            game_time=200,
            minimap={
                "1": {"xpos": 1500, "ypos": 1000, "unitname": "npc_dota_hero_axe", "team": 3},
            },
        )
        del payload["hero"]["mana"]

        with pytest.raises(ValidationError):
            _ = GSIRequest.model_validate(payload)

        stream_entries = await fake_redis.xrange("inference:input", min="-", max="+")
        assert stream_entries == []
