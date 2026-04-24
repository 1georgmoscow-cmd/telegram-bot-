import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.defalt import DefaultBotProperties
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
    # DB
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

    reminder_service.restore()

    # =====================
    # DISPATCHER
    # =====================
    dp = Dispatcher()

    # 🔥 ЕДИНСТВЕННЫЙ ПРАВИЛЬНЫЙ СПОСОБ DI
    dp["repo"] = repo
    dp["settings"] = settings
    dp["reminder_service"] = reminder_service
    dp["bot"] = bot

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
    # START
    # =====================
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


# =====================
# ENTRYPOINT (RAILWAY SAFE)
# =====================
def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()

print("BOT STARTED ✔")
