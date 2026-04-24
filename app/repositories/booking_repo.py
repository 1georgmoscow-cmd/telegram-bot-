import sqlite3
from datetime import datetime


class BookingRepository:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT 'active',
            reminder_job_id TEXT
        )
        """)

        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_slot
        ON bookings(date, time)
        WHERE status = 'active'
        """)

        self.conn.commit()

    # =========================
    # CREATE
    # =========================
    def create_booking(self, user_id, name, phone, date, time):
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
            INSERT INTO bookings (user_id, name, phone, date, time)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, phone, date, time))

            self.conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # слот уже занят
            return None

    # =========================
    # ACTIVE BOOKING
    # =========================
    def has_active_booking(self, user_id: int) -> bool:
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT 1 FROM bookings
        WHERE user_id = ? AND status = 'active'
        LIMIT 1
        """, (user_id,))

        return cursor.fetchone() is not None

    def get_active_booking(self, user_id: int):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT * FROM bookings
        WHERE user_id = ? AND status = 'active'
        LIMIT 1
        """, (user_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    # =========================
    # SLOTS
    # =========================
    def get_free_slots(self, date: str) -> list[str]:
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00",
        ]

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT time FROM bookings
        WHERE date = ? AND status = 'active'
        """, (date,))

        busy = {row["time"] for row in cursor.fetchall()}

        return [slot for slot in all_slots if slot not in busy]

    # =========================
    # WORK DAYS
    # =========================
    def get_month_work_days(self, start: str, end: str) -> list[str]:
        # пока просто все дни доступны (можешь потом сделать выходные)
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)

        days = []
        current = start_date

        while current <= end_date:
            days.append(current.date().isoformat())
            current += timedelta(days=1)

        return days

    # =========================
    # REMINDERS
    # =========================
    def set_reminder_job_id(self, booking_id: int, job_id: str | None):
        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE bookings
        SET reminder_job_id = ?
        WHERE id = ?
        """, (job_id, booking_id))

        self.conn.commit()

    def get_active_bookings_for_restore(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT * FROM bookings
        WHERE status = 'active'
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # =========================
    # CANCEL
    # =========================
    def cancel_booking(self, booking_id: int):
        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE bookings
        SET status = 'cancelled'
        WHERE id = ?
        """, (booking_id,))

        self.conn.commit()
