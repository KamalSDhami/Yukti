from __future__ import annotations

from pathlib import Path
from typing import Optional

import aiosqlite


class Database:
    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: Optional[aiosqlite.Connection] = None

    async def init(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_prefs (
                user_id INTEGER PRIMARY KEY,
                lang_code TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS disabled_channels (
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, channel_id)
            );
            """
        )
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lang_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                detected_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                character_count INTEGER NOT NULL
            );
            """
        )
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    async def get_user_lang(self, user_id: int) -> Optional[str]:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT lang_code FROM user_prefs WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else None

    async def set_user_lang(self, user_id: int, lang_code: str) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO user_prefs (user_id, lang_code, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                lang_code = excluded.lang_code,
                updated_at = datetime('now');
            """,
            (user_id, lang_code),
        )
        await self._conn.commit()

    async def is_channel_disabled(self, guild_id: int, channel_id: int) -> bool:
        assert self._conn is not None
        async with self._conn.execute(
            """
            SELECT 1 FROM disabled_channels
            WHERE guild_id = ? AND channel_id = ?
            """,
            (guild_id, channel_id),
        ) as cursor:
            row = await cursor.fetchone()
        return row is not None

    async def set_channel_disabled(
        self, guild_id: int, channel_id: int, disabled: bool
    ) -> None:
        assert self._conn is not None
        if disabled:
            await self._conn.execute(
                """
                INSERT OR IGNORE INTO disabled_channels (guild_id, channel_id)
                VALUES (?, ?)
                """,
                (guild_id, channel_id),
            )
        else:
            await self._conn.execute(
                """
                DELETE FROM disabled_channels
                WHERE guild_id = ? AND channel_id = ?
                """,
                (guild_id, channel_id),
            )
        await self._conn.commit()

    async def list_disabled_channels(self, guild_id: int) -> list[int]:
        assert self._conn is not None
        async with self._conn.execute(
            "SELECT channel_id FROM disabled_channels WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def log_language_detection(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        detected_language: str,
        target_language: str,
        character_count: int,
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO lang_logs (
                timestamp,
                guild_id,
                channel_id,
                user_id,
                detected_language,
                target_language,
                character_count
            ) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                channel_id,
                user_id,
                detected_language,
                target_language,
                character_count,
            ),
        )
        await self._conn.commit()

    async def get_lang_stats(self, guild_id: int, days: int = 7) -> list[tuple[str, int]]:
        assert self._conn is not None
        async with self._conn.execute(
            """
            SELECT detected_language, COUNT(*) AS count
            FROM lang_logs
            WHERE guild_id = ?
              AND timestamp >= datetime('now', ?)
            GROUP BY detected_language
            ORDER BY count DESC
            LIMIT 5
            """,
            (guild_id, f"-{days} days"),
        ) as cursor:
            rows = await cursor.fetchall()
        return [(row[0], row[1]) for row in rows]
