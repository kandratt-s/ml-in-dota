from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from scr.api.router import router
from scr.infra.config import settings
from scr.infra.redis import InferenceRedisRepository, PredictionConfigRepository, RedisClient
from scr.services.batch import BatchBuilder
from scr.services.model import ModelRegistryFactory
from scr.services.worker import InferenceWorkerService, WorkerSettings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = RedisClient.from_url(settings.redis_url)
    redis_repository = InferenceRedisRepository(
        client=redis_client,
        input_queue_name=settings.INFERENCE_INPUT_QUEUE,
        output_queue_name=settings.INFERENCE_OUTPUT_QUEUE,
        consumer_name=settings.CONSUMER_NAME,
    )

    prediction_config_repository = PredictionConfigRepository(client=redis_client)
    model_registry = ModelRegistryFactory(
        boosting_models_dir=settings.BOOSTING_MODELS_DIR,
        logreg_models_dir=settings.LOGREG_MODELS_DIR,
    ).build_registry()

    worker_service = InferenceWorkerService(
        redis_repository=redis_repository,
        predictor=None,
        batch_builder=BatchBuilder(),
        worker_settings=WorkerSettings(
            batch_size=settings.BATCH_SIZE,
            poll_interval_seconds=settings.POLL_INTERVAL_SECONDS,
            cells=settings.CELLS,
            heatmap_result_key=settings.HEATMAP_RESULT_KEY,
        ),
        config_repository=prediction_config_repository,
        model_registry=model_registry,
    )

    app.state.redis_client = redis_client
    app.state.worker_service = worker_service
    app.state.worker_task = asyncio.create_task(worker_service.run_forever())

    yield
    
    worker_service.stop()
    worker_task = app.state.worker_task
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await redis_client.close()

app = FastAPI(title="Dota 2 Inference Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)

