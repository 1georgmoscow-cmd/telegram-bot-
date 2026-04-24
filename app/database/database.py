import sqlite3


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    # =========================
    # EXECUTE
    # =========================
    def execute(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur

    # =========================
    # FETCH ONE
    # =========================
    def fetchone(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()

    # =========================
    # FETCH ALL
    # =========================
    def fetchall(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    # =========================
    # INIT TABLES (НОВАЯ СХЕМА)
    # =========================
    def init(self):
        # реальные записи клиентов
        self.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                reminder_job_id TEXT
            )
        """)

        # рабочие дни мастера
        self.execute("""
            CREATE TABLE IF NOT EXISTS work_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL
            )
        """)

        # слоты времени
        self.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                UNIQUE(date, time)
            )
        """)
