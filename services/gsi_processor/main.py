from fastapi import FastAPI
from contextlib import asynccontextmanager

from scr.infra.catalog import JsonCatalog
from scr.infra.redis import ActiveTokensRepository, EnemyStateRepository, RedisClient
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

    app.state.enemy_state_repository = EnemyStateRepository(client=app.state.redis)
    app.state.active_tokens_repository = ActiveTokensRepository(client=app.state.redis)

    app.state.GSI_processor_service = GSIProcessorService(
        abilities_catalog=app.state.abilities_catalog,
        hero_stats_catalog=app.state.hero_stats_catalog,
        items_catalog=app.state.items_catalog,
        enemy_state_repo=app.state.enemy_state_repository,
        active_token_repo=app.state.active_tokens_repository
    )

    yield

    await app.state.redis.close()
    # после убийства сервиса

app = FastAPI(lifespan=lifespan)
app.include_router(router=router.router)