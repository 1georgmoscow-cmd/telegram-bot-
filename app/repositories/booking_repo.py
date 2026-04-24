from app.database.database import Database


class BookingRepository:
    def __init__(self, db: Database):
        self.db = db

    # =========================
    # CREATE BOOKING
    # =========================
    def create_booking(self, user_id, name, phone, date, time):
        # проверка занятого слота
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

    # =========================
    # CHECK ACTIVE BOOKING
    # =========================
    def has_active_booking(self, user_id):
        row = self.db.fetchone(
            "SELECT id FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )
        return bool(row)

    # =========================
    # GET ACTIVE BOOKING
    # =========================
    def get_active_booking(self, user_id):
        return self.db.fetchone(
            "SELECT * FROM bookings WHERE user_id=? AND active=1",
            (user_id,),
        )

    # =========================
    # GET BUSY SLOTS
    # =========================
    def get_busy_slots(self, date):
        rows = self.db.fetchall(
            "SELECT time FROM bookings WHERE date=? AND active=1",
            (date,),
        )
        return [row["time"] for row in rows]

    # =========================
    # GET FREE SLOTS
    # =========================
    def get_free_slots(self, date):
        all_slots = [
            "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00",
        ]

        busy = self.get_busy_slots(date)
        return [slot for slot in all_slots if slot not in busy]

    # =========================
    # GET WORK DAYS
    # =========================
    def get_month_work_days(self, start_date, end_date):
        rows = self.db.fetchall(
            """
            SELECT DISTINCT date
            FROM bookings
            WHERE date BETWEEN ? AND ?
            """,
            (start_date, end_date),
        )
        return [row["date"] for row in rows]

    # =========================
    # FOR SCHEDULER
    # =========================
    def get_active_bookings_for_restore(self):
        return self.db.fetchall(
            "SELECT * FROM bookings WHERE active=1"
        )

    # =========================
    # SET REMINDER ID
    # =========================
    def set_reminder_job_id(self, booking_id, job_id):
        self.db.execute(
            "UPDATE bookings SET reminder_job_id=? WHERE id=?",
            (job_id, booking_id),
        )