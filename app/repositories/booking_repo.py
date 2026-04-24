from app.database.database import Database


class BookingRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, user_id, name, phone, date, time):
        exists = self.db.fetchone(
            "SELECT id FROM bookings WHERE date=? AND time=? AND active=1",
            (date, time),
        )
        if exists:
            return None

        cur = self.db.execute(
            """
            INSERT INTO bookings (user_id, name, phone, date, time, active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (user_id, name, phone, date, time),
        )
        return cur.lastrowid

    def get_active_by_user(self, user_id):
        return self.db.fetchone(
            "SELECT * FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )

    def get_slots_for_date(self, date):
        return self.db.fetchall(
            "SELECT time FROM bookings WHERE date=? AND active=1",
            (date,),
        )

    def get_all_for_restore(self):
        return self.db.fetchall(
            "SELECT * FROM bookings WHERE active=1"
        )

    def set_reminder(self, booking_id, job_id):
        self.db.execute(
            "UPDATE bookings SET reminder_job_id=? WHERE id=?",
            (job_id, booking_id),
        )