from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from scr.api.router import router
from scr.infra.config import settings
from scr.infra.redis import InferenceRedisRepository, RedisClient
from scr.services.batch import BatchBuilder
from scr.services.model import ModelFactory
from scr.services.worker import InferenceWorkerService, WorkerSettings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def build_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        redis_client = RedisClient.from_url(settings.redis_url)
        redis_repository = InferenceRedisRepository(
            client=redis_client,
            input_queue_name=settings.INFERENCE_INPUT_QUEUE,
            output_queue_name=settings.INFERENCE_OUTPUT_QUEUE,
            consumer_name=settings.CONSUMER_NAME,
        )

        model_factory = ModelFactory(model_path=settings.MODEL_PATH)
        predictor = model_factory.build_predictor()

        worker_service = InferenceWorkerService(
            redis_repository=redis_repository,
            predictor=predictor,
            batch_builder=BatchBuilder(),
            worker_settings=WorkerSettings(
                batch_size=settings.BATCH_SIZE,
                poll_interval_seconds=settings.POLL_INTERVAL_SECONDS,
                cells=settings.CELLS,
                heatmap_result_key=settings.HEATMAP_RESULT_KEY,
            ),
        )

        app.state.redis_client = redis_client
        app.state.worker_service = worker_service
        app.state.worker_task = asyncio.create_task(worker_service.run_forever())

        try:
            yield
        finally:
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
    return app


app = build_app()


def main() -> None:
    uvicorn.run("scr.main:app", host="0.0.0.0", port=8000, reload=False)