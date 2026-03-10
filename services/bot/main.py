import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from scr.config import settings
from scr.models.database import init_database, get_db_manager
from scr.handlers import registration_router, dota_play_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Initialize database
    init_database(settings.DATABASE_URL)
    
    storage = RedisStorage.from_url(settings.redis_url)
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN.get_secret_value())
    dp = Dispatcher(storage=storage)

    dp.include_router(registration_router)
    dp.include_router(dota_play_router)

    logger.info("Bot started")
    
    try:
        await dp.start_polling(bot)
    finally:
        # Clean up database connections
        db_manager = get_db_manager()
        await db_manager.close()
        logger.info("Database connections closed")


if __name__ == "__main__":
    asyncio.run(main())
