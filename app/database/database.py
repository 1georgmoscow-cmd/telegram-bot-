import sqlite3


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

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