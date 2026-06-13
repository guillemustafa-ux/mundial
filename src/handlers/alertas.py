from telegram import Update
from telegram.ext import ContextTypes


async def alertas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data["db"]
    user = update.effective_user

    row = await db.subscriber_get(user.id)
    currently_active = bool(row and row["active"])

    new_state = 0 if currently_active else 1
    await db.subscriber_upsert(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        active=new_state,
    )

    if new_state == 1:
        text = (
            "🔔 <b>Alertas activadas</b>\n\n"
            "Recibirás una notificación cuando Argentina anote un gol "
            "o finalice un partido.\n\n"
            "Para desactivarlas, enviá /alertas de nuevo."
        )
    else:
        text = (
            "🔕 <b>Alertas desactivadas</b>\n\n"
            "Ya no recibirás notificaciones de Argentina.\n"
            "Para reactivarlas, enviá /alertas."
        )

    await update.message.reply_text(text, parse_mode="HTML")
