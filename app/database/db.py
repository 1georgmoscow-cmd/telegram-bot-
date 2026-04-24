import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    # =========================
    # CONNECT
    # =========================
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================
    # INIT DB
    # =========================
    def init(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS work_days (
                    date TEXT PRIMARY KEY,
                    is_closed INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS time_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(date, time)
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    reminder_job_id TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(date, time)
                );
                """
            )
            conn.commit()

    # =========================
    # WORK DAYS
    # =========================
    def add_work_day(self, date: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO work_days(date, is_closed)
                VALUES(?, 0)
                ON CONFLICT(date) DO UPDATE SET is_closed = 0
                """,
                (date,),
            )
            conn.commit()

    def close_day(self, date: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO work_days(date, is_closed)
                VALUES(?, 1)
                ON CONFLICT(date) DO UPDATE SET is_closed = 1
                """,
                (date,),
            )
            conn.commit()

    def get_month_work_days(self, start_date: str, end_date: str) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT date
                FROM work_days
                WHERE date BETWEEN ? AND ?
                  AND is_closed = 0
                ORDER BY date ASC
                """,
                (start_date, end_date),
            ).fetchall()

        return [r["date"] for r in rows]

    # =========================
    # MASTER SLOTS
    # =========================
    def add_slot(self, date: str, time: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO time_slots(date, time, is_active)
                VALUES(?, ?, 1)
                ON CONFLICT(date, time) DO UPDATE SET is_active = 1
                """,
                (date, time),
            )
            conn.commit()

    def delete_slot(self, date: str, time: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                UPDATE time_slots
                SET is_active = 0
                WHERE date = ? AND time = ?
                """,
                (date, time),
            )
            conn.commit()

    def get_master_slots(self, date: str) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT time
                FROM time_slots
                WHERE date = ?
                  AND is_active = 1
                ORDER BY time ASC
                """,
                (date,),
            ).fetchall()

        return [r["time"] for r in rows]

    # =========================
    # BOOKED SLOTS
    # =========================
    def get_booked_times(self, date: str) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT time
                FROM bookings
                WHERE date = ?
                  AND status = 'active'
                """,
                (date,),
            ).fetchall()

        return [r["time"] for r in rows]

    # =========================
    # AVAILABLE SLOTS (MAIN LOGIC)
    # =========================
    def get_available_slots(self, date: str) -> list[str]:
        master = self.get_master_slots(date)
        booked = set(self.get_booked_times(date))
        return [t for t in master if t not in booked]

    # =========================
    # BOOKING CREATE
    # =========================
    def create_booking(
        self,
        user_id: int,
        name: str,
        phone: str,
        date: str,
        time: str,
        reminder_job_id: str | None = None,
    ) -> int | None:

        with closing(self._connect()) as conn:

            existing = conn.execute(
                """
                SELECT 1 FROM bookings
                WHERE date = ? AND time = ? AND status = 'active'
                """,
                (date, time),
            ).fetchone()

            if existing:
                return None

            cursor = conn.execute(
                """
                INSERT INTO bookings (
                    user_id, name, phone,
                    date, time,
                    status,
                    reminder_job_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (
                    user_id,
                    name,
                    phone,
                    date,
                    time,
                    reminder_job_id,
                    datetime.utcnow().isoformat(),
                ),
            )

            conn.commit()
            return cursor.lastrowid

    # =========================
    # USER BOOKING
    # =========================
    def get_active_booking(self, user_id: int):
        with closing(self._connect()) as conn:
            row = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE user_id = ?
                  AND status = 'active'
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

        return dict(row) if row else None

    def has_active_booking(self, user_id: int) -> bool:
        return self.get_active_booking(user_id) is not None

    # =========================
    # CANCEL
    # =========================
    def cancel_booking_by_user(self, user_id: int):
        with closing(self._connect()) as conn:
            booking = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE user_id = ? AND status = 'active'
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            if not booking:
                return None

            conn.execute(
                """
                UPDATE bookings
                SET status = 'cancelled', reminder_job_id = NULL
                WHERE id = ?
                """,
                (booking["id"],),
            )

            conn.commit()
            return dict(booking)

    # =========================
    # RESTORE (FIXED - IMPORTANT)
    # =========================
    def get_active_bookings_for_restore(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM bookings
                WHERE status = 'active'
                ORDER BY date ASC, time ASC
                """
            ).fetchall()

        return [dict(r) for r in rows]

    # =========================
    # ADMIN VIEW
    # =========================
    def get_schedule_by_date(self, date: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT s.time,
                       b.id AS booking_id,
                       b.name,
                       b.phone,
                       b.user_id,
                       b.status
                FROM time_slots s
                LEFT JOIN bookings b
                  ON b.date = s.date
                 AND b.time = s.time
                 AND b.status = 'active'
                WHERE s.date = ?
                  AND s.is_active = 1
                ORDER BY s.time ASC
                """,
                (date,),
            ).fetchall()

        return [dict(r) for r in rows]
