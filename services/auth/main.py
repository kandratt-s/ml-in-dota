from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scr.core.config import settings
from scr.core.database import init_db, engine
from scr.core.redis import close_redis_pool
from scr.api.router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Конфигурация уже инициализирована в scr.core.config.settings.
    await init_db()
    yield

    # после убийства сервиса
    await close_redis_pool()
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(router=router)



app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)