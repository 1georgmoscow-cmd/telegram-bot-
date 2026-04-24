from app.database.database import Database


class BookingRepository:
    def __init__(self, db: Database):
        self.db = db

    # =========================
    # BOOKING CREATE
    # =========================
    def create_booking(self, user_id, name, phone, date, time):
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

    # =========================
    # ACTIVE CHECK
    # =========================
    def has_active_booking(self, user_id):
        row = self.db.fetchone(
            "SELECT id FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )
        return bool(row)

    def get_active_booking(self, user_id):
        return self.db.fetchone(
            "SELECT * FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )

    # =========================
    # SLOTS
    # =========================
    def get_busy_slots(self, date):
        rows = self.db.fetchall(
            "SELECT time FROM bookings WHERE date=? AND active=1",
            (date,),
        )
        return [r["time"] for r in rows]

    def get_free_slots(self, date):
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00",
        ]

        busy = self.get_busy_slots(date)
        return [s for s in all_slots if s not in busy]

    # =========================
    # WORK DAYS (для календаря)
    # =========================
    def get_month_work_days(self, start_date, end_date):
        rows = self.db.fetchall(
            """
            SELECT DISTINCT date
            FROM bookings
            WHERE date BETWEEN ? AND ?
            """,
            (start_date, end_date),
        )
        return [r["date"] for r in rows]

    # =========================
    # ADMIN: WORK DAYS
    # =========================
    def add_work_day(self, day: str):
        # просто создаём "пустой слот-день"
        self.db.execute(
            """
            INSERT INTO bookings (user_id, name, phone, date, time, active)
            VALUES (0, '', '', ?, '', 0)
            """,
            (day,),
        )

    # =========================
    # ADMIN: SLOTS
    # =========================
    def add_slot(self, date: str, time: str):
        self.db.execute(
            """
            INSERT INTO bookings (user_id, name, phone, date, time, active)
            VALUES (0, '', '', ?, ?, 0)
            """,
            (date, time),
        )

    def delete_slot(self, date: str, time: str):
        cur = self.db.execute(
            """
            DELETE FROM bookings
            WHERE date=? AND time=? AND user_id=0
            """,
            (date, time),
        )
        return cur.rowcount > 0

    # =========================
    # ADMIN: SCHEDULE VIEW
    # =========================
    def get_schedule_by_date(self, date: str):
        return self.db.fetchall(
            """
            SELECT *
            FROM bookings
            WHERE date=?
            ORDER BY time
            """,
            (date,),
        )

    # =========================
    # ADMIN: BOOKINGS LIST
    # =========================
    def get_bookings_for_date(self, date: str):
        return self.db.fetchall(
            """
            SELECT *
            FROM bookings
            WHERE date=? AND active=1
            ORDER BY time
            """,
            (date,),
        )

    # =========================
    # ADMIN: CANCEL BOOKING
    # =========================
    def cancel_booking_by_id(self, booking_id: int):
        booking = self.db.fetchone(
            "SELECT * FROM bookings WHERE id=?",
            (booking_id,),
        )

        if not booking:
            return None

        self.db.execute(
            "UPDATE bookings SET active=0 WHERE id=?",
            (booking_id,),
        )

        return booking

    # =========================
    # SCHEDULER RESTORE
    # =========================
    def get_active_bookings_for_restore(self):
        return self.db.fetchall(
            "SELECT * FROM bookings WHERE active=1"
        )

    def set_reminder_job_id(self, booking_id, job_id):
        self.db.execute(
            "UPDATE bookings SET reminder_job_id=? WHERE id=?",
            (job_id, booking_id),
        )
