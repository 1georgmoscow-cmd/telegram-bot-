from app.database.database import Database


class BookingRepository:
    def __init__(self, db: Database):
        self.db = db

    # =========================
    # BOOKING CORE
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
    # SLOTS (CLIENT SIDE)
    # =========================
    def get_busy_slots(self, date):
        rows = self.db.fetchall(
            "SELECT time FROM bookings WHERE date=? AND active=1",
            (date,),
        )
        return [row["time"] for row in rows]

    def get_free_slots(self, date):
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00",
        ]

        busy = self.get_busy_slots(date)
        return [slot for slot in all_slots if slot not in busy]

    # =========================
    # ADMIN: WORK DAYS
    # =========================
    def add_work_day(self, day: str):
        self.db.execute(
            "INSERT OR IGNORE INTO work_days (date) VALUES (?)",
            (day,),
        )

    def get_work_days(self):
        rows = self.db.fetchall("SELECT date FROM work_days ORDER BY date")
        return [r["date"] for r in rows]

    # =========================
    # ADMIN: SLOTS
    # =========================
    def add_slot(self, date: str, time: str):
        self.db.execute(
            "INSERT OR IGNORE INTO slots (date, time, active) VALUES (?, ?, 1)",
            (date, time),
        )

    def delete_slot(self, date: str, time: str):
        cur = self.db.execute(
            "DELETE FROM slots WHERE date=? AND time=?",
            (date, time),
        )
        return cur.rowcount > 0

    def get_slots_for_date(self, date: str):
        rows = self.db.fetchall(
            "SELECT time FROM slots WHERE date=? AND active=1",
            (date,),
        )
        return [r["time"] for r in rows]

    # =========================
    # ADMIN: SCHEDULE VIEW
    # =========================
    def get_schedule_by_date(self, date: str):
        return self.db.fetchall(
            """
            SELECT s.time,
                   b.id as booking_id,
                   b.name,
                   b.phone
            FROM slots s
            LEFT JOIN bookings b
                ON b.date = s.date AND b.time = s.time AND b.active = 1
            WHERE s.date=?
            ORDER BY s.time
            """,
            (date,),
        )

    def get_bookings_for_date(self, date: str):
        return self.db.fetchall(
            "SELECT * FROM bookings WHERE date=? AND active=1 ORDER BY time",
            (date,),
        )

    # =========================
    # CANCEL BOOKING
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
    # SCHEDULER SUPPORT
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
