from fastapi import FastAPI, lifespan
from contextlib import asynccontextmanager

from services.gsi_processor.scr.infra.catalog import JsonCatalog
from services.gsi_processor.scr.infra.redis import RedisClient
from .scr.api.routers import router
from .scr.infra.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # инициализационные процессы
    
    app.state.redis = RedisClient(url=settings.redis_url)
    app.state.abilities_catalog = JsonCatalog(path=str(settings.ABILITIES_JSON))
    app.state.hero_stats_catalog = JsonCatalog(path=str(settings.HERO_STATS_JSON))
    app.state.items_catalog = JsonCatalog(path=str(settings.ITEMS_JSON))

    yield

    await app.state.redis.close()
    # после убийства сервиса

app = FastAPI(lifespan=lifespan)
app.include_router(router=router)