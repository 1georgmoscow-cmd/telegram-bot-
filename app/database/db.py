import sqlite3
from typing import List, Optional, Dict
from datetime import datetime


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    # =========================
    # INIT DB
    # =========================
    def init(self):
        self.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT 'active',
            reminder_job_id TEXT
        );

        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            is_booked INTEGER DEFAULT 0
        );
        """)
        self.conn.commit()

    # =========================
    # BOOKINGS
    # =========================
    def create_booking(self, user_id: int, name: str, phone: str, date: str, time: str):
        # проверка занятости слота
        self.cursor.execute(
            "SELECT * FROM bookings WHERE date=? AND time=? AND status='active'",
            (date, time),
        )
        if self.cursor.fetchone():
            return None

        self.cursor.execute(
            """
            INSERT INTO bookings (user_id, name, phone, date, time, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            (user_id, name, phone, date, time),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def has_active_booking(self, user_id: int) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM bookings WHERE user_id=? AND status='active' LIMIT 1",
            (user_id,),
        )
        return self.cursor.fetchone() is not None

    def get_active_booking(self, user_id: int) -> Optional[Dict]:
        self.cursor.execute(
            "SELECT * FROM bookings WHERE user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # =========================
    # SLOTS
    # =========================
    def get_available_slots(self, date_str: str) -> List[str]:
        # дефолтные слоты (можешь менять)
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00"
        ]

        self.cursor.execute(
            "SELECT time FROM bookings WHERE date=? AND status='active'",
            (date_str,),
        )
        booked = {row["time"] for row in self.cursor.fetchall()}

        return [s for s in all_slots if s not in booked]

    # =========================
    # CALENDAR
    # =========================
    def get_month_work_days(self, start_date: str, end_date: str):
        self.cursor.execute(
            """
            SELECT DISTINCT date
            FROM bookings
            WHERE date BETWEEN ? AND ?
            """,
            (start_date, end_date),
        )
        return [row["date"] for row in self.cursor.fetchall()]

    # =========================
    # REMINDER RESTORE (ВАЖНО!)
    # =========================
    def get_active_bookings_for_restore(self):
        self.cursor.execute(
            """
            SELECT * FROM bookings
            WHERE status='active'
        """
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def set_reminder_job_id(self, booking_id: int, job_id: str | None):
        self.cursor.execute(
            """
            UPDATE bookings
            SET reminder_job_id=?
            WHERE id=?
            """,
            (job_id, booking_id),
        )
        self.conn.commit()
