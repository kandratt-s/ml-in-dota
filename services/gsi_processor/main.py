from fastapi import FastAPI
from contextlib import asynccontextmanager

from scr.infra.catalog import JsonCatalog
from scr.infra.redis import ActiveTokensRepository, InferenceQueueRepository, SnapshotStateRepository, RedisClient 
from scr.services.process import GSIProcessorService
from scr.api import router
from scr.infra.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # инициализационные процессы
    
    app.state.redis = RedisClient(url=settings.redis_url)
    app.state.abilities_catalog = JsonCatalog(path=str(settings.ABILITIES_JSON))
    app.state.hero_stats_catalog = JsonCatalog(path=str(settings.HERO_STATS_JSON))
    app.state.items_catalog = JsonCatalog(path=str(settings.ITEMS_JSON))
    app.state.hero_names_catalog = JsonCatalog(path=str(settings.HERO_NAMES_JSON))

    app.state.active_tokens_repository = ActiveTokensRepository(client=app.state.redis)
    app.state.inference_queue_repository = InferenceQueueRepository(
        client=app.state.redis,
        queue_name=settings.INFERENCE_INPUT_QUEUE,
    )
    app.state.snapshot_state_repository = SnapshotStateRepository(client=app.state.redis)

    app.state.GSI_processor_service = GSIProcessorService(
        abilities_catalog=app.state.abilities_catalog,
        hero_stats_catalog=app.state.hero_stats_catalog,
        hero_names_catalog=app.state.hero_names_catalog,
        items_catalog=app.state.items_catalog,
        active_token_repo=app.state.active_tokens_repository,
        inference_queue_repo=app.state.inference_queue_repository,
        snapshot_state_repo=app.state.snapshot_state_repository,
    )

    yield

    await app.state.redis.close()
    # после убийства сервиса

app = FastAPI(lifespan=lifespan)
app.include_router(router=router.router)