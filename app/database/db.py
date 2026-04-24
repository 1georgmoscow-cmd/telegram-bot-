import sqlite3
from typing import Optional, List, Dict
from pathlib import Path


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    # =========================
    # INIT DATABASE
    # =========================
    def init(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT,
            is_active INTEGER DEFAULT 1,
            reminder_job_id TEXT
        )
        """)
        self.conn.commit()

    # =========================
    # CREATE BOOKING
    # =========================
    def create_booking(self, user_id: int, name: str, phone: str, date: str, time: str) -> Optional[int]:
        # проверка занятости слота
        self.cursor.execute(
            "SELECT id FROM bookings WHERE date=? AND time=? AND is_active=1",
            (date, time)
        )
        if self.cursor.fetchone():
            return None

        self.cursor.execute(
            """
            INSERT INTO bookings (user_id, name, phone, date, time)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, phone, date, time)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    # =========================
    # ACTIVE BOOKING USER
    # =========================
    def has_active_booking(self, user_id: int) -> bool:
        self.cursor.execute(
            "SELECT id FROM bookings WHERE user_id=? AND is_active=1",
            (user_id,)
        )
        return self.cursor.fetchone() is not None

    def get_active_booking(self, user_id: int) -> Optional[Dict]:
        self.cursor.execute(
            "SELECT * FROM bookings WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # =========================
    # SLOTS
    # =========================
    def get_available_slots(self, date_str: str) -> List[str]:
        all_slots = [
            "10:00", "11:00", "12:00", "13:00",
            "14:00", "15:00", "16:00", "17:00", "18:00"
        ]

        self.cursor.execute(
            "SELECT time FROM bookings WHERE date=? AND is_active=1",
            (date_str,)
        )
        taken = {row["time"] for row in self.cursor.fetchall()}

        return [t for t in all_slots if t not in taken]

    # =========================
    # WORK DAYS (упрощённо)
    # =========================
    def get_month_work_days(self, start_date: str, end_date: str):
        # пока просто возвращаем все дни (можешь потом усложнить)
        self.cursor.execute(
            "SELECT DISTINCT date FROM bookings"
        )
        return [row["date"] for row in self.cursor.fetchall()]

    # =========================
    # REMINDER SUPPORT
    # =========================
    def set_reminder_job_id(self, booking_id: int, job_id: Optional[str]):
        self.cursor.execute(
            "UPDATE bookings SET reminder_job_id=? WHERE id=?",
            (job_id, booking_id)
        )
        self.conn.commit()

    def get_active_bookings_for_restore(self):
        self.cursor.execute(
            """
            SELECT * FROM bookings
            WHERE is_active=1
            """
        )
        return [dict(row) for row in self.cursor.fetchall()]
