from __future__ import annotations

from pathlib import Path

import pytest

fakeredis = pytest.importorskip("fakeredis")
import fakeredis.aioredis
from pydantic import ValidationError

from conftest import import_service_scr


def test_prediction_config_defaults_and_validation(inference_service_path: Path) -> None:
    with import_service_scr(inference_service_path):
        from scr.schemas.prediction_config import PredictionConfig

        config = PredictionConfig()
        assert config.model == "boosting"
        assert config.time == 10
        assert config.interval == 1
        assert config.full_map is True

        with pytest.raises(ValidationError):
            PredictionConfig.model_validate(
                {"model": "xgboost", "time": 10, "interval": 1, "full_map": True}
            )


@pytest.mark.asyncio
async def test_prediction_config_repository_roundtrip_and_default(inference_service_path: Path) -> None:
    with import_service_scr(inference_service_path):
        from scr.infra.redis import PredictionConfigRepository, RedisClient
        from scr.schemas.prediction_config import PredictionConfig

        fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        repo = PredictionConfigRepository(client=RedisClient(client=fake_redis))

        default_config = await repo.get_for_token("missing-token")
        assert default_config == PredictionConfig()

        config = PredictionConfig(model="logreg", time=5, interval=3, full_map=False)
        await repo.set_for_token("token-1", config)

        loaded = await repo.get_for_token("token-1")
        assert loaded == config
