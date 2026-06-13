import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    telegram_token: str
    football_api_key: str
    football_base_url: str
    wc_league_id: int
    wc_season: int
    argentina_team_id: int
    db_path: str
    display_tz: str
    daily_api_budget: int
    live_poll_interval: int
    live_poll_lead_minutes: int
    # worldcup26.ir — free, no key
    worldcup26_base_url: str
    # BALLDONTLIE
    balldontlie_api_key: str
    balldontlie_enabled: bool
    # Odds
    odds_enabled: bool
    odds_api_key: str             # api-ninjas.com
    admin_user_id: int | None


def load_config() -> Config:
    def _req(key: str) -> str:
        val = os.getenv(key, "").strip()
        if not val:
            raise RuntimeError(f"Variable de entorno requerida faltante: {key}")
        return val

    return Config(
        telegram_token=_req("TELEGRAM_TOKEN"),
        football_api_key=_req("FOOTBALL_API_KEY"),
        football_base_url=os.getenv("FOOTBALL_BASE_URL", "https://v3.football.api-sports.io"),
        wc_league_id=int(os.getenv("WC_LEAGUE_ID", "1")),
        wc_season=int(os.getenv("WC_SEASON", "2026")),
        argentina_team_id=int(os.getenv("ARGENTINA_TEAM_ID", "6")),
        db_path=os.getenv("DB_PATH", "./data/worldcup.db"),
        display_tz=os.getenv("DISPLAY_TZ", "America/Argentina/Buenos_Aires"),
        daily_api_budget=int(os.getenv("DAILY_API_BUDGET", "100")),
        live_poll_interval=int(os.getenv("LIVE_POLL_INTERVAL", "120")),
        live_poll_lead_minutes=int(os.getenv("LIVE_POLL_LEAD_MINUTES", "30")),
        worldcup26_base_url=os.getenv("WORLDCUP26_BASE_URL", "https://worldcup26.ir"),
        balldontlie_api_key=os.getenv("BALLDONTLIE_API_KEY", ""),
        balldontlie_enabled=os.getenv("BALLDONTLIE_ENABLED", "false").lower() == "true",
        odds_enabled=os.getenv("ODDS_ENABLED", "false").lower() == "true",
        odds_api_key=os.getenv("ODDS_API_KEY", ""),
        admin_user_id=int(os.getenv("ADMIN_USER_ID")) if os.getenv("ADMIN_USER_ID") else None,
    )


config = load_config()
