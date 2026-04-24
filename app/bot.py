import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_settings

from app.database.database import Database
from app.repositories.booking_repo import BookingRepository

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

    # =========================
    # DB
    # =========================
    db = Database(settings.database_path)
    db.init()

    booking_repo = BookingRepository(db)

    # =========================
    # BOT
    # =========================
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # =========================
    # GLOBAL DEPENDENCIES (ВАЖНО)
    # =========================
    dp.workflow_data.update(
        settings=settings,
        repo=booking_repo,
    )

    # =========================
    # SCHEDULER
    # =========================
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.start()

    reminder_service = ReminderService(
        scheduler=scheduler,
        repo=booking_repo,
        bot=bot,
    )

    reminder_service.restore_jobs_from_db()

    dp.workflow_data.update(
        reminder_service=reminder_service,
    )

    # =========================
    # ROUTERS
    # =========================
    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(booking.router)
    dp.include_router(menu_handlers.router)
    dp.include_router(misc.router)
    dp.include_router(admin.router)

    # =========================
    # START
    # =========================
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
