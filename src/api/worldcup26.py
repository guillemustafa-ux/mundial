import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class WorldCup26Client:
    """Free open API — worldcup26.ir — no key, no rate limit."""

    def __init__(self, base_url: str = "https://worldcup26.ir"):
        self._base = base_url.rstrip("/")

    async def _get(self, path: str) -> list | dict:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self._base}{path}")
            r.raise_for_status()
            return r.json()

    async def games(self) -> list:
        data = await self._get("/get/games")
        if isinstance(data, dict):
            return data.get("games", [])
        return data if isinstance(data, list) else []

    async def groups(self) -> list:
        """Returns groups enriched with team names via /get/teams lookup."""
        groups_raw = await self._get("/get/groups")
        groups = groups_raw.get("groups", []) if isinstance(groups_raw, dict) else groups_raw

        teams_raw = await self._get("/get/teams")
        teams_list = teams_raw.get("teams", []) if isinstance(teams_raw, dict) else teams_raw
        teams_by_id = {str(t.get("id", "")): t for t in teams_list}

        for group in groups:
            for t in group.get("teams", []):
                tid = str(t.get("team_id", ""))
                info = teams_by_id.get(tid, {})
                t["name"] = info.get("name_en", f"T{tid}")
        return groups

    async def teams(self) -> list:
        data = await self._get("/get/teams")
        if isinstance(data, dict):
            return data.get("teams", [])
        return data if isinstance(data, list) else []

    async def games_today(self, date_str: str) -> list:
        """Filter games by date. local_date format: 'MM/DD/YYYY HH:MM'."""
        all_games = await self.games()
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            prefix = dt.strftime("%m/%d/%Y")
        except Exception:
            prefix = date_str
        return [g for g in all_games if str(g.get("local_date", "")).startswith(prefix)]

    async def games_for_team(self, team_name: str) -> list:
        all_games = await self.games()
        name_lower = team_name.lower()
        return [
            g for g in all_games
            if name_lower in str(g.get("home_team_name_en", "")).lower()
            or name_lower in str(g.get("away_team_name_en", "")).lower()
        ]

    async def standing_for_team(self, team_name: str) -> dict | None:
        all_groups = await self.groups()
        name_lower = team_name.lower()
        for group in all_groups:
            for t in group.get("teams", []):
                if name_lower in str(t.get("name", "")).lower():
                    return {"group": group.get("name"), "standing": t}
        return None
