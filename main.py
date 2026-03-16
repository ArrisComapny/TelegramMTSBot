import sys
import asyncio
import logging

import database.models # импортируем модели, чтобы они зарегистрировались

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from config import TOKEN, PROXY
from routers.admin import admin_router
from routers.other import other_router
from database.db import Database, Base
from database.middlewares import DbSessionMiddleware


async def init_db(db: Database) -> None:
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    session = AiohttpSession(proxy=PROXY)

    # Инициализация бота и диспетчера
    bot = Bot(token=TOKEN, session=session, default=(DefaultBotProperties(parse_mode=ParseMode.HTML)))
    dp = Dispatcher()

    db = Database()
    await db.connect()
    await init_db(db)

    # dp.update.outer_middleware(DbSessionMiddleware(db))

    dp.include_router(admin_router)
    dp.include_router(other_router)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await db.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
