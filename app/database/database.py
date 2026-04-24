import sqlite3


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    # =========================
    # CORE
    # =========================
    def execute(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur

    def fetchone(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()

    def fetchall(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    # =========================
    # INIT DB
    # =========================
    def init(self):
        # bookings
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                phone TEXT,
                date TEXT,
                time TEXT,
                active INTEGER DEFAULT 1,
                reminder_job_id TEXT
            )
            """
        )

        # work days (админ добавляет рабочие дни)
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS work_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE
            )
            """
        )

        # slots (админ управление временем)
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                active INTEGER DEFAULT 1,
                UNIQUE(date, time)
            )
            """
        )
