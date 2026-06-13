from telegram import Update
from telegram.ext import ContextTypes
from ..formatters.match import format_live


async def vivo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = context.bot_data["cache"]
    fixtures = await cache.get("live:scores") or []
    text = format_live(fixtures)
    await update.message.reply_text(text, parse_mode="HTML")
