import logging
from telegram import Bot
from telegram.error import Forbidden

logger = logging.getLogger(__name__)


class AlertDispatcher:
    def __init__(self, bot: Bot, db):
        self._bot = bot
        self._db = db

    async def process(self, live_data: list):
        for fixture in live_data:
            # Normalize across API shapes
            teams = fixture.get("teams", {})
            home_name = teams.get("home", {}).get("name", fixture.get("home_team", ""))
            away_name = teams.get("away", {}).get("name", fixture.get("away_team", ""))

            is_argentina = (
                "argentina" in home_name.lower()
                or "argentina" in away_name.lower()
            )
            if not is_argentina:
                continue

            # Score
            goals = fixture.get("goals", {})
            h_score = goals.get("home", fixture.get("home_score")) or 0
            a_score = goals.get("away", fixture.get("away_score")) or 0

            # Status
            status_obj = fixture.get("fixture", {}).get("status", {})
            status = status_obj.get("short", fixture.get("status", ""))
            if isinstance(status, dict):
                status = status.get("short", "")

            fixture_id = (
                fixture.get("fixture", {}).get("id")
                or fixture.get("id")
                or hash(f"{home_name}{away_name}")
            )

            prev = await self._db.alert_state_get(fixture_id)

            if prev is None:
                # First time we see this match — seed state, no alert
                await self._db.alert_state_upsert(
                    fixture_id, h_score, a_score, status, home_name, away_name
                )
                continue

            prev_h = prev["home_score"]
            prev_a = prev["away_score"]
            prev_status = prev["status"]

            # Goal event
            if h_score > prev_h or a_score > prev_a:
                scorer_team = home_name if h_score > prev_h else away_name
                arg_score = h_score if "argentina" in home_name.lower() else a_score
                opp_score = a_score if "argentina" in home_name.lower() else h_score
                elapsed = status_obj.get("elapsed", "") or ""
                msg = (
                    f"⚽ <b>GOL DE ARGENTINA</b>\n\n"
                    f"<b>{home_name} {h_score} - {a_score} {away_name}</b>\n"
                    f"Minuto {elapsed}'"
                )
                await self._broadcast(msg)

            # Full time
            if prev_status not in ("FT", "AET", "PEN_FT") and status in ("FT", "AET", "PEN_FT"):
                arg_score = h_score if "argentina" in home_name.lower() else a_score
                opp_score = a_score if "argentina" in home_name.lower() else h_score
                if arg_score > opp_score:
                    result_emoji = "🏆 VICTORIA"
                elif arg_score == opp_score:
                    result_emoji = "🤝 EMPATE"
                else:
                    result_emoji = "😔 DERROTA"
                msg = (
                    f"🏁 <b>FINAL DEL PARTIDO</b>\n\n"
                    f"<b>{home_name} {h_score} - {a_score} {away_name}</b>\n"
                    f"{result_emoji} 🇦🇷"
                )
                await self._broadcast(msg)
                await self._db.alert_state_delete(fixture_id)
                continue

            await self._db.alert_state_upsert(
                fixture_id, h_score, a_score, status, home_name, away_name
            )

    async def _broadcast(self, text: str):
        subscribers = await self._db.subscribers_active()
        logger.info("Enviando alerta a %d suscriptores", len(subscribers))
        for sub in subscribers:
            try:
                await self._bot.send_message(
                    chat_id=sub["user_id"],
                    text=text,
                    parse_mode="HTML",
                )
            except Forbidden:
                logger.warning("Usuario %d bloqueó el bot — desactivando", sub["user_id"])
                await self._db.subscriber_upsert(
                    sub["user_id"], sub["username"], sub["first_name"], active=0
                )
            except Exception as exc:
                logger.error("Error enviando a %d: %s", sub["user_id"], exc)
