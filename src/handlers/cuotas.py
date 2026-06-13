from telegram import Update
from telegram.ext import ContextTypes
from ..formatters.match import format_odds


async def cuotas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.bot_data["config"]
    if not cfg.odds_enabled:
        await update.message.reply_text(
            "Las cuotas de apuestas no están habilitadas en este bot.",
            parse_mode="HTML",
        )
        return

    args = context.args
    if not args or "vs" not in " ".join(args).lower():
        await update.message.reply_text(
            "Uso: /cuotas [local] vs [visitante]\n"
            "Ejemplo: /cuotas argentina vs france",
            parse_mode="HTML",
        )
        return

    raw = " ".join(args)
    parts = raw.lower().split("vs", 1)
    home_team = parts[0].strip().title()
    away_team = parts[1].strip().title()

    cache = context.bot_data["cache"]
    # Try to find fixture_id in today's cache for keying odds
    today_key = None
    fixtures_today = await cache.get(f"fixtures:today:{_today()}")
    fixture_id = None
    if fixtures_today:
        for f in fixtures_today:
            h = f.get("teams", {}).get("home", {}).get("name", f.get("home_team", ""))
            a = f.get("teams", {}).get("away", {}).get("name", f.get("away_team", ""))
            if home_team.lower() in h.lower() or away_team.lower() in a.lower():
                fixture_id = f.get("fixture", {}).get("id") or f.get("id")
                break

    cache_key = f"odds:{fixture_id}" if fixture_id else f"odds:{home_team}:{away_team}"
    event = await cache.get(cache_key)

    if event is None:
        odds_client = context.bot_data.get("odds")
        if odds_client:
            try:
                event = await odds_client.odds_for_match(home_team, away_team)
                if event:
                    await cache.set_odds(fixture_id or 0, event)
            except Exception as exc:
                await update.message.reply_text(f"Error al obtener cuotas: {exc}")
                return

    if not event:
        await update.message.reply_text(
            f"No se encontraron cuotas para <b>{home_team} vs {away_team}</b>.",
            parse_mode="HTML",
        )
        return

    text = format_odds(event)
    await update.message.reply_text(f"<pre>{text}</pre>", parse_mode="HTML")


def _today() -> str:
    from ..formatters.timezone import today_str_art
    return today_str_art()
