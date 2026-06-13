from typing import Any, Optional


# TTLs en segundos
TTL_LIVE = 120
TTL_TODAY = 43_200       # 12h
TTL_STANDINGS = 86_400   # 24h
TTL_ARGENTINA = 86_400   # 24h
TTL_TEAM = 21_600        # 6h
TTL_ODDS = 14_400        # 4h
TTL_STATIC = 604_800     # 7 días (equipos, estadios)


class CacheManager:
    def __init__(self, db):
        self._db = db

    async def get(self, key: str) -> Optional[Any]:
        return await self._db.cache_get(key)

    async def set(self, key: str, value: Any, ttl: int):
        await self._db.cache_set(key, value, ttl)

    async def is_stale(self, key: str) -> bool:
        return await self._db.cache_is_stale(key)

    async def evict_expired(self, pattern: str = "%"):
        await self._db.cache_evict_pattern(pattern)

    # ── helpers con TTL preconfigurado ─────────────────────────────────────

    async def set_live(self, value: Any):
        await self.set("live:scores", value, TTL_LIVE)

    async def set_today(self, date_str: str, value: Any):
        await self.set(f"fixtures:today:{date_str}", value, TTL_TODAY)

    async def set_standings(self, value: Any):
        await self.set("standings:all", value, TTL_STANDINGS)

    async def set_argentina(self, value: Any):
        await self.set("argentina:next", value, TTL_ARGENTINA)

    async def set_team_fixtures(self, team_id: int, value: Any):
        await self.set(f"fixtures:team:{team_id}", value, TTL_TEAM)

    async def set_odds(self, fixture_id: int, value: Any):
        await self.set(f"odds:{fixture_id}", value, TTL_ODDS)

    async def set_teams_static(self, value: Any):
        await self.set("teams:all", value, TTL_STATIC)
