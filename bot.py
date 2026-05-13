import asyncio
import logging
import threading
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
import common
import admin
import driver
import passenger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_api():
    from api import app
    port = int(os.getenv("API_PORT", 8000))
    logger.info(f"🌐 API server port {port} da ishga tushdi!")
    app.run(host="0.0.0.0", port=port, use_reloader=False)


async def main():
    await init_db()

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(driver.router)
    dp.include_router(passenger.router)

    logger.info("🚖 JolawshiBot ishga tushdi!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
