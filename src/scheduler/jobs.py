import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..api.budget import BudgetExceeded
from ..cache.manager import (
    TTL_TODAY, TTL_STANDINGS, TTL_ARGENTINA, TTL_LIVE, TTL_STATIC,
)
from ..formatters.timezone import today_str_art

logger = logging.getLogger(__name__)


def setup_scheduler(app) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    # ── budget reset midnight UTC ──────────────────────────────────────────
    @scheduler.scheduled_job(CronTrigger(hour=0, minute=0))
    async def reset_daily_budget():
        budget = app.bot_data["budget"]
        await budget.reset()

    # ── standings via worldcup26 (free) — 06:00 UTC ───────────────────────
    @scheduler.scheduled_job(CronTrigger(hour=6, minute=0))
    async def refresh_standings():
        cache = app.bot_data["cache"]
        wc26 = app.bot_data.get("wc26")
        football = app.bot_data.get("football")
        budget = app.bot_data["budget"]

        data = None
        if wc26:
            try:
                data = await wc26.groups()
                logger.info("standings: worldcup26 OK (%d grupos)", len(data))
            except Exception as exc:
                logger.warning("standings worldcup26 falló: %s", exc)

        if not data and football:
            try:
                await budget.consume(1)
                raw = await football.standings()
                data = raw.get("response", [])
                logger.info("standings: API-Football OK")
            except BudgetExceeded:
                logger.warning("standings: budget agotado")
            except Exception as exc:
                logger.warning("standings API-Football falló: %s", exc)

        if data:
            await cache.set_standings(data)

    # ── argentina fixtures via worldcup26 — 06:30 UTC ─────────────────────
    @scheduler.scheduled_job(CronTrigger(hour=6, minute=30))
    async def refresh_argentina():
        cache = app.bot_data["cache"]
        wc26 = app.bot_data.get("wc26")
        football = app.bot_data.get("football")
        budget = app.bot_data["budget"]

        next_fix = last_fix = group_row = None

        if wc26:
            try:
                all_games = await wc26.games_for_team("Argentina")
                now_ts = datetime.now(timezone.utc).timestamp()
                future = [g for g in all_games if _game_ts(g) > now_ts]
                past   = [g for g in all_games if _game_ts(g) <= now_ts]
                next_fix = sorted(future, key=_game_ts)[:5]
                last_fix = sorted(past,   key=_game_ts)[-5:]
                group_row = await wc26.standing_for_team("Argentina")
                logger.info("argentina: worldcup26 OK")
            except Exception as exc:
                logger.warning("argentina worldcup26 falló: %s", exc)

        if not next_fix and football:
            try:
                await budget.consume(2)
                raw_next = await football.fixtures_argentina_next()
                raw_last = await football.fixtures_argentina_last()
                next_fix = raw_next.get("response", [])
                last_fix = raw_last.get("response", [])
                logger.info("argentina: API-Football OK")
            except BudgetExceeded:
                logger.warning("argentina: budget agotado")
            except Exception as exc:
                logger.warning("argentina API-Football falló: %s", exc)

        if next_fix is not None:
            await cache.set_argentina(next_fix)
        if last_fix is not None:
            await cache.set("argentina:last", last_fix, TTL_ARGENTINA)
        if group_row is not None:
            await cache.set("argentina:group", group_row, TTL_STANDINGS)

    # ── fixtures today via worldcup26 — 09:00 and 15:00 UTC ──────────────
    @scheduler.scheduled_job(CronTrigger(hour="9,15", minute=0))
    async def refresh_today():
        cache = app.bot_data["cache"]
        wc26 = app.bot_data.get("wc26")
        football = app.bot_data.get("football")
        budget = app.bot_data["budget"]
        date_str = today_str_art()

        data = None
        if wc26:
            try:
                data = await wc26.games_today(date_str)
                logger.info("fixtures today: worldcup26 OK (%d partidos)", len(data))
            except Exception as exc:
                logger.warning("fixtures today worldcup26 falló: %s", exc)

        if not data and football:
            try:
                await budget.consume(1)
                raw = await football.fixtures_today(date_str)
                data = raw.get("response", [])
                logger.info("fixtures today: API-Football OK")
            except BudgetExceeded:
                logger.warning("fixtures today: budget agotado")
            except Exception as exc:
                logger.warning("fixtures today API-Football falló: %s", exc)

        if data is not None:
            await cache.set_today(date_str, data)

    # ── toggle live polling — cada 5min ───────────────────────────────────
    @scheduler.scheduled_job(IntervalTrigger(minutes=5))
    async def toggle_live_polling():
        cache = app.bot_data["cache"]
        cfg = app.bot_data["config"]
        date_str = today_str_art()
        fixtures = await cache.get(f"fixtures:today:{date_str}") or []

        now_ts = datetime.now(timezone.utc).timestamp()
        lead = cfg.live_poll_lead_minutes * 60

        has_active = any(
            _is_active_or_imminent(f, now_ts, lead) for f in fixtures
        )

        try:
            job = scheduler.get_job("live_score_poll")
            if job:
                if has_active:
                    job.resume()
                else:
                    job.pause()
        except Exception:
            pass

    # ── live score poll — interval 120s (starts paused) ──────────────────
    @scheduler.scheduled_job(
        IntervalTrigger(seconds=120),
        id="live_score_poll",
        next_run_time=None,  # start paused
    )
    async def live_score_poll():
        cache = app.bot_data["cache"]
        football = app.bot_data.get("football")
        budget = app.bot_data["budget"]
        dispatcher = app.bot_data.get("dispatcher")

        if not football:
            return
        try:
            await budget.consume(1)
            raw = await football.fixtures_live()
            fixtures = raw.get("response", [])
            await cache.set_live(fixtures)
            if dispatcher:
                await dispatcher.process(fixtures)
        except BudgetExceeded:
            logger.warning("live_score_poll: budget agotado — pausando")
            scheduler.get_job("live_score_poll").pause()
        except Exception as exc:
            logger.error("live_score_poll error: %s", exc)

    # ── evict stale team fixtures — 03:00 UTC ─────────────────────────────
    @scheduler.scheduled_job(CronTrigger(hour=3, minute=0))
    async def evict_team_cache():
        cache = app.bot_data["cache"]
        await cache.evict_expired("fixtures:team:%")

    return scheduler


