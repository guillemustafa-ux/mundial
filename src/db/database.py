import json
import time
from pathlib import Path
from typing import Any, Optional
import aiosqlite
from .schema import SCHEMA


class Database:
    def __init__(self, db_path: str):
        self._path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def init(self):
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    # ── cache ──────────────────────────────────────────────────────────────

    async def cache_get(self, key: str) -> Optional[Any]:
        async with self._conn.execute(
            "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return json.loads(row["value"])

    async def cache_set(self, key: str, value: Any, ttl: int):
        now = time.time()
        payload = json.dumps(value)
        await self._conn.execute(
            """INSERT INTO cache(key, value, fetched_at, expires_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET
                 value=excluded.value,
                 fetched_at=excluded.fetched_at,
                 expires_at=excluded.expires_at""",
            (key, payload, now, now + ttl),
        )
        await self._conn.commit()

    async def cache_is_stale(self, key: str) -> bool:
        async with self._conn.execute(
            "SELECT expires_at FROM cache WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return True
        return time.time() > row["expires_at"]

    async def cache_evict_pattern(self, pattern: str):
        await self._conn.execute(
            "DELETE FROM cache WHERE key LIKE ? AND expires_at < ?",
            (pattern, time.time()),
        )
        await self._conn.commit()

    # ── subscribers ────────────────────────────────────────────────────────

    async def subscriber_get(self, user_id: int) -> Optional[aiosqlite.Row]:
        async with self._conn.execute(
            "SELECT * FROM subscribers WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone()

    async def subscriber_upsert(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        active: int,
    ):
        now = time.time()
        await self._conn.execute(
            """INSERT INTO subscribers(user_id, username, first_name, active, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username,
                 first_name=excluded.first_name,
                 active=excluded.active""",
            (user_id, username, first_name, active, now),
        )
        await self._conn.commit()

    async def subscribers_active(self) -> list[aiosqlite.Row]:
        async with self._conn.execute(
            "SELECT * FROM subscribers WHERE active = 1"
        ) as cur:
            return await cur.fetchall()

    # ── alert_state ────────────────────────────────────────────────────────

    async def alert_state_get(self, match_id: int) -> Optional[aiosqlite.Row]:
        async with self._conn.execute(
            "SELECT * FROM alert_state WHERE match_id = ?", (match_id,)
        ) as cur:
            return await cur.fetchone()

    async def alert_state_upsert(
        self,
        match_id: int,
        home_score: int,
        away_score: int,
        status: str,
        home_team: str,
        away_team: str,
    ):
        await self._conn.execute(
            """INSERT INTO alert_state(match_id, home_score, away_score, status, home_team, away_team)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(match_id) DO UPDATE SET
                 home_score=excluded.home_score,
                 away_score=excluded.away_score,
                 status=excluded.status""",
            (match_id, home_score, away_score, status, home_team, away_team),
        )
        await self._conn.commit()

    async def alert_state_delete(self, match_id: int):
        await self._conn.execute(
            "DELETE FROM alert_state WHERE match_id = ?", (match_id,)
        )
        await self._conn.commit()

    # ── api_budget ─────────────────────────────────────────────────────────

    async def budget_get(self, date_str: str, limit: int) -> aiosqlite.Row:
        await self._conn.execute(
            "INSERT OR IGNORE INTO api_budget(date, used, limit_day) VALUES (?, 0, ?)",
            (date_str, limit),
        )
        await self._conn.commit()
        async with self._conn.execute(
            "SELECT used, limit_day FROM api_budget WHERE date = ?", (date_str,)
        ) as cur:
            return await cur.fetchone()

    async def budget_increment(self, date_str: str, n: int = 1):
        await self._conn.execute(
            "UPDATE api_budget SET used = used + ? WHERE date = ?", (n, date_str)
        )
        await self._conn.commit()

    async def budget_reset(self, date_str: str, limit: int):
        await self._conn.execute(
            """INSERT INTO api_budget(date, used, limit_day) VALUES (?, 0, ?)
               ON CONFLICT(date) DO UPDATE SET used=0, limit_day=excluded.limit_day""",
            (date_str, limit),
        )
        await self._conn.commit()
