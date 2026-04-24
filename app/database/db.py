import aiosqlite
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    # ---------------- INIT ----------------

    async def init(self):
        """Создание подключения и таблиц"""
        self.conn = await aiosqlite.connect(self.db_path)

        await self.conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    # ---------------- BOOKINGS ----------------

    async def add_booking(self, user_id: int, time: str) -> int:
        """Создать запись"""
        cursor = await self.conn.execute(
            """
            INSERT INTO bookings (user_id, time, status)
            VALUES (?, ?, 'active')
            """,
            (user_id, time)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_user_bookings(self, user_id: int) -> List[tuple]:
        """Все записи пользователя"""
        cursor = await self.conn.execute(
            """
            SELECT id, time, status
            FROM bookings
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,)
        )
        return await cursor.fetchall()

    async def get_active_bookings_for_restore(self) -> List[Dict]:
        """
        НУЖНО ТЕБЕ ДЛЯ scheduler.restore_jobs_from_db()
        """
        cursor = await self.conn.execute(
            """
            SELECT id, user_id, time, status
            FROM bookings
            WHERE status = 'active'
            """
        )
        rows = await cursor.fetchall()

        return [
            {
                "id": row[0],
                "user_id": row[1],
                "time": row[2],
                "status": row[3],
            }
            for row in rows
        ]

    async def get_booking_by_id(self, booking_id: int) -> Optional[Dict]:
        cursor = await self.conn.execute(
            """
            SELECT id, user_id, time, status
            FROM bookings
            WHERE id = ?
            """,
            (booking_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "user_id": row[1],
            "time": row[2],
            "status": row[3],
        }

    async def cancel_booking(self, booking_id: int):
        """Отменить запись"""
        await self.conn.execute(
            """
            UPDATE bookings
            SET status = 'cancelled'
            WHERE id = ?
            """,
            (booking_id,)
        )
        await self.conn.commit()

    async def delete_booking(self, booking_id: int):
        """Удалить запись"""
        await self.conn.execute(
            "DELETE FROM bookings WHERE id = ?",
            (booking_id,)
        )
        await self.conn.commit()
