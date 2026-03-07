import asyncio
import logging

from aiogram import Bot, Dispatcher

from scr.config import settings
from scr.models.database import init_database, get_db_manager
from scr.handlers import registration_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Initialize database
    init_database(settings.DATABASE_URL)
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN.get_secret_value())
    dp = Dispatcher()

    dp.include_router(registration_router)

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
