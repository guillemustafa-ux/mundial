import logging
import httpx

logger = logging.getLogger(__name__)


class FootballClient:
    def __init__(self, api_key: str, base_url: str, league_id: int, season: int, argentina_team_id: int):
        self._headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io",
        }
        self._base = base_url.rstrip("/")
        self._league = league_id
        self._season = season
        self._arg_id = argentina_team_id

    async def _get(self, path: str, params: dict) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self._base}{path}",
                headers=self._headers,
                params=params,
            )
            r.raise_for_status()
            data = r.json()
            logger.debug("API %s %s → %d resultados", path, params, data.get("results", 0))
            return data

    async def fixtures_today(self, date_str: str) -> dict:
        return await self._get("/fixtures", {
            "league": self._league,
            "season": self._season,
            "date": date_str,
        })

    async def fixtures_live(self) -> dict:
        return await self._get("/fixtures", {
            "league": self._league,
            "live": "all",
        })

    async def fixtures_argentina_next(self) -> dict:
        return await self._get("/fixtures", {
            "league": self._league,
            "season": self._season,
            "team": self._arg_id,
            "next": 5,
        })

    async def fixtures_argentina_last(self) -> dict:
        return await self._get("/fixtures", {
            "league": self._league,
            "season": self._season,
            "team": self._arg_id,
            "last": 5,
        })

    async def standings(self) -> dict:
        return await self._get("/standings", {
            "league": self._league,
            "season": self._season,
        })

    async def team_fixtures(self, team_id: int) -> dict:
        return await self._get("/fixtures", {
            "league": self._league,
            "season": self._season,
            "team": team_id,
        })
