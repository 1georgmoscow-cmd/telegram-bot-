import sqlite3
from typing import Optional, List, Dict
from datetime import date


class Database:
    def __init__(self, path: str = "database.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    # =========================
    # INIT (ВАЖНО для твоей ошибки)
    # =========================
    def init(self):
        self.create_tables()

    def create_tables(self):
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

        self.conn.commit()

    # =========================
    # BOOKING CREATE
    # =========================
    def create_booking(self, user_id: int, name: str, phone: str, date_: str, time_: str):
        cursor = self.conn.cursor()

        # проверка на занятый слот
        cursor.execute(
            "SELECT id FROM bookings WHERE date=? AND time=? AND status='active'",
            (date_, time_)
        )
        if cursor.fetchone():
            return None

        cursor.execute("""
            INSERT INTO bookings (user_id, name, phone, date, time)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, phone, date_, time_))

        self.conn.commit()
        return cursor.lastrowid

    # =========================
    # ACTIVE BOOKING USER
    # =========================
    def has_active_booking(self, user_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM bookings WHERE user_id=? AND status='active' LIMIT 1",
            (user_id,)
        )
        return cursor.fetchone() is not None

    def get_active_booking(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM bookings WHERE user_id=? AND status='active' LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # =========================
    # SLOTS
    # =========================
    def get_available_slots(self, date_: str) -> List[str]:
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00"
        ]

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT time FROM bookings WHERE date=? AND status='active'",
            (date_,)
        )

        booked = {row["time"] for row in cursor.fetchall()}

        return [t for t in all_slots if t not in booked]

    # =========================
    # CALENDAR WORK DAYS (упрощённо)
    # =========================
    def get_month_work_days(self, start_date: str, end_date: str) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date FROM bookings
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))

        rows = cursor.fetchall()
        return [r["date"] for r in rows]

    # =========================
    # REMINDER RESTORE
    # =========================
    def get_active_bookings_for_restore(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM bookings
            WHERE status='active'
        """)
        return [dict(row) for row in cursor.fetchall()]

    def set_reminder_job_id(self, booking_id: int, job_id: Optional[str]):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE bookings
            SET reminder_job_id=?
            WHERE id=?
        """, (job_id, booking_id))

        self.conn.commit()
