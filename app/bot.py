import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_settings
from app.database.db import Database

from app.handlers import (
    admin,
    booking,
    misc,
    start,
    subscription,
    menu_handlers,
)

from app.services.scheduler import ReminderService


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()

    db = Database(settings.database_path)
    db.init()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.start()

    reminder_service = ReminderService(
        scheduler=scheduler,
        db=db,
        bot=bot,
    )

    reminder_service.restore_jobs_from_db()

    # 🔥 ВАЖНО: booking ПЕРВЫЙ
    dp.include_router(start.router)
    dp.include_router(subscription.router)

    dp.include_router(booking.router)        # 👈 сюда должен попадать start_booking

    dp.include_router(menu_handlers.router)   # 👈 UI кнопки (prices, portfolio)

    dp.include_router(misc.router)
    dp.include_router(admin.router)

    await dp.start_polling(
        bot,
        settings=settings,
        db=db,
        reminder_service=reminder_service,
    )


if __name__ == "__main__":
    asyncio.run(main())
