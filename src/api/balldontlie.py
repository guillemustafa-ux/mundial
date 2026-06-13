import logging
import httpx

logger = logging.getLogger(__name__)

_BASE = "https://api.balldontlie.io/fifa/worldcup/v1"


class BallDontLieClient:
    """BALLDONTLIE FIFA World Cup API — free tier covers matches, teams, standings."""

    def __init__(self, api_key: str):
        self._headers = {"Authorization": api_key}

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_BASE}{path}",
                headers=self._headers,
                params=params or {},
            )
            r.raise_for_status()
            return r.json()

    async def matches(self, **kwargs) -> dict:
        return await self._get("/matches", kwargs)

    async def teams(self) -> dict:
        return await self._get("/teams")

    async def standings(self) -> dict:
        return await self._get("/standings")

    async def team_match_stats(self, match_id: int) -> dict:
        return await self._get("/team_match_stats", {"match_id": match_id})

    async def match_momentum(self, match_id: int) -> dict:
        return await self._get("/match_momentum", {"match_id": match_id})

    async def lineups(self, match_id: int) -> dict:
        return await self._get("/lineups", {"match_id": match_id})

    async def players(self, team_id: int | None = None) -> dict:
        params = {"team_id": team_id} if team_id else {}
        return await self._get("/players", params)
