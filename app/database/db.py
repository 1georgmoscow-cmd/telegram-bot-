import sqlite3
from datetime import datetime, date, timedelta


class Database:
    def __init__(self, path: str = "bot.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    # =========================
    # TABLES
    # =========================
    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT 'active'
        )
        """)

        self.conn.commit()

    # =========================
    # BOOKING CHECKS
    # =========================
    def has_active_booking(self, user_id: int) -> bool:
        self.cursor.execute(
            "SELECT id FROM bookings WHERE user_id=? AND status='active'",
            (user_id,)
        )
        return self.cursor.fetchone() is not None

    def get_active_booking(self, user_id: int):
        self.cursor.execute(
            "SELECT date, time, name, phone FROM bookings WHERE user_id=? AND status='active'",
            (user_id,)
        )
        row = self.cursor.fetchone()

        if not row:
            return None

        return {
            "date": row[0],
            "time": row[1],
            "name": row[2],
            "phone": row[3],
        }

    # =========================
    # CREATE BOOKING
    # =========================
    def create_booking(self, user_id: int, name: str, phone: str, date_str: str, time_str: str):
        # защита от двойной записи
        self.cursor.execute(
            "SELECT id FROM bookings WHERE date=? AND time=? AND status='active'",
            (date_str, time_str)
        )

        if self.cursor.fetchone():
            return None

        self.cursor.execute("""
            INSERT INTO bookings (user_id, name, phone, date, time, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        """, (user_id, name, phone, date_str, time_str))

        self.conn.commit()
        return self.cursor.lastrowid

    # =========================
    # SLOTS (ВАЖНО 🔥)
    # =========================
    def get_free_slots(self, date_str: str):
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00"
        ]

        self.cursor.execute(
            "SELECT time FROM bookings WHERE date=? AND status='active'",
            (date_str,)
        )

        booked = {row[0] for row in self.cursor.fetchall()}

        return [s for s in all_slots if s not in booked]

    # =========================
    # WORK DAYS (упрощённо)
    # =========================
    def get_month_work_days(self, start_date: str, end_date: str):
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()

        days = []
        current = start

        while current <= end:
            # убираем только воскресенье (пример логики)
            if current.weekday() != 6:
                days.append(current.isoformat())

            current += timedelta(days=1)

        return days

    # =========================
    # RESTORE SCHEDULER FIX 🔥
    # =========================
    def get_active_bookings_for_restore(self):
        self.cursor.execute("""
            SELECT id, user_id, date, time, name, phone
            FROM bookings
            WHERE status='active'
        """)

        rows = self.cursor.fetchall()

        return [
            {
                "id": r[0],
                "user_id": r[1],
                "date": r[2],
                "time": r[3],
                "name": r[4],
                "phone": r[5],
            }
            for r in rows
        ]
