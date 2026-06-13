from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚽ <b>Bot del Mundial 2026</b>\n\n"
        "Comandos disponibles:\n"
        "/hoy — Partidos de hoy\n"
        "/argentina — Próximo partido y posición de Argentina\n"
        "/grupos — Tabla de todas las zonas\n"
        "/fixture [equipo] — Fixture completo de un equipo\n"
        "/vivo — Marcadores en vivo\n"
        "/cuotas [local] vs [visitante] — Cuotas de apuestas\n"
        "/alertas — Activar/desactivar alertas de Argentina\n\n"
        "Mundial 2026 🇺🇸🇲🇽🇨🇦  |  48 selecciones  |  11 jun – 19 jul"
    )
    await update.message.reply_text(text, parse_mode="HTML")
