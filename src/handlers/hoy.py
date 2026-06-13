from telegram import Update
from telegram.ext import ContextTypes
from ..formatters.match import format_day_list
from ..formatters.timezone import today_str_art


async def hoy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = context.bot_data["cache"]
    date_str = today_str_art()
    key = f"fixtures:today:{date_str}"

    fixtures = await cache.get(key)
    if fixtures is None:
        await update.message.reply_text(
            "⏳ Cargando partidos de hoy... intentá en unos minutos.",
            parse_mode="HTML",
        )
        return

    text = format_day_list(fixtures, date_str)
    await update.message.reply_text(text, parse_mode="HTML")
