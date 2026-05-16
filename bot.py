import asyncio
import logging
import threading
import os
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, get_setting
import common
import admin
import driver
import passenger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BotActiveMiddleware(BaseMiddleware):
    """Бот тоқтатылған болса, админлардан басқа ҳамманы блоклайды."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Фойдаланувчи ID сини аниқлаш
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        # Админларга ҳар доим рухсат
        if user_id and user_id in ADMIN_IDS:
            return await handler(event, data)

        # Бот ҳолатини текшириш
        bot_active = await get_setting("bot_active")
        if bot_active == "0":
            if isinstance(event, Message):
                await event.answer(
                    "🔴 <b>Бот ҳәзир ислемей тур.</b>\n\n"
                    "Кейинирек қайта уринип көриң.",
                    parse_mode="HTML"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "🔴 Бот ҳәзир ислемей тур. Кейинирек уриниң.",
                    show_alert=True
                )
            return  # handlerrни чақирмаймиз

        return await handler(event, data)


def run_api():
    from api import app
    port = int(os.getenv("API_PORT", 8000))
    logger.info(f"🌐 API сервер порты {port} да иске түсти!")
    app.run(host="0.0.0.0", port=port, use_reloader=False)


async def main():
    await init_db()

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware — барча Message ва CallbackQuery учун
    dp.message.middleware(BotActiveMiddleware())
    dp.callback_query.middleware(BotActiveMiddleware())

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(driver.router)
    dp.include_router(passenger.router)

    logger.info("🚖 Jolawshi_Bot иске түсти!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
