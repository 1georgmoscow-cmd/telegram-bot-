import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self, path: str = "bot.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    # =========================
    # INIT DB
    # =========================
    def init(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    # =========================
    # CHECK ACTIVE BOOKING
    # =========================
    def has_active_booking(self, user_id: int) -> bool:
        self.cursor.execute("""
            SELECT id FROM bookings
            WHERE user_id=? AND status='active'
            LIMIT 1
        """, (user_id,))

        return self.cursor.fetchone() is not None

    # =========================
    # GET ACTIVE BOOKING
    # =========================
    def get_active_booking(self, user_id: int):
        self.cursor.execute("""
            SELECT date, time
            FROM bookings
            WHERE user_id=? AND status='active'
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))

        row = self.cursor.fetchone()

        if not row:
            return None

        return {
            "date": row[0],
            "time": row[1]
        }

    # =========================
    # CREATE BOOKING
    # =========================
    def create_booking(self, user_id: int, name: str, phone: str, date: str, time: str):
        # проверка занятости слота
        self.cursor.execute("""
            SELECT id FROM bookings
            WHERE date=? AND time=? AND status='active'
        """, (date, time))

        if self.cursor.fetchone():
            return None

        self.cursor.execute("""
            INSERT INTO bookings (user_id, name, phone, date, time)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, phone, date, time))

        self.conn.commit()
        return self.cursor.lastrowid

    # =========================
    # WORK DAYS (для календаря)
    # =========================
    def get_month_work_days(self, start: str, end: str):
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)

        days = []
        current = start_date

        while current <= end_date:
            if current.date() >= datetime.today().date():
                days.append(current.date().isoformat())
            current += timedelta(days=1)

        return days

    # =========================
    # FREE SLOTS
    # =========================
    def get_free_slots(self, date_str: str):
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00"
        ]

        self.cursor.execute("""
            SELECT time FROM bookings
            WHERE date=? AND status='active'
        """, (date_str,))

        booked = {row[0] for row in self.cursor.fetchall()}

        return [slot for slot in all_slots if slot not in booked]

    # =========================
    # CLOSE
    # =========================
    def close(self):
        self.conn.close()
