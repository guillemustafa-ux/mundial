import logging
import httpx

logger = logging.getLogger(__name__)


class OddsClient:
    """API-Ninjas odds — free tier, no rate limit beyond monthly quota."""

    def __init__(self, api_key: str):
        self._key = api_key

    async def odds_for_match(self, home_team: str, away_team: str) -> dict | None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://api.api-ninjas.com/v1/odds",
                    headers={"X-Api-Key": self._key},
                    params={"sport": "soccer"},
                )
            if r.status_code != 200:
                logger.warning("api-ninjas odds %d: %s", r.status_code, r.text[:120])
                return None
            return self._find_event(r.json(), home_team, away_team)
        except Exception as exc:
            logger.warning("api-ninjas odds: %s", exc)
            return None

    @staticmethod
    def _find_event(events: list, home_team: str, away_team: str) -> dict | None:
        hl, al = home_team.lower(), away_team.lower()
        for event in events:
            ht = event.get("home_team", "").lower()
            at = event.get("away_team", "").lower()
            if (hl in ht or ht in hl) and (al in at or at in al):
                return event
        return None
