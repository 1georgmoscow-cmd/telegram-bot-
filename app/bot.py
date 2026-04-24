import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_settings

# ❗ НОВАЯ АРХИТЕКТУРА
from app.database.connection import get_connection
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
    conn = get_connection(settings.database_path)
    booking_repo = BookingRepository(conn)

    # =========================
    # BOT
    # =========================
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # =========================
    # SCHEDULER
    # =========================
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.start()

    reminder_service = ReminderService(
        scheduler=scheduler,
        db=booking_repo,  # 👈 теперь repo
        bot=bot,
    )

    reminder_service.restore_jobs_from_db()

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
    await dp.start_polling(
        bot,
        settings=settings,
        repo=booking_repo,              # 👈 ВАЖНО
        reminder_service=reminder_service,
    )


if __name__ == "__main__":
    asyncio.run(main())
