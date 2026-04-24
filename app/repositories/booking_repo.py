from app.database.database import Database


class BookingRepository:
    def __init__(self, db: Database):
        self.db = db

    # =========================
    # CREATE
    # =========================
    def create_booking(self, user_id: int, name: str, phone: str, date: str, time: str):
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
    def has_active_booking(self, user_id: int) -> bool:
        row = self.db.fetchone(
            "SELECT id FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )
        return row is not None

    def get_active_booking(self, user_id: int):
        return self.db.fetchone(
            "SELECT * FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )

    # =========================
    # SLOTS (RAW DATA ONLY)
    # =========================
    def get_busy_slots(self, date: str):
        rows = self.db.fetchall(
            "SELECT time FROM bookings WHERE date=? AND active=1",
            (date,),
        )
        return rows

    def get_bookings_for_date(self, date: str):
        return self.db.fetchall(
            "SELECT * FROM bookings WHERE date=? AND active=1",
            (date,),
        )

    # =========================
    # WORK DAYS
    # =========================
    def get_month_work_days(self, start_date: str, end_date: str):
        rows = self.db.fetchall(
            """
            SELECT DISTINCT date
            FROM bookings
            WHERE date BETWEEN ? AND ?
            """,
            (start_date, end_date),
        )
        return rows

    # =========================
    # SCHEDULE VIEW
    # =========================
    def get_schedule_by_date(self, date: str):
        return self.db.fetchall(
            """
            SELECT id as booking_id, name, phone, date, time
            FROM bookings
            WHERE date=?
            ORDER BY time
            """,
            (date,),
        )

    # =========================
    # DELETE / CANCEL
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
    # REMINDER
    # =========================
    def set_reminder_job_id(self, booking_id: int, job_id: str | None):
        self.db.execute(
            "UPDATE bookings SET reminder_job_id=? WHERE id=?",
            (job_id, booking_id),
        )
