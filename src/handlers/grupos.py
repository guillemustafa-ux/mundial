from telegram import Update
from telegram.ext import ContextTypes
from ..formatters.standings import format_all_groups


async def grupos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = context.bot_data["cache"]

    data = await cache.get("standings:all")
    if not data:
        await update.message.reply_text(
            "⏳ Cargando tablas... intentá en unos minutos.",
            parse_mode="HTML",
        )
        return

    msg1, msg2 = format_all_groups(data)
    await update.message.reply_text(f"<pre>{msg1}</pre>", parse_mode="HTML")
    await update.message.reply_text(f"<pre>{msg2}</pre>", parse_mode="HTML")