def _game_ts(game: dict) -> float:
    # API-Football: ISO date with timezone offset
    date = game.get("date") or game.get("datetime") or game.get("fixture", {}).get("date", "")
    if date:
        try:
            from ..formatters.timezone import parse_iso
            return parse_iso(date).timestamp()
        except Exception:
            pass
    # worldcup26: "MM/DD/YYYY HH:MM" local time — treat as UTC-6 (WC 2026 venues avg)
    local_date = game.get("local_date", "")
    if local_date:
        try:
            from datetime import timedelta, timezone as tz
            dt = datetime.strptime(local_date, "%m/%d/%Y %H:%M")
            return dt.replace(tzinfo=tz(timedelta(hours=-6))).timestamp()
        except Exception:
            pass
    return 0.0


def _is_active_or_imminent(fixture: dict, now_ts: float, lead_secs: int) -> bool:
    status_obj = fixture.get("fixture", {}).get("status", {})
    status = status_obj.get("short", fixture.get("status", ""))
    if isinstance(status, dict):
        status = status.get("short", "")
    # worldcup26 uses time_elapsed
    if not status:
        te = fixture.get("time_elapsed", "")
        status = te.upper() if te and te != "notstarted" else ""
    if status in ("1H", "HT", "2H", "ET", "PEN"):
        return True
    game_ts = _game_ts(fixture)
    return 0 < (game_ts - now_ts) <= lead_secs
