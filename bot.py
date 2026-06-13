import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import ApplicationBuilder, CommandHandler


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def _start_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), _HealthHandler).serve_forever()


threading.Thread(target=_start_health_server, daemon=True).start()

from config import load_config
from src.db.database import Database
from src.api.budget import BudgetTracker
from src.api.football import FootballClient
from src.api.worldcup26 import WorldCup26Client
from src.api.balldontlie import BallDontLieClient
from src.api.odds import OddsClient
from src.cache.manager import CacheManager, TTL_TODAY, TTL_STANDINGS, TTL_ARGENTINA
from src.scheduler.jobs import setup_scheduler
from src.alerts.dispatcher import AlertDispatcher
from src.formatters.timezone import today_str_art

from src.handlers.start import start_handler
from src.handlers.hoy import hoy_handler
from src.handlers.argentina import argentina_handler
from src.handlers.grupos import grupos_handler
from src.handlers.fixture import fixture_handler
from src.handlers.vivo import vivo_handler
from src.handlers.cuotas import cuotas_handler
from src.handlers.alertas import alertas_handler
from src.handlers.error import error_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def post_init(app):
    cfg = app.bot_data["config"]

    # DB
    db = Database(cfg.db_path)
    await db.init()
    app.bot_data["db"] = db

    # Cache
    cache = CacheManager(db)
    app.bot_data["cache"] = cache

    # Budget
    budget = BudgetTracker(db, cfg.daily_api_budget)
    app.bot_data["budget"] = budget

    # API clients
    football = FootballClient(
        cfg.football_api_key,
        cfg.football_base_url,
        cfg.wc_league_id,
        cfg.wc_season,
        cfg.argentina_team_id,
    )
    app.bot_data["football"] = football

    wc26 = WorldCup26Client(cfg.worldcup26_base_url)
    app.bot_data["wc26"] = wc26

    if cfg.balldontlie_enabled and cfg.balldontlie_api_key:
        app.bot_data["bdl"] = BallDontLieClient(cfg.balldontlie_api_key)
    else:
        app.bot_data["bdl"] = None

    if cfg.odds_enabled:
        app.bot_data["odds"] = OddsClient(cfg.odds_api_key)
    else:
        app.bot_data["odds"] = None

    # Alert dispatcher
    app.bot_data["dispatcher"] = AlertDispatcher(app.bot, db)

    # Scheduler
    scheduler = setup_scheduler(app)
    app.bot_data["scheduler"] = scheduler
    scheduler.start()
    logger.info("Scheduler iniciado")

    # Seed cache on startup
    await _seed_cache(app, cache, wc26, football, budget)


async def _seed_cache(app, cache, wc26, football, budget):
    """Warm up cache on bot start so first user commands don't return 'Cargando...'"""
    date_str = today_str_art()

    # Try worldcup26 first (free)
    seeded = {"standings": False, "argentina": False, "today": False}

    try:
        groups = await wc26.groups()
        if groups:
            await cache.set_standings(groups)
            seeded["standings"] = True
            logger.info("seed: standings OK (worldcup26)")
    except Exception as exc:
        logger.warning("seed standings worldcup26: %s", exc)

    try:
        today_games = await wc26.games_today(date_str)
        await cache.set_today(date_str, today_games)
        seeded["today"] = True
        logger.info("seed: fixtures today OK (worldcup26, %d partidos)", len(today_games))
    except Exception as exc:
        logger.warning("seed today worldcup26: %s", exc)

    try:
        all_games = await wc26.games_for_team("Argentina")
        from datetime import datetime, timezone
        now_ts = datetime.now(timezone.utc).timestamp()
        from src.scheduler.jobs import _game_ts
        future = sorted([g for g in all_games if _game_ts(g) > now_ts], key=_game_ts)
        past   = sorted([g for g in all_games if _game_ts(g) <= now_ts], key=_game_ts)
        await cache.set_argentina(future[:5])
        await cache.set("argentina:last", past[-5:], TTL_ARGENTINA)
        group_row = await wc26.standing_for_team("Argentina")
        if group_row:
            await cache.set("argentina:group", group_row, TTL_STANDINGS)
        seeded["argentina"] = True
        logger.info("seed: argentina OK (worldcup26)")
    except Exception as exc:
        logger.warning("seed argentina worldcup26: %s", exc)

    # Fallback to API-Football for anything not seeded
    if not seeded["standings"]:
        try:
            await budget.consume(1)
            raw = await football.standings()
            await cache.set_standings(raw.get("response", []))
            logger.info("seed: standings OK (API-Football)")
        except Exception as exc:
            logger.warning("seed standings API-Football: %s", exc)

    if not seeded["today"]:
        try:
            await budget.consume(1)
            raw = await football.fixtures_today(date_str)
            await cache.set_today(date_str, raw.get("response", []))
            logger.info("seed: fixtures today OK (API-Football)")
        except Exception as exc:
            logger.warning("seed today API-Football: %s", exc)

    if not seeded["argentina"]:
        try:
            await budget.consume(2)
            raw_next = await football.fixtures_argentina_next()
            raw_last = await football.fixtures_argentina_last()
            await cache.set_argentina(raw_next.get("response", []))
            await cache.set("argentina:last", raw_last.get("response", []), TTL_ARGENTINA)
            logger.info("seed: argentina OK (API-Football)")
        except Exception as exc:
            logger.warning("seed argentina API-Football: %s", exc)


async def post_shutdown(app):
    scheduler = app.bot_data.get("scheduler")
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    db = app.bot_data.get("db")
    if db:
        await db.close()
    logger.info("Bot apagado correctamente")


def main():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    cfg = load_config()

    app = (
        ApplicationBuilder()
        .token(cfg.telegram_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.bot_data["config"] = cfg

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("hoy", hoy_handler))
    app.add_handler(CommandHandler("argentina", argentina_handler))
    app.add_handler(CommandHandler("grupos", grupos_handler))
    app.add_handler(CommandHandler("fixture", fixture_handler))
    app.add_handler(CommandHandler("vivo", vivo_handler))
    app.add_handler(CommandHandler("cuotas", cuotas_handler))
    app.add_handler(CommandHandler("alertas", alertas_handler))
    app.add_error_handler(error_handler)

    logger.info("Bot Mundial 2026 iniciando...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
