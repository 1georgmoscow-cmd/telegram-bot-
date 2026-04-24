from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.repositories.booking_repo import BookingRepository


class ReminderService:
    def __init__(
        self,
        scheduler: AsyncIOScheduler,
        repo: BookingRepository,
        bot: Bot,
    ):
        self.scheduler = scheduler
        self.repo = repo
        self.bot = bot

    # =========================
    # SEND
    # =========================
    async def send_reminder(self, user_id: int, booking_time: str) -> None:
        await self.bot.send_message(
            user_id,
            f"Напоминаем, что вы записаны на наращивание ресниц завтра в <b>{booking_time}</b>.\nЖдём вас ❤️",
        )

    # =========================
    # CREATE JOB
    # =========================
    def schedule_booking_reminder(
        self, booking_id: int, user_id: int, date_str: str, time_str: str
    ) -> str | None:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        reminder_at = dt - timedelta(hours=24)

        if reminder_at <= datetime.now():
            return None

        job_id = f"booking_reminder_{booking_id}"

        self.scheduler.add_job(
            self.send_reminder,
            trigger="date",
            run_date=reminder_at,
            kwargs={
                "user_id": user_id,
                "booking_time": time_str,
            },
            id=job_id,
            replace_existing=True,
        )

        return job_id

    # =========================
    # DELETE JOB
    # =========================
    def cancel_reminder(self, job_id: str | None) -> None:
        if not job_id:
            return

        job = self.scheduler.get_job(job_id)
        if job:
            job.remove()

    # =========================
    # RESTORE AFTER RESTART
    # =========================
    def restore_jobs_from_db(self) -> None:
        bookings = self.repo.get_active_bookings_for_restore()

        for booking in bookings:
            existing_job_id = booking["reminder_job_id"]

            if existing_job_id and self.scheduler.get_job(existing_job_id):
                continue

            new_job_id = self.schedule_booking_reminder(
                booking_id=booking["id"],
                user_id=booking["user_id"],
                date_str=booking["date"],
                time_str=booking["time"],
            )

            self.repo.set_reminder_job_id(
                booking["id"],
                new_job_id,
            )