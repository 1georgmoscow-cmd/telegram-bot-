from app.database.database import Database


class BookingRepository:
    def __init__(self, db: Database):
        self.db = db

    # =========================
    # BOOKING (CLIENTS)
    # =========================
    def create_booking(self, user_id, name, phone, date, time):
        exists = self.db.fetchone(
            """
            SELECT id FROM bookings
            WHERE date=? AND time=? AND active=1
            """,
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
    # ACTIVE BOOKING CHECK
    # =========================
    def has_active_booking(self, user_id: int) -> bool:
        row = self.db.fetchone(
            "SELECT id FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )
        return bool(row)

    def get_active_booking(self, user_id: int):
        return self.db.fetchone(
            "SELECT * FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )

    # =========================
    # SLOTS LOGIC
    # =========================
    def get_busy_slots(self, date: str):
        rows = self.db.fetchall(
            "SELECT time FROM bookings WHERE date=? AND active=1",
            (date,),
        )
        return [r["time"] for r in rows]

    def get_free_slots(self, date: str):
        slots = self.db.fetchall(
            "SELECT time FROM slots WHERE date=?",
            (date,),
        )

        busy = set(self.get_busy_slots(date))

        return [s["time"] for s in slots if s["time"] not in busy]

    # =========================
    # WORK DAYS
    # =========================
    def add_work_day(self, day: str):
        self.db.execute(
            "INSERT OR IGNORE INTO work_days (date) VALUES (?)",
            (day,),
        )

    def get_month_work_days(self, start_date: str, end_date: str):
        rows = self.db.fetchall(
            """
            SELECT date
            FROM work_days
            WHERE date BETWEEN ? AND ?
            ORDER BY date
            """,
            (start_date, end_date),
        )
        return [r["date"] for r in rows]

    # =========================
    # SLOTS (ADMIN)
    # =========================
    def add_slot(self, date: str, time: str):
        self.db.execute(
            """
            INSERT OR IGNORE INTO slots (date, time)
            VALUES (?, ?)
            """,
            (date, time),
        )

    def delete_slot(self, date: str, time: str):
        cur = self.db.execute(
            "DELETE FROM slots WHERE date=? AND time=?",
            (date, time),
        )
        return cur.rowcount > 0

    # =========================
    # SCHEDULE VIEW (ADMIN)
    # =========================
    def get_schedule_by_date(self, date: str):
        slots = self.db.fetchall(
            "SELECT * FROM slots WHERE date=? ORDER BY time",
            (date,),
        )

        bookings = self.db.fetchall(
            "SELECT * FROM bookings WHERE date=? AND active=1",
            (date,),
        )

        booking_map = {b["time"]: b for b in bookings}

        result = []

        for s in slots:
            time = s["time"]

            if time in booking_map:
                b = booking_map[time]
                result.append({
                    "time": time,
                    "booking_id": b["id"],
                    "name": b["name"],
                    "phone": b["phone"],
                })
            else:
                result.append({
                    "time": time,
                    "booking_id": None,
                    "name": None,
                    "phone": None,
                })

        return result

    # =========================
    # ADMIN BOOKINGS
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

    def set_reminder_job_id(self, booking_id: int, job_id: str):
        self.db.execute(
            """
            UPDATE bookings
            SET reminder_job_id=?
            WHERE id=?
            """,
            (job_id, booking_id),
        )
