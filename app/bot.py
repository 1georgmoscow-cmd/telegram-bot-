import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_settings
from app.database.db import Database
from app.handlers import admin, booking, misc, start
from app.services.scheduler import ReminderService
from app.services.subscription import SubscriptionService


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()

    # DB
    db = Database(settings.database_path)
    db.init()

    # Bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.start()

    reminder_service = ReminderService(
        scheduler=scheduler,
        db=db,
        bot=bot
    )
    reminder_service.restore_jobs_from_db()

    # Subscription service (ВАЖНО: это НЕ router)
    subscription_service = SubscriptionService(cache_ttl=120)

    # Routers (ТОЛЬКО handlers)
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(misc.router)
    dp.include_router(admin.router)

    # polling
    await dp.start_polling(
        bot,
        settings=settings,
        db=db,
        reminder_service=reminder_service,
        subscription_service=subscription_service,  # передаём сервис сюда
    )


if __name__ == "__main__":
    asyncio.run(main())
