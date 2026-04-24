import sqlite3


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def init(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT,
            reminder_job_id TEXT
        )
        """)

        self.conn.commit()

    # =========================
    # CREATE
    # =========================
    def create_booking(self, user_id, name, phone, date, time):
        cursor = self.conn.cursor()

        # проверка занятости
        cursor.execute("""
        SELECT 1 FROM bookings
        WHERE date = ? AND time = ?
        """, (date, time))

        if cursor.fetchone():
            return None

        cursor.execute("""
        INSERT INTO bookings (user_id, name, phone, date, time)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, phone, date, time))

        self.conn.commit()
        return cursor.lastrowid

    # =========================
    # USER BOOKING
    # =========================
    def has_active_booking(self, user_id):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT 1 FROM bookings
        WHERE user_id = ?
        """, (user_id,))

        return cursor.fetchone() is not None

    def get_active_booking(self, user_id):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT * FROM bookings
        WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    # =========================
    # SLOTS
    # =========================
    def get_available_slots(self, date):
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00"
        ]

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT time FROM bookings
        WHERE date = ?
        """, (date,))

        taken = {row["time"] for row in cursor.fetchall()}

        return [t for t in all_slots if t not in taken]

    # =========================
    # CALENDAR
    # =========================
    def get_month_work_days(self, start_date, end_date):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT DISTINCT date FROM bookings
        WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))

        return [row["date"] for row in cursor.fetchall()]

    # =========================
    # REMINDERS
    # =========================
    def get_active_bookings_for_restore(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT * FROM bookings
        WHERE date IS NOT NULL
        """)

        return [dict(row) for row in cursor.fetchall()]

    def set_reminder_job_id(self, booking_id, job_id):
        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE bookings
        SET reminder_job_id = ?
        WHERE id = ?
        """, (job_id, booking_id))

        self.conn.commit()
