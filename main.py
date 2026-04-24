import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_settings

from app.database.database import Database
from app.repositories.booking_repo import BookingRepository

from app.services.reminder_service import ReminderService

from app.handlers import (
    admin,
    booking,
    misc,
    start,
    subscription,
    menu_handlers,
)


async def main():
    logging.basicConfig(level=logging.INFO)

    # =====================
    # CONFIG
    # =====================
    settings = load_settings()

    # =====================
    # DB + REPO
    # =====================
    db = Database(settings.database_path)
    repo = BookingRepository(db)

    # =====================
    # BOT
    # =====================
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # =====================
    # SCHEDULER
    # =====================
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.start()

    reminder_service = ReminderService(
        scheduler=scheduler,
        bot=bot,
        booking_repo=repo,
    )

    # 🔥 восстановление задач
    reminder_service.restore()

    # =====================
    # DISPATCHER
    # =====================
    dp = Dispatcher()

    # прокидываем зависимости в handlers через workflow_data
    dp["repo"] = repo
    dp["reminder_service"] = reminder_service
    dp["settings"] = settings

    # =====================
    # ROUTERS
    # =====================
    dp.include_router(start.router)
    dp.include_router(subscription.router)

    dp.include_router(booking.router)
    dp.include_router(menu_handlers.router)

    dp.include_router(misc.router)
    dp.include_router(admin.router)

    # =====================
    # START BOT
    # =====================
    await dp.start_polling(
        bot,
        settings=settings,
        repo=repo,
        reminder_service=reminder_service,
    )


if __name__ == "__main__":
    asyncio.run(main())