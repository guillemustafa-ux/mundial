from telegram import Update
from telegram.ext import ContextTypes
from ..formatters.match import format_argentina_summary


async def argentina_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = context.bot_data["cache"]

    next_fixtures = await cache.get("argentina:next") or []
    last_fixtures = await cache.get("argentina:last") or []
    group_row     = await cache.get("argentina:group") or None

    text = format_argentina_summary(next_fixtures, last_fixtures, group_row)
    await update.message.reply_text(text, parse_mode="HTML")
