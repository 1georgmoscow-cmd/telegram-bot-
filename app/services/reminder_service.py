from datetime import datetime, timedelta


class ReminderService:
    def __init__(self, scheduler, bot, booking_repo):
        self.scheduler = scheduler
        self.bot = bot
        self.repo = booking_repo

    async def send_reminder(self, user_id: int, time: str):
        await self.bot.send_message(
            user_id,
            f"Напоминание: запись завтра в <b>{time}</b>",
            parse_mode="HTML",
        )

    def schedule(self, booking_id, user_id, date, time):
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        reminder_at = dt - timedelta(hours=24)

        if reminder_at <= datetime.now():
            return None

        job_id = f"booking_{booking_id}"

        self.scheduler.add_job(
            self.send_reminder,
            "date",
            run_date=reminder_at,
            kwargs={"user_id": user_id, "time": time},
            id=job_id,
            replace_existing=True,
        )

        self.repo.set_reminder(booking_id, job_id)
        return job_id

    def restore(self):
        for b in self.repo.get_all_for_restore():
            if b["reminder_job_id"] and self.scheduler.get_job(b["reminder_job_id"]):
                continue

            self.schedule(
                booking_id=b["id"],
                user_id=b["user_id"],
                date=b["date"],
                time=b["time"],
            )